# A10 · Pruebas automatizadas y CI

| Dato | Valor |
|---|---|
| Tipo | Calidad: pruebas de contrato, de aceptación y de resiliencia, más integración continua |
| Carpetas | `tests/` y `.github/workflows/ci.yml` |
| Dificultad | 4 puntos · paquete **P6** (con A06) |
| Semanas | 1 a 4 (anticipa la semana 9) |
| Provee a | todo el grupo (retroalimentación automática en cada Pull Request) |
| Consume | los contratos de `paquetes/` y las salidas de los servicios levantados |

## Contexto del cliente

«Un contrato que cambia sin avisar es un incidente de producción.» El equipo necesita que cada cambio se valide solo. Esta acción **no reemplaza** las pruebas unitarias que cada dueño escribe en su servicio (cada ficha exige las suyas); agrega la red de seguridad **transversal**.

## Qué debe construir

### 1. Pruebas de contrato (`tests/contrato/`)

Un archivo `contratos.yaml` que codifica, por servicio, los endpoints, los verbos y los códigos de estado de las fichas `A01`–`A06`. Una prueba parametrizada lee `GET /openapi.json` de cada servicio levantado y verifica que **existen** las rutas y los verbos acordados, y que `title` y `version` están definidos. Las pruebas se saltan (`skip`) con un mensaje claro si el servicio no está arriba.

### 2. Pruebas de aceptación (`tests/aceptacion/`)

Con `pytest` y `httpx`, replique como pruebas los criterios de aceptación de los laboratorios 1 a 4:

| Semana | Verificaciones |
|---|---|
| 1 | Salud `200`; alta de stock `201`; reserva válida `201` con disponible 90; reserva excesiva `409`; SKU inexistente `404` |
| 2 | `/diagnostico` refleja el perfil; configuración inválida impide el arranque (prueba de proceso con `subprocess`); reserva excesiva traducida con `sku`, `solicitado` y `disponible` |
| 3 | Autorización `201`; reintento con la misma `Idempotency-Key`; unidades superiores al disponible `409` |
| 4 | Tres réplicas registradas y sanas; el reparto no es uniforme si los pesos difieren; al detener una réplica el consumidor sigue respondiendo `200` |

### 3. Resiliencia (`tests/resiliencia/`, marcador `@pytest.mark.resiliencia`)

Apaga `ms-inventario` con `docker compose stop` y verifica que `ms-pagos` responde **`503` en menos de 4 s** con `detail = "ms-inventario no disponible"`; luego lo reinicia. Verifica además que un `AsyncClient` sin timeout no existe: busca en el código fuente de los servicios llamadas a `httpx.AsyncClient(` fuera del `lifespan`.

### 4. Integración continua (`.github/workflows/ci.yml`)

Un flujo de GitHub Actions que, en cada Pull Request: (a) ejecuta `scripts/verificar_estructura.sh`; (b) para cada servicio presente, usa una **matriz** que ejecuta `uv sync` y `uv run pytest` con cobertura; (c) comprueba que `grep -r fastapi app/servicios/` esté vacío; (d) publica el resumen de cobertura. El flujo debe **pasar** en `main`.

### 5. Documentación (`tests/README.md`)

Cómo ejecutar cada grupo de pruebas y una **matriz de trazabilidad** requisito → prueba (por ejemplo: «A02 RF reserva excesiva → `tests/aceptacion/test_s1_inventario.py::test_reserva_excesiva_409`»).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Pruebas de contrato: `contratos.yaml` cubre los seis servicios y la prueba parametrizada detecta una ruta faltante | 7 |
| 2 | Pruebas de aceptación de las semanas 1 a 4, trazables a los criterios de los laboratorios | 8 |
| 3 | Prueba de resiliencia automática: `503` en menos de 4 s con la dependencia apagada | 4 |
| 4 | `ci.yml` con matriz por servicio, cobertura y reglas de arquitectura; **pasa** en `main` | 5 |
| 5 | Informe de cobertura y umbral mínimo documentado (propuesto y justificado por usted) | 2 |
| 6 | `tests/README.md` con instrucciones y matriz de trazabilidad completa | 4 |

## Preguntas de sustentación

1. ¿Qué diferencia hay entre una prueba de contrato y una prueba unitaria? ¿Por qué el contrato debe vivir fuera del servicio?
2. ¿Por qué la capa de servicio sin FastAPI se prueba con `pytest` «sin levantar servidor»?
3. ¿Qué cambio compatible y qué cambio rompiente detectaría su `contratos.yaml`?
