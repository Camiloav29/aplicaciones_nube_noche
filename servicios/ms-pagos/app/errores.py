"""Excepciones de dominio de ms-pagos.

La capa de servicio lanza estas excepciones (nunca ``HTTPException``) y
``main.py`` las traduce al código HTTP correspondiente, siempre con la clave
``detail`` y, cuando aplica, campos adicionales (``extra``).
"""

from typing import Any


class ErrorDominio(Exception):
    """Base de todas las excepciones de ms-pagos."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail

    def extra(self) -> dict[str, Any]:
        """Campos adicionales que acompañan a ``detail`` en la respuesta."""
        return {}


# --- Reglas de negocio -------------------------------------------------------


class ProductoNoEncontrado(ErrorDominio):
    """El SKU no existe en ms-catalogo o en ms-inventario → 404."""

    def __init__(self, sku: str) -> None:
        super().__init__(f"No existe el producto con SKU {sku}")
        self.sku = sku


class AutorizacionNoEncontrada(ErrorDominio):
    """→ 404."""

    def __init__(self, autorizacion_id: str) -> None:
        super().__init__(f"No existe la autorizacion {autorizacion_id}")


class StockInsuficiente(ErrorDominio):
    """El disponible es menor que las unidades pedidas → 409."""

    def __init__(self, sku: str, solicitado: int, disponible: int) -> None:
        super().__init__(f"Stock insuficiente para {sku}")
        self.sku = sku
        self.solicitado = solicitado
        self.disponible = disponible

    def extra(self) -> dict[str, Any]:
        return {"sku": self.sku, "solicitado": self.solicitado, "disponible": self.disponible}


class PagoRechazado(ErrorDominio):
    """El total supera ``PAGOS_MONTO_MAXIMO`` → 402."""

    def __init__(self) -> None:
        super().__init__("Pago rechazado")

    def extra(self) -> dict[str, Any]:
        return {"estado": "RECHAZADA"}


# --- Fallos de las dependencias ---------------------------------------------


class DependenciaNoDisponible(ErrorDominio):
    """Conexión rechazada, sin DNS o sin poder conectar a tiempo → 503."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} no disponible")
        self.servicio = servicio


class DependenciaSinRespuesta(ErrorDominio):
    """Conectó, pero no respondió a tiempo (lectura) → 504."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} no respondio")
        self.servicio = servicio


class DependenciaRespondioMal(ErrorDominio):
    """La dependencia devolvió 5xx o una respuesta inesperada → 502."""

    def __init__(self, servicio: str) -> None:
        super().__init__(f"{servicio} respondio mal")
        self.servicio = servicio
