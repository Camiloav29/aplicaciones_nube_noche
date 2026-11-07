"""Implementaciones en memoria (una por proceso; se pierden al reiniciar)."""

import asyncio
from collections import defaultdict

from app.dominio import Autorizacion


class RepositorioAutorizacionesMemoria:
    def __init__(self) -> None:
        self._datos: dict[str, Autorizacion] = {}

    async def guardar(self, autorizacion: Autorizacion) -> None:
        self._datos[autorizacion.autorizacion_id] = autorizacion

    async def obtener(self, autorizacion_id: str) -> Autorizacion | None:
        return self._datos.get(autorizacion_id)


class AlmacenIdempotenciaMemoria:
    def __init__(self) -> None:
        self._claves: dict[str, str] = {}
        self._bloqueos: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def buscar(self, clave: str) -> str | None:
        return self._claves.get(clave)

    async def registrar(self, clave: str, autorizacion_id: str) -> None:
        self._claves[clave] = autorizacion_id

    def bloqueo(self, clave: str) -> asyncio.Lock:
        return self._bloqueos[clave]
