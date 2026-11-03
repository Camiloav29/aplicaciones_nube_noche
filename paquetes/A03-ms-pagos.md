# A03 · `ms-pagos` — autorización de pagos con llamadas salientes

| Dato | Valor |
|---|---|
| Tipo | Servicio **core** con llamadas salientes a `ms-catalogo` y `ms-inventario` |
| Puerto / prefijo | `8004` / `PAGOS_` |
| Carpeta | `servicios/ms-pagos/` |
| Dificultad | 4 puntos · paquete **P2** (con A11) |
| Semanas | 1, 2 y 3 |
| Provee a | `ms-pedidos` |
| Consume | `ms-catalogo` (precio) y `ms-inventario` (disponible) |

## Contexto del cliente

«Autorice el pago de un pedido antes de confirmarlo.» El servicio es suyo: usted decide nombres de campos internos, política de reintentos y estructura, siempre que respete el contrato.

## Contrato público

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health`, `/diagnostico` | 200 | — |
| POST | `/api/v1/autorizaciones` (`sku`, `unidades` 1–1000, `medio_pago` ∈ `tarjeta`/`pse`/`efectivo`, `reserva_id` opcional). Cabecera opcional `Idempotency-Key` | 201 `{autorizacion_id, sku, unidades, total, estado:"AUTORIZADA"}` | 409, 402, 404, 502, 503, 504, 422 |
| GET | `/api/v1/autorizaciones/{autorizacion_id}` | 200 | 404 |
| PUT | `/api/v1/autorizaciones/{autorizacion_id}/anulacion` | 200 `estado:"ANULADA"` (idempotente) | 404 |

`reserva_id` es un **campo opcional agregado** (cambio compatible según la ley de Postel): si viene, `ms-pagos` entiende que `ms-pedidos` ya reservó las unidades y **omite** la verificación de disponible; solo consulta el precio.

## Reglas de negocio

1. Sin `reserva_id`: consulta el precio en `ms-catalogo` **y** el disponible en `ms-inventario` en la misma operación. Si el disponible es menor a `unidades`, `409` con las unidades reales.
2. `total = precio * unidades` (con `Decimal`, 2 decimales).
3. Si `total` supera `PAGOS_MONTO_MAXIMO`, responde `402` con `estado:"RECHAZADA"`.
4. Con la misma `Idempotency-Key`, devuelve el **mismo** `autorizacion_id` y `201`, sin repetir el efecto.
5. Si una dependencia no responde: conexión rechazada → `503`, timeout de lectura → `504`, respuesta 5xx → `502`; el `detail` nombra al servicio (`"ms-inventario no disponible"`). **Con inventario apagado, responde en menos de 4 s.**
6. Anular una autorización ya anulada devuelve `200` con el mismo estado.

## Requisitos técnicos

- **Un único** `httpx.AsyncClient` creado en el `lifespan` y guardado en `app.state`; inyectado con `Annotated[..., Depends(obtener_http)]`.
- `httpx.Timeout` con los **cuatro relojes explícitos** (`connect=2.0`, `read=3.0`, `write=2.0`, `pool=1.0`) y `httpx.Limits`.
- Las dos llamadas salientes se ejecutan **concurrentemente** con `asyncio.gather`.
- Manejo diferenciado de `HTTPStatusError`, `TimeoutException` y `RequestError`. Las URL provienen de `pydantic-settings` (`PAGOS_URL_CATALOGO`, `PAGOS_URL_INVENTARIO`).
- Almacén de autorizaciones y de claves de idempotencia detrás de un `Protocol` (memoria).
- Middleware que registra `ruta`, `estado` y `duracion_ms` con `structlog`.
- **Prohibido:** `requests`, crear un cliente dentro de una ruta o dejar una llamada saliente sin timeout.

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Cliente HTTP único en el `lifespan` con los cuatro timeouts y límites explícitos | 6 |
| 2 | `asyncio.gather` en las dos llamadas salientes (la latencia es la de la más lenta, no la suma) | 3 |
| 3 | Manejo de fallos: `409`, `502`, `503` y `504` diferenciados con el nombre del servicio; **sin cuelgues** con la dependencia caída (< 4 s) | 6 |
| 4 | Idempotencia: el reintento con la misma clave devuelve la misma autorización | 5 |
| 5 | Contrato y reglas: `201`, `402`, `404`, `GET` y anulación idempotente | 5 |
| 6 | Capas, configuración externalizada (URL no fijas en el código) y servicio sin `HTTPException` | 3 |
| 7 | Calidad: pruebas con `httpx.MockTransport` o `dependency_overrides` que cubren el `409` y el `503` | 2 |

## Entregables

`servicios/ms-pagos/` y, en su `README.md`, las capturas o salidas de `curl` de los cinco criterios del Laboratorio 3: salud, autorización válida, reintento con la misma clave, unidades superiores al disponible (`409`) y **apagado de `ms-inventario` → `503` en menos de 4 s**.

## Preguntas de sustentación

1. ¿Por qué un `POST` necesita clave de idempotencia y un `PUT` no?
2. ¿Qué pasa con el pool de conexiones si no hay timeout y la dependencia se pone lenta?
3. ¿Por qué `409` se propaga tal cual y `503` se traduce?

## Extensión opcional

`tenacity` con reintento exponencial solo para errores de red, verificando con la clave de idempotencia que el reintento no duplica la autorización.
