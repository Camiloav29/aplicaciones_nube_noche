"""Contrato HTTP: qué JSON entra y qué JSON sale de cada endpoint."""
# Importa Annotated para adjuntar metadatos de validación a tipos de datos
# Importa Literal para restringir valores a opciones de texto específicas
from typing import Annotated, Literal

# Importa BaseModel para definir esquemas JSON y Field para reglas de validación
from pydantic import BaseModel, Field

# ==============================================================================
# TIPOS REUTILIZABLES (Custom Types con Annotated)
# ==============================================================================

# Representa un número decimal entre 0 y 1 (excluye 0, incluye 1)
# gt=0: greater than 0 (mayor que 0)
# le=1: less than or equal to 1 (menor o igual a 1)
Fraccion = Annotated[float, Field(gt=0, le=1)]

# Representa opcionalmente un número entero mayor o igual a 1
# default=None: si no se envía en el JSON, su valor inicial es None
# ge=1: greater than or equal to 1 (mayor o igual a 1)
MinutosMes = Annotated[int | None, Field(default=None, ge=1)]


# ==============================================================================
# 1. ESQUEMAS DE DISPONIBILIDAD
# ==============================================================================

class ServicioEnCadena(BaseModel):
    """Estructura individual de un servicio dentro de una cadena en serie."""

    # El nombre debe ser una cadena de texto no vacía (mínimo 1 carácter)
    nombre: str = Field(min_length=1)

    # Disponibilidad del servicio individual (debe ser un valor de tipo Fraccion)
    disponibilidad: Fraccion


class SerieEntrada(BaseModel):
    """JSON de entrada para calcular la disponibilidad en serie."""

    # Lista con al menos un servicio en cadena (min_length=1 evita listas vacías)
    servicios: list[ServicioEnCadena] = Field(min_length=1)

    # Minutos del mes opcionales para calcular el tiempo de caída
    minutos_mes: MinutosMes


class ParaleloEntrada(BaseModel):
    """JSON de entrada para calcular la disponibilidad con réplicas en paralelo."""

    # Disponibilidad de una sola réplica (entre 0 y 1)
    disponibilidad: Fraccion

    # Número de réplicas en paralelo (mínimo 1 réplica)
    replicas: int = Field(ge=1)

    # Minutos del mes opcionales para calcular el tiempo de caída
    minutos_mes: MinutosMes


class DisponibilidadSalida(BaseModel):
    """JSON de respuesta devuelto para cálculos de disponibilidad (serie/paralelo)."""

    # Resultado numérico puro (ej: 0.999)
    disponibilidad_total: float

    # Resultado formateado como texto porcentual (ej: "99.9%")
    porcentaje: str

    # Total de minutos estimados de inactividad al mes
    indisponibilidad_minutos_mes: float

    # Texto descriptivo con la fórmula matemática aplicada
    formula: str


class MttrSalida(BaseModel):
    """JSON de respuesta devuelto tras calcular disponibilidad con MTBF y MTTR."""

    # Disponibilidad calculada en decimal
    disponibilidad: float

    # Porcentaje formateado en texto
    porcentaje: str

    # Minutos de caída calculados al mes
    indisponibilidad_minutos_mes: float

    # Expresión o explicación de la fórmula utilizada
    formula: str


# ==============================================================================
# 2. ESQUEMAS DE MTBF (Tiempo Medio Entre Fallas)
# ==============================================================================

class MtbfEntrada(BaseModel):
    """JSON de entrada para calcular el MTBF de un sistema en serie."""

    # Tiempo medio entre fallas individual (estrictamente mayor a 0 horas)
    mtbf_individual_horas: float = Field(gt=0)

    # Cantidad de servicios conectados (mínimo 1)
    servicios: int = Field(ge=1)


class MtbfSalida(BaseModel):
    """JSON de respuesta para cálculos de MTBF."""

    # Tiempo medio entre fallas resultante para todo el sistema (en horas)
    mtbf_sistema_horas: float

    # Equivalente en días del MTBF calculado
    equivale_dias: float

    # Texto descriptivo de la fórmula aplicada
    formula: str


# ==============================================================================
# 3. ESQUEMAS DE PRESUPUESTO DE ERROR (Error Budget)
# ==============================================================================

class PresupuestoEntrada(BaseModel):
    """JSON de entrada para calcular el margen de error permitido."""

    # Objetivo de Nivel de Servicio (ej: 0.999)
    slo: Fraccion

    # Minutos totales del mes
    minutos_mes: MinutosMes


class PresupuestoSalida(BaseModel):
    """JSON de respuesta con el presupuesto de error calculado."""

    # Fracción decimal permitida de falla (1 - SLO)
    presupuesto_fraccion: float

    # Total de minutos al mes que el sistema puede estar fuera de servicio
    presupuesto_minutos: float

    # Representación en texto de la fórmula usada
    formula: str


# ==============================================================================
# 4. ESQUEMAS DE LATENCIA Y RENDIMIENTO
# ==============================================================================

class ColaLargaEntrada(BaseModel):
    """JSON de entrada para evaluar el impacto de la latencia en la cola larga."""

    # Cantidad de llamadas o peticiones independientes (mínimo 1)
    llamadas: int = Field(ge=1)

    # Probabilidad individual de respuesta rápida (por defecto 0.99, entre 0 y 1 excluyentes)
    percentil: float = Field(default=0.99, gt=0, lt=1)


class ColaLargaSalida(BaseModel):
    """JSON de respuesta para análisis de cola larga."""

    # Probabilidad de que ninguna llamada sea lenta
    probabilidad_evitar_cola: float

    # Frecuencia promedio (1 de cada X peticiones sufrirá lentitud)
    una_de_cada: float

    # Texto explicativo de la fórmula matemática usada
    formula: str


class CompuestaEntrada(BaseModel):
    """JSON de entrada para calcular latencia acumulada según la estrategia."""

    # Lista con al menos una latencia en milisegundos (cada valor debe ser >= 0)
    latencias_ms: list[Annotated[float, Field(ge=0)]] = Field(min_length=1)

    # Solo admite las cadenas exactas "secuencial" o "concurrente"
    estrategia: Literal["secuencial", "concurrente"]


class CompuestaSalida(BaseModel):
    """JSON de respuesta con el tiempo de latencia total calculado."""

    # Latencia total resultante en milisegundos
    total_ms: float

    # Explicación de la fórmula empleada según la estrategia
    formula: str