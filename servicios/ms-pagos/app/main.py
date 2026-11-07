"""Ensambla la aplicación: lifespan, middleware, manejadores de errores y routers.

Aquí no hay lógica de negocio.
"""

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Configuracion, get_configuracion
from app.errores import (
    AutorizacionNoEncontrada,
    DependenciaNoDisponible,
    DependenciaRespondioMal,
    DependenciaSinRespuesta,
    ErrorDominio,
    PagoRechazado,
    ProductoNoEncontrado,
    StockInsuficiente,
)
from app.repositorios.memoria import AlmacenIdempotenciaMemoria, RepositorioAutorizacionesMemoria
from app.rutas import autorizaciones, salud

VERSION = "0.1.0"


def configurar_logs(nivel: str) -> None:
    """Registros en JSON por salida estándar."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, nivel)),
    )


def crear_cliente_http(config: Configuracion) -> httpx.AsyncClient:
    """Un único cliente con los cuatro relojes y límites explícitos."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=config.timeout_connect,
            read=config.timeout_read,
            write=config.timeout_write,
            pool=config.timeout_pool,
        ),
        limits=httpx.Limits(
            max_connections=config.max_conexiones,
            max_keepalive_connections=config.max_conexiones_keepalive,
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = get_configuracion()
    configurar_logs(config.nivel_log)
    log = structlog.get_logger()
    app.state.http = crear_cliente_http(config)
    app.state.repositorio = RepositorioAutorizacionesMemoria()
    app.state.idempotencia = AlmacenIdempotenciaMemoria()
    log.info("arranque", servicio="ms-pagos", entorno=config.entorno)
    try:
        yield
    finally:
        await app.state.http.aclose()
        log.info("apagado", servicio="ms-pagos")


def crear_app() -> FastAPI:
    config = get_configuracion()
    app = FastAPI(
        title="MercadoAndino - Pagos",
        version=VERSION,
        lifespan=lifespan,
        docs_url="/docs" if config.docs_habilitada else None,
        redoc_url="/redoc" if config.docs_habilitada else None,
    )

    @app.middleware("http")
    async def registrar_peticion(request: Request, call_next):
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        structlog.get_logger().info(
            "peticion",
            ruta=request.url.path,
            metodo=request.method,
            estado=respuesta.status_code,
            duracion_ms=round((time.perf_counter() - inicio) * 1000, 2),
        )
        return respuesta

    # Traducción de excepciones de dominio a HTTP (siempre con la clave "detail").
    codigos: dict[type[ErrorDominio], int] = {
        PagoRechazado: 402,
        ProductoNoEncontrado: 404,
        AutorizacionNoEncontrada: 404,
        StockInsuficiente: 409,
        DependenciaRespondioMal: 502,
        DependenciaNoDisponible: 503,
        DependenciaSinRespuesta: 504,
    }

    @app.exception_handler(ErrorDominio)
    async def manejar_error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
        codigo = codigos.get(type(exc), 500)
        return JSONResponse(status_code=codigo, content={"detail": exc.detail, **exc.extra()})

    app.include_router(salud.router)
    app.include_router(autorizaciones.router)
    return app


app = crear_app()
