from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CATALOGO_", extra="ignore")

    entorno: Literal["local", "dev", "test", "prod"] = "local"
    nivel_log: str = "INFO"
    docs_habilitada: bool = True
    tipo_repositorio: Literal["memoria", "sql"] = "memoria"
    pagina_tamano_maximo: int = Field(default=50, ge=1, le=200)
    cargar_datos_ejemplo: bool = False

    @field_validator("nivel_log")
    @classmethod
    def validar_nivel_log(cls, valor: str) -> str:
        nivel = valor.strip().upper()
        if nivel not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ValueError("nivel_log debe ser DEBUG, INFO, WARNING o ERROR")
        return nivel


@lru_cache
def get_configuracion() -> Configuracion:
    return Configuracion()
