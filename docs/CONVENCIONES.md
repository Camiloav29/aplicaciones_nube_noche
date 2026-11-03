# Convenciones comunes de MercadoAndino

Este documento es el **contrato entre los seis estudiantes**. Permite que cada uno avance sin esperar al otro. Si una ficha de `paquetes/` y este documento discrepan, manda este documento y se avisa al docente.

## 1. Tecnología

| Elemento | Decisión |
|---|---|
| Lenguaje y framework | Python 3.13, FastAPI, Pydantic v2 (versiones de referencia del curso) |
| Gestor de paquetes | `uv` (`pyproject.toml` y `uv.lock` se versionan; `.venv` no) |
| Cliente HTTP entre servicios | `httpx.AsyncClient` (prohibido `requests`) |
| Configuración | `pydantic-settings` (`BaseSettings`) |
| Registros | `structlog` en JSON por salida estándar |
| Pruebas | `pytest` y `TestClient` / `httpx.MockTransport` |
| Contenedores | un `Dockerfile` por servicio y un `docker-compose.yml` en la raíz |

## 2. Servicios, tipos y puertos

| Servicio | Tipo (taxonomía del syllabus) | Puerto | Prefijo de variables | Nombre en Consul |
|---|---|---|---|---|
| `gateway` | Perimetral (**semana 7, fuera del parcial**) | 8000 | `GATEWAY_` | — |
| `bff-web` | API | 8080 | `BFF_` | `bff-web` |
| `ms-catalogo` | Core | 8001 | `CATALOGO_` | `ms-catalogo` |
| `ms-inventario` | Core | 8002 (réplicas 8012 y 8022) | `INVENTARIO_` | `ms-inventario` |
| `ms-pedidos` | Compuesto | 8003 | `PEDIDOS_` | `ms-pedidos` |
| `ms-pagos` | Core con llamadas salientes | 8004 | `PAGOS_` | `ms-pagos` |
| `ms-confiabilidad` | Core sin estado | 8005 | `CONFIABILIDAD_` | `ms-confiabilidad` |
| Consul | Infraestructura | 8500 (UI y API), 8600/udp (DNS) | — | — |

Orden de dependencias de negocio: `bff-web → ms-pedidos → {ms-catalogo, ms-inventario, ms-pagos}`; y `ms-pagos → {ms-catalogo, ms-inventario}`. **Los servicios core no llaman a otros servicios de negocio, salvo `ms-pagos` (excepción definida en la semana 3).**

## 3. Estructura de carpetas de un servicio (semanas 1 y 2)

