from app.errores import LimitePaginaExcedido, ProductoDuplicado, ProductoNoEncontrado
from app.esquemas import Producto, ProductoActualizar, ProductoCrear
from app.repositorios.base import RepositorioProductos


class ServicioCatalogo:
    def __init__(self, repositorio: RepositorioProductos, max_pagina: int = 50) -> None:
        self._repo = repositorio
        self._max_pagina = max_pagina

    def listar(self, categoria: str | None = None, limite: int = 20) -> list[Producto]:
        if limite > self._max_pagina:
            raise LimitePaginaExcedido(limite=limite, maximo=self._max_pagina)
        return self._repo.listar(categoria=categoria, limite=limite)

    def obtener(self, sku: str) -> Producto:
        producto = self._repo.obtener(sku)
        if producto is None:
            raise ProductoNoEncontrado(sku)
        return producto

    def crear(self, datos: ProductoCrear) -> Producto:
        if self._repo.obtener(datos.sku) is not None:
            raise ProductoDuplicado(datos.sku)
        entidad = Producto(
            sku=datos.sku,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            categoria=datos.categoria,
            precio=datos.precio,
            activo=True,
        )
        return self._repo.guardar(entidad)

    def reemplazar(self, sku: str, datos: ProductoActualizar) -> Producto:
        self.obtener(sku)
        entidad = Producto(
            sku=sku,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            categoria=datos.categoria,
            precio=datos.precio,
            activo=datos.activo,
        )
        return self._repo.guardar(entidad)

    def eliminar(self, sku: str) -> None:
        if not self._repo.eliminar(sku):
            raise ProductoNoEncontrado(sku)
