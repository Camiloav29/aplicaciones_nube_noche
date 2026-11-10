"""Dependencias que FastAPI inyecta en las rutas."""
from typing import Annotated

from fastapi import Depends

from app.config import Configuracion, get_configuracion
from app.servicios.confiabilidad import ServicioConfiabilidad

# Alias que indica a FastAPI resolver e inyectar la configuración del sistema
ConfigDep = Annotated[Configuracion, Depends(get_configuracion)]


# Función fábrica que construye el servicio inyectando la configuración resuelta
def get_servicio(config: ConfigDep) -> ServicioConfiabilidad:
    return ServicioConfiabilidad(config)


# Alias reutilizable que inyecta directamente ServicioConfiabilidad en los endpoints HTTP
ServicioDep = Annotated[ServicioConfiabilidad, Depends(get_servicio)]