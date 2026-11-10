"""Fórmulas de confiabilidad.

Funciones puras: reciben números y devuelven números.
No saben nada de HTTP, ni de FastAPI, ni de configuración.
"""
import math


def disponibilidad_serie(disponibilidades: list[float]) -> float:
    """prod(Ai): en serie, TODOS deben funcionar a la vez."""
    return math.prod(disponibilidades)


def disponibilidad_paralelo(disponibilidad: float, replicas: int) -> float:
    """1-(1-A)^n: en paralelo, basta con que funcione UNA réplica."""
    return 1 - (1 - disponibilidad) ** replicas


def disponibilidad_por_mttr(mtbf_horas: float, mttr_horas: float) -> float:
    """MTBF/(MTBF+MTTR): fracción del tiempo en que el servicio está arriba."""
    return mtbf_horas / (mtbf_horas + mttr_horas)


def mtbf_serie(mtbf_individual_horas: float, servicios: int) -> float:
    """MTBF/n: con n servicios en serie, las fallas de todos se acumulan."""
    return mtbf_individual_horas / servicios


def presupuesto_error(slo: float) -> float:
    """1-SLO: fracción del tiempo que se nos permite fallar."""
    return 1 - slo


def minutos_caidos(disponibilidad: float, minutos_mes: int) -> float:
    """(1-A)*minutos_mes: cuántos minutos al mes está caído."""
    return (1 - disponibilidad) * minutos_mes


def probabilidad_evitar_cola(percentil: float, llamadas: int) -> float:
    """p^n: probabilidad de que NINGUNA de las n llamadas sea lenta."""
    return percentil ** llamadas


def una_de_cada(probabilidad_evitar: float) -> float:
    """1/(1-p^n): cada cuántas peticiones una sufre la cola lenta."""
    return 1 / (1 - probabilidad_evitar)


def latencia_compuesta(latencias_ms: list[float], estrategia: str) -> float:
    """Secuencial: una tras otra, se suman. Concurrente: a la vez, manda la más lenta."""
    if estrategia == "secuencial":
        return sum(latencias_ms)
    return max(latencias_ms)