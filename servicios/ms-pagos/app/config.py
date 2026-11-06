"""Configuración externalizada de ms-pagos (factor III).

Todos los valores se leen de variables de entorno con prefijo ``PAGOS_``.
Los valores por defecto son seguros para trabajar en local; nunca de producción.
Un valor inválido impide el arranque (``ValidationError``).
"""

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

NIVELES_LOG = {"DEBUG", "INFO", "WARNING", "ERROR"}


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PAGOS_",
        env_file=".env",
        extra="ignore",
    )

    # Campos comunes obligatorios (CONVENCIONES §5)
    entorno: Literal["local", "dev", "test", "prod"] = "local"
    nivel_log: str = "INFO"
    docs_habilitada: bool = True

    # Dependencias (modo estático: URL por configuración, nunca fijas en el código)
    modo_descubrimiento: Literal["estatico", "consul"] = "estatico"
    url_catalogo: str = "http://localhost:8001/api/v1"
    url_inventario: str = "http://localhost:8002/api/v1"

    # Reglas de negocio
    monto_maximo: Decimal = Field(default=Decimal("1000000.00"), gt=0)
    cargar_datos_ejemplo: bool = False

    # Cliente HTTP (CONVENCIONES §8)
    timeout_connect: float = Field(default=2.0, gt=0)
    timeout_read: float = Field(default=3.0, gt=0)
    timeout_write: float = Field(default=2.0, gt=0)
    timeout_pool: float = Field(default=1.0, gt=0)
    max_conexiones: int = Field(default=20, ge=1)
    max_conexiones_keepalive: int = Field(default=10, ge=0)

    @field_validator("nivel_log")
    @classmethod
    def validar_nivel_log(cls, valor: str) -> str:
        normalizado = valor.strip().upper()
        if normalizado not in NIVELES_LOG:
            raise ValueError(f"nivel_log debe ser uno de {sorted(NIVELES_LOG)}")
        return normalizado

    @field_validator("url_catalogo", "url_inventario")
    @classmethod
    def quitar_barra_final(cls, valor: str) -> str:
        return valor.rstrip("/")

    @model_validator(mode="after")
    def sin_docs_en_prod(self) -> "Configuracion":
        if self.entorno == "prod":
            self.docs_habilitada = False
        return self


@lru_cache
def get_configuracion() -> Configuracion:
    """Una sola lectura del entorno por proceso."""
    return Configuracion()
