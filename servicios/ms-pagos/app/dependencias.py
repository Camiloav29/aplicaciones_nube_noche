"""Alias de inyección de dependencias con ``Annotated``."""

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.clientes.catalogo import ClienteCatalogo
from app.clientes.inventario import ClienteInventario
from app.config import Configuracion, get_configuracion
from app.servicios.autorizaciones import ServicioAutorizaciones


def obtener_http(request: Request) -> httpx.AsyncClient:
    """Devuelve el único cliente HTTP creado en el lifespan (nunca uno por petición)."""
    return request.app.state.http


ConfigDep = Annotated[Configuracion, Depends(get_configuracion)]
HttpDep = Annotated[httpx.AsyncClient, Depends(obtener_http)]


def obtener_servicio(request: Request, http: HttpDep, config: ConfigDep) -> ServicioAutorizaciones:
    """Arma el caso de uso: los clientes reciben el cliente HTTP compartido y
    las URL salen de la configuración; los almacenes viven en ``app.state``."""
    return ServicioAutorizaciones(
        catalogo=ClienteCatalogo(http, config.url_catalogo),
        inventario=ClienteInventario(http, config.url_inventario),
        repositorio=request.app.state.repositorio,
        idempotencia=request.app.state.idempotencia,
        monto_maximo=config.monto_maximo,
    )


ServicioDep = Annotated[ServicioAutorizaciones, Depends(obtener_servicio)]
