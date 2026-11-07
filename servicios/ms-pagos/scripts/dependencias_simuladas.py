"""Simuladores mínimos de ms-catalogo (8001) y ms-inventario (8002).

Sirven para probar ms-pagos con curl mientras los compañeros terminan los
servicios reales. Usan los datos semilla de CONVENCIONES §9.

    uv run python scripts/dependencias_simuladas.py catalogo     # puerto 8001
    uv run python scripts/dependencias_simuladas.py inventario   # puerto 8002

Para la evidencia del 503: detenga el de inventario (Ctrl+C) y repita la petición.
"""

import sys

import uvicorn
from fastapi import FastAPI, HTTPException

PRODUCTOS = {
    "CAF-001": ("Café Huila 500g", "38500.00", 100),
    "PAN-001": ("Panela en bloque 1kg", "6200.00", 50),
    "CHO-001": ("Chocolate de mesa 500g", "14900.00", 30),
    "QUE-001": ("Queso campesino 500g", "16800.00", 20),
    "ARE-001": ("Arepas de maíz x10", "9500.00", 80),
}

catalogo = FastAPI(title="ms-catalogo SIMULADO")
inventario = FastAPI(title="ms-inventario SIMULADO")


@catalogo.get("/api/v1/productos/{sku}")
def producto(sku: str):
    if sku not in PRODUCTOS:
        raise HTTPException(404, f"No existe el producto con SKU {sku}")
    nombre, precio, _ = PRODUCTOS[sku]
    return {"sku": sku, "nombre": nombre, "precio": precio}


@inventario.get("/api/v1/existencias/{sku}")
def existencia(sku: str):
    if sku not in PRODUCTOS:
        raise HTTPException(404, f"No existe el producto con SKU {sku}")
    return {"sku": sku, "disponible": PRODUCTOS[sku][2]}


if __name__ == "__main__":
    cual = sys.argv[1] if len(sys.argv) > 1 else ""
    if cual == "catalogo":
        uvicorn.run(catalogo, port=8001)
    elif cual == "inventario":
        uvicorn.run(inventario, port=8002)
    else:
        sys.exit("Uso: python scripts/dependencias_simuladas.py catalogo|inventario")
