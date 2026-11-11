import httpx
import pytest
from pydantic import ValidationError

from app.config import Configuracion


def test_health_responde_activo(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"estado": "activo", "servicio": "ms-pagos"}


def test_diagnostico_sin_secretos(cliente):
    r = cliente.get("/diagnostico")
    assert r.status_code == 200
    assert set(r.json()) == {"entorno", "nivel_log"}


def test_openapi_con_titulo_y_version(cliente):
    info = cliente.get("/openapi.json").json()["info"]
    assert info["title"] == "MercadoAndino - Pagos"
    assert info["version"]


def test_cliente_http_unico_con_cuatro_relojes(cliente):
    http = cliente.app.state.http
    assert isinstance(http, httpx.AsyncClient)
    assert http.timeout == httpx.Timeout(connect=2.0, read=3.0, write=2.0, pool=1.0)


def test_docs_deshabilitada_por_variable(monkeypatch):
    monkeypatch.setenv("PAGOS_DOCS_HABILITADA", "false")
    from fastapi.testclient import TestClient

    from app.main import crear_app

    with TestClient(crear_app()) as c:
        assert c.get("/docs").status_code == 404


def test_nivel_log_se_normaliza(monkeypatch):
    monkeypatch.setenv("PAGOS_NIVEL_LOG", "debug")
    assert Configuracion().nivel_log == "DEBUG"


def test_prod_apaga_docs(monkeypatch):
    monkeypatch.setenv("PAGOS_ENTORNO", "prod")
    assert Configuracion().docs_habilitada is False


@pytest.mark.parametrize(
    ("variable", "valor"),
    [
        ("PAGOS_NIVEL_LOG", "CHISME"),
        ("PAGOS_ENTORNO", "staging"),
        ("PAGOS_MONTO_MAXIMO", "0"),
    ],
)
def test_valor_invalido_impide_arranque(monkeypatch, variable, valor):
    monkeypatch.setenv(variable, valor)
    with pytest.raises(ValidationError):
        Configuracion()


def test_puerto_por_defecto_es_8004(monkeypatch):
    monkeypatch.delenv("PUERTO_SERVICIO", raising=False)
    monkeypatch.delenv("PAGOS_PUERTO", raising=False)
    assert Configuracion().puerto == 8004


def test_puerto_se_configura_por_entorno(monkeypatch):
    monkeypatch.setenv("PUERTO_SERVICIO", "8014")
    assert Configuracion().puerto == 8014


def test_puerto_invalido_impide_arranque(monkeypatch):
    monkeypatch.setenv("PUERTO_SERVICIO", "70000")
    with pytest.raises(ValidationError):
        Configuracion()
