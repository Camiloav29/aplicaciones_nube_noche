"""Alias de inyección de dependencias con ``Annotated``."""

from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.config import Configuracion, get_configuracion


def obtener_http(request: Request) -> httpx.AsyncClient:
    """Devuelve el único cliente HTTP creado en el lifespan."""
    return request.app.state.http


ConfigDep = Annotated[Configuracion, Depends(get_configuracion)]
HttpDep = Annotated[httpx.AsyncClient, Depends(obtener_http)]
