# A02 · `ms-inventario` — servicio core de existencias

| Dato | Valor |
|---|---|
| Tipo | Servicio **core** |
| Puerto / prefijo | `8002` (réplicas `8012` y `8022`) / `INVENTARIO_` |
| Carpeta | `servicios/ms-inventario/` |
| Dificultad | 3 puntos · paquete **P3** (con A08) |
| Semanas | 1, 2 y 4 |
| Provee a | `ms-pagos`, `ms-pedidos`, `bff-web` |
| Consume | nada |

## Contexto del cliente

«No quiero vender lo que no tengo.» `ms-inventario` conoce, en todo momento, cuántas unidades de cada SKU hay disponibles en bodega. **Tiene prohibido acceder a los datos de `ms-catalogo`.**

## Contrato público

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health` | 200 | — |
| GET | `/diagnostico` | 200 `{entorno, nivel_log}` | — |
| GET | `/api/v1/diagnostico` | 200 `{instancia, puerto}` (qué réplica atendió) | — |
| GET | `/api/v1/existencias?bodega=&limite=&desplazamiento=` | 200 lista paginada | 422 |
| GET | `/api/v1/existencias/{sku}` | 200 con `disponible` | 404 |
| POST | `/api/v1/existencias` (`sku`, `bodega`, `cantidad`) | 201 | 409 si ya existe, 422 |
| PUT | `/api/v1/existencias/{sku}` (`cantidad`) | 200 | 404, 422 |
| POST | `/api/v1/existencias/{sku}/reservas` (`unidades` 1 a `reserva_maxima_unidades`) | 201 `{reserva_id, sku, unidades, disponible}` | 404, 409, 422 |
| DELETE | `/api/v1/existencias/{sku}/reservas/{reserva_id}` | 204 (libera solo esa reserva) | 404 |

Modelo `Existencia`: `sku` (3–20), `bodega` (defecto `bodega_por_defecto`), `cantidad` ≥ 0, `reservadas` ≥ 0 y propiedad `disponible = cantidad - reservadas`.

## Reglas de negocio

1. **Una reserva que excede el disponible se rechaza con `409`** y un cuerpo `{"detail", "sku", "solicitado", "disponible"}` con las unidades reales.
2. Reservar suma a `reservadas`; liberar resta exactamente las unidades de esa reserva.
3. La capa de servicio lanza `StockInsuficiente` y `ExistenciaNoEncontrada` (sin `HTTPException`); el manejador en `main.py` las traduce.
4. `GET /api/v1/existencias` respeta `pagina_tamano_maximo`.
5. Con `INVENTARIO_CARGAR_DATOS_EJEMPLO=true` carga las existencias de `CONVENCIONES.md`.

## Requisitos técnicos

- `Configuracion` con prefijo `INVENTARIO_` y al menos: `entorno`, `nivel_log` (validado), `pagina_tamano_maximo` (`ge=1, le=500`), `reserva_maxima_unidades` (1 a 1000) y `bodega_por_defecto` (máx. 40).
- Repositorio como `Protocol` con implementación en memoria.
- Se ejecuta en tres réplicas (puertos 8002, 8012, 8022) y `PUERTO_SERVICIO` define cuál es cada una.
- **Registro en Consul** al arrancar con identificador `ms-inventario-<host>-<puerto>`, comprobación HTTP a `/health` cada 10 s, **cancelación en el `finally` del `lifespan`** y etiqueta `peso=N` por réplica. Se apoya en el módulo de A08 (o uno equivalente propio si A08 aún no lo publica).
- El servicio es **sin estado** compartido entre réplicas salvo su repositorio (documente en el `README` qué implica que cada réplica tenga su memoria y cómo lo resolvería con una base por servicio).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Contrato REST: rutas, verbos, `/api/v1`, `201`, `204`, `404`, `409` y `422` correctos | 7 |
| 2 | Regla de reserva: `409` con `sku`, `solicitado` y `disponible`; liberación de una reserva individual; `404` en SKU inexistente | 8 |
| 3 | Capas y excepciones de dominio: `grep -r fastapi app/servicios/` vacío; manejador único | 5 |
| 4 | Configuración externalizada: cinco campos, fallo temprano, `/diagnostico` sin secretos | 4 |
| 5 | Patrón repositorio con `Protocol` y aislamiento en su propio módulo | 2 |
| 6 | Tres réplicas registradas con identificador único, cancelación en `finally` y `/api/v1/diagnostico` que revela la réplica | 3 |
| 7 | Calidad: pruebas (incluya el caso `409`), `title` y `version`, `Dockerfile`, `README` | 1 |

## Entregables

`servicios/ms-inventario/` y, en su `README.md`, la salida de los cinco criterios de la semana 1 (salud, alta de stock, reserva válida con disponible 90, reserva excesiva `409`, SKU inexistente `404`) y una captura de Consul con las tres réplicas en verde.

## Preguntas de sustentación

1. ¿Por qué `StockInsuficiente` no extiende `HTTPException` y dónde se traduce a `409`?
2. ¿Qué ocurre con una réplica registrada pero no lista? ¿Por qué es peor que una ausente?
3. Si dos réplicas tienen memoria propia, ¿qué estado se pierde y cómo se corrige respetando «una base por servicio»?

## Extensión opcional

Paginación con `limite` y `desplazamiento`, campo `actualizado_en` con zona horaria y `/health/live` y `/health/ready` por separado (registrar en Consul solo la segunda).
