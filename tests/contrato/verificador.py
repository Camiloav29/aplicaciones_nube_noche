"""Compara un contrato (contratos.yaml) con el /openapi.json que publica un servicio."""
from pathlib import Path

import yaml

ARCHIVO = Path(__file__).with_name("contratos.yaml")


def cargar_contratos() -> dict:
    """Lee contratos.yaml y lo devuelve como diccionario."""
    return yaml.safe_load(ARCHIVO.read_text(encoding="utf-8"))


def incumplimientos(contrato: dict, openapi: dict) -> list[str]:
    """Lista lo que falta: rutas, verbos, title y version. Lista vacía = cumple el contrato."""
    faltan = []
    info = openapi.get("info", {})
    if not info.get("title"):
        faltan.append("falta info.title")
    if not info.get("version"):
        faltan.append("falta info.version")
    publicadas = openapi.get("paths", {})
    for ruta, verbos in contrato["rutas"].items():
        if ruta not in publicadas:
            faltan.append(f"falta la ruta {ruta}")
            continue
        for verbo in verbos:
            if verbo not in publicadas[ruta]:
                faltan.append(f"falta {verbo.upper()} {ruta}")
    return faltan
