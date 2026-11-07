"""Cliente de ms-inventario: solo le interesa el disponible de un SKU."""

import httpx

from app.clientes.base import obtener_json
from app.errores import DependenciaRespondioMal, ProductoNoEncontrado

SERVICIO = "ms-inventario"


class ClienteInventario:
    def __init__(self, http: httpx.AsyncClient, url_base: str) -> None:
        self._http = http
        self._url_base = url_base

    async def disponible(self, sku: str) -> int:
        """``GET {url_base}/existencias/{sku}`` → ``disponible``."""
        datos = await obtener_json(self._http, f"{self._url_base}/existencias/{sku}", SERVICIO)
        if datos is None:
            raise ProductoNoEncontrado(sku)
        try:
            return int(datos["disponible"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DependenciaRespondioMal(SERVICIO) from exc