```
servicios/ms-xxx/
├── app/
│   ├── main.py            # ensambla routers, manejadores de excepciones y lifespan
│   ├── config.py          # Configuracion(BaseSettings) + get_configuracion() con lru_cache
│   ├── dependencias.py    # alias Annotated[..., Depends(...)]
│   ├── esquemas.py        # contrato HTTP (entrada y salida distintos)
│   ├── errores.py         # excepciones de dominio
│   ├── rutas/             # solo traducen HTTP; salud.py y el recurso
│   ├── servicios/         # casos de uso. NO importa fastapi
│   ├── repositorios/      # base.py (Protocol), memoria.py (y sql.py opcional)
│   └── clientes/          # solo si el servicio llama a otros (httpx)
├── tests/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

Verificación automática: `grep -r "fastapi" app/servicios/` debe devolver vacío.

## 4. Elementos mínimos de todo servicio (semana 1)

| Elemento | Ruta |
|---|---|
| Salud | `GET /health` → `200 {"estado":"activo","servicio":"<nombre>"}` |
| Contrato | `GET /openapi.json` (con `title` `MercadoAndino - <Servicio>` y `version` definidos) |
| Documentación | `GET /docs` (deshabilitada si `<PFX>_DOCS_HABILITADA=false`) |
| Diagnóstico de configuración | `GET /diagnostico` → `{"entorno": "...", "nivel_log": "..."}` **sin secretos** |
| Recursos de negocio | bajo `/api/v1/...` (el BFF usa `/bff/v1/...`) |
| Registros | JSON por salida estándar; en `bff-web`, `ms-pedidos` y `ms-pagos`, un middleware registra `ruta`, `estado` y `duracion_ms` |

## 5. Configuración (factor III, semana 2)

Todo servicio tiene una clase `Configuracion(BaseSettings)` con `env_prefix` propio, `extra="ignore"` y **al menos cinco campos**. Campos comunes obligatorios:

| Campo | Tipo | Valores / reglas |
|---|---|---|
| `entorno` | `Literal` | `local`, `dev`, `test`, `prod` (defecto: `local`) |
| `nivel_log` | `str` con `@field_validator` | `DEBUG`, `INFO`, `WARNING`, `ERROR` (se normaliza a mayúsculas) |
| `docs_habilitada` | `bool` | defecto `true`; en `prod` es `false` |

Reglas:

- Los valores por defecto son **seguros** (`local`, repositorio en memoria), nunca de producción.
- `get_configuracion()` usa `@lru_cache`: una sola lectura del entorno por proceso.
- Un valor inválido (por ejemplo `pagina_tamano_maximo=0`) **impide el arranque** (`ValidationError`).
- Jerarquía (gana la más específica): defectos en el código → `config-repo/<servicio>/default.yaml` → perfil (`dev.yaml`, `test.yaml`, `prod.yaml`) → variables de entorno → secretos en `/run/secrets`.
- **Ningún secreto va al repositorio.** Solo `.env.example`, y `.env` está en `.gitignore`.

Variables de descubrimiento (las lee el módulo de A08; el nombre, el puerto y la dirección anunciada **nunca** van en el código):

| Variable | Significado | Ejemplo |
|---|---|---|
| `CONSUL_URL` | URL del agente Consul | `http://consul:8500` |
| `NOMBRE_SERVICIO` | Nombre lógico del servicio | `ms-inventario` |
| `HOST_ANUNCIADO` | Dirección que verán los consumidores (no `localhost` dentro de un contenedor) | `ms-inventario-1` |
| `PUERTO_SERVICIO` | Puerto de la réplica | `8012` |
| `PESO_SERVICIO` | Peso para balanceo ponderado (etiqueta `peso=N` en Consul) | `3` |
| `DESCUBRIMIENTO_TTL_SEGUNDOS` | TTL de la caché del resolvedor | `10` |

Variables de dependencias en un consumidor (ejemplo para `ms-pedidos`):

| Variable | Ejemplo |
|---|---|
| `PEDIDOS_MODO_DESCUBRIMIENTO` | `estatico` (local) o `consul` (dev/prod) |
| `PEDIDOS_URL_CATALOGO` | `http://localhost:8001/api/v1` (solo en modo `estatico`) |
| `PEDIDOS_URL_INVENTARIO` | `http://localhost:8002/api/v1` (solo en modo `estatico`) |
| `PEDIDOS_URL_PAGOS` | `http://localhost:8004/api/v1` (solo en modo `estatico`) |

En modo `consul` no se lee ninguna URL fija: se resuelve el nombre lógico.

## 6. Formato de errores

Todo error responde JSON con la clave **`detail`** (la misma que usa FastAPI para `HTTPException` y para los 422) y, cuando aplica, campos adicionales. Los manejadores de excepciones de dominio también devuelven `detail`.

| Situación | Código | Cuerpo |
|---|---|---|
| Validación del cuerpo o de parámetros | 422 | el estándar de FastAPI |
| Recurso inexistente | 404 | `{"detail":"No existe el producto con SKU X"}` |
| Conflicto con el estado actual (SKU duplicado, stock insuficiente) | 409 | `{"detail":"Stock insuficiente para CAF-001","sku":"CAF-001","solicitado":9999,"disponible":100}` |
| Pago rechazado | 402 | `{"detail":"Pago rechazado","estado":"RECHAZADA"}` |
| Dependencia devolvió un error inesperado (5xx) | 502 | `{"detail":"ms-inventario respondio mal"}` |
| Dependencia no disponible (conexión rechazada, sin DNS) | 503 | `{"detail":"ms-inventario no disponible"}` (siempre con el nombre del servicio) |
| Dependencia no respondió a tiempo (timeout de lectura) | 504 | `{"detail":"ms-inventario no respondio"}` |

> La demostración de la semana 2 usaba la clave `detalle` en un manejador; el parcial la unifica en `detail` para que todos los servicios se comporten igual.

El `409` de la dependencia es del negocio y **se propaga**; `502`, `503` y `504` describen el fallo de la dependencia.

## 7. Idempotencia

`POST /api/v1/pedidos` (A04) y `POST /api/v1/autorizaciones` (A03) aceptan la cabecera `Idempotency-Key`. Si la clave ya se procesó, devuelven **la misma respuesta** (mismo identificador y mismo código `201`) sin repetir el efecto. El almacén de claves va detrás de un `Protocol` (en memoria por ahora). El `bff-web` reenvía la clave tal cual.

