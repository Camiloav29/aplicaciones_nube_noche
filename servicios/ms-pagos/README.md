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
- [x] `POST /api/v1/autorizaciones` con `asyncio.gather` e idempotencia (`Idempotency-Key`)
- [x] `GET /api/v1/autorizaciones/{id}` y `PUT .../anulacion` idempotente
- [x] Traducción de fallos 404 / 409 / 402 / 502 / 503 / 504 con el nombre del servicio
- [x] Evidencia de los cinco criterios del Laboratorio 3

## Contrato

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health`, `/diagnostico` | 200 | — |
| POST | `/api/v1/autorizaciones` (`sku` 3–20, `unidades` 1–1000, `medio_pago` ∈ `tarjeta`/`pse`/`efectivo`, `reserva_id` opcional). Cabecera opcional `Idempotency-Key` | 201 + `Location` | 402, 404, 409, 422, 502, 503, 504 |
| GET | `/api/v1/autorizaciones/{autorizacion_id}` | 200 | 404 |
| PUT | `/api/v1/autorizaciones/{autorizacion_id}/anulacion` | 200 `estado:"ANULADA"` (idempotente) | 404 |

Dependencias consumidas: `GET {PAGOS_URL_CATALOGO}/productos/{sku}` (campo `precio`) y `GET {PAGOS_URL_INVENTARIO}/existencias/{sku}` (campo `disponible`). Con `reserva_id` solo se consulta el catálogo.

## Flujo de `POST /api/v1/autorizaciones`

1. Si la `Idempotency-Key` ya se usó, devuelve la misma autorización (201, cabecera `Idempotent-Replayed: true`) sin llamar a nadie.
2. Consulta precio y disponible **en paralelo** (`asyncio.gather`).
3. `disponible < unidades` → `409` con `sku`, `solicitado` y `disponible`.
4. `total = precio × unidades` con `Decimal` y 2 decimales; si supera `PAGOS_MONTO_MAXIMO` → `402`.
5. Guarda y responde `201` con `estado:"AUTORIZADA"`.

| Fallo de la dependencia | Respuesta |
|---|---|
| Conexión rechazada, sin DNS o sin conectar en 2 s | `503 {"detail":"<servicio> no disponible"}` |
| Conectó pero no respondió en 3 s | `504 {"detail":"<servicio> no respondio"}` |
| Respondió 5xx | `502 {"detail":"<servicio> respondio mal"}` |
| Respondió 404 | `404 {"detail":"No existe el producto con SKU X"}` |

## Estructura

```
app/
├── main.py            # lifespan, middleware, manejadores de errores, routers
├── dominio.py         # entidad Autorizacion (nunca sale por HTTP)
├── config.py          # Configuracion(BaseSettings) + get_configuracion()
├── dependencias.py    # ConfigDep, HttpDep, ServicioDep (arma el caso de uso)
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

## Evidencia (Laboratorio 3)

Obtenida con ms-pagos real y las dependencias simuladas de `scripts/dependencias_simuladas.py` (datos semilla de `CONVENCIONES.md`).

Para reproducirla, en tres terminales dentro de `servicios/ms-pagos`:

```bash
uv run python scripts/dependencias_simuladas.py catalogo     # 8001
uv run python scripts/dependencias_simuladas.py inventario   # 8002
uv run uvicorn app.main:app --port 8004
```

**1. Salud**

```text
$ curl -s localhost:8004/health
{"estado":"activo","servicio":"ms-pagos"}
```

**2. Autorización válida**

```text
$ curl -s -X POST localhost:8004/api/v1/autorizaciones -H "Content-Type: application/json" \
    -H "Idempotency-Key: pedido-001" -d '{"sku":"CAF-001","unidades":2,"medio_pago":"tarjeta"}'
{"autorizacion_id":"79c0f18d-b10f-4abb-aba4-cc5bcab81e28","sku":"CAF-001","unidades":2,"total":77000.0,"medio_pago":"tarjeta","reserva_id":null,"estado":"AUTORIZADA"}
HTTP 201
```

**3. Reintento con la misma clave** (mismo `autorizacion_id`, sin repetir el efecto)

```text
{"autorizacion_id":"79c0f18d-b10f-4abb-aba4-cc5bcab81e28","sku":"CAF-001","unidades":2,"total":77000.0,"medio_pago":"tarjeta","reserva_id":null,"estado":"AUTORIZADA"}
HTTP 201
```

**4. Unidades superiores al disponible**

```text
$ curl -s -X POST localhost:8004/api/v1/autorizaciones -H "Content-Type: application/json" \
    -d '{"sku":"CAF-001","unidades":101,"medio_pago":"pse"}'
{"detail":"Stock insuficiente para CAF-001","sku":"CAF-001","solicitado":101,"disponible":100}
HTTP 409
```

**5. ms-inventario apagado → 503 en menos de 4 s**

```text
$ curl -s -w "\nHTTP %{http_code} en %{time_total}s\n" -X POST localhost:8004/api/v1/autorizaciones \
    -H "Content-Type: application/json" -d '{"sku":"CAF-001","unidades":1,"medio_pago":"pse"}'
{"detail":"ms-inventario no disponible"}
HTTP 503 en 0.005150s
```

**Otras reglas**

```text
# SKU inexistente
{"detail":"No existe el producto con SKU ZZZ-999"}                       HTTP 404
# Total mayor que PAGOS_MONTO_MAXIMO (30 x 38500 = 1155000 > 1000000)
{"detail":"Pago rechazado","estado":"RECHAZADA"}                          HTTP 402
# Anulación repetida (idempotente)
PUT /api/v1/autorizaciones/{id}/anulacion  → 200 "estado":"ANULADA"   (dos veces)
```

**Pruebas**

```text
$ uv run pytest -q
28 passed
```

Cubren: 201, 402, 404, 409, 422, idempotencia, GET, anulación idempotente, 502/503/504 con `httpx.MockTransport`, ejecución en paralelo (`gather`) y 503 en menos de 4 s contra un puerto real cerrado.
