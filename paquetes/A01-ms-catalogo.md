# A01 · `ms-catalogo` — servicio core de productos

| Dato | Valor |
|---|---|
| Tipo | Servicio **core** (posee el dominio de productos y sus datos) |
| Puerto / prefijo | `8001` / `CATALOGO_` |
| Carpeta | `servicios/ms-catalogo/` |
| Dificultad | 3 puntos · paquete **P4** (con A12) |
| Semanas | 1, 2 y 4 (registro en Consul) |
| Provee a | `ms-pagos`, `ms-pedidos`, `bff-web` |
| Consume | nada (un core no llama a otros servicios de negocio) |

## Contexto del cliente

«Quiero ver el catálogo filtrado por categoría.» El catálogo es dueño del significado de *Producto* en su contexto delimitado: `sku`, `nombre`, `descripción`, `categoría`, `precio`. Otros contextos (pedidos) usan el mismo sustantivo con otros atributos.

## Contrato público (invariante: no cambia al refactorizar)

| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/health` | 200 | — |
| GET | `/diagnostico` | 200 `{entorno, nivel_log}` | — |
| GET | `/api/v1/productos?categoria=&limite=` | 200 lista | 422 si `limite` supera `pagina_tamano_maximo` |
| GET | `/api/v1/productos/{sku}` | 200 | 404 |
| POST | `/api/v1/productos` | 201 con cabecera `Location` | 409 SKU repetido, 422 |
| PUT | `/api/v1/productos/{sku}` | 200 (reemplazo completo) | 404, 422 |
| DELETE | `/api/v1/productos/{sku}` | 204 | 404 |

Esquemas: `ProductoCrear` (`sku` 3–20, `nombre` 1–120, `precio` `Decimal` > 0 con 2 decimales, `categoria` 1–60) y `ProductoRespuesta` (los anteriores y `activo: bool = True`). **Nunca** se devuelve la entidad de dominio.

## Reglas de negocio

1. El `sku` es único: crear uno existente responde `409`.
2. El `limite` por defecto es 20 y no puede superar `pagina_tamano_maximo` (configurable, 1 a 200).
3. `PUT` reemplaza todo el recurso; no crea si no existe.
4. Con `CATALOGO_CARGAR_DATOS_EJEMPLO=true` carga los cinco productos de `CONVENCIONES.md`.

## Requisitos técnicos

- Estructura en capas de `CONVENCIONES.md`; `servicios/catalogo.py` no importa FastAPI.
- `Configuracion` con prefijo `CATALOGO_` y al menos: `entorno`, `nivel_log` (validado), `docs_habilitada`, `tipo_repositorio` (`Literal["memoria","sql"]`), `pagina_tamano_maximo` (`Field(ge=1, le=200)`).
- Repositorio declarado como `Protocol` con implementación en memoria y fábrica seleccionada por configuración.
- Excepciones de dominio (`ProductoNoEncontrado`, `ProductoDuplicado`) traducidas a 404 y 409 por manejadores en `main.py`.
- Registro en Consul al arrancar y cancelación en el `finally` del `lifespan` (usa el módulo de A08 o uno propio equivalente), con `/health` como comprobación.
- `Dockerfile`, `README.md` con instrucciones, `pyproject.toml` y `uv.lock`.
- Al menos 6 pruebas con `pytest` (incluya 404, 409 y la regla del límite; use `app.dependency_overrides` para la configuración).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Contrato REST: rutas, verbos, versionado `/api/v1`, `201` con `Location`, `204`, `404`, `409` y `422` correctos | 8 |
| 2 | Validación con Pydantic v2: esquemas de entrada y salida distintos, sin validaciones manuales redundantes | 4 |
| 3 | Arquitectura en capas: `grep -r fastapi app/servicios/` vacío; excepciones de dominio con manejador único | 6 |
| 4 | Configuración externalizada: 5 campos o más, fallo temprano (`pagina_tamano_maximo=0` impide arrancar), `/diagnostico` sin secretos | 5 |
| 5 | Patrón repositorio: `Protocol`, implementación en memoria y fábrica por configuración | 3 |
| 6 | Registro y cancelación en Consul con identificador único, y `/health` operativo | 2 |
| 7 | Calidad: 6 pruebas o más, `title` y `version` en `/docs`, `Dockerfile`, `.gitignore` con `.venv` y `.env` | 2 |

## Entregables

`servicios/ms-catalogo/` completo, más una sección en su `README.md` con las salidas de `curl` de los criterios 1 y 4.

## Preguntas de sustentación

1. ¿Por qué `ms-catalogo` no debe leer las existencias de `ms-inventario` aunque «el dato esté al lado»?
2. ¿Cuántas líneas cambiaría para correr en `prod` con otra base y otro nivel de registro, y por qué eso es un asunto de arquitectura?
3. ¿Qué diferencia hay entre `404`, `409` y `422` en este servicio?

## Extensión opcional

`RepositorioSQL` con SQLModel y SQLite seleccionado por `CATALOGO_TIPO_REPOSITORIO`, sin tocar la capa de servicio.
