from fastapi import APIRouter
from app.dependencias import ConfigDep

router = APIRouter(tags=["salud"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"estado": "activo", "servicio": "ms-catalogo"}


@router.get("/diagnostico")
def diagnostico(config: ConfigDep) -> dict[str, object]:
    return {
        "entorno": config.entorno,
        "nivel_log": config.nivel_log,
        "tipo_repositorio": config.tipo_repositorio,
        "pagina_tamano_maximo": config.pagina_tamano_maximo,
    }
