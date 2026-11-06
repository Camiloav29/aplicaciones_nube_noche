"""Rutas de salud y diagnóstico. Solo traducen HTTP."""

from fastapi import APIRouter

from app.dependencias import ConfigDep
from app.esquemas import DiagnosticoSalida, SaludSalida

NOMBRE_SERVICIO = "ms-pagos"

router = APIRouter(tags=["salud"])


@router.get("/health", response_model=SaludSalida)
async def salud() -> SaludSalida:
    return SaludSalida(estado="activo", servicio=NOMBRE_SERVICIO)


@router.get("/diagnostico", response_model=DiagnosticoSalida)
async def diagnostico(config: ConfigDep) -> DiagnosticoSalida:
    return DiagnosticoSalida(entorno=config.entorno, nivel_log=config.nivel_log)
