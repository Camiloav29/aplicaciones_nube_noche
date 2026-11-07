"""Sin simulaciones: ms-inventario apuntando a un puerto donde no escucha nadie.

Comprueba el requisito "con la dependencia caída, responde en menos de 4 s".
"""

import socket
import time

import httpx
from fastapi.testclient import TestClient


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_inventario_apagado_503_en_menos_de_4s(monkeypatch):
    puerto = puerto_libre()  # se cierra al salir: nadie escucha ahí
    monkeypatch.setenv("PAGOS_URL_INVENTARIO", f"http://127.0.0.1:{puerto}/api/v1")

    from app.dependencias import obtener_http
    from app.main import crear_app

    app = crear_app()

    # Catálogo responde (simulado); inventario usa red real hacia el puerto cerrado.
    real = httpx.AsyncHTTPTransport()

    async def mixto(request: httpx.Request) -> httpx.Response:
        if request.url.port == puerto:
            return await real.handle_async_request(request)
        return httpx.Response(200, json={"sku": "CAF-001", "precio": "38500.00"})

    http = httpx.AsyncClient(
        transport=httpx.MockTransport(mixto),
        timeout=httpx.Timeout(connect=2.0, read=3.0, write=2.0, pool=1.0),
    )
    app.dependency_overrides[obtener_http] = lambda: http

    with TestClient(app) as c:
        inicio = time.perf_counter()
        r = c.post(
            "/api/v1/autorizaciones",
            json={"sku": "CAF-001", "unidades": 1, "medio_pago": "pse"},
        )
        duracion = time.perf_counter() - inicio

    assert r.status_code == 503
    assert r.json() == {"detail": "ms-inventario no disponible"}
    assert duracion < 4
