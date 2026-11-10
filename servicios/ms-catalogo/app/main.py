from contextlib import asynccontextmanager
from typing import AsyncIterator
import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.clientes.consul import cancelar_en_consul, registrar_en_consul
from app.config import get_configuracion
from app.errores import LimitePaginaExcedido, ProductoDuplicado, ProductoNoEncontrado
from app.repositorios.memoria import crear_repositorio
from app.rutas import productos, salud


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = get_configuracion()
    if not hasattr(app.state, "repositorio"):
        app.state.repositorio = crear_repositorio(config)
    timeout = httpx.Timeout(connect=2.0, read=3.0, write=2.0, pool=1.0)
    async with httpx.AsyncClient(timeout=timeout) as cliente:
        app.state.http_client = cliente
        instancia_id = await registrar_en_consul(cliente)
        try:
            yield
        finally:
            await cancelar_en_consul(cliente, instancia_id)


def crear_app() -> FastAPI:
    config = get_configuracion()
    app = FastAPI(
        title="MercadoAndino - ms-catalogo",
        version="1.0.0",
        docs_url="/docs" if config.docs_habilitada else None,
        lifespan=lifespan,
    )
    app.state.repositorio = crear_repositorio(config)

    @app.exception_handler(ProductoNoEncontrado)
    async def manejar_no_encontrado(_: Request, exc: ProductoNoEncontrado) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.mensaje, "sku": exc.sku},
        )

    @app.exception_handler(ProductoDuplicado)
    async def manejar_duplicado(_: Request, exc: ProductoDuplicado) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.mensaje, "sku": exc.sku},
        )

    @app.exception_handler(LimitePaginaExcedido)
    async def manejar_limite(_: Request, exc: LimitePaginaExcedido) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.mensaje},
        )

    app.include_router(salud.router)
    app.include_router(productos.router)
    return app


app = crear_app()
