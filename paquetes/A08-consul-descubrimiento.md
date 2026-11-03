# A08 · Consul y descubrimiento de servicios

| Dato | Valor |
|---|---|
| Tipo | Plataforma: registro, comprobaciones de salud y resolvedor con caché |
| Carpetas | `plataforma/consul/` y `plataforma/descubrimiento/` |
| Dificultad | 4 puntos · paquete **P3** (con A02) |
| Semana | 4 |
| Provee a | todos los servicios (registro) y a A09 (resolvedor) |
| Consume | Consul (`http://localhost:8500`) |

## Contexto del cliente

MercadoAndino va a escalar horizontalmente durante las promociones. La operación exige que **ningún consumidor tenga direcciones escritas en su configuración**: las réplicas cambian de IP en cada despliegue y a veces están arrancando o muertas. El registro es la única fuente de verdad sobre la ubicación de los servicios.

## Qué debe construir

### 1. `plataforma/consul/`

`docker-compose.consul.yml` con `hashicorp/consul:1.21` en modo desarrollo (`agent -dev -client=0.0.0.0`, puertos 8500 y 8600/udp), y un `README` con los comandos de verificación (`/v1/status/leader`, `/v1/catalog/services`, la UI en `http://localhost:8500/ui`). Advierta por escrito que `-dev` **no** es para producción (3 o 5 servidores con quórum).

### 2. `plataforma/descubrimiento/` — paquete Python copiable (`pyproject.toml`, `uv.lock`, tests)

| Módulo | Responsabilidad |
|---|---|
| `registro.py` | `registrar()`, `desregistrar()` y un `asynccontextmanager` `ciclo_vida_consul(...)` utilizable como `lifespan` de FastAPI. Registra con `PUT /v1/agent/service/register`: `ID` único `nombre-host-puerto`, `Name`, `Address`, `Port`, `Tags: ["peso=N"]` y `Check` HTTP a `/health` (`Interval 10s`, `Timeout 2s`, `DeregisterCriticalServiceAfter 1m`). **La cancelación va en el `finally`.** |
| `resolvedor.py` | `ResolvedorConsul` implementa el `Protocol` `Resolvedor` de `CONVENCIONES.md`: consulta `/v1/health/service/{nombre}?passing=true`, interpreta el peso de la etiqueta, **cachea con TTL configurable por entorno** (`DESCUBRIMIENTO_TTL_SEGUNDOS`) y protege el acceso concurrente con `asyncio.Lock`. |
| `modelos.py` | `Instancia` (dataclass inmutable) y errores. |

**Modo degradado:** si Consul no responde, se conserva la última lista conocida y se registra una advertencia; solo si la caché está vacía se lanza un error.

Nombre, puerto, dirección anunciada y peso vienen **del entorno** (`NOMBRE_SERVICIO`, `PUERTO_SERVICIO`, `HOST_ANUNCIADO`, `PESO_SERVICIO`), nunca del código. La comunicación con Consul usa `httpx.AsyncClient` con **timeout explícito**.

### 3. Documentación (`plataforma/descubrimiento/README.md`)

- El ciclo **registro → renovación → expiración → cancelación**, y por qué la expiración es la única defensa ante una muerte abrupta.
- La tabla de **tiempo real de expulsión**: intervalo del check + propagación en el registro + TTL de la caché, con los números de su configuración y qué se sacrificaría al reducirlos.
- Cómo lo integra un servicio (copiar el paquete a `app/` o dependencia local con `uv add --editable`), con un ejemplo de `main.py` de 10 líneas.
- Una nota de **Consul (CP) frente a Eureka (AP)** ante una partición de red.

## Evidencia exigida

```bash
curl -s "localhost:8500/v1/health/service/ms-inventario?passing=true" | jq 'length'   # -> 3
# detener una réplica (kill) y, en menos de 30 s:
curl -s "localhost:8500/v1/health/service/ms-inventario?passing=true" | jq 'length'   # -> 2
```

más una captura de la UI de Consul con las tres réplicas en verde (puede usar réplicas de `ms-inventario` de A02 o un servicio de prueba propio).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Registro correcto (ID único, `Check` HTTP) y cancelación en `finally` dentro de un `lifespan` con `asynccontextmanager` | 7 |
| 2 | Comprobación de salud operativa y **expulsión demostrada** de la réplica caída en menos de 30 s | 5 |
| 3 | Resolvedor con caché y TTL configurable por variable de entorno, `passing=true` y `asyncio.Lock` | 6 |
| 4 | Modo degradado: Consul caído → se sirve la última lista conocida y se registra la advertencia | 4 |
| 5 | Peso leído de la etiqueta `peso=N`; configuración solo desde el entorno | 2 |
| 6 | Pruebas con `httpx.MockTransport` (TTL, degradado, `passing`, peso, payload de registro, cancelación) | 3 |
| 7 | `README` con ciclo de vida, tabla de tiempo de expulsión y captura de la UI | 3 |

## Preguntas de sustentación

1. ¿Por qué una instancia registrada pero no lista es peor que una ausente?
2. ¿Cuánto tarda realmente en salir una réplica muerta de la rotación? ¿De qué suma depende?
3. ¿Qué haría Consul y qué haría Eureka ante una partición de red, y qué significa «CP» y «AP»?
