"""Entidad de dominio. Nunca se devuelve tal cual por HTTP: las rutas usan esquemas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4


class EstadoAutorizacion(StrEnum):
    AUTORIZADA = "AUTORIZADA"
    ANULADA = "ANULADA"


@dataclass
class Autorizacion:
    sku: str
    unidades: int
    total: Decimal
    medio_pago: str
    reserva_id: str | None = None
    estado: EstadoAutorizacion = EstadoAutorizacion.AUTORIZADA
    autorizacion_id: str = field(default_factory=lambda: str(uuid4()))
    creada_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def anular(self) -> None:
        """Idempotente: anular dos veces deja el mismo estado."""
        self.estado = EstadoAutorizacion.ANULADA
