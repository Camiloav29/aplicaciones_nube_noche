# ms-pagos · MercadoAndino (A03)

Servicio **core con llamadas salientes**: autoriza el pago de un pedido antes de confirmarlo. Consulta el precio en `ms-catalogo` y el disponible en `ms-inventario`.

| Dato | Valor |
|---|---|
| Puerto | `8004` |
| Prefijo de variables | `PAGOS_` |
| Provee a | `ms-pedidos` |
| Consume | `ms-catalogo`, `ms-inventario` |

## Estado

- [x] Esqueleto en capas, `/health`, `/diagnostico`, `/openapi.json`, `/docs`
- [x] Configuración con `pydantic-settings` y fallo temprano
- [x] Cliente `httpx.AsyncClient` único en el `lifespan` con los cuatro timeouts y límites
- [x] Middleware de registros JSON (`ruta`, `estado`, `duracion_ms`)
- [ ] `POST /api/v1/autorizaciones` con `asyncio.gather` e idempotencia
- [ ] `GET /api/v1/autorizaciones/{id}` y `PUT .../anulacion`
- [ ] Traducción de fallos 409 / 502 / 503 / 504
- [ ] Evidencia de los cinco criterios del Laboratorio 3

## Estructura

```
app/
├── main.py            # lifespan, middleware, manejadores de errores, routers
├── config.py          # Configuracion(BaseSettings) + get_configuracion()
├── dependencias.py    # ConfigDep, HttpDep
├── esquemas.py        # contrato HTTP
├── errores.py         # excepciones de dominio (sin HTTPException)
├── rutas/             # solo traducen HTTP
├── servicios/         # casos de uso (no importa el framework web)
├── repositorios/      # Protocol + memoria
└── clientes/          # llamadas a ms-catalogo y ms-inventario
```

## Ejecutar en local

Requisitos: Python 3.13 y [`uv`](https://docs.astral.sh/uv/).

```bash
cd servicios/ms-pagos
uv sync
cp .env.example .env          # opcional
uv run uvicorn app.main:app --reload --port 8004
```

- Salud: http://localhost:8004/health
- Documentación: http://localhost:8004/docs

## Pruebas

```bash
uv run pytest -q
```

## Docker

```bash
docker build -t ms-pagos .
docker run --rm -p 8004:8004 -e PAGOS_ENTORNO=dev ms-pagos
```

## Configuración

| Variable | Defecto | Descripción |
|---|---|---|
| `PAGOS_ENTORNO` | `local` | `local`, `dev`, `test` o `prod` (en `prod` se apaga `/docs`) |
| `PAGOS_NIVEL_LOG` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` (se normaliza a mayúsculas) |
| `PAGOS_DOCS_HABILITADA` | `true` | Publica `/docs` |
| `PAGOS_MODO_DESCUBRIMIENTO` | `estatico` | `estatico` o `consul` |
| `PAGOS_URL_CATALOGO` | `http://localhost:8001/api/v1` | Solo en modo `estatico` |
| `PAGOS_URL_INVENTARIO` | `http://localhost:8002/api/v1` | Solo en modo `estatico` |
| `PAGOS_MONTO_MAXIMO` | `1000000.00` | Un total mayor se rechaza con `402` |
| `PAGOS_CARGAR_DATOS_EJEMPLO` | `false` | Datos semilla |
| `PAGOS_TIMEOUT_CONNECT` / `_READ` / `_WRITE` / `_POOL` | `2.0` / `3.0` / `2.0` / `1.0` | Relojes del cliente HTTP (segundos) |

Un valor inválido (por ejemplo `PAGOS_NIVEL_LOG=CHISME` o `PAGOS_MONTO_MAXIMO=0`) impide el arranque con `ValidationError`.

## Evidencia

```text
$ curl -s localhost:8004/health
{"estado":"activo","servicio":"ms-pagos"}

$ curl -s localhost:8004/diagnostico
{"entorno":"local","nivel_log":"INFO"}
```

<!-- Pendiente: autorización válida, reintento con la misma clave, 409 por unidades, 503 en < 4 s con ms-inventario apagado. -->
