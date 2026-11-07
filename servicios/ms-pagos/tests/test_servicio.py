"""La capa de servicio se prueba sin servidor ni HTTP: con dobles en memoria."""

from decimal import Decimal

import pytest

from app.errores import PagoRechazado, StockInsuficiente
from app.repositorios.memoria import AlmacenIdempotenciaMemoria, RepositorioAutorizacionesMemoria
from app.servicios.autorizaciones import ServicioAutorizaciones, SolicitudAutorizacion


class CatalogoFalso:
    async def precio(self, sku: str) -> Decimal:
        return Decimal("0.10")


class InventarioFalso:
    def __init__(self, disponible: int) -> None:
        self._disponible = disponible

    async def disponible(self, sku: str) -> int:
        return self._disponible


def servicio(disponible=10, maximo="100.00") -> ServicioAutorizaciones:
    return ServicioAutorizaciones(
        CatalogoFalso(),
        InventarioFalso(disponible),
        RepositorioAutorizacionesMemoria(),
        AlmacenIdempotenciaMemoria(),
        Decimal(maximo),
    )


async def test_total_con_decimal_exacto():
    # Con float, 0.1 * 3 = 0.30000000000000004
    r = await servicio().autorizar(SolicitudAutorizacion("ABC-1", 3, "pse"))
    assert r.autorizacion.total == Decimal("0.30")


async def test_stock_insuficiente():
    with pytest.raises(StockInsuficiente) as e:
        await servicio(disponible=2).autorizar(SolicitudAutorizacion("ABC-1", 3, "pse"))
    assert e.value.extra() == {"sku": "ABC-1", "solicitado": 3, "disponible": 2}


async def test_monto_igual_al_maximo_se_autoriza_y_mayor_se_rechaza():
    s = servicio(disponible=1000, maximo="1.00")
    assert (await s.autorizar(SolicitudAutorizacion("ABC-1", 10, "pse"))).autorizacion.total == Decimal("1.00")
    with pytest.raises(PagoRechazado):
        await s.autorizar(SolicitudAutorizacion("ABC-1", 11, "pse"))
