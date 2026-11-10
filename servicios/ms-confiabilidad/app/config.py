"""Configuración del servicio (factor III): se lee del entorno, no del código."""
# Permite almacenar en caché el resultado de la función para evitar releer las variables de entorno
from functools import lru_cache

# Permite restringir el valor de una variable a un conjunto exacto de opciones de texto
from typing import Literal

# Herramientas de Pydantic para definir restricciones avanzadas y validadores de campos
from pydantic import Field, field_validator

# Clases base de Pydantic Settings para mapear variables de entorno a atributos de clase
from pydantic_settings import BaseSettings, SettingsConfigDict

# Conjunto constante con los niveles de registro (logs) permitidos en el sistema
NIVELES_LOG = {"DEBUG", "INFO", "WARNING", "ERROR"}


class Configuracion(BaseSettings):
    """Clase que define, lee y valida la configuración del sistema desde el entorno."""

    # Configuración del comportamiento del modelo:
    # - env_prefix: busca variables con el prefijo indicado (ej: CONFIABILIDAD_ENTORNO)
    # - extra="ignore": omite otras variables de entorno del sistema que no estén declaradas aquí
    model_config = SettingsConfigDict(env_prefix="CONFIABILIDAD_", extra="ignore")

    # Entorno de ejecución: solo acepta uno de los 4 valores indicados (por defecto: "local")
    entorno: Literal["local", "dev", "test", "prod"] = "local"

    # Nivel predeterminado para el registro de eventos en consola/servidor
    nivel_log: str = "INFO"

    # Interruptor booleano para habilitar o deshabilitar la documentación interactiva de la API
    docs_habilitada: bool = True

    # Minutos base en un mes (43.200 min = 30 días); ge=1 exige que el valor sea mayor o igual a 1
    minutos_mes_defecto: int = Field(default=43_200, ge=1)

    # Precisión de redondeo para cálculos; ge=0 y le=10 exigen un valor entre 0 y 10
    decimales_porcentaje: int = Field(default=4, ge=0, le=10)

    @field_validator("nivel_log")
    @classmethod
    def validar_nivel_log(cls, valor: str) -> str:
        """Valida y normaliza el campo 'nivel_log' antes de asignarlo."""
        # Convierte el texto recibido a mayúsculas para evitar fallas por minúsculas (ej: "info" -> "INFO")
        valor = valor.upper()

        # Comprueba si el nivel existe dentro del conjunto de valores permitidos
        if valor not in NIVELES_LOG:
            raise ValueError(f"nivel_log debe ser uno de {sorted(NIVELES_LOG)}")

        # Retorna el valor ya transformado y validado
        return valor


@lru_cache
def get_configuracion() -> Configuracion:
    """Crea y almacena en caché una instancia única de la configuración (Singleton)."""
    # Al usar @lru_cache, la primera llamada lee el entorno y las siguientes reutilizan el objeto en memoria
    return Configuracion()