"""Caso de uso: autorizar, consultar y anular pagos.

Esta capa no conoce HTTP: recibe datos simples, lanza excepciones de dominio
y depende de interfaces (``Protocol``), no de clases concretas. Por eso se
prueba con pytest sin levantar servidor.
"""

import asyncio
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

from app.dominio import Autorizacion
from app.errores import AutorizacionNoEncontrada, PagoRechazado, StockInsuficiente
from app.repositorios.base import AlmacenIdempotencia, RepositorioAutorizaciones

DOS_DECIMALES = Decimal("0.01")


class FuentePrecios(Protocol):
    async def precio(self, sku: str) -> Decimal: ...


class FuenteDisponible(Protocol):
    async def disponible(self, sku: str) -> int: ...


@dataclass(frozen=True)
class SolicitudAutorizacion:
    sku: str
    unidades: int
    medio_pago: str
    reserva_id: str | None = None


@dataclass(frozen=True)
class ResultadoAutorizacion:
    autorizacion: Autorizacion
    repetida: bool  # True si vino de la clave de idempotencia (no se repitió el efecto)


class ServicioAutorizaciones:
    def __init__(
        self,
        catalogo: FuentePrecios,
        inventario: FuenteDisponible,
        repositorio: RepositorioAutorizaciones,
        idempotencia: AlmacenIdempotencia,
        monto_maximo: Decimal,
    ) -> None:
        self._catalogo = catalogo
        self._inventario = inventario
        self._repo = repositorio
        self._idem = idempotencia
        self._monto_maximo = monto_maximo

    async def autorizar(
        self, solicitud: SolicitudAutorizacion, clave_idempotencia: str | None = None
    ) -> ResultadoAutorizacion:
        if clave_idempotencia is None:
            return ResultadoAutorizacion(await self._autorizar(solicitud), repetida=False)

        # El candado evita que dos reintentos simultáneos con la misma clave
        # pasen ambos la búsqueda y creen dos autorizaciones.
        async with self._idem.bloqueo(clave_idempotencia):
            previa_id = await self._idem.buscar(clave_idempotencia)
            if previa_id is not None:
                previa = await self._repo.obtener(previa_id)
                if previa is not None:
                    return ResultadoAutorizacion(previa, repetida=True)

            autorizacion = await self._autorizar(solicitud)
            await self._idem.registrar(clave_idempotencia, autorizacion.autorizacion_id)
            return ResultadoAutorizacion(autorizacion, repetida=False)

    async def _autorizar(self, solicitud: SolicitudAutorizacion) -> Autorizacion:
        precio, disponible = await self._consultar_dependencias(solicitud)

        # Regla 1: no se autoriza lo que no hay (solo si nadie reservó antes).
        if disponible is not None and disponible < solicitud.unidades:
            raise StockInsuficiente(solicitud.sku, solicitud.unidades, disponible)

        # Regla 2: total con Decimal y 2 decimales.
        total = (precio * solicitud.unidades).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

        # Regla 3: tope de monto configurable.
        if total > self._monto_maximo:
            raise PagoRechazado()

        autorizacion = Autorizacion(
            sku=solicitud.sku,
            unidades=solicitud.unidades,
            total=total,
            medio_pago=solicitud.medio_pago,
            reserva_id=solicitud.reserva_id,
        )
        await self._repo.guardar(autorizacion)
        return autorizacion

    async def _consultar_dependencias(
        self, solicitud: SolicitudAutorizacion
    ) -> tuple[Decimal, int | None]:
        """Precio y disponible en paralelo: la latencia es la de la más lenta, no la suma.

        Con ``reserva_id``, ms-pedidos ya reservó: solo se consulta el precio.
        """
        if solicitud.reserva_id is not None:
            return await self._catalogo.precio(solicitud.sku), None

        resultados = await asyncio.gather(
            self._catalogo.precio(solicitud.sku),
            self._inventario.disponible(solicitud.sku),
            return_exceptions=True,
        )
        # Si ambas fallan, se informa primero la de catálogo (orden determinista).
        for resultado in resultados:
            if isinstance(resultado, BaseException):
                raise resultado
        precio, disponible = resultados
        return precio, disponible

    async def obtener(self, autorizacion_id: str) -> Autorizacion:
        autorizacion = await self._repo.obtener(autorizacion_id)
        if autorizacion is None:
            raise AutorizacionNoEncontrada(autorizacion_id)
        return autorizacion

    async def anular(self, autorizacion_id: str) -> Autorizacion:
        autorizacion = await self.obtener(autorizacion_id)
        autorizacion.anular()
        await self._repo.guardar(autorizacion)
        return autorizacion
