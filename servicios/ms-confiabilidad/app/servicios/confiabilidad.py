"""Casos de uso de confiabilidad.

Valida reglas de negocio, completa valores por defecto y usa las fórmulas puras.
NO importa FastAPI: recibe datos de Python y devuelve diccionarios.
"""
from app.config import Configuracion
from app.dominio import calculos
from app.errores import ValorFueraDeRango

# Conjunto de estrategias de ejecución permitidas para el cálculo de latencia
ESTRATEGIAS = {"secuencial", "concurrente"}


class ServicioConfiabilidad:
    # Inicializa la capa de servicio inyectando la configuración de la aplicación
    def __init__(self, config: Configuracion) -> None:
        self._config = config

    # ---------- Ayudas privadas ----------

    # Valida que una probabilidad o porcentaje se encuentre en el rango (0, 1]
    @staticmethod
    def _validar_fraccion(campo: str, valor: float) -> None:
        if not 0 < valor <= 1:
            raise ValorFueraDeRango(campo, valor, "> 0 y <= 1")

    # Valida que un número cumpla con un valor límite mínimo permitido
    @staticmethod
    def _validar_minimo(campo: str, valor: float, minimo: float) -> None:
        if valor < minimo:
            raise ValorFueraDeRango(campo, valor, f">= {minimo}")

    # Devuelve los minutos del mes especificados o los asignados por defecto en la configuración
    def _minutos(self, minutos_mes: int | None) -> int:
        if minutos_mes is None:
            return self._config.minutos_mes_defecto
        self._validar_minimo("minutos_mes", minutos_mes, 1)
        return minutos_mes

    # Formatea una fracción decimal a una representación textual con porcentaje
    def _porcentaje(self, fraccion: float) -> str:
        decimales = self._config.decimales_porcentaje
        return f"{fraccion * 100:.{decimales}f} %"

    # ---------- Métodos de disponibilidad ----------

    # Valida y calcula la disponibilidad total de una arquitectura de servicios en serie
    def serie(self, disponibilidades: list[float], minutos_mes: int | None = None) -> dict:
        if not disponibilidades:
            raise ValorFueraDeRango("servicios", disponibilidades, "una lista con al menos un servicio")
        for a in disponibilidades:
            self._validar_fraccion("disponibilidad", a)
        total = calculos.disponibilidad_serie(disponibilidades)
        return {
            "disponibilidad_total": total,
            "porcentaje": self._porcentaje(total),
            "indisponibilidad_minutos_mes": calculos.minutos_caidos(total, self._minutos(minutos_mes)),
            "formula": "prod(Ai)",
        }

    # Valida y calcula la disponibilidad resultante para réplicas redundantes en paralelo
    def paralelo(self, disponibilidad: float, replicas: int, minutos_mes: int | None = None) -> dict:
        self._validar_fraccion("disponibilidad", disponibilidad)
        self._validar_minimo("replicas", replicas, 1)
        total = calculos.disponibilidad_paralelo(disponibilidad, replicas)
        return {
            "disponibilidad_total": total,
            "porcentaje": self._porcentaje(total),
            "indisponibilidad_minutos_mes": calculos.minutos_caidos(total, self._minutos(minutos_mes)),
            "formula": "1-(1-A)^n",
        }

    # Valida métricas operacionales y calcula la disponibilidad a partir del MTBF y MTTR
    def por_mttr(self, mtbf_horas: float, mttr_horas: float) -> dict:
        if mtbf_horas <= 0:
            raise ValorFueraDeRango("mtbf_horas", mtbf_horas, "> 0")
        self._validar_minimo("mttr_horas", mttr_horas, 0)
        a = calculos.disponibilidad_por_mttr(mtbf_horas, mttr_horas)
        return {
            "disponibilidad": a,
            "porcentaje": self._porcentaje(a),
            "indisponibilidad_minutos_mes": calculos.minutos_caidos(a, self._minutos(None)),
            "formula": "MTBF/(MTBF+MTTR)",
        }

    # ---------- Métodos de MTBF ----------

    # Valida y calcula el tiempo medio entre fallas (MTBF) compuesto para 'n' servicios en serie
    def mtbf_serie(self, mtbf_individual_horas: float, servicios: int) -> dict:
        if mtbf_individual_horas <= 0:
            raise ValorFueraDeRango("mtbf_individual_horas", mtbf_individual_horas, "> 0")
        self._validar_minimo("servicios", servicios, 1)
        horas = calculos.mtbf_serie(mtbf_individual_horas, servicios)
        return {"mtbf_sistema_horas": horas, "equivale_dias": horas / 24, "formula": "MTBF/n"}

    # ---------- Métodos de presupuesto de error ----------

    # Valida el SLO y calcula el tiempo total de caída permitido al mes (Error Budget)
    def presupuesto_error(self, slo: float, minutos_mes: int | None = None) -> dict:
        self._validar_fraccion("slo", slo)
        fraccion = calculos.presupuesto_error(slo)
        return {
            "presupuesto_fraccion": fraccion,
            "presupuesto_minutos": fraccion * self._minutos(minutos_mes),
            "formula": "1-SLO",
        }

    # ---------- Métodos de latencia ----------

    # Valida los datos y calcula la probabilidad de evitar impacto por latencias de cola larga
    def cola_larga(self, llamadas: int, percentil: float = 0.99) -> dict:
        self._validar_minimo("llamadas", llamadas, 1)
        if not 0 < percentil < 1:
            raise ValorFueraDeRango("percentil", percentil, "> 0 y < 1")
        p = calculos.probabilidad_evitar_cola(percentil, llamadas)
        return {"probabilidad_evitar_cola": p, "una_de_cada": calculos.una_de_cada(p), "formula": "p^n"}

    # Valida y calcula la latencia compuesta según la estrategia seleccionada (secuencial o concurrente)
    def latencia_compuesta(self, latencias_ms: list[float], estrategia: str) -> dict:
        if not latencias_ms:
            raise ValorFueraDeRango("latencias_ms", latencias_ms, "una lista con al menos una latencia")
        for latencia in latencias_ms:
            self._validar_minimo("latencias_ms", latencia, 0)
        if estrategia not in ESTRATEGIAS:
            raise ValorFueraDeRango("estrategia", estrategia, "secuencial o concurrente")
        total = calculos.latencia_compuesta(latencias_ms, estrategia)
        formula = "sum(Li)" if estrategia == "secuencial" else "max(Li)"
        return {"total_ms": total, "formula": formula}