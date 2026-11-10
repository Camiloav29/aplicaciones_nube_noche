from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, field_serializer, field_validator


@dataclass
class Producto:
    sku: str
    nombre: str
    descripcion: str
    categoria: str
    precio: Decimal
    activo: bool = True


class ProductoCrear(BaseModel):
    sku: str = Field(..., min_length=3, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: str = Field(default="", max_length=500)
    categoria: str = Field(..., min_length=1, max_length=60)
    precio: Decimal = Field(..., gt=Decimal("0"))

    @field_validator("precio", mode="before")
    @classmethod
    def validar_dos_decimales(cls, valor: object) -> Decimal:
        try:
            dec = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Precio invalido") from exc
        exponente = dec.as_tuple().exponent
        if isinstance(exponente, int) and exponente < -2:
            raise ValueError("El precio debe tener maximo 2 decimales")
        return dec.quantize(Decimal("0.01"))


class ProductoActualizar(BaseModel):
    sku: str | None = Field(default=None, min_length=3, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: str = Field(default="", max_length=500)
    categoria: str = Field(..., min_length=1, max_length=60)
    precio: Decimal = Field(..., gt=Decimal("0"))
    activo: bool = True

    @field_validator("precio", mode="before")
    @classmethod
    def validar_dos_decimales(cls, valor: object) -> Decimal:
        return ProductoCrear.validar_dos_decimales(valor)


class ProductoRespuesta(BaseModel):
    sku: str
    nombre: str
    descripcion: str
    categoria: str
    precio: Decimal
    activo: bool = True

    @field_serializer("precio")
    def serializar_precio(self, valor: Decimal) -> float:
        return float(valor)
