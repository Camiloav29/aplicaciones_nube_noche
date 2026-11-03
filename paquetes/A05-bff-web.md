# A05 · `bff-web` — API de canal (Backend for Frontend)

| Dato | Valor |
|---|---|
| Tipo | Servicio **API**: adapta el sistema a un canal; solo **transforma y agrega, no decide** |
| Puerto / prefijo | `8080` / `BFF_` |
| Carpeta | `servicios/bff-web/` |
| Dificultad | 3 puntos · paquete **P5** (con A09) |
| Semanas | 3 y 4 |
| Provee a | clientes web y móvil (más adelante, el gateway) |
| Consume | `ms-catalogo`, `ms-inventario`, `ms-pedidos` |

## Contexto del cliente

«La app móvil no debe hacer seis llamadas.» Sin BFF, la app haría cinco viajes por la red móvil y conocería la topología interna. Con BFF hace uno.

## Contrato público

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health`, `/diagnostico` | 200 | — |
| GET | `/bff/v1/fichas/{sku}` | 200 `{sku, nombre, categoria, precio (str), disponible}` | 404, 502, 503, 504 |
| GET | `/bff/v1/catalogo?categoria=&limite=` (máx. 20) | 200 lista de fichas | 422 |
| POST | `/bff/v1/compras` (`sku`, `unidades`, `medio_pago`). Cabecera opcional `Idempotency-Key` | 201 `{pedido_id, total, estado, mensaje}` | 404, 409, 402, 502, 503, 504, 422 |

## Reglas

1. **No decide**: no calcula totales, no valida stock, no aplica reglas de negocio. Reenvía a `ms-pedidos` y reformatea.
2. La ficha agrega catálogo e inventario **en paralelo** (`asyncio.gather`): la latencia es la de la llamada más lenta.
3. **Degradación elegante** en `GET /bff/v1/catalogo`: si el inventario de un SKU falla, esa ficha sale con `"disponible": null` y `"degradado": true`; el catálogo completo **no** falla por un solo SKU.
4. La respuesta es «a la medida del canal»: no incluye campos internos (`reservadas`, `bodega`, identificadores de reserva o autorización).
5. `Idempotency-Key` se reenvía **tal cual** a `ms-pedidos`.
6. Traduce los fallos de dependencias a `502`, `503` o `504` con el nombre del servicio, y propaga `404`, `409` y `402` de negocio.
7. Presupuesto de timeouts: lectura hacia `ms-pedidos` de 8 s y hacia catálogo e inventario de 3 s (el gateway de la semana 7 esperará 10 s).

## Requisitos técnicos

- Un solo `httpx.AsyncClient` en el `lifespan`, con cuatro timeouts explícitos.
- Esquemas propios del canal (`FichaProducto`, `CompraSolicitud`, `CompraRespuesta`): no reutilice los de otro servicio.
- `Configuracion` con `BFF_MODO_DESCUBRIMIENTO` (`estatico`/`consul`) y las URL de dependencias. En modo `consul`, resuelve `ms-catalogo`, `ms-inventario` y `ms-pedidos` con el balanceador de A09.
- Capas: `rutas/`, `servicios/` (agregación sin FastAPI), `clientes/`.
- Middleware de latencia con `structlog`.
- Registro en Consul con cancelación en `finally`.

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Agregación: ficha y catálogo con `asyncio.gather`, respuesta a la medida del canal | 7 |
| 2 | Degradación elegante: un SKU sin inventario no tumba el catálogo | 4 |
| 3 | Compras: reenvío con `Idempotency-Key`, respuesta reducida y traducción de errores `402`/`409`/`502`/`503`/`504` | 5 |
| 4 | El BFF no decide: ninguna regla de negocio, esquemas propios del canal | 3 |
| 5 | Cliente `httpx` único en el `lifespan`, cuatro timeouts y presupuesto de timeouts respetado | 4 |
| 6 | Capas, configuración externalizada y `servicios/` sin FastAPI | 3 |
| 7 | Modo `consul`: resuelve las dependencias con el balanceador de A09 | 2 |
| 8 | Calidad: pruebas (incluyendo la degradación) con `MockTransport`, `README` y `Dockerfile` | 2 |

## Entregables

`servicios/bff-web/` y, en su `README.md`, la salida de `curl localhost:8080/bff/v1/fichas/CAF-001` y un ejemplo de ficha degradada, más una comparación de **5 viajes frente a 1** (diagrama o tabla).

## Preguntas de sustentación

1. ¿Qué problemas resuelve el BFF y por qué «no decide»?
2. ¿Qué pasa con la latencia si en vez de `gather` encadena `await`? Dé números con 80 ms y 120 ms.
3. ¿Por qué el timeout del BFF debe ser menor que el del gateway?

## Extensión opcional

Cabecera `Deprecation` y segundo prefijo `/bff/v2` para un cambio rompiente en la ficha.
