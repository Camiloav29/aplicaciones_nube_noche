"""Pruebas del contrato HTTP: rutas, 422 por rangos, formula y manejador único."""
import pytest
from fastapi.testclient import TestClient  # simula peticiones HTTP sin levantar uvicorn

from app.dependencias import get_servicio
from app.errores import ValorFueraDeRango
from app.main import app

# Un "cliente falso" que habla directo con la app, como si fuera un navegador.
cliente = TestClient(app)


def test_health():
    r = cliente.get("/health")
    assert r.status_code == 200
    # Formato exigido por CONVENCIONES.md §4
    assert r.json() == {"estado": "activo", "servicio": "ms-confiabilidad"}


def test_diagnostico_muestra_configuracion():
    r = cliente.get("/diagnostico")
    assert r.status_code == 200
    # CONVENCIONES.md §4 exige al menos entorno y nivel_log
    assert {"entorno", "nivel_log"} <= r.json().keys()


# Cuerpos VÁLIDOS para cada endpoint POST: todos deben responder 200 con "formula".
CASOS_VALIDOS = [
    ("/api/v1/disponibilidad/serie", {"servicios": [{"nombre": "pagos", "disponibilidad": 0.999}]}),
    ("/api/v1/disponibilidad/paralelo", {"disponibilidad": 0.99, "replicas": 2}),
    ("/api/v1/mtbf/serie", {"mtbf_individual_horas": 2000, "servicios": 5}),
    ("/api/v1/presupuesto-error", {"slo": 0.999}),
    ("/api/v1/latencia/cola-larga", {"llamadas": 5}),
    ("/api/v1/latencia/compuesta", {"latencias_ms": [100, 200], "estrategia": "secuencial"}),
]


@pytest.mark.parametrize(("ruta", "cuerpo"), CASOS_VALIDOS)
def test_toda_respuesta_incluye_formula(ruta, cuerpo):
    # json=cuerpo convierte el diccionario a JSON y lo envía en el cuerpo del POST
    r = cliente.post(ruta, json=cuerpo)
    assert r.status_code == 200
    assert "formula" in r.json()


def test_mttr_por_parametros_de_url():
    # Es un GET: los datos van en la URL → ?mtbf_horas=720&mttr_horas=1
    r = cliente.get("/api/v1/disponibilidad/mttr", params={"mtbf_horas": 720, "mttr_horas": 1})
    assert r.status_code == 200
    assert r.json()["disponibilidad"] == pytest.approx(0.998613, abs=1e-6)
    assert r.json()["formula"] == "MTBF/(MTBF+MTTR)"


# Cuerpos INVÁLIDOS: cada uno rompe una regla de rango → todos deben dar 422.
CASOS_FUERA_DE_RANGO = [
    ("/api/v1/disponibilidad/serie", {"servicios": []}),                                   # lista vacía
    ("/api/v1/disponibilidad/serie", {"servicios": [{"nombre": "x", "disponibilidad": 0}]}),  # A = 0
    ("/api/v1/disponibilidad/paralelo", {"disponibilidad": 1.5, "replicas": 2}),             # A > 1
    ("/api/v1/disponibilidad/paralelo", {"disponibilidad": 0.99, "replicas": 0}),            # réplicas < 1
    ("/api/v1/mtbf/serie", {"mtbf_individual_horas": 2000, "servicios": 0}),                 # servicios < 1
    ("/api/v1/presupuesto-error", {"slo": 1.2}),                                             # SLO > 1
    ("/api/v1/latencia/cola-larga", {"llamadas": 5, "percentil": 1}),                        # evita dividir entre 0
    ("/api/v1/latencia/compuesta", {"latencias_ms": [], "estrategia": "secuencial"}),        # lista vacía
    ("/api/v1/latencia/compuesta", {"latencias_ms": [10], "estrategia": "aleatoria"}),       # estrategia inválida
]


@pytest.mark.parametrize(("ruta", "cuerpo"), CASOS_FUERA_DE_RANGO)
def test_valores_fuera_de_rango_responden_422(ruta, cuerpo):
    r = cliente.post(ruta, json=cuerpo)
    assert r.status_code == 422


# Un servicio FALSO que siempre lanza la excepción de dominio.
# Sirve para probar el manejador único, porque por HTTP Pydantic frena todo antes.
class ServicioQueFalla:
    def paralelo(self, *args):
        raise ValorFueraDeRango("replicas", 0, ">= 1")


def test_manejador_unico_traduce_valor_fuera_de_rango_a_422():
    # dependency_overrides: "cuando una ruta pida get_servicio, dale ESTO en su lugar".
    app.dependency_overrides[get_servicio] = lambda: ServicioQueFalla()
    try:
        r = cliente.post("/api/v1/disponibilidad/paralelo", json={"disponibilidad": 0.99, "replicas": 2})
    finally:
        # Se limpia SIEMPRE (incluso si algo falla), para no contaminar las otras pruebas.
        app.dependency_overrides.clear()
    assert r.status_code == 422
    assert "detail" in r.json()            # CONVENCIONES.md §6: todo error trae "detail"
    assert r.json()["campo"] == "replicas"  # y nuestro campo adicional