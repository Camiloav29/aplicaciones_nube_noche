class ErrorDominio(Exception):
    def __init__(self, mensaje: str) -> None:
        self.mensaje = mensaje
        super().__init__(mensaje)


class ProductoNoEncontrado(ErrorDominio):
    def __init__(self, sku: str) -> None:
        self.sku = sku
        super().__init__(f"No existe el producto con SKU {sku}")


class ProductoDuplicado(ErrorDominio):
    def __init__(self, sku: str) -> None:
        self.sku = sku
        super().__init__(f"Ya existe el producto con SKU {sku}")


class LimitePaginaExcedido(ErrorDominio):
    def __init__(self, limite: int, maximo: int) -> None:
        self.limite = limite
        self.maximo = maximo
        super().__init__(f"El limite {limite} supera pagina_tamano_maximo ({maximo})")
