"""Vectores de prueba de la ficha A06.

Tolerancia de la ficha: 1e-6 en fracciones y 0.01 en minutos.
"""
import pytest  # framework de pruebas: encuentra y ejecuta las funciones test_*

from app.config import Configuracion
from app.servicios.confiabilidad import ServicioConfiabilidad


# Una "fixture" prepara algo que varias pruebas necesitan.
# Toda prueba que tenga un parámetro llamado "servicio" recibe
# automáticamente un ServicioConfiabilidad NUEVO (no se comparte entre pruebas).
@pytest.fixture
def servicio() -> ServicioConfiabilidad:
    # Inyección de dependencias: le paso la configuración explícita,
    # así la prueba NO depende de las variables de entorno de mi PC.
    return ServicioConfiabilidad(Configuracion(minutos_mes_defecto=43_200))


# parametrize = una sola función de prueba, varios casos.
# Primero van los NOMBRES de los parámetros y luego la lista de casos.
# pytest ejecuta test_serie una vez por cada tupla de la lista.
@pytest.mark.parametrize(
    ("disponibilidades", "total", "minutos"),
    [
        # 5 servicios al 99,9 % → 0.995009990005 y 215,57 min/mes
        ([0.999] * 5, 0.995009990005, 215.57),
        # gateway al 99,95 % + 4 servicios al 99,9 % → 0.995508 y 194,05 min/mes
        ([0.9995] + [0.999] * 4, 0.995508, 194.05),
    ],
)
def test_serie(servicio, disponibilidades, total, minutos):
    # Llamo al caso de uso (sin minutos_mes → usa los 43 200 de la configuración).
    r = servicio.serie(disponibilidades)
    # approx compara "casi igual": los decimales en binario nunca son exactos.
    # abs=1e-6 es la tolerancia que da la ficha para fracciones.
    assert r["disponibilidad_total"] == pytest.approx(total, abs=1e-6)
    # Para minutos, la ficha da una tolerancia de 0.01.
    assert r["indisponibilidad_minutos_mes"] == pytest.approx(minutos, abs=0.01)
    # La ficha exige que toda respuesta diga qué fórmula usó.
    assert r["formula"] == "prod(Ai)"


@pytest.mark.parametrize(
    ("disponibilidad", "replicas", "total", "minutos"),
    [
        # 2 réplicas al 99 % → 0.9999 y 4,32 min/mes
        (0.99, 2, 0.9999, 4.32),
        # 3 réplicas al 99 % → 0.999999 y 0,0432 min/mes (≈ 2,6 segundos)
        (0.99, 3, 0.999999, 0.0432),
    ],
)
def test_paralelo(servicio, disponibilidad, replicas, total, minutos):
    r = servicio.paralelo(disponibilidad, replicas)
    assert r["disponibilidad_total"] == pytest.approx(total, abs=1e-6)
    assert r["indisponibilidad_minutos_mes"] == pytest.approx(minutos, abs=0.01)
    assert r["formula"] == "1-(1-A)^n"


# Un solo caso: no hace falta parametrize.
def test_mtbf_serie(servicio):
    # MTBF individual 2000 h con 5 servicios en serie → 2000 / 5 = 400 h
    r = servicio.mtbf_serie(2000, 5)
    assert r["mtbf_sistema_horas"] == pytest.approx(400)
    # 400 h / 24 = 16,67 días
    assert r["equivale_dias"] == pytest.approx(16.67, abs=0.01)
    assert r["formula"] == "MTBF/n"


@pytest.mark.parametrize(
    ("slo", "fraccion", "minutos"),
    [
        # SLO 99,9 % → puedo fallar el 0,1 % del mes = 43,2 min
        (0.999, 0.001, 43.2),
        # SLO 99,99 % → solo 0,01 % = 4,32 min (cada 9 extra divide entre 10)
        (0.9999, 0.0001, 4.32),
    ],
)
def test_presupuesto_error(servicio, slo, fraccion, minutos):
    r = servicio.presupuesto_error(slo)
    assert r["presupuesto_fraccion"] == pytest.approx(fraccion, abs=1e-6)
    assert r["presupuesto_minutos"] == pytest.approx(minutos, abs=0.01)
    assert r["formula"] == "1-SLO"


def test_cola_larga(servicio):
    # Una página que hace 5 llamadas, cada una rápida el 99 % de las veces.
    # Probabilidad de que NINGUNA sea lenta: 0.99^5 ≈ 0.95099
    r = servicio.cola_larga(llamadas=5, percentil=0.99)
    assert r["probabilidad_evitar_cola"] == pytest.approx(0.95099, abs=1e-6)
    # 1 / (1 - 0.95099) ≈ 20,40 → 1 de cada ~20 usuarios sufre la latencia del p99
    assert r["una_de_cada"] == pytest.approx(20.40, abs=0.01)
    assert r["formula"] == "p^n"


def test_mttr(servicio):
    # Falla cada 720 h (un mes) y tarda 1 h en repararse → 720 / 721 ≈ 0.998613
    r = servicio.por_mttr(mtbf_horas=720, mttr_horas=1)
    assert r["disponibilidad"] == pytest.approx(0.998613, abs=1e-6)
    assert r["formula"] == "MTBF/(MTBF+MTTR)"


@pytest.mark.parametrize(
    ("estrategia", "total"),
    [
        # Secuencial: una llamada tras otra → se suman: 100 + 200 + 300 = 600
        ("secuencial", 600),
        # Concurrente: todas a la vez → manda la más lenta: max = 300
        ("concurrente", 300),
    ],
)
def test_latencia_compuesta(servicio, estrategia, total):
    r = servicio.latencia_compuesta([100, 200, 300], estrategia)
    # Aquí son enteros exactos, no hace falta approx.
    assert r["total_ms"] == total