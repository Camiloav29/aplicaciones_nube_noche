# A12 · Integración E2E y Docker Compose

| Dato | Valor |
|---|---|
| Tipo | Plataforma: ensamblar y demostrar que todo funciona junto |
| Archivos | `docker-compose.yml`, `.env.example`, `scripts/levantar.sh`, `scripts/e2e.sh`, `docs/E2E.md` |
| Dificultad | 4 puntos · paquete **P4** (con A01) |
| Semanas | 1, 3 y 4 |
| Provee a | la nota de integración del grupo (15 puntos de la rúbrica) |
| Consume | los `Dockerfile` y puertos de los seis servicios, Consul (A08) y `config-repo` (A07) |

## Contexto del cliente

«Despliegue con un solo comando y demuéstreme que funciona.» Esta acción es el pegamento del parcial: sin ella, seis servicios correctos no forman una plataforma.

## Qué debe construir

### 1. `docker-compose.yml`

Levanta, con **`docker compose up --build`**, todos los componentes:

| Servicio | Observación |
|---|---|
| `consul` | `hashicorp/consul:1.21`, `agent -dev`, puertos 8500 y 8600/udp |
| `ms-catalogo` | 8001 |
| `ms-inventario-1`, `ms-inventario-2`, `ms-inventario-3` | puertos 8002, 8012, 8022; `PUERTO_SERVICIO`, `HOST_ANUNCIADO` (el nombre del contenedor, **no `localhost`**) y `PESO_SERVICIO` por réplica |
| `ms-pagos` | 8004 |
| `ms-pedidos` | 8003, `PEDIDOS_MODO_DESCUBRIMIENTO=consul` |
| `bff-web` | 8080, `BFF_MODO_DESCUBRIMIENTO=consul` |
| `ms-confiabilidad` | 8005 |

Con `healthcheck` por servicio (consulta a `/health`) y `depends_on` con `condition: service_healthy` donde corresponda. Las variables salen de `.env` (ignorado por Git) con `.env.example` versionado y de los perfiles de `config-repo` (A07). **Ninguna credencial** en el repositorio.

### 2. `Dockerfile`s (revisión transversal)

Revise y acuerde con cada dueño: imagen base delgada, instalación con `uv` a partir de `uv.lock`, **usuario sin privilegios**, `.dockerignore` (sin `.venv`, `.env`, `.git`), `EXPOSE` correcto y arranque con `uvicorn app.main:app --host 0.0.0.0`.

### 3. `scripts/e2e.sh` — el recorrido de aceptación del grupo

Imprime `PASS` o `FAIL` por verificación y termina con código distinto de cero si alguna falla. Debe cubrir **al menos nueve** verificaciones:

| # | Verificación |
|---|---|
| 1 | `/health` de los siete servicios (y réplicas) → `200` |
| 2 | Las tres réplicas de `ms-inventario` aparecen **sanas** en Consul |
| 3 | `GET /bff/v1/fichas/CAF-001` → `200` con nombre, precio y disponible |
| 4 | `POST /bff/v1/compras` válido → `201` |
| 5 | Reintento con la **misma `Idempotency-Key`** → mismo `pedido_id` |
| 6 | Compra de más unidades que el disponible → `409` con `disponible` |
| 7 | SKU inexistente `ZZZ-999` → `404` |
| 8 | El reparto entre réplicas (nueve llamadas a `/api/v1/diagnostico/inventario`) rota entre tres puertos |
| 9 | Se detiene una réplica: en menos de 30 s deja de aparecer en Consul y el consumidor sigue respondiendo `200` |
| 10 | Se detiene `ms-inventario` por completo: `ms-pagos` responde `503` en menos de 4 s con el nombre del servicio |

`scripts/levantar.sh` arma el entorno, espera a que todo esté sano y ejecuta los datos semilla de `CONVENCIONES.md`.

### 4. `docs/E2E.md`

La **salida completa** de una ejecución exitosa de `e2e.sh` y una **bitácora de integración**: cada problema que apareció al juntar los servicios (rutas, puertos, formatos de error, claves de configuración…), quién era el dueño, el issue o PR donde se resolvió. Esta bitácora es evidencia del trabajo colaborativo.

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | `docker compose up --build` levanta la plataforma completa con `healthcheck` y orden de arranque correcto | 7 |
| 2 | `e2e.sh` cubre al menos nueve verificaciones con salida `PASS`/`FAIL` y código de salida correcto | 8 |
| 3 | Los escenarios de falla (réplica caída, `ms-inventario` apagado) están **automatizados** y con tiempos verificados | 5 |
| 4 | `Dockerfile`s revisados: `uv`, usuario sin privilegios, `.dockerignore`, sin secretos | 4 |
| 5 | Datos semilla, `.env.example` y ausencia de credenciales | 2 |
| 6 | `docs/E2E.md` con la salida real y la bitácora de integración | 4 |

## Preguntas de sustentación

1. ¿Por qué `HOST_ANUNCIADO` no puede ser `localhost` dentro de un contenedor?
2. Tras apagar una réplica, ¿qué tiempos suman el retraso real de expulsión?
3. ¿Qué diferencia hay entre `liveness` y `readiness`, y cuál debe consultar Consul?
