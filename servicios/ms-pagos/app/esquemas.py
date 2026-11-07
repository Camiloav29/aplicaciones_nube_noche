"""Contrato HTTP de ms-pagos. Los esquemas de entrada y de salida son distintos."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Internamente Decimal (sin errores de redondeo); en JSON sale como número.
Dinero = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class SaludSalida(BaseModel):
    estado: str
    servicio: str


class DiagnosticoSalida(BaseModel):
    """Solo valores no sensibles: nunca se exponen secretos."""

    entorno: str
    nivel_log: str


class AutorizacionCrear(BaseModel):
    """Entrada de ``POST /api/v1/autorizaciones``."""

    model_config = ConfigDict(extra="ignore")  # ley de Postel: tolerante con lo que recibe

    sku: str = Field(min_length=3, max_length=20, examples=["CAF-001"])
    unidades: int = Field(ge=1, le=1000, examples=[2])
    medio_pago: Literal["tarjeta", "pse", "efectivo"]
    reserva_id: str | None = Field(
        default=None,
        description="Si viene, ms-pedidos ya reservó: no se verifica el disponible.",
    )


class AutorizacionRespuesta(BaseModel):
    """Salida: nunca se devuelve la entidad de dominio."""

    autorizacion_id: str
    sku: str
    unidades: int
    total: Dinero
    medio_pago: str
    reserva_id: str | None
    estado: Literal["AUTORIZADA", "ANULADA"]
