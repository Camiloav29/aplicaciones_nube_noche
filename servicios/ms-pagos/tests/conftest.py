import json
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_configuracion
from app.dependencias import obtener_http

# Datos semilla de CONVENCIONES §9
PRECIOS = {"CAF-001": "38500.00", "PAN-001": "6200.00", "QUE-001": "16800.00"}
DISPONIBLE = {"CAF-001": 100, "PAN-001": 50, "QUE-001": 20}


def dependencias_sanas(request: httpx.Request) -> httpx.Response:
    """Simula ms-catalogo (puerto 8001) y ms-inventario (puerto 8002)."""
    sku = request.url.path.rsplit("/", 1)[-1]
    if request.url.port == 8001:
        if sku not in PRECIOS:
            return httpx.Response(404, json={"detail": f"No existe el producto con SKU {sku}"})
        return httpx.Response(200, json={"sku": sku, "precio": PRECIOS[sku]})
    if request.url.port == 8002:
        if sku not in DISPONIBLE:
            return httpx.Response(404, json={"detail": "no existe"})
        return httpx.Response(200, json={"sku": sku, "disponible": DISPONIBLE[sku]})
    return httpx.Response(500)


@pytest.fixture(autouse=True)
def limpiar_cache_configuracion():
    """Cada prueba lee el entorno desde cero."""
    get_configuracion.cache_clear()
    yield
    get_configuracion.cache_clear()


@pytest.fixture
def cliente():
    from app.main import crear_app

    with TestClient(crear_app()) as c:
        yield c


@pytest.fixture
def cliente_con(request):
    """Fábrica: TestClient cuyas dependencias responde ``manejador`` (httpx.MockTransport).

    Se reemplaza el cliente HTTP del lifespan con ``dependency_overrides``;
    el resto de la aplicación es la real.
    """
    from app.main import crear_app

    abiertos: list[TestClient] = []

    def _crear(manejador: Callable = dependencias_sanas) -> TestClient:
        app = crear_app()
        http_falso = httpx.AsyncClient(
            transport=httpx.MockTransport(manejador),
            timeout=httpx.Timeout(connect=2.0, read=3.0, write=2.0, pool=1.0),
        )
        app.dependency_overrides[obtener_http] = lambda: http_falso
        c = TestClient(app)
        c.__enter__()
        abiertos.append(c)
        return c

    yield _crear
    for c in abiertos:
        c.__exit__(None, None, None)


def cuerpo(sku="CAF-001", unidades=2, medio_pago="tarjeta", **extra) -> str:
    return json.dumps({"sku": sku, "unidades": unidades, "medio_pago": medio_pago, **extra})
