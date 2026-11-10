"""Aceptación semana 3 (laboratorio 3): autorización de pagos con idempotencia (A03)."""
import uuid

import pytest


@pytest.fixture
def sku_con_stock(cliente_inventario) -> str:
    """SKU único con 100 unidades en inventario."""
    sku = f"T-{uuid.uuid4().hex[:8]}"
    cliente_inventario.post("/api/v1/existencias", json={"sku": sku, "cantidad": 100})
    return sku


def autorizar(cliente, sku: str, unidades: int, clave: str | None = None):
    """POST /api/v1/autorizaciones, con Idempotency-Key opcional."""
    cabeceras = {"Idempotency-Key": clave} if clave else {}
    return cliente.post("/api/v1/autorizaciones", headers=cabeceras,
                        json={"sku": sku, "unidades": unidades, "medio_pago": "tarjeta"})


def test_autorizacion_201(cliente_pagos, sku_con_stock):
    r = autorizar(cliente_pagos, sku_con_stock, 5)
    assert r.status_code == 201
    assert r.json()["estado"] == "AUTORIZADA"


def test_reintento_con_la_misma_idempotency_key_no_cobra_dos_veces(cliente_pagos, sku_con_stock):
    clave = str(uuid.uuid4())
    primera = autorizar(cliente_pagos, sku_con_stock, 5, clave)
    segunda = autorizar(cliente_pagos, sku_con_stock, 5, clave)
    assert primera.status_code == segunda.status_code == 201
    assert primera.json()["autorizacion_id"] == segunda.json()["autorizacion_id"]


def test_unidades_superiores_al_disponible_409(cliente_pagos, sku_con_stock):
    assert autorizar(cliente_pagos, sku_con_stock, 101).status_code == 409
