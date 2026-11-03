# A06 · `ms-confiabilidad` — calculadora de disponibilidad, MTBF y presupuesto de error

| Dato | Valor |
|---|---|
| Tipo | Servicio **core** sin estado (posee el dominio «confiabilidad») |
| Puerto / prefijo | `8005` / `CONFIABILIDAD_` |
| Carpeta | `servicios/ms-confiabilidad/` y `docs/DISPONIBILIDAD.md` |
| Dificultad | 3 puntos · paquete **P6** (con A10) |
| Semanas | 1, 2 y 3 (cálculo obligatorio del Corte 1) |
| Provee a | el equipo de operaciones y el `README` de la plataforma |
| Consume | nada |

## Contexto del cliente

«Cada uno de sus cinco microservicios tiene una disponibilidad del 99,9 %. ¿Qué disponibilidad percibe realmente el cliente?» Operaciones pide una **API** que calcule, con fórmula y resultado en minutos, la disponibilidad en serie y en paralelo, el MTBF efectivo y el presupuesto de error. El cálculo sin fórmula **no se valora**.

## Contrato público

Disponibilidades como fracción en `(0, 1]` (por ejemplo `0.999`). `minutos_mes` por defecto 43 200. Toda respuesta incluye la `formula` usada.

| Método | Ruta | Cuerpo / parámetros | Respuesta |
|---|---|---|---|
| GET | `/health`, `/diagnostico` | — | 200 |
| POST | `/api/v1/disponibilidad/serie` | `servicios: [{nombre, disponibilidad}]`, `minutos_mes?` | `disponibilidad_total`, `indisponibilidad_minutos_mes`, `formula: "prod(Ai)"` |
| POST | `/api/v1/disponibilidad/paralelo` | `disponibilidad`, `replicas ≥ 1`, `minutos_mes?` | `disponibilidad_total`, `indisponibilidad_minutos_mes`, `formula: "1-(1-A)^n"` |
| GET | `/api/v1/disponibilidad/mttr` | `mtbf_horas`, `mttr_horas` | `disponibilidad = MTBF/(MTBF+MTTR)`, `indisponibilidad_minutos_mes` |
| POST | `/api/v1/mtbf/serie` | `mtbf_individual_horas`, `servicios` (entero ≥ 1) | `mtbf_sistema_horas = MTBF/n`, `equivale_dias` |
| POST | `/api/v1/presupuesto-error` | `slo` (fracción), `minutos_mes?` | `presupuesto_fraccion`, `presupuesto_minutos` |
| POST | `/api/v1/latencia/cola-larga` | `llamadas ≥ 1`, `percentil` (defecto 0.99) | `probabilidad_evitar_cola = p^n`, `una_de_cada` |
| POST | `/api/v1/latencia/compuesta` | `latencias_ms: [..]`, `estrategia: "secuencial" \| "concurrente"` | `total_ms` (suma o máximo) |

Un valor fuera de rango (disponibilidad ≤ 0 o > 1, `replicas` < 1, lista vacía) responde `422`.

## Vectores de prueba (resultados esperados; tolerancia 1e-6 en fracciones y 0,01 en minutos)

| Entrada | Resultado |
|---|---|
| Serie: 5 servicios al 0,999 | `disponibilidad_total ≈ 0.995009990005`; indisponibilidad ≈ **215,57 min/mes** |
| Serie: `gateway 0.9995` + cuatro servicios al 0,999 | ≈ 0.995508; indisponibilidad ≈ **194,05 min/mes** |
| Paralelo: A = 0,99 con 2 réplicas | 0.9999; indisponibilidad ≈ **4,32 min/mes** |
| Paralelo: A = 0,99 con 3 réplicas | 0.999999; indisponibilidad ≈ **0,0432 min/mes** (≈ 2,6 s) |
| MTBF: individual 2 000 h, 5 servicios | **400 h** (≈ 16,67 días) |
| Presupuesto de error: SLO 0,999 | fracción 0,001; **43,2 min** |
| Presupuesto de error: SLO 0,9999 | fracción 0,0001; **4,32 min** |
| Cola larga: p = 0,99 con 5 llamadas | ≈ 0.95099 (1 de cada ≈ 20 sufre el p99) |
| MTTR: MTBF 720 h y MTTR 1 h | ≈ 0.998613 |

## Requisitos técnicos

- Lógica de cálculo en un módulo **puro** (`app/dominio/calculos.py`), sin importar FastAPI; la capa de servicio lo usa y lanza excepciones de dominio (`ValorFueraDeRango`) que `main.py` traduce a `422`.
- `Configuracion` con prefijo `CONFIABILIDAD_`: `entorno`, `nivel_log` (validado), `docs_habilitada`, `minutos_mes_defecto` (`Field(ge=1)`), `decimales_porcentaje` (0 a 10).
- Sin estado (`GET /health`, `Dockerfile`, `/docs`).
- Esquemas Pydantic v2 con validaciones explícitas (`Field(gt=0, le=1)`).
- Registro en Consul con cancelación en `finally`.

## Documento de disponibilidad de la plataforma (`docs/DISPONIBILIDAD.md`)

Complete la tabla del Laboratorio 3 para la cadena de compra de MercadoAndino usando **su propia API**:

| Servicio de la cadena | A individual | Fuente del dato | Supuesto o medición |
|---|---|---|---|
| `bff-web`, `ms-pedidos`, `ms-catalogo`, `ms-inventario`, `ms-pagos` | | | |
| **Compuesta (producto)** | | | |
| **Minutos/mes de indisponibilidad** | | | |

Incluya además: (a) el cálculo repetido con dos réplicas de `ms-pagos` (`1-(1-A)^2`); (b) dos líneas argumentadas: ¿qué mejora más, agregar réplicas o reducir el MTTR a la mitad?; (c) el MTBF efectivo de la cadena con MTBF individual de 2 000 h; (d) el presupuesto de error para el SLO que usted proponga. **Cada número con su fórmula.**

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Fórmulas correctas: los **vectores de prueba** de la tabla pasan | 10 |
| 2 | Contrato y validación: rutas, `422` por rangos, respuesta con `formula` | 5 |
| 3 | Capas: módulo de cálculo puro sin FastAPI, servicio y excepciones de dominio con manejador único | 4 |
| 4 | Configuración externalizada con fallo temprano y `/diagnostico` | 3 |
| 5 | `docs/DISPONIBILIDAD.md` completo, con fórmulas y análisis argumentado | 5 |
| 6 | Servicio sin estado, `/health`, `/docs`, `Dockerfile`, registro en Consul | 1 |
| 7 | Pruebas parametrizadas (`pytest.mark.parametrize`) sobre los vectores de prueba | 2 |

## Preguntas de sustentación

1. ¿Por qué cinco servicios al 99,9 % no entregan 99,9 %? Muestre la fórmula.
2. ¿Por qué el MTBF del sistema se divide entre el número de servicios?
3. ¿Qué condiciones debe cumplir la redundancia para que `1-(1-A)^n` sea válida?
