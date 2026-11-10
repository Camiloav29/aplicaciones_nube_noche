# Pruebas transversales de MercadoAndino (A10)

Autor: Carlos Andrés Wilches Guerra · Acción A10

Estas pruebas **no reemplazan** las pruebas unitarias de cada servicio. Son la red de seguridad del grupo: verifican que los servicios cumplen lo acordado en las fichas.

## Por qué hay simuladores

El día de la entrega varios servicios aún no existían. Por indicación del docente, las pruebas corren contra **simuladores** (`simuladores/`) que implementan el mismo contrato que las fichas:

| Simulador | Simula | Qué tiene |
|---|---|---|
| `simuladores/inventario.py` | `ms-inventario` (A02) | Existencias y reservas en memoria, 404/409/422, configuración `INVENTARIO_` |
| `simuladores/pagos.py` | `ms-pagos` (A03) | Autorizaciones, `Idempotency-Key`, consulta a inventario por HTTP con timeout, 503/504/502 |
| `simuladores/balanceador.py` | registro (A08) y balanceador (A09) | Chequeo `/health` y reparto ponderado por pesos |

Cada prueba usa el **servicio real** si se define su URL, y el simulador si no:

| Variable | Ejemplo |
|---|---|
| `URL_MS_INVENTARIO` | `http://localhost:8002` |
| `URL_MS_PAGOS` | `http://localhost:8004` |
| `URL_MS_CATALOGO`, `URL_MS_PEDIDOS`, `URL_BFF_WEB`, `URL_MS_CONFIABILIDAD` | Solo para las pruebas de contrato (por defecto `http://localhost:<puerto>`) |

La prueba `test_simulador_cumple_contrato` garantiza que los simuladores respetan `contratos.yaml`. Si no lo respetaran, las pruebas de aceptación darían un resultado falso.

## Cómo ejecutar

Desde la carpeta `tests/`:

```bash
uv sync
uv run pytest -v                   # todo (contrato, aceptación con simuladores y resiliencia)
uv run pytest contrato -v          # solo contrato
uv run pytest aceptacion -v        # solo aceptación (semanas 1 a 4)
uv run pytest -m resiliencia -v    # solo resiliencia con contenedores reales
```

Contra la plataforma real levantada con `docker compose up`:

```bash
set URL_MS_INVENTARIO=http://localhost:8002
set URL_MS_PAGOS=http://localhost:8004
uv run pytest -v
```

Las pruebas que dependen de un servicio apagado se **saltan** (`SKIPPED`) con un mensaje que dice qué levantar. Nunca fallan en silencio, y las pruebas del detector y de los simuladores corren siempre, así el CI nunca pasa «sin verificar nada».

## Integración continua (`.github/workflows/ci.yml`)

En cada Pull Request y en cada push a `main`:

1. **Reglas:** `scripts/verificar_estructura.sh` y `grep` que exige que ninguna capa `app/servicios/` importe FastAPI.
2. **Descubrir:** lista los servicios que tienen `pyproject.toml`. La matriz crece sola cuando un compañero integra su servicio.
3. **Matriz por servicio:** `uv sync` y `pytest --cov=app --cov-fail-under=70`, con el resumen de cobertura publicado en la pestaña *Summary* de la ejecución.
4. **Transversales:** `uv run pytest -v` en esta carpeta.

### Umbral de cobertura: 70 %

- **Por qué no 100 %:** obliga a probar líneas triviales (por ejemplo, los `__init__.py` o los registros de log) y premia pruebas que no verifican nada.
- **Por qué no 50 %:** con la mitad del código sin ejecutar, pueden quedar sin probar reglas de negocio completas, como el 409 de una reserva.
- **70 %** es un punto medio habitual: cubre los caminos principales y los errores de negocio. Como referencia, `ms-confiabilidad` (A06) tiene **95 %**.
- Si un servicio baja del 70 %, su trabajo en la matriz queda en rojo y el PR no debería integrarse.

## Matriz de trazabilidad (requisito → prueba)

