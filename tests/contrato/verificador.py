"""Compara un contrato (contratos.yaml) con el /openapi.json que publica un servicio."""
from pathlib import Path

import yaml

# Ruta del archivo contratos.yaml (en la misma carpeta que este archivo)
ARCHIVO = Path(__file__).with_name("contratos.yaml")


# Lee contratos.yaml y lo devuelve como diccionario de Python
def cargar_contratos() -> dict:
    return yaml.safe_load(ARCHIVO.read_text(encoding="utf-8"))


# Lista lo que falta (title, version, rutas y verbos). Lista vacía = cumple el contrato
def incumplimientos(contrato: dict, openapi: dict) -> list[str]:
    faltan = []
    # 1. El openapi debe declarar title y version
    info = openapi.get("info", {})
    if not info.get("title"):
        faltan.append("falta info.title")
    if not info.get("version"):
        faltan.append("falta info.version")
    # 2. Cada ruta acordada debe existir con cada uno de sus verbos
    publicadas = openapi.get("paths", {})
    for ruta, verbos in contrato["rutas"].items():
        if ruta not in publicadas:
            faltan.append(f"falta la ruta {ruta}")
            continue
        for verbo in verbos:
            if verbo not in publicadas[ruta]:
                faltan.append(f"falta {verbo.upper()} {ruta}")
    return faltan
