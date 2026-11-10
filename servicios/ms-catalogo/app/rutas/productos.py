from fastapi import APIRouter, Query, Response, status
from app.dependencias import ServicioCatalogoDep
from app.esquemas import ProductoActualizar, ProductoCrear, ProductoRespuesta

router = APIRouter(prefix="/api/v1/productos", tags=["productos"])


@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    servicio: ServicioCatalogoDep,
    categoria: str | None = Query(default=None),
    limite: int = Query(default=20, ge=1),
) -> list[ProductoRespuesta]:
    productos = servicio.listar(categoria=categoria, limite=limite)
    return [ProductoRespuesta(**p.__dict__) for p in productos]


@router.get("/{sku}", response_model=ProductoRespuesta)
def obtener_producto(sku: str, servicio: ServicioCatalogoDep) -> ProductoRespuesta:
    producto = servicio.obtener(sku)
    return ProductoRespuesta(**producto.__dict__)


@router.post("", response_model=ProductoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_producto(
    datos: ProductoCrear,
    response: Response,
    servicio: ServicioCatalogoDep,
) -> ProductoRespuesta:
    creado = servicio.crear(datos)
    response.headers["Location"] = f"/api/v1/productos/{creado.sku}"
    return ProductoRespuesta(**creado.__dict__)


@router.put("/{sku}", response_model=ProductoRespuesta)
def actualizar_producto(
    sku: str,
    datos: ProductoActualizar,
    servicio: ServicioCatalogoDep,
) -> ProductoRespuesta:
    actualizado = servicio.reemplazar(sku, datos)
    return ProductoRespuesta(**actualizado.__dict__)


@router.delete("/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(sku: str, servicio: ServicioCatalogoDep) -> Response:
    servicio.eliminar(sku)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
