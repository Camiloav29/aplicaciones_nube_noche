"""Fixtures compartidas: cada prueba usa el servicio real si se indica su URL, si no, el simulador."""
import os

import httpx
import pytest
from fastapi.testclient import TestClient

from simuladores import inventario, pagos


# True si el servicio responde /health en menos de 1 segundo
def servicio_arriba(url: str) -> bool:
    try:
        return httpx.get(f"{url}/health", timeout=1.0).status_code == 200
    except httpx.HTTPError:
        return False


# Si existe la variable (p. ej. URL_MS_INVENTARIO) devuelve un cliente al servicio real; si no responde, salta
def cliente_real(variable: str) -> httpx.Client | None:
    url = os.environ.get(variable)
    if url is None:
        return None  # sin variable → se usará el simulador
    if not servicio_arriba(url):
        pytest.skip(f"{variable}={url} no responde /health: levante el servicio")
    return httpx.Client(base_url=url, timeout=5.0)


# Simulador de inventario nuevo (memoria vacía) para cada prueba
@pytest.fixture
def app_inventario():
    return inventario.crear_app()


# Cliente de inventario: real con URL_MS_INVENTARIO, simulador si no
@pytest.fixture
def cliente_inventario(app_inventario):
    real = cliente_real("URL_MS_INVENTARIO")
    if real:
        yield real
        real.close()
    else:
        with TestClient(app_inventario) as cliente:
            yield cliente


# Cliente de pagos: real con URL_MS_PAGOS; si no, el simulador conectado en memoria al simulador de inventario
@pytest.fixture
def cliente_pagos(app_inventario):
    real = cliente_real("URL_MS_PAGOS")
    if real:
        yield real
        real.close()
    else:
        # ASGITransport: pagos le habla a inventario sin red, directo a su app
        app = pagos.crear_app(url_inventario="http://inventario",
                              transporte=httpx.ASGITransport(app=app_inventario))
        with TestClient(app) as cliente:
            yield cliente
