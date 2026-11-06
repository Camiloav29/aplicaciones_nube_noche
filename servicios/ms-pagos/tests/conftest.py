import pytest
from fastapi.testclient import TestClient

from app.config import get_configuracion


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
