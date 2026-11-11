FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /servicio

# Primero dependencias (capa en caché), luego el código.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

ENV PATH="/servicio/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# El puerto se toma de PUERTO_SERVICIO (por defecto 8004 en config.py).
# EXPOSE es solo documentación; no fija el puerto real.
EXPOSE 8004

CMD ["python", "-m", "app"]
