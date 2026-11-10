import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.config import Configuracion, get_configuracion
from app.main import crear_app
from app.repositorios.memoria import RepositorioProductosMemoria


@pytest.fixture()
def client() -> TestClient:
    app = crear_app()
    app.state.repositorio = RepositorioProductosMemoria(cargar_semilla=True)
    return TestClient(app)


def test_salud_y_diagnostico(client: TestClient) -> None:
    r_salud = client.get("/health")
    assert r_salud.status_code == 200
    assert r_salud.json() == {"estado": "activo", "servicio": "ms-catalogo"}

    r_diag = client.get("/diagnostico")
    assert r_diag.status_code == 200
    assert "entorno" in r_diag.json()
    assert "nivel_log" in r_diag.json()


def test_crear_y_obtener_producto(client: TestClient) -> None:
    nuevo = {
        "sku": "ARR-001",
        "nombre": "Arroz Diana 1kg",
        "descripcion": "Arroz blanco seleccionado",
        "categoria": "despensa",
        "precio": "4800.00",
    }
    r_post = client.post("/api/v1/productos", json=nuevo)
    assert r_post.status_code == 201
    assert r_post.headers["Location"] == "/api/v1/productos/ARR-001"
    cuerpo = r_post.json()
    assert cuerpo["sku"] == "ARR-001"
    assert cuerpo["activo"] is True

    r_get = client.get("/api/v1/productos/ARR-001")
    assert r_get.status_code == 200
    assert r_get.json()["nombre"] == "Arroz Diana 1kg"


def test_crear_producto_duplicado_409(client: TestClient) -> None:
    repetido = {
        "sku": "CAF-001",
        "nombre": "Cafe duplicado",
        "descripcion": "Intento duplicado",
        "categoria": "bebidas",
        "precio": 38500.00,
    }
    r_post = client.post("/api/v1/productos", json=repetido)
    assert r_post.status_code == 409
    assert "detail" in r_post.json()


def test_producto_inexistente_404(client: TestClient) -> None:
    assert client.get("/api/v1/productos/ZZZ-999").status_code == 404
    assert client.delete("/api/v1/productos/ZZZ-999").status_code == 404
    r_put = client.put(
        "/api/v1/productos/ZZZ-999",
        json={"nombre": "No existe", "descripcion": "", "categoria": "otros", "precio": 1000.00},
    )
    assert r_put.status_code == 404


def test_reemplazar_y_eliminar_producto(client: TestClient) -> None:
    r_put = client.put(
        "/api/v1/productos/CAF-001",
        json={
            "nombre": "Café Huila Especial 500g",
            "descripcion": "Tostión media",
            "categoria": "bebidas",
            "precio": 41000.00,
        },
    )
    assert r_put.status_code == 200
    assert r_put.json()["precio"] == 41000.0

    r_del = client.delete("/api/v1/productos/CAF-001")
    assert r_del.status_code == 204
    assert client.get("/api/v1/productos/CAF-001").status_code == 404


def test_filtro_categoria_y_regla_limite_con_override(client: TestClient) -> None:
    r_cat = client.get("/api/v1/productos?categoria=bebidas")
    assert r_cat.status_code == 200
    assert len(r_cat.json()) == 2

    client.app.dependency_overrides[get_configuracion] = lambda: Configuracion(pagina_tamano_maximo=2)
    r_lim_ok = client.get("/api/v1/productos?limite=2")
    assert r_lim_ok.status_code == 200
    assert len(r_lim_ok.json()) == 2

    r_lim_mal = client.get("/api/v1/productos?limite=3")
    assert r_lim_mal.status_code == 422
    client.app.dependency_overrides.clear()


def test_configuracion_fallo_temprano() -> None:
    with pytest.raises(ValidationError):
        Configuracion(pagina_tamano_maximo=0)
    with pytest.raises(ValidationError):
        Configuracion(nivel_log="TRAZA")
