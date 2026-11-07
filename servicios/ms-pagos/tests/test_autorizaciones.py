"""Pruebas del contrato HTTP con las dependencias simuladas por httpx.MockTransport."""

import asyncio
import time

import httpx

from tests.conftest import dependencias_sanas

URL = "/api/v1/autorizaciones"
VALIDA = {"sku": "CAF-001", "unidades": 2, "medio_pago": "tarjeta"}


# --- Caso feliz y reglas -------------------------------------------------------


def test_autorizacion_valida_201(cliente_con):
    r = cliente_con().post(URL, json=VALIDA)
    assert r.status_code == 201
    datos = r.json()
    assert datos["estado"] == "AUTORIZADA"
    assert datos["total"] == 77000.00  # 38500.00 * 2
    assert datos["sku"] == "CAF-001"
    assert r.headers["Location"] == f"{URL}/{datos['autorizacion_id']}"


def test_stock_insuficiente_409_con_unidades_reales(cliente_con):
    r = cliente_con().post(URL, json={**VALIDA, "sku": "QUE-001", "unidades": 21})
    assert r.status_code == 409
    assert r.json() == {
        "detail": "Stock insuficiente para QUE-001",
        "sku": "QUE-001",
        "solicitado": 21,
        "disponible": 20,
    }


def test_total_mayor_al_maximo_402(cliente_con, monkeypatch):
    monkeypatch.setenv("PAGOS_MONTO_MAXIMO", "50000")
    r = cliente_con().post(URL, json=VALIDA)  # 77000 > 50000
    assert r.status_code == 402
    assert r.json() == {"detail": "Pago rechazado", "estado": "RECHAZADA"}


def test_sku_inexistente_404(cliente_con):
    r = cliente_con().post(URL, json={**VALIDA, "sku": "ZZZ-999"})
    assert r.status_code == 404
    assert r.json()["detail"] == "No existe el producto con SKU ZZZ-999"


def test_validacion_422(cliente_con):
    c = cliente_con()
    assert c.post(URL, json={**VALIDA, "unidades": 0}).status_code == 422
    assert c.post(URL, json={**VALIDA, "unidades": 1001}).status_code == 422
    assert c.post(URL, json={**VALIDA, "medio_pago": "bitcoin"}).status_code == 422


def test_con_reserva_id_no_consulta_inventario(cliente_con):
    llamadas: list[int] = []

    def manejador(request: httpx.Request) -> httpx.Response:
        llamadas.append(request.url.port)
        return dependencias_sanas(request)

    # 25 unidades superan el disponible (20), pero ms-pedidos ya reservó: no da 409.
    r = cliente_con(manejador).post(
        URL, json={**VALIDA, "sku": "QUE-001", "unidades": 25, "reserva_id": "res-1"}
    )
    assert r.status_code == 201
    assert r.json()["reserva_id"] == "res-1"
    assert llamadas == [8001]


# --- Idempotencia ---------------------------------------------------------------


def test_misma_clave_devuelve_misma_autorizacion(cliente_con):
    llamadas: list[str] = []

    def manejador(request: httpx.Request) -> httpx.Response:
        llamadas.append(str(request.url))
        return dependencias_sanas(request)

    c = cliente_con(manejador)
    cabecera = {"Idempotency-Key": "pedido-123"}
    r1 = c.post(URL, json=VALIDA, headers=cabecera)
    r2 = c.post(URL, json=VALIDA, headers=cabecera)
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["autorizacion_id"] == r2.json()["autorizacion_id"]
    assert r2.headers["Idempotent-Replayed"] == "true"
    assert len(llamadas) == 2  # el reintento no repitió el efecto (ni llamó a nadie)


def test_claves_distintas_crean_autorizaciones_distintas(cliente_con):
    c = cliente_con()
    a = c.post(URL, json=VALIDA, headers={"Idempotency-Key": "a"}).json()
    b = c.post(URL, json=VALIDA, headers={"Idempotency-Key": "b"}).json()
    assert a["autorizacion_id"] != b["autorizacion_id"]


# --- GET y anulación ---------------------------------------------------------------


def test_get_y_anulacion_idempotente(cliente_con):
    c = cliente_con()
    creada = c.post(URL, json=VALIDA).json()
    id_ = creada["autorizacion_id"]

    assert c.get(f"{URL}/{id_}").json() == creada

    r1 = c.put(f"{URL}/{id_}/anulacion")
    r2 = c.put(f"{URL}/{id_}/anulacion")
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["estado"] == r2.json()["estado"] == "ANULADA"
    assert c.get(f"{URL}/{id_}").json()["estado"] == "ANULADA"


def test_get_y_anulacion_inexistente_404(cliente_con):
    c = cliente_con()
    assert c.get(f"{URL}/no-existe").status_code == 404
    assert c.put(f"{URL}/no-existe/anulacion").status_code == 404


# --- Fallos de dependencias ---------------------------------------------------------


def test_inventario_caido_503(cliente_con):
    def manejador(request: httpx.Request) -> httpx.Response:
        if request.url.port == 8002:
            raise httpx.ConnectError("Connection refused", request=request)
        return dependencias_sanas(request)

    r = cliente_con(manejador).post(URL, json=VALIDA)
    assert r.status_code == 503
    assert r.json() == {"detail": "ms-inventario no disponible"}


def test_catalogo_lento_504(cliente_con):
    def manejador(request: httpx.Request) -> httpx.Response:
        if request.url.port == 8001:
            raise httpx.ReadTimeout("timeout", request=request)
        return dependencias_sanas(request)

    r = cliente_con(manejador).post(URL, json=VALIDA)
    assert r.status_code == 504
    assert r.json() == {"detail": "ms-catalogo no respondio"}


def test_inventario_5xx_502(cliente_con):
    def manejador(request: httpx.Request) -> httpx.Response:
        if request.url.port == 8002:
            return httpx.Response(500, json={"detail": "boom"})
        return dependencias_sanas(request)

    r = cliente_con(manejador).post(URL, json=VALIDA)
    assert r.status_code == 502
    assert r.json() == {"detail": "ms-inventario respondio mal"}


def test_llamadas_en_paralelo_con_gather(cliente_con):
    """Cada dependencia tarda 0.3 s: en paralelo ~0.3 s; en serie serían 0.6 s."""

    async def lento(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)
        return dependencias_sanas(request)

    c = cliente_con(lento)
    inicio = time.perf_counter()
    r = c.post(URL, json=VALIDA)
    duracion = time.perf_counter() - inicio
    assert r.status_code == 201
    assert duracion < 0.5, f"tardó {duracion:.2f}s: ¿las llamadas van en serie?"
