"""Simulador de ms-inventario (A02): mismo contrato, datos en memoria."""
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Configuración con prefijo INVENTARIO_, igual que el servicio real."""

    model_config = SettingsConfigDict(env_prefix="INVENTARIO_", extra="ignore")
    entorno: Literal["local", "dev", "test", "prod"] = "local"
    nivel_log: str = "INFO"
    reserva_maxima_unidades: int = Field(default=1000, ge=1)
    instancia: str = "ms-inventario-1"
    puerto: int = 8002


class ExistenciaCrear(BaseModel):
    """Cuerpo para dar de alta stock."""

    sku: str = Field(min_length=3, max_length=20)
    bodega: str = "principal"
    cantidad: int = Field(ge=0)


class CantidadNueva(BaseModel):
    """Cuerpo para reemplazar la cantidad."""

    cantidad: int = Field(ge=0)


class ReservaCrear(BaseModel):
    """Cuerpo de una reserva (el tope se valida con la configuración)."""

    unidades: int = Field(ge=1)


def crear_app(config: Configuracion | None = None) -> FastAPI:
    """Crea una app nueva con su propia memoria; si no recibe config, la lee del entorno."""
    config = config or Configuracion()
    app = FastAPI(title="MercadoAndino - Inventario (simulador)", version="0.1.0")
    existencias: dict[str, dict] = {}
    reservas: dict[str, dict] = {}

    def buscar(sku: str) -> dict:
        """Devuelve la existencia o responde 404."""
        if sku not in existencias:
            raise HTTPException(404, f"No existe el SKU {sku}")
        return existencias[sku]

    def vista(e: dict) -> dict:
        """Agrega el campo calculado disponible = cantidad - reservadas."""
        return {**e, "disponible": e["cantidad"] - e["reservadas"]}

    @app.get("/health")
    def health() -> dict:
        return {"estado": "activo", "servicio": "ms-inventario"}

    @app.get("/diagnostico")
    def diagnostico() -> dict:
        return {"entorno": config.entorno, "nivel_log": config.nivel_log}

    @app.get("/api/v1/diagnostico")
    def diagnostico_replica() -> dict:
        return {"instancia": config.instancia, "puerto": config.puerto}

    @app.get("/api/v1/existencias")
    def listar(limite: int = Query(default=20, ge=1), desplazamiento: int = Query(default=0, ge=0)) -> list[dict]:
        return [vista(e) for e in existencias.values()][desplazamiento : desplazamiento + limite]

    @app.get("/api/v1/existencias/{sku}")
    def obtener(sku: str) -> dict:
        return vista(buscar(sku))

    @app.post("/api/v1/existencias", status_code=201)
    def crear(entrada: ExistenciaCrear) -> dict:
        if entrada.sku in existencias:
            raise HTTPException(409, f"Ya existe el SKU {entrada.sku}")
        existencias[entrada.sku] = {**entrada.model_dump(), "reservadas": 0}
        return vista(existencias[entrada.sku])

    @app.put("/api/v1/existencias/{sku}")
    def reemplazar(sku: str, entrada: CantidadNueva) -> dict:
        buscar(sku)["cantidad"] = entrada.cantidad
        return vista(existencias[sku])

    @app.post("/api/v1/existencias/{sku}/reservas", status_code=201, response_model=None)
    def reservar(sku: str, entrada: ReservaCrear):
        e = buscar(sku)
        if entrada.unidades > config.reserva_maxima_unidades:
            raise HTTPException(422, f"unidades supera el máximo de {config.reserva_maxima_unidades}")
        disponible = e["cantidad"] - e["reservadas"]
        if entrada.unidades > disponible:
            # 409 con los campos extra que pide CONVENCIONES.md §6
            return JSONResponse(
                status_code=409,
                content={"detail": f"Stock insuficiente para {sku}", "sku": sku,
                         "solicitado": entrada.unidades, "disponible": disponible},
            )
        e["reservadas"] += entrada.unidades
        reserva_id = str(uuid.uuid4())
        reservas[reserva_id] = {"sku": sku, "unidades": entrada.unidades}
        return {"reserva_id": reserva_id, "sku": sku, "unidades": entrada.unidades,
                "disponible": e["cantidad"] - e["reservadas"]}

    @app.delete("/api/v1/existencias/{sku}/reservas/{reserva_id}", status_code=204)
    def liberar(sku: str, reserva_id: str) -> None:
        reserva = reservas.pop(reserva_id, None)
        if reserva is None or reserva["sku"] != sku:
            raise HTTPException(404, f"No existe la reserva {reserva_id}")
        buscar(sku)["reservadas"] -= reserva["unidades"]

    return app
