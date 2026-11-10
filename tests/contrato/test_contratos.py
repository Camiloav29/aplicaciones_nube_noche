"""Pruebas de contrato: cada servicio publica en /openapi.json las rutas y verbos acordados."""
import os

import httpx
import pytest

from contrato.verificador import cargar_contratos, incumplimientos
from simuladores import inventario, pagos

# Contratos de los 6 servicios, leídos una sola vez
CONTRATOS = cargar_contratos()


# ---------- 1. El detector funciona (siempre corre, no depende de nadie) ----------

# Contrato pequeño de ejemplo para probar el detector
CONTRATO_EJEMPLO = {"rutas": {"/health": {"get": 200}, "/api/v1/items": {"get": 200, "post": 201}}}


# Arma un /openapi.json mínimo para probar el detector
def openapi_falso(paths: dict, title: str = "Demo", version: str = "1.0") -> dict:
    return {"info": {"title": title, "version": version}, "paths": paths}


# Si el servicio publica todo lo acordado, el detector no reporta nada
def test_contrato_completo_no_reporta_nada():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}, "post": {}}})
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == []


# Si falta una ruta, el detector la reporta (criterio 1 de la ficha)
def test_detecta_ruta_faltante():
    publicado = openapi_falso({"/health": {"get": {}}})
    assert "falta la ruta /api/v1/items" in incumplimientos(CONTRATO_EJEMPLO, publicado)


# Si la ruta existe pero le falta un verbo (POST), también se reporta
def test_detecta_verbo_faltante():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}}})
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == ["falta POST /api/v1/items"]


# Si title o version están vacíos, se reportan
def test_detecta_title_y_version_vacios():
    publicado = openapi_falso({"/health": {"get": {}}, "/api/v1/items": {"get": {}, "post": {}}}, "", "")
    assert incumplimientos(CONTRATO_EJEMPLO, publicado) == ["falta info.title", "falta info.version"]


# contratos.yaml debe tener exactamente los seis servicios de las fichas A01-A06
def test_contratos_yaml_cubre_los_seis_servicios():
    esperados = {"ms-catalogo", "ms-inventario", "ms-pagos", "ms-pedidos", "bff-web", "ms-confiabilidad"}
    assert set(CONTRATOS) == esperados


# ---------- 2. Los simuladores respetan el contrato (si no, las pruebas de aceptación mentirían) ----------

# Compara el openapi de cada simulador con su contrato
@pytest.mark.parametrize(("nombre", "app"), [
    ("ms-inventario", inventario.crear_app()),
    ("ms-pagos", pagos.crear_app()),
])
def test_simulador_cumple_contrato(nombre, app):
    assert incumplimientos(CONTRATOS[nombre], app.openapi()) == []


# ---------- 3. Los servicios reales levantados cumplen el contrato (se saltan si no están arriba) ----------

# Por cada servicio: lee su /openapi.json real; si no responde, se salta con un mensaje claro
@pytest.mark.parametrize("nombre", sorted(CONTRATOS))
def test_servicio_real_cumple_contrato(nombre):
    variable = "URL_" + nombre.upper().replace("-", "_")  # ms-pagos -> URL_MS_PAGOS
    url = os.environ.get(variable, f"http://localhost:{CONTRATOS[nombre]['puerto']}")
    try:
        openapi = httpx.get(f"{url}/openapi.json", timeout=2.0).json()
    except httpx.HTTPError:
        pytest.skip(f"{nombre} no está levantado en {url} (defina {variable} o levántelo)")
    assert incumplimientos(CONTRATOS[nombre], openapi) == []
