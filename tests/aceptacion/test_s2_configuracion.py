"""Aceptación semana 2 (laboratorio 2): configuración externalizada y errores traducidos."""
import os
import subprocess
import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from simuladores import inventario

# Carpeta tests/ (desde ahí se puede importar simuladores)
CARPETA_TESTS = Path(__file__).resolve().parents[1]
# Código que se ejecuta en el proceso aparte: crear la app = arrancar el servicio
ARRANCAR = "from simuladores.inventario import crear_app; crear_app()"


# Arranca el servicio en un proceso aparte con las variables de entorno dadas
def arrancar_con(variables: dict) -> subprocess.CompletedProcess:
    entorno = {**os.environ, **variables}
    return subprocess.run([sys.executable, "-c", ARRANCAR], cwd=CARPETA_TESTS, env=entorno,
                          capture_output=True, text=True, timeout=30)


# Con INVENTARIO_ENTORNO=dev, /diagnostico debe mostrar "dev"
def test_diagnostico_refleja_el_perfil(monkeypatch):
    monkeypatch.setenv("INVENTARIO_ENTORNO", "dev")  # variable solo durante esta prueba
    with TestClient(inventario.crear_app()) as cliente:
        assert cliente.get("/diagnostico").json()["entorno"] == "dev"


# Control: con una configuración válida el proceso arranca bien (código de salida 0)
def test_configuracion_valida_arranca():
    assert arrancar_con({"INVENTARIO_RESERVA_MAXIMA_UNIDADES": "500"}).returncode == 0


# Con un valor inválido (0 < 1) el proceso falla al arrancar con ValidationError
def test_configuracion_invalida_impide_el_arranque():
    proceso = arrancar_con({"INVENTARIO_RESERVA_MAXIMA_UNIDADES": "0"})
    assert proceso.returncode != 0
    assert "ValidationError" in proceso.stderr


# El 409 de reserva excesiva trae detail, sku, solicitado y disponible
def test_reserva_excesiva_trae_sku_solicitado_y_disponible(cliente_inventario):
    sku = f"T-{uuid.uuid4().hex[:8]}"
    cliente_inventario.post("/api/v1/existencias", json={"sku": sku, "cantidad": 100})
    cuerpo = cliente_inventario.post(f"/api/v1/existencias/{sku}/reservas", json={"unidades": 500}).json()
    assert {"detail", "sku", "solicitado", "disponible"} <= cuerpo.keys()
    assert (cuerpo["sku"], cuerpo["solicitado"], cuerpo["disponible"]) == (sku, 500, 100)
