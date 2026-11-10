"""Aceptación semana 4 (laboratorio 4): réplicas registradas, reparto ponderado y tolerancia a una caída."""
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from simuladores import inventario
from simuladores.balanceador import Balanceador, Replica

PESOS = {"ms-inventario-1": 3, "ms-inventario-2": 2, "ms-inventario-3": 1}


@pytest.fixture
def balanceador() -> Balanceador:
    """Tres réplicas de inventario con pesos 3/2/1, como en docker-compose (puertos 8002/8012/8022)."""
    replicas = []
    for (nombre, peso), puerto in zip(PESOS.items(), (8002, 8012, 8022)):
        app = inventario.crear_app(inventario.Configuracion(instancia=nombre, puerto=puerto))
        replicas.append(Replica(nombre, peso, TestClient(app)))
    return Balanceador(replicas)


def repartir(b: Balanceador, peticiones: int) -> Counter:
    """Hace N peticiones y cuenta qué réplica atendió cada una."""
    return Counter(b.get("/api/v1/diagnostico").json()["instancia"] for _ in range(peticiones))


def test_tres_replicas_registradas_y_sanas(balanceador):
    assert len(balanceador.sanas()) == 3


def test_reparto_no_es_uniforme_si_los_pesos_difieren(balanceador):
    # Con pesos 3/2/1, en 12 peticiones el reparto es 6:4:2 (no 4:4:4)
    assert repartir(balanceador, 12) == {"ms-inventario-1": 6, "ms-inventario-2": 4, "ms-inventario-3": 2}


def test_al_detener_una_replica_el_consumidor_sigue_respondiendo_200(balanceador):
    balanceador.replicas[0].detenida = True
    respuestas = [balanceador.get("/api/v1/diagnostico") for _ in range(6)]
    assert all(r.status_code == 200 for r in respuestas)
    assert "ms-inventario-1" not in {r.json()["instancia"] for r in respuestas}
