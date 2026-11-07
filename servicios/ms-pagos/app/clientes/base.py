"""Llamada GET común a las dependencias, con traducción de fallos.

Aquí se decide qué significa cada fallo de red para el negocio:

| Lo que pasa                                   | Excepción de dominio        | HTTP |
|-----------------------------------------------|-----------------------------|------|
| Conexión rechazada / sin DNS / connect timeout | ``DependenciaNoDisponible`` | 503  |
| Conectó pero no respondió a tiempo            | ``DependenciaSinRespuesta`` | 504  |
| Respondió 5xx o algo inesperado               | ``DependenciaRespondioMal`` | 502  |
| Respondió 404                                 | ``None`` (decide el llamador) | —  |
"""

from typing import Any

import httpx

from app.errores import (
    DependenciaNoDisponible,
    DependenciaRespondioMal,
    DependenciaSinRespuesta,
)


async def obtener_json(http: httpx.AsyncClient, url: str, servicio: str) -> dict[str, Any] | None:
    """GET a ``url``. Devuelve el JSON, ``None`` si es 404, o lanza un error de dominio."""
    try:
        respuesta = await http.get(url)
        if respuesta.status_code == 404:
            return None
        respuesta.raise_for_status()
        return respuesta.json()
    except httpx.ConnectTimeout as exc:
        # No logró ni conectar: para el consumidor es "no disponible".
        raise DependenciaNoDisponible(servicio) from exc
    except httpx.TimeoutException as exc:
        # ReadTimeout, WriteTimeout o PoolTimeout: conectó, pero no respondió a tiempo.
        raise DependenciaSinRespuesta(servicio) from exc
    except httpx.HTTPStatusError as exc:
        # 5xx (o un 4xx distinto de 404 que no esperamos): la dependencia respondió mal.
        raise DependenciaRespondioMal(servicio) from exc
    except httpx.RequestError as exc:
        # ConnectError (conexión rechazada, sin DNS) y demás errores de red.
        raise DependenciaNoDisponible(servicio) from exc
    except ValueError as exc:
        # Cuerpo que no es JSON.
        raise DependenciaRespondioMal(servicio) from exc