| Requisito (ficha / laboratorio) | Prueba |
|---|---|
| A10 · contrato de los 6 servicios en `contratos.yaml` | `contrato/test_contratos.py::test_contratos_yaml_cubre_los_seis_servicios` |
| A10 · la prueba detecta una ruta faltante | `contrato/test_contratos.py::test_detecta_ruta_faltante` |
| A10 · la prueba detecta un verbo faltante | `contrato/test_contratos.py::test_detecta_verbo_faltante` |
| A10 · `title` y `version` definidos | `contrato/test_contratos.py::test_detecta_title_y_version_vacios` |
| A01–A06 · cada servicio levantado publica sus rutas | `contrato/test_contratos.py::test_servicio_real_cumple_contrato[<servicio>]` |
| Los simuladores respetan el contrato | `contrato/test_contratos.py::test_simulador_cumple_contrato` |
| Lab 1 · salud 200 | `aceptacion/test_s1_inventario.py::test_salud_200` |
| Lab 1 · A02 alta de stock 201 | `aceptacion/test_s1_inventario.py::test_alta_de_stock_201` |
| Lab 1 · A02 reserva válida 201 con disponible 90 | `aceptacion/test_s1_inventario.py::test_reserva_valida_201_deja_disponible_90` |
| Lab 1 · A02 reserva excesiva 409 | `aceptacion/test_s1_inventario.py::test_reserva_excesiva_409` |
| Lab 1 · A02 SKU inexistente 404 | `aceptacion/test_s1_inventario.py::test_sku_inexistente_404` |
| Lab 2 · `/diagnostico` refleja el perfil | `aceptacion/test_s2_configuracion.py::test_diagnostico_refleja_el_perfil` |
| Lab 2 · configuración válida arranca (control) | `aceptacion/test_s2_configuracion.py::test_configuracion_valida_arranca` |
| Lab 2 · configuración inválida impide el arranque (`subprocess`) | `aceptacion/test_s2_configuracion.py::test_configuracion_invalida_impide_el_arranque` |
| Lab 2 · reserva excesiva con `sku`, `solicitado` y `disponible` | `aceptacion/test_s2_configuracion.py::test_reserva_excesiva_trae_sku_solicitado_y_disponible` |
| Lab 3 · A03 autorización 201 | `aceptacion/test_s3_pagos.py::test_autorizacion_201` |
| Lab 3 · A03 reintento con la misma `Idempotency-Key` | `aceptacion/test_s3_pagos.py::test_reintento_con_la_misma_idempotency_key_no_cobra_dos_veces` |
| Lab 3 · A03 unidades superiores al disponible 409 | `aceptacion/test_s3_pagos.py::test_unidades_superiores_al_disponible_409` |
| Lab 4 · A08 tres réplicas registradas y sanas | `aceptacion/test_s4_replicas.py::test_tres_replicas_registradas_y_sanas` |
| Lab 4 · A09 reparto no uniforme con pesos distintos (6:4:2) | `aceptacion/test_s4_replicas.py::test_reparto_no_es_uniforme_si_los_pesos_difieren` |
| Lab 4 · al detener una réplica el consumidor sigue con 200 | `aceptacion/test_s4_replicas.py::test_al_detener_una_replica_el_consumidor_sigue_respondiendo_200` |
| A10 · 503 en menos de 4 s con inventario caído (simulador) | `resiliencia/test_resiliencia.py::test_pagos_responde_503_en_menos_de_4s_si_inventario_cae` |
| A10 · 503 en menos de 4 s con `docker compose stop` (real) | `resiliencia/test_resiliencia.py::test_real_docker_compose_stop_inventario_da_503` |
| A10 · ningún `AsyncClient` por petición ni sin timeout | `resiliencia/test_resiliencia.py::test_ningun_servicio_del_repo_crea_async_client_mal` |
| A10 · el escáner detecta el error y acepta el uso correcto | `resiliencia/test_resiliencia.py::test_escaner_detecta_cliente_por_peticion_y_sin_timeout`, `test_escaner_acepta_cliente_en_lifespan_con_timeout` |

## Notas de diseño

- **SKU únicos** (`T-xxxxxxxx`): cada réplica de inventario tiene su propia memoria. Con SKU fijos, una prueba podría chocar con datos de otra o caer en otra réplica.
- **Reserva excesiva con 500 unidades:** supera las 100 disponibles, pero no el tope `reserva_maxima_unidades` (1000). Así el resultado es 409 y no 422.
- **`docker compose stop`** usa los nombres de las réplicas `ms-inventario-1/-2/-3` (variable `REPLICAS_INVENTARIO`), porque `ms-inventario` a secas no existe en compose.
- **Reparto 6:4:2:** con pesos 3/2/1 y 12 peticiones, cada réplica atiende en proporción a su peso.
