"""Rutas de autorizaciones. Solo traducen HTTP ↔ caso de uso."""

from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.dependencias import ServicioDep
from app.dominio import Autorizacion
from app.esquemas import AutorizacionCrear, AutorizacionRespuesta
from app.servicios.autorizaciones import SolicitudAutorizacion

router = APIRouter(prefix="/api/v1/autorizaciones", tags=["autorizaciones"])

ERRORES_POST = {
    402: {"description": "Pago rechazado (total mayor que PAGOS_MONTO_MAXIMO)"},
    404: {"description": "No existe el producto"},
    409: {"description": "Stock insuficiente"},
    502: {"description": "Una dependencia respondió mal"},
    503: {"description": "Una dependencia no está disponible"},
    504: {"description": "Una dependencia no respondió a tiempo"},
}


def a_respuesta(a: Autorizacion) -> AutorizacionRespuesta:
    return AutorizacionRespuesta(
        autorizacion_id=a.autorizacion_id,
        sku=a.sku,
        unidades=a.unidades,
        total=a.total,
        medio_pago=a.medio_pago,
        reserva_id=a.reserva_id,
        estado=a.estado.value,
    )


@router.post(
    "",
    response_model=AutorizacionRespuesta,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES_POST,
)
async def autorizar(
    datos: AutorizacionCrear,
    servicio: ServicioDep,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> AutorizacionRespuesta:
    resultado = await servicio.autorizar(
        SolicitudAutorizacion(
            sku=datos.sku,
            unidades=datos.unidades,
            medio_pago=datos.medio_pago,
            reserva_id=datos.reserva_id,
        ),
        clave_idempotencia=idempotency_key,
    )
    autorizacion = resultado.autorizacion
    response.headers["Location"] = f"/api/v1/autorizaciones/{autorizacion.autorizacion_id}"
    if resultado.repetida:
        response.headers["Idempotent-Replayed"] = "true"
    return a_respuesta(autorizacion)


@router.get("/{autorizacion_id}", response_model=AutorizacionRespuesta, responses={404: {}})
async def obtener(autorizacion_id: str, servicio: ServicioDep) -> AutorizacionRespuesta:
    return a_respuesta(await servicio.obtener(autorizacion_id))


@router.put(
    "/{autorizacion_id}/anulacion", response_model=AutorizacionRespuesta, responses={404: {}}
)
async def anular(autorizacion_id: str, servicio: ServicioDep) -> AutorizacionRespuesta:
    """Idempotente: anular una autorización ya anulada devuelve 200 con el mismo estado."""
    return a_respuesta(await servicio.anular(autorizacion_id))
