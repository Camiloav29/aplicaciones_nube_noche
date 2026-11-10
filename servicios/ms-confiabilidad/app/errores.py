"""Excepciones de dominio: errores del negocio, no de HTTP."""


class ValorFueraDeRango(Exception):
    """Un dato no tiene sentido para la fórmula (ej: disponibilidad 1.5 o 0 réplicas)."""

    def __init__(self, campo: str, valor: object, regla: str) -> None:
        self.campo = campo  
        self.valor = valor
        self.regla = regla
        super().__init__(f"{campo}={valor} fuera de rango: debe ser {regla}")