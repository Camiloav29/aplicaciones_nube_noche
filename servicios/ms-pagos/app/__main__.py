"""Arranque del servicio: ``python -m app``.

El host y el puerto salen de la configuración (``PUERTO_SERVICIO`` o
``PAGOS_PUERTO``; por defecto 8004), nunca de un valor fijo en el código.
"""

import uvicorn

from app.config import get_configuracion


def main() -> None:
    config = get_configuracion()
    uvicorn.run("app.main:app", host=config.host, port=config.puerto)


if __name__ == "__main__":
    main()
