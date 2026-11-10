"""Rutas de salud y diagnóstico."""
# Importa la clase para agrupar endpoints y modularizar las rutas de la API
from fastapi import APIRouter

# Importa la dependencia personalizada que inyecta la configuración
from app.dependencias import ConfigDep

# Instancia el enrutador asociando las rutas a la categoría "salud"
router = APIRouter(tags=["salud"])


@router.get("/health")
def health() -> dict:
    # Endpoint público de estado que confirma que la aplicación responde peticiones
    return {"estado": "activo", "servicio": "ms-confiabilidad"}


@router.get("/diagnostico")
def diagnostico(config: ConfigDep) -> dict:
    # Endpoint de inspección que retorna los parámetros de entorno inyectados en runtime
    return {
        "entorno": config.entorno,
        "nivel_log": config.nivel_log,
        "docs_habilitada": config.docs_habilitada,
        "minutos_mes_defecto": config.minutos_mes_defecto,
        "decimales_porcentaje": config.decimales_porcentaje,
    }