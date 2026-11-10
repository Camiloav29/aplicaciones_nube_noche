FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir uv && addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
USER appuser\EXPOSE 8001
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
