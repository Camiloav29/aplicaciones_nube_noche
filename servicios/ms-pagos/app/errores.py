"""Excepciones de dominio de ms-pagos.

La capa de servicio lanza estas excepciones (nunca ``HTTPException``) y
``main.py`` las traduce al código HTTP correspondiente con la clave ``detail``.
"""


class ErrorDominio(Exception):
    """Base de todas las excepciones de ms-pagos."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class DependenciaNoDisponible(ErrorDominio):
    """Conexión rechazada o sin DNS → 503."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} no disponible")
        self.servicio = servicio


class DependenciaSinRespuesta(ErrorDominio):
    """Timeout de lectura → 504."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} no respondio")
        self.servicio = servicio


class DependenciaRespondioMal(ErrorDominio):
    """La dependencia devolvió 5xx → 502."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} respondio mal")
        self.servicio = servicio
