"""Cliente de ms-catalogo: solo le interesa el precio de un SKU."""

from decimal import Decimal, InvalidOperation

import httpx

from app.clientes.base import obtener_json
from app.errores import DependenciaRespondioMal, ProductoNoEncontrado

SERVICIO = "ms-catalogo"


class ClienteCatalogo:
    def __init__(self, http: httpx.AsyncClient, url_base: str) -> None:
        self._http = http
        self._url_base = url_base

    async def precio(self, sku: str) -> Decimal:
        """``GET {url_base}/productos/{sku}`` → ``precio`` como ``Decimal``."""
        datos = await obtener_json(self._http, f"{self._url_base}/productos/{sku}", SERVICIO)
        if datos is None:
            raise ProductoNoEncontrado(sku)
        try:
            # str() evita arrastrar errores de float (38500.1 → Decimal("38500.1")).
            return Decimal(str(datos["precio"]))
        except (KeyError, InvalidOperation) as exc:
            raise DependenciaRespondioMal(SERVICIO) from exc
