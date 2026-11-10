"""Simulador de ms-inventario (A02): mismo contrato, datos en memoria."""
import uuid
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Configuración leída de variables INVENTARIO_*; un valor inválido impide arrancar
class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INVENTARIO_", extra="ignore")
    entorno: Literal["local", "dev", "test", "prod"] = "local"
    nivel_log: str = "INFO"
    reserva_maxima_unidades: int = Field(default=1000, ge=1)  # tope por reserva (>= 1)
    instancia: str = "ms-inventario-1"  # nombre de la réplica
    puerto: int = 8002


# Cuerpo JSON para dar de alta stock
class ExistenciaCrear(BaseModel):
    sku: str = Field(min_length=3, max_length=20)
    bodega: str = "principal"
    cantidad: int = Field(ge=0)


# Cuerpo JSON para reemplazar la cantidad de un SKU
class CantidadNueva(BaseModel):
    cantidad: int = Field(ge=0)


# Cuerpo JSON de una reserva (el tope máximo se valida con la configuración)
class ReservaCrear(BaseModel):
    unidades: int = Field(ge=1)


# Crea una app nueva con su propia memoria; si no recibe config, la lee del entorno
def crear_app(config: Configuracion | None = None) -> FastAPI:
    config = config or Configuracion()
    app = FastAPI(title="MercadoAndino - Inventario (simulador)", version="0.1.0")
    existencias: dict[str, dict] = {}  # sku -> {sku, bodega, cantidad, reservadas}
    reservas: dict[str, dict] = {}     # reserva_id -> {sku, unidades}

    # Devuelve la existencia del SKU o responde 404
    def buscar(sku: str) -> dict:
        if sku not in existencias:
            raise HTTPException(404, f"No existe el SKU {sku}")
        return existencias[sku]

    # Agrega el campo calculado disponible = cantidad - reservadas
    def vista(e: dict) -> dict:
        return {**e, "disponible": e["cantidad"] - e["reservadas"]}

    # Salud: lo usa el chequeo de Consul y el balanceador
    @app.get("/health")
    def health() -> dict:
        return {"estado": "activo", "servicio": "ms-inventario"}

    # Diagnóstico: muestra la configuración activa (sin secretos)
    @app.get("/diagnostico")
    def diagnostico() -> dict:
        return {"entorno": config.entorno, "nivel_log": config.nivel_log}

    # Dice qué réplica atendió la petición (sirve para medir el reparto)
    @app.get("/api/v1/diagnostico")
    def diagnostico_replica() -> dict:
        return {"instancia": config.instancia, "puerto": config.puerto}

    # Lista paginada de existencias
    @app.get("/api/v1/existencias")
    def listar(limite: int = Query(default=20, ge=1), desplazamiento: int = Query(default=0, ge=0)) -> list[dict]:
        return [vista(e) for e in existencias.values()][desplazamiento : desplazamiento + limite]

    # Consulta un SKU (404 si no existe)
    @app.get("/api/v1/existencias/{sku}")
    def obtener(sku: str) -> dict:
        return vista(buscar(sku))

    # Alta de stock: 201, o 409 si el SKU ya existe
    @app.post("/api/v1/existencias", status_code=201)
    def crear(entrada: ExistenciaCrear) -> dict:
        if entrada.sku in existencias:
            raise HTTPException(409, f"Ya existe el SKU {entrada.sku}")
        existencias[entrada.sku] = {**entrada.model_dump(), "reservadas": 0}
        return vista(existencias[entrada.sku])

    # Reemplaza la cantidad de un SKU existente
    @app.put("/api/v1/existencias/{sku}")
    def reemplazar(sku: str, entrada: CantidadNueva) -> dict:
        buscar(sku)["cantidad"] = entrada.cantidad
        return vista(existencias[sku])

    # Reserva unidades: 422 si supera el tope, 409 si no hay disponible, 201 si se reserva
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
        # Registra la reserva y descuenta del disponible
        e["reservadas"] += entrada.unidades
        reserva_id = str(uuid.uuid4())
        reservas[reserva_id] = {"sku": sku, "unidades": entrada.unidades}
        return {"reserva_id": reserva_id, "sku": sku, "unidades": entrada.unidades,
                "disponible": e["cantidad"] - e["reservadas"]}

    # Libera solo esa reserva (204) o 404 si no existe
    @app.delete("/api/v1/existencias/{sku}/reservas/{reserva_id}", status_code=204)
    def liberar(sku: str, reserva_id: str) -> None:
        reserva = reservas.pop(reserva_id, None)
        if reserva is None or reserva["sku"] != sku:
            raise HTTPException(404, f"No existe la reserva {reserva_id}")
        buscar(sku)["reservadas"] -= reserva["unidades"]

    return app
