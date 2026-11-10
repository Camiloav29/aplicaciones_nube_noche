from decimal import Decimal
from app.config import Configuracion
from app.esquemas import Producto
from app.repositorios.base import RepositorioProductos

DATOS_SEMILLA: list[Producto] = [
    Producto("CAF-001", "Café Huila 500g", "Café especial origen Huila", "bebidas", Decimal("38500.00")),
    Producto("PAN-001", "Panela en bloque 1kg", "Panela artesanal", "despensa", Decimal("6200.00")),
    Producto("CHO-001", "Chocolate de mesa 500g", "Chocolate tradicional", "bebidas", Decimal("14900.00")),
    Producto("QUE-001", "Queso campesino 500g", "Queso fresco", "lácteos", Decimal("16800.00")),
    Producto("ARE-001", "Arepas de maíz x10", "Paquete de 10 arepas", "panadería", Decimal("9500.00")),
]


class RepositorioProductosMemoria:
    def __init__(self, cargar_semilla: bool = False) -> None:
        self._almacen: dict[str, Producto] = {}
        if cargar_semilla:
            for prod in DATOS_SEMILLA:
                self._almacen[prod.sku] = prod

    def listar(self, categoria: str | None = None, limite: int = 20) -> list[Producto]:
        items = list(self._almacen.values())
        if categoria:
            items = [p for p in items if p.categoria.lower() == categoria.lower()]
        return items[:limite]

    def obtener(self, sku: str) -> Producto | None:
        return self._almacen.get(sku)

    def guardar(self, producto: Producto) -> Producto:
        self._almacen[producto.sku] = producto
        return producto

    def eliminar(self, sku: str) -> bool:
        return self._almacen.pop(sku, None) is not None


def crear_repositorio(config: Configuracion) -> RepositorioProductos:
    if config.tipo_repositorio == "memoria":
        return RepositorioProductosMemoria(cargar_semilla=config.cargar_datos_ejemplo)
    return RepositorioProductosMemoria(cargar_semilla=config.cargar_datos_ejemplo)
