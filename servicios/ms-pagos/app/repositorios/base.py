"""Contratos de persistencia (``Protocol``: tipado estructural, sin herencia).

El servicio depende de estas interfaces, no de una implementación concreta.
Hoy se usan las de ``memoria.py``; mañana podría ser SQL o Redis sin tocar el servicio.
"""

import asyncio
from typing import Protocol

from app.dominio import Autorizacion


class RepositorioAutorizaciones(Protocol):
    async def guardar(self, autorizacion: Autorizacion) -> None: ...

    async def obtener(self, autorizacion_id: str) -> Autorizacion | None: ...


class AlmacenIdempotencia(Protocol):
    async def buscar(self, clave: str) -> str | None:
        """Devuelve el ``autorizacion_id`` ya creado con esa clave, o ``None``."""
        ...

    async def registrar(self, clave: str, autorizacion_id: str) -> None: ...

    def bloqueo(self, clave: str) -> asyncio.Lock:
        """Candado por clave: dos reintentos simultáneos no crean dos autorizaciones."""
        ...
