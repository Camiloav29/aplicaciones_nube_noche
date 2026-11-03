# A04 · `ms-pedidos` — servicio compuesto (orquestador con saga)

| Dato | Valor |
|---|---|
| Tipo | Servicio **compuesto**: orquesta servicios core y **no tiene base de datos de dominio propia** |
| Puerto / prefijo | `8003` / `PEDIDOS_` |
| Carpeta | `servicios/ms-pedidos/` |
| Dificultad | 5 puntos · paquete **P1** (con A07) |
| Semanas | 2, 3 y 4 |
| Provee a | `bff-web` |
| Consume | `ms-catalogo`, `ms-inventario`, `ms-pagos` |

## Contexto del cliente

«Que la compra sea un solo paso.» `ms-pedidos` coordina catálogo, inventario y pagos. Guarda **el estado del pedido**, pero no guarda productos ni existencias.

## Contrato público

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health`, `/diagnostico` | 200 | — |
| POST | `/api/v1/pedidos` (`sku`, `unidades`, `medio_pago`). Cabecera opcional `Idempotency-Key` | 201 `{pedido_id, sku, unidades, total, estado:"CONFIRMADO", reserva_id, autorizacion_id}` | 404, 409, 402, 502, 503, 504, 422 |
| GET | `/api/v1/pedidos/{pedido_id}` | 200 | 404 |
| GET | `/api/v1/pedidos?estado=` | 200 lista | 422 |
| GET | `/api/v1/diagnostico/inventario` | 200 `{instancia, puerto}` de la réplica de inventario que atendió | 503 |

## La saga (orquestación con compensación)

```
T1  catálogo.obtener_producto  ┐ en paralelo (asyncio.gather)
T1' inventario.reservar        ┘
T2  pagos.autorizar (con reserva_id)
T3  emitir PedidoConfirmado (registro estructurado)

Compensaciones:
 - T1' hecho y T1 falla (SKU inexistente)  → liberar la reserva → 404
 - T2 rechazado (402)                      → liberar la reserva → estado ANULADO, 402, PedidoAnulado
 - T2 con pagos caído                      → liberar la reserva → 503/504, PedidoAnulado
 - T1' falla con 409                       → nada que compensar  → 409 con el disponible real
```

Entre T1 y T3 el sistema está temporalmente inconsistente; eso es la **consistencia eventual** aceptada. Documente en el `README` qué ve el cliente en cada fallo.

## Reglas de negocio

1. El `total` lo calcula el servicio (`precio * unidades`, `Decimal`), no el cliente.
2. Nunca queda una reserva huérfana: si el pedido no se confirma, la reserva se libera (`DELETE` de la reserva).
3. Con la misma `Idempotency-Key` se devuelve el mismo pedido sin volver a reservar ni a cobrar.
4. Los errores de dependencias se traducen según `CONVENCIONES.md` (`409` se propaga; `502`, `503`, `504` nombran al servicio).

## Requisitos técnicos

- Un único `httpx.AsyncClient` en el `lifespan`, con cuatro timeouts explícitos y lectura de 3 s hacia cada dependencia.
- `asyncio.gather(..., return_exceptions=True)` en T1/T1' para poder **compensar** cuando una llamada tuvo éxito y la otra no.
- Capas: `rutas/`, `servicios/pedidos.py` (**sin FastAPI**; lanza excepciones de dominio), `repositorios/` (estado del pedido y claves de idempotencia detrás de `Protocol`), `clientes/` (catálogo, inventario, pagos).
- `Configuracion` con `PEDIDOS_MODO_DESCUBRIMIENTO` (`estatico` o `consul`) y las URL de `CONVENCIONES.md`.
- En modo `consul`, resuelve `ms-inventario` con el balanceador de A09 y el resolvedor de A08 (módulos copiables a `app/`); `GET /api/v1/diagnostico/inventario` demuestra el reparto entre réplicas.
- Middleware de latencia con `structlog` (`ruta`, `estado`, `duracion_ms`).
- Registro en Consul con cancelación en `finally`.

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Orquestación y saga: T1–T3 y las **cuatro compensaciones** de la tabla funcionan (sin reservas huérfanas) | 8 |
| 2 | Concurrencia: `gather` con `return_exceptions=True` y decisión correcta según qué llamada falló | 4 |
| 3 | Cliente `httpx` único en el `lifespan`, cuatro timeouts, sin llamadas sin timeout | 4 |
| 4 | Traducción de fallos: `404`, `409`, `402`, `502`, `503` y `504` con el nombre del servicio | 4 |
| 5 | Idempotencia: reintento con la misma clave devuelve el mismo pedido sin repetir efectos | 3 |
| 6 | Capas, configuración externalizada y `servicios/` sin FastAPI | 3 |
| 7 | Modo `consul`: usa el balanceador y `/api/v1/diagnostico/inventario` muestra rotación entre réplicas | 2 |
| 8 | Calidad: 8 pruebas o más (incluyendo compensación) con `MockTransport` o dependencias simuladas, y `README` con la tabla de qué ve el cliente en cada fallo | 2 |

## Entregables

`servicios/ms-pedidos/` y, en su `README.md`, la salida de las nueve llamadas de la semana 4 (`8002 8012 8022 ...`) cuando A09 y A08 estén integrados, y una prueba documentada de cada compensación.

## Preguntas de sustentación

1. ¿Por qué `ms-pedidos` es compuesto y no core? Aplique la tabla de decisión de la semana 2.
2. ¿Qué es una saga y qué compensa cada paso? ¿Qué inconsistencia temporal ve el cliente?
3. ¿Qué habría pasado con `gather` sin `return_exceptions=True` cuando el catálogo responde `404` y la reserva ya se hizo?

## Extensión opcional

Reintento con `tenacity` solo para errores de red, verificado con la clave de idempotencia.
