"""Ensambla la aplicación: configuración, manejador de errores y rutas."""
# Importa la clase principal FastAPI y la clase Request para inspeccionar peticiones HTTP
from fastapi import FastAPI, Request
# Importa JSONResponse para retornar estructuradamente errores en formato JSON
from fastapi.responses import JSONResponse

# Importa el proveedor de la configuración del sistema
from app.config import get_configuracion
# Importa la excepción personalizada de negocio para datos fuera de rango
from app.errores import ValorFueraDeRango
# Importa los módulos con las rutas de salud y confiabilidad
from app.rutas import confiabilidad, salud

# Carga la configuración al arrancar (falla de inmediato si las variables de entorno son inválidas)
config = get_configuracion()

# Instancia la aplicación FastAPI definiendo el título, la versión y la activación condicional de Swagger
app = FastAPI(
    title="MercadoAndino - Confiabilidad",
    version="0.1.0",
    docs_url="/docs" if config.docs_habilitada else None,
    redoc_url=None,
)


# Intercepta la excepción ValorFueraDeRango y devuelve una respuesta HTTP 422 Unprocessable Entity
@app.exception_handler(ValorFueraDeRango)
async def manejar_fuera_de_rango(request: Request, exc: ValorFueraDeRango) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "campo": exc.campo, "valor": exc.valor, "regla": exc.regla},
    )


# Registra los endpoints para verificación de estado y diagnóstico
app.include_router(salud.router)
# Registra los endpoints para cálculos de confiabilidad y latencia
app.include_router(confiabilidad.router)