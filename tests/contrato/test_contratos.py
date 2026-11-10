"""Pruebas de contrato: cada servicio publica en /openapi.json las rutas y verbos acordados."""
import os

import httpx
import pytest

from contrato.verificador import cargar_contratos, incumplimientos
from simuladores import inventario, pagos

CONTRATOS = cargar_contratos()


# ---------- 1. El detector funciona (siempre corre, no depende de nadie) ----------
CONTRATO_EJEMPLO = {"rutas": {"/health": {"get": 200}, "/api/v1/items": {"get": 200, "post": 201}}}


def openapi_falso(paths: dict, title: str = "Demo", version: str = "1.0") -> dict:
    """Arma un /openapi.json mínimo para probar el detector."""
    return {"info": {"title": title, "version": version}, "paths": paths}


def test_contrato_completo_no_reporta_nada():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}, "post": {}}})
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == []


def test_detecta_ruta_faltante():
    publicado = openapi_falso({"/health": {"get": {}}})
    assert "falta la ruta /api/v1/items" in incumplimientos(CONTRATO_EJEMPLO, publicado)


def test_detecta_verbo_faltante():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}}})
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == ["falta POST /api/v1/items"]


def test_detecta_title_y_version_vacios():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}, "post": {}}}, "", "")
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == ["falta info.title", "falta info.version"]


def test_contratos_yaml_cubre_los_seis_servicios():
    esperados = {"ms-catalogo", "ms-inventario", "ms-pagos", "ms-pedidos", "bff-web", "ms-confiabilidad"}
    assert set(CONTRATOS) == esperados


# ---------- 2. Los simuladores respetan el contrato (si no, las pruebas de aceptación mentirían) ----------
@pytest.mark.parametrize(("nombre", "app"), [
    ("ms-inventario", inventario.crear_app()),
    ("ms-pagos", pagos.crear_app()),
])
def test_simulador_cumple_contrato(nombre, app):
    assert incumplimientos(CONTRATOS[nombre], app.openapi()) == []


# ---------- 3. Los servicios reales levantados cumplen el contrato (se saltan si no están arriba) ----------
@pytest.mark.parametrize("nombre", sorted(CONTRATOS))
def test_servicio_real_cumple_contrato(nombre):
    variable = "URL_" + nombre.upper().replace("-", "_")
    url = os.environ.get(variable, f"http://localhost:{CONTRATOS[nombre]['puerto']}")
    try:
        openapi = httpx.get(f"{url}/openapi.json", timeout=2.0).json()
    except httpx.HTTPError:
        pytest.skip(f"{nombre} no está levantado en {url} (defina {variable} o levántelo)")
    assert incumplimientos(CONTRATOS[nombre], openapi) == []
