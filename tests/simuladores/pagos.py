"""Simulador de ms-pagos (A03): consulta inventario por HTTP y aplica idempotencia."""
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Precios fijos: simulan ms-catalogo para no depender de él
PRECIOS = {"CAF-001": 38_500, "PAN-001": 6_200, "ARR-001": 4_900}
MONTO_MAXIMO = 1_000_000


class AutorizacionCrear(BaseModel):
    """Cuerpo de la autorización según la ficha A03."""

    sku: str
    unidades: int = Field(ge=1, le=1000)
    medio_pago: Literal["tarjeta", "pse", "efectivo"]
    reserva_id: str | None = None


def crear_app(url_inventario: str = "http://ms-inventario:8002",
              transporte: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    """Crea la app; el transporte permite conectarla a otro simulador o simular una caída."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Un único cliente con timeout, creado en el lifespan y cerrado en el finally
        app.state.http = httpx.AsyncClient(base_url=url_inventario, transport=transporte,
                                           timeout=httpx.Timeout(2.0, connect=1.0))
        try:
            yield
        finally:
            await app.state.http.aclose()

    app = FastAPI(title="MercadoAndino - Pagos (simulador)", version="0.1.0", lifespan=lifespan)
    autorizaciones: dict[str, dict] = {}
    por_clave: dict[str, str] = {}

    async def disponible_en_inventario(http: httpx.AsyncClient, sku: str) -> int:
        """Pregunta el disponible y traduce las fallas de la dependencia a 404/502/503/504."""
        try:
            r = await http.get(f"/api/v1/existencias/{sku}")
        except httpx.ConnectError:
            raise HTTPException(503, "ms-inventario no disponible")
        except httpx.TimeoutException:
            raise HTTPException(504, "ms-inventario no respondio")
        if r.status_code == 404:
            raise HTTPException(404, f"No existe el SKU {sku}")
        if r.status_code >= 500:
            raise HTTPException(502, "ms-inventario respondio mal")
        return r.json()["disponible"]

    @app.get("/health")
    def health() -> dict:
        return {"estado": "activo", "servicio": "ms-pagos"}

    @app.get("/diagnostico")
    def diagnostico() -> dict:
        return {"entorno": "local", "nivel_log": "INFO"}

    @app.post("/api/v1/autorizaciones", status_code=201, response_model=None)
    async def autorizar(entrada: AutorizacionCrear, request: Request,
                        idempotency_key: Annotated[str | None, Header()] = None):
        # Mismo Idempotency-Key → misma respuesta, sin cobrar dos veces
        if idempotency_key and idempotency_key in por_clave:
            return autorizaciones[por_clave[idempotency_key]]
        if entrada.reserva_id is None:
            disponible = await disponible_en_inventario(request.app.state.http, entrada.sku)
            if entrada.unidades > disponible:
                return JSONResponse(status_code=409, content={
                    "detail": f"Stock insuficiente para {entrada.sku}", "sku": entrada.sku,
                    "solicitado": entrada.unidades, "disponible": disponible})
        total = PRECIOS.get(entrada.sku, 10_000) * entrada.unidades
        if total > MONTO_MAXIMO:
            return JSONResponse(status_code=402, content={"detail": "Pago rechazado", "estado": "RECHAZADA"})
        autorizacion = {"autorizacion_id": str(uuid.uuid4()), "sku": entrada.sku,
                        "unidades": entrada.unidades, "total": total, "estado": "AUTORIZADA"}
        autorizaciones[autorizacion["autorizacion_id"]] = autorizacion
        if idempotency_key:
            por_clave[idempotency_key] = autorizacion["autorizacion_id"]
        return autorizacion

    @app.get("/api/v1/autorizaciones/{autorizacion_id}")
    def obtener(autorizacion_id: str) -> dict:
        if autorizacion_id not in autorizaciones:
            raise HTTPException(404, f"No existe la autorizacion {autorizacion_id}")
        return autorizaciones[autorizacion_id]

    @app.put("/api/v1/autorizaciones/{autorizacion_id}/anulacion")
    def anular(autorizacion_id: str) -> dict:
        autorizacion = obtener(autorizacion_id)
        autorizacion["estado"] = "ANULADA"  # idempotente: anular dos veces deja ANULADA
        return autorizacion

    return app
