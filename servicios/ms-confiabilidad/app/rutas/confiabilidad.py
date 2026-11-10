"""Rutas de confiabilidad: solo traducen HTTP <-> servicio. Sin lógica."""
# Importa Annotated para adjuntar metadatos de validación a parámetros de tipo
from typing import Annotated

# Importa APIRouter para declarar grupos de rutas y Query para validar parámetros GET en URL
from fastapi import APIRouter, Query

# Importa la dependencia que inyecta la instancia del servicio de confiabilidad
from app.dependencias import ServicioDep

# Importa todos los esquemas Pydantic de entrada (DTOs de petición) y salida (DTOs de respuesta)
from app.esquemas import (
    ColaLargaEntrada,
    ColaLargaSalida,
    CompuestaEntrada,
    CompuestaSalida,
    DisponibilidadSalida,
    MtbfEntrada,
    MtbfSalida,
    MttrSalida,
    ParaleloEntrada,
    PresupuestoEntrada,
    PresupuestoSalida,
    SerieEntrada,
)

# Inicializa el enrutador aplicando el prefijo de versión '/api/v1' y la etiqueta OpenAPI 'confiabilidad'
router = APIRouter(prefix="/api/v1", tags=["confiabilidad"])


# Endpoint POST para calcular la disponibilidad total de componentes en serie
@router.post("/disponibilidad/serie", response_model=DisponibilidadSalida)
def disponibilidad_serie(entrada: SerieEntrada, servicio: ServicioDep) -> dict:
    disponibilidades = [s.disponibilidad for s in entrada.servicios]
    return servicio.serie(disponibilidades, entrada.minutos_mes)


# Endpoint POST para calcular la disponibilidad con réplicas redundantes en paralelo
@router.post("/disponibilidad/paralelo", response_model=DisponibilidadSalida)
def disponibilidad_paralelo(entrada: ParaleloEntrada, servicio: ServicioDep) -> dict:
    return servicio.paralelo(entrada.disponibilidad, entrada.replicas, entrada.minutos_mes)


# Endpoint GET para obtener la disponibilidad basada en métricas operacionales MTBF y MTTR mediante Query Params
@router.get("/disponibilidad/mttr", response_model=MttrSalida)
def disponibilidad_mttr(
    servicio: ServicioDep,
    mtbf_horas: Annotated[float, Query(gt=0)],
    mttr_horas: Annotated[float, Query(ge=0)],
) -> dict:
    return servicio.por_mttr(mtbf_horas, mttr_horas)


# Endpoint POST para calcular el tiempo medio entre fallas de un sistema en serie
@router.post("/mtbf/serie", response_model=MtbfSalida)
def mtbf_serie(entrada: MtbfEntrada, servicio: ServicioDep) -> dict:
    return servicio.mtbf_serie(entrada.mtbf_individual_horas, entrada.servicios)


# Endpoint POST para calcular el presupuesto de error (Error Budget) tolerado a partir del SLO
@router.post("/presupuesto-error", response_model=PresupuestoSalida)
def presupuesto_error(entrada: PresupuestoEntrada, servicio: ServicioDep) -> dict:
    return servicio.presupuesto_error(entrada.slo, entrada.minutos_mes)


# Endpoint POST para calcular el impacto de la latencia de cola larga en múltiples llamadas
@router.post("/latencia/cola-larga", response_model=ColaLargaSalida)
def latencia_cola_larga(entrada: ColaLargaEntrada, servicio: ServicioDep) -> dict:
    return servicio.cola_larga(entrada.llamadas, entrada.percentil)


# Endpoint POST para calcular la latencia compuesta (secuencial o concurrente) entre microservicios
@router.post("/latencia/compuesta", response_model=CompuestaSalida)
def latencia_compuesta(entrada: CompuestaEntrada, servicio: ServicioDep) -> dict:
    return servicio.latencia_compuesta(entrada.latencias_ms, entrada.estrategia)