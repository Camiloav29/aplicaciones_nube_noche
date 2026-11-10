"""Revisa el código fuente: todo httpx.AsyncClient debe tener timeout y no crearse dentro de una ruta."""
import ast
from pathlib import Path

VERBOS = {"get", "post", "put", "delete", "patch"}


def es_ruta(funcion: ast.AST) -> bool:
    """True si la función tiene un decorador tipo @router.get(...) o @app.post(...)."""
    for d in getattr(funcion, "decorator_list", []):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in VERBOS:
            return True
    return False


def problemas_en_codigo(codigo: str, archivo: str = "<código>") -> list[str]:
    """Devuelve los AsyncClient mal creados en un texto de Python."""
    problemas = []
    arbol = ast.parse(codigo)
    for funcion in [n for n in ast.walk(arbol) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        for nodo in ast.walk(funcion):
            if isinstance(nodo, ast.Call) and getattr(nodo.func, "attr", getattr(nodo.func, "id", "")) == "AsyncClient":
                if es_ruta(funcion):
                    problemas.append(f"{archivo}:{nodo.lineno} AsyncClient creado por petición en la ruta {funcion.name}")
                if not any(k.arg == "timeout" for k in nodo.keywords):
                    problemas.append(f"{archivo}:{nodo.lineno} AsyncClient sin timeout")
    return sorted(set(problemas))


def problemas_en_servicios(raiz: Path) -> list[str]:
    """Aplica la revisión a todos los servicios/*/app/**/*.py del repositorio."""
    problemas = []
    for archivo in sorted(raiz.glob("servicios/*/app/**/*.py")):
        problemas += problemas_en_codigo(archivo.read_text(encoding="utf-8"), str(archivo.relative_to(raiz)))
    return problemas