## 8. Presupuesto de timeouts (el llamador espera menos que su propio llamador)

| Capa | Lectura máxima total |
|---|---|
| gateway (semana 7) | 10 s |
| `bff-web` hacia `ms-pedidos` | 8 s |
| `ms-pedidos` hacia cada dependencia | 3 s de lectura |
| `ms-pagos` hacia catálogo e inventario | 3 s de lectura |

Valores de `httpx.Timeout` por defecto en todo cliente: `connect=2.0`, `read=3.0`, `write=2.0`, `pool=1.0` (el `read` de `bff-web` hacia `ms-pedidos` es 8.0). Con la dependencia caída (conexión rechazada) la respuesta debe llegar en **menos de 4 s**.

## 9. Datos semilla comunes (para integrar sin sorpresas)

Cada servicio puede cargar estos datos al arrancar si `<PFX>_CARGAR_DATOS_EJEMPLO=true` (defecto `false`):

| SKU | Nombre | Precio | Categoría | Existencias (`ms-inventario`) |
|---|---|---|---|---|
| `CAF-001` | Café Huila 500g | 38500.00 | bebidas | 100 |
| `PAN-001` | Panela en bloque 1kg | 6200.00 | despensa | 50 |
| `CHO-001` | Chocolate de mesa 500g | 14900.00 | bebidas | 30 |
| `QUE-001` | Queso campesino 500g | 16800.00 | lácteos | 20 |
| `ARE-001` | Arepas de maíz x10 | 9500.00 | panadería | 80 |

El E2E usa `CAF-001` y un SKU inexistente `ZZZ-999`. `ms-pagos` define `PAGOS_MONTO_MAXIMO` (defecto `1000000.00`): un total mayor se rechaza con `402`.

## 10. Interfaces compartidas entre A08, A09, A04 y A05

Para que el balanceador (A09) no dependa de que el resolvedor (A08) ya exista, ambos se acuerdan sobre este contrato estructural (un `Protocol`, sin herencia). Es solo la interfaz: la implementación es de cada estudiante.

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Instancia:
    id: str          # nombre-host-puerto, único por réplica
    host: str
    puerto: int
    peso: int = 1    # etiqueta "peso=N" de Consul; 1 si no existe


class Resolvedor(Protocol):
    async def instancias(self) -> list[Instancia]:
        """Instancias sanas (passing=true). Puede devolver la caché anterior en modo degradado."""
        ...
```

`Balanceador.siguiente()` (A09) devuelve una `Instancia`; si no hay instancias sanas lanza `SinInstanciasSanas`. Los consumidores (`ms-pedidos`, `bff-web`) construyen la URL como `http://{host}:{puerto}/api/v1/...`.

## 11. Git

- Una rama por acción (`feat/A04-ms-pedidos`) y Pull Requests revisados por otro integrante.
- Commits en español, en imperativo y con alcance: `ms-pedidos: agrega compensacion de la reserva`.
- **Monorepo por motivos didácticos.** El factor I pide un repositorio por servicio y la semana 2 pide un repositorio de configuración separado. Aquí viven en carpetas para entregar un solo repositorio; cada servicio es autónomo (su `pyproject.toml`, su `Dockerfile`, su `README`) y `config-repo/` se trata como si fuera un repositorio aparte (lo documenta A11 en una ADR).

## 12. Errores frecuentes que se penalizan

| Error | Corrección |
|---|---|
| Devolver la entidad de dominio | Esquema de salida propio |
| Responder `200` con `{"error": ...}` | Usar el código de estado correcto |
| Lógica en `main.py` | Separar rutas, servicio y repositorio |
| `HTTPException` en `servicios/` | Excepción de dominio y manejador en `main.py` |
| Un `AsyncClient` por petición | Un cliente en el `lifespan` |
| Llamada saliente sin timeout | `httpx.Timeout` con los cuatro relojes |
| Anunciar `localhost` desde un contenedor | Anunciar el nombre del contenedor |
| Identificador de instancia repetido | `nombre-host-puerto` |
| Consultar Consul en cada petición | Caché con TTL |
| Olvidar `passing=true` | Filtrar por salud en la consulta |
| No cancelar el registro al apagar | Cancelación en el `finally` del `lifespan` |
| Subir `.env` | `.gitignore` y rotar la credencial si ya se subió |
