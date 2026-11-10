"""Aceptación semana 1 (laboratorio 1): salud y reglas básicas de inventario (A02)."""
import uuid

import pytest


@pytest.fixture
def sku_con_stock(cliente_inventario) -> str:
    """Da de alta un SKU único con 100 unidades (único para no chocar con otras réplicas o pruebas)."""
    sku = f"T-{uuid.uuid4().hex[:8]}"
    r = cliente_inventario.post("/api/v1/existencias", json={"sku": sku, "cantidad": 100})
    assert r.status_code == 201
    return sku


def test_salud_200(cliente_inventario):
    assert cliente_inventario.get("/health").status_code == 200


def test_alta_de_stock_201(cliente_inventario):
    r = cliente_inventario.post("/api/v1/existencias", json={"sku": f"T-{uuid.uuid4().hex[:8]}", "cantidad": 100})
    assert r.status_code == 201


def test_reserva_valida_201_deja_disponible_90(cliente_inventario, sku_con_stock):
    r = cliente_inventario.post(f"/api/v1/existencias/{sku_con_stock}/reservas", json={"unidades": 10})
    assert r.status_code == 201
    assert r.json()["disponible"] == 90


def test_reserva_excesiva_409(cliente_inventario, sku_con_stock):
    # 500 > 100 disponibles pero < 1000 (tope): así da 409 y no 422
    r = cliente_inventario.post(f"/api/v1/existencias/{sku_con_stock}/reservas", json={"unidades": 500})
    assert r.status_code == 409


def test_sku_inexistente_404(cliente_inventario):
    assert cliente_inventario.get("/api/v1/existencias/NO-EXISTE-999").status_code == 404
