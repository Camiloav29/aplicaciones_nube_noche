# ms-confiabilidad

Calculadora de disponibilidad, MTBF, presupuesto de error y latencia de la plataforma MercadoAndino (ficha [A06](../../paquetes/A06-ms-confiabilidad.md)). Servicio **core sin estado**: no guarda datos ni llama a otros servicios.

- Puerto: `8005`
- Prefijo de configuración: `CONFIABILIDAD_`

## Arquitectura

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Rutas | `app/rutas/` | Traducen HTTP ↔ servicio. Sin lógica |
| Servicio | `app/servicios/confiabilidad.py` | Valida reglas, completa valores por defecto y lanza `ValorFueraDeRango`. No importa FastAPI |
| Dominio | `app/dominio/calculos.py` | Fórmulas puras |
| Ensamblado | `app/main.py` | Manejador único `ValorFueraDeRango` → `422` |

## Ejecutar en local

```bash
uv sync
uv run uvicorn app.main:app --port 8005 --reload
```

Documentación interactiva: http://localhost:8005/docs

## Pruebas

```bash
uv run pytest -v
```

- `tests/test_vectores.py`: los 9 vectores de la ficha con `pytest.mark.parametrize`.
- `tests/test_api.py`: contrato HTTP, `422` por rangos, `formula` en cada respuesta y manejador único.

## Docker

```bash
docker build -t ms-confiabilidad .
docker run -p 8005:8005 -e CONFIABILIDAD_ENTORNO=dev ms-confiabilidad
```

## Configuración

Ver `.env.example`. Un valor inválido impide el arranque (fallo temprano).

| Variable | Defecto | Regla |
|---|---|---|
| `CONFIABILIDAD_ENTORNO` | `local` | `local`, `dev`, `test`, `prod` |
| `CONFIABILIDAD_NIVEL_LOG` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CONFIABILIDAD_DOCS_HABILITADA` | `true` | `false` oculta `/docs` |
| `CONFIABILIDAD_MINUTOS_MES_DEFECTO` | `43200` | ≥ 1 |
| `CONFIABILIDAD_DECIMALES_PORCENTAJE` | `4` | 0 a 10 (solo afecta al texto `porcentaje`) |

## Contrato

| Método | Ruta | Fórmula |
|---|---|---|
| GET | `/health`, `/diagnostico` | — |
| POST | `/api/v1/disponibilidad/serie` | `prod(Ai)` |
| POST | `/api/v1/disponibilidad/paralelo` | `1-(1-A)^n` |
| GET | `/api/v1/disponibilidad/mttr?mtbf_horas=&mttr_horas=` | `MTBF/(MTBF+MTTR)` |
| POST | `/api/v1/mtbf/serie` | `MTBF/n` |
| POST | `/api/v1/presupuesto-error` | `1-SLO` |
| POST | `/api/v1/latencia/cola-larga` | `p^n` |
| POST | `/api/v1/latencia/compuesta` | `sum(Li)` o `max(Li)` |

## Cambio en vivo (sustentación)

Detén el servidor y reinícialo con otra configuración, **sin recompilar**:

```bash
set CONFIABILIDAD_DECIMALES_PORCENTAJE=2
uv run uvicorn app.main:app --port 8005
```

Luego `GET /diagnostico` muestra el nuevo valor, y el campo `porcentaje` sale con 2 decimales.