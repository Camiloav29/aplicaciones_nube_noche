"""Contrato HTTP de ms-pagos. Los esquemas de entrada y de salida son distintos."""

from pydantic import BaseModel


class SaludSalida(BaseModel):
    estado: str
    servicio: str


class DiagnosticoSalida(BaseModel):
    """Solo valores no sensibles: nunca se exponen secretos."""

    entorno: str
    nivel_log: str
