# Imagen base: Python 3.13 en versión "slim" (liviana, sin herramientas extra)
FROM python:3.13-slim

# Copia el ejecutable de uv desde su imagen oficial (misma versión que uso en mi PC)
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

# Carpeta de trabajo dentro del contenedor
WORKDIR /servicio

# 1) PRIMERO solo las dependencias. Docker guarda cada paso en "capas":
#    si solo cambio mi código, no vuelve a descargar FastAPI (build más rápido).
COPY pyproject.toml uv.lock ./
# --frozen: instala EXACTAMENTE lo de uv.lock | --no-dev: sin pytest ni httpx
RUN uv sync --frozen --no-dev --no-install-project

# 2) DESPUÉS el código
COPY app ./app

# Usa el Python del entorno virtual que creó uv; muestra los logs al instante
ENV PATH="/servicio/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Documenta el puerto de la ficha (8005)
EXPOSE 8005

# 0.0.0.0 = escuchar en todas las interfaces (con 127.0.0.1 nadie fuera del contenedor llegaría)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]