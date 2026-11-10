"""Resiliencia: si ms-inventario cae, ms-pagos responde 503 rápido, y nadie crea clientes HTTP mal."""
import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from resiliencia.escaner import problemas_en_codigo, problemas_en_servicios
from simuladores import pagos

RAIZ_REPO = Path(__file__).resolve().parents[2]
CUERPO = {"sku": "PAN-001", "unidades": 1, "medio_pago": "tarjeta"}


def inventario_apagado(request: httpx.Request) -> httpx.Response:
    """Transporte que simula un contenedor detenido: la conexión es rechazada."""
    raise httpx.ConnectError("Connection refused", request=request)


# ---------- 1. Con simulador (siempre corre) ----------
def test_pagos_responde_503_en_menos_de_4s_si_inventario_cae():
    app = pagos.crear_app(transporte=httpx.MockTransport(inventario_apagado))
    with TestClient(app) as cliente:
        inicio = time.perf_counter()
        r = cliente.post("/api/v1/autorizaciones", json=CUERPO)
        duracion = time.perf_counter() - inicio
    assert r.status_code == 503
    assert r.json()["detail"] == "ms-inventario no disponible"
    assert duracion < 4


# ---------- 2. Con contenedores reales (solo con Docker y URL_MS_PAGOS) ----------
@pytest.mark.resiliencia
def test_real_docker_compose_stop_inventario_da_503():
    url = os.environ.get("URL_MS_PAGOS")
    if not url or not shutil.which("docker"):
        pytest.skip("Requiere Docker y URL_MS_PAGOS (p. ej. http://localhost:8004) con la plataforma levantada")
    # Las réplicas se llaman ms-inventario-1/-2/-3: "ms-inventario" a secas no existe en compose
    replicas = os.environ.get("REPLICAS_INVENTARIO", "ms-inventario-1 ms-inventario-2 ms-inventario-3").split()
    subprocess.run(["docker", "compose", "stop", *replicas], cwd=RAIZ_REPO, check=True)
    try:
        inicio = time.perf_counter()
        r = httpx.post(f"{url}/api/v1/autorizaciones", json=CUERPO, timeout=10)
        duracion = time.perf_counter() - inicio
    finally:
        subprocess.run(["docker", "compose", "start", *replicas], cwd=RAIZ_REPO, check=True)
    assert r.status_code == 503
    assert r.json()["detail"] == "ms-inventario no disponible"
    assert duracion < 4


# ---------- 3. Revisión del código: AsyncClient con timeout y fuera de las rutas ----------
def test_escaner_detecta_cliente_por_peticion_y_sin_timeout():
    malo = (
        "@router.get('/x')\n"
        "async def ruta():\n"
        "    async with httpx.AsyncClient() as c:\n"
        "        return await c.get('http://otro')\n"
    )
    problemas = problemas_en_codigo(malo)
    assert any("por petición" in p for p in problemas)
    assert any("sin timeout" in p for p in problemas)


def test_escaner_acepta_cliente_en_lifespan_con_timeout():
    bueno = (
        "@asynccontextmanager\n"
        "async def lifespan(app):\n"
        "    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(2.0))\n"
        "    try:\n"
        "        yield\n"
        "    finally:\n"
        "        await app.state.http.aclose()\n"
    )
    assert problemas_en_codigo(bueno) == []


def test_ningun_servicio_del_repo_crea_async_client_mal():
    assert problemas_en_servicios(RAIZ_REPO) == []
