# Disponibilidad de la plataforma MercadoAndino

Autor: Carlos Andrés Wilches Guerra · Acción A06

Todos los números se obtuvieron con `ms-confiabilidad` (puerto 8005). `minutos_mes` = 43 200 (30 días). Debajo de cada tabla está la petición que la reproduce.

## 1. Cadena de compra (en serie)

Una compra pasa por los cinco servicios: si **cualquiera** cae, la compra falla. Por eso la disponibilidad se multiplica.

| Servicio de la cadena | A individual | Fuente del dato | Supuesto o medición |
|---|---|---|---|
| `bff-web` | 0,999 | SLA típico de un servicio propio en la nube | Supuesto |
| `ms-pedidos` | 0,999 | SLA típico de un servicio propio en la nube | Supuesto |
| `ms-catalogo` | 0,9995 | Solo lectura: menos fuentes de falla | Supuesto |
| `ms-inventario` | 0,999 | SLA típico de un servicio propio en la nube | Supuesto |
| `ms-pagos` | 0,998 | Depende de una pasarela externa que no controlamos | Supuesto |
| **Compuesta (producto)** | **0,994511 (99,4511 %)** | `prod(Ai)` = 0,999 × 0,999 × 0,9995 × 0,999 × 0,998 | Calculado |
| **Minutos/mes de indisponibilidad** | **237,10 min** (≈ 4 h) | `(1 - 0,994511) × 43 200` | Calculado |

```bash
curl -X POST http://localhost:8005/api/v1/disponibilidad/serie -H "Content-Type: application/json" \
  -d '{"servicios":[{"nombre":"bff-web","disponibilidad":0.999},{"nombre":"ms-pedidos","disponibilidad":0.999},{"nombre":"ms-catalogo","disponibilidad":0.9995},{"nombre":"ms-inventario","disponibilidad":0.999},{"nombre":"ms-pagos","disponibilidad":0.998}]}'
```

**Conclusión:** ningún servicio baja del 99,8 %, pero la cadena queda en **99,45 %**. Cada eslabón suma su indisponibilidad.

## 2. (a) Dos réplicas de `ms-pagos`

`ms-pagos` es el eslabón más débil. Con dos réplicas independientes basta con que **una** responda:

| Cálculo | Fórmula | Resultado |
|---|---|---|
| `ms-pagos` con 2 réplicas | `1-(1-A)^n` = 1 − (1 − 0,998)² = 1 − 0,000004 | **0,999996** (0,17 min/mes) |
| Cadena con `ms-pagos` replicado | `prod(Ai)` = 0,999 × 0,999 × 0,9995 × 0,999 × 0,999996 | **0,996501 (99,6501 %)** |
| Minutos/mes de la cadena | `(1 - 0,996501) × 43 200` | **151,18 min** (antes 237,10) |

```bash
curl -X POST http://localhost:8005/api/v1/disponibilidad/paralelo -H "Content-Type: application/json" \
  -d '{"disponibilidad":0.998,"replicas":2}'
```

## 3. (b) ¿Qué mejora más: agregar réplicas o reducir el MTTR a la mitad?

Supuesto para `ms-pagos`: MTBF = 720 h (una falla al mes) y MTTR = 1,44 h, lo que da A = 0,998, coherente con la tabla.

| Opción | Fórmula | A de `ms-pagos` | Cadena | Min/mes de la cadena |
|---|---|---|---|---|
| Situación actual | `MTBF/(MTBF+MTTR)` = 720 / 721,44 | 0,998004 | 0,994511 | 237,10 |
| MTTR a la mitad (0,72 h) | `MTBF/(MTBF+MTTR)` = 720 / 720,72 | 0,999001 | 0,995509 | 194,01 |
| Dos réplicas | `1-(1-A)^n` | 0,999996 | 0,996501 | **151,18** |

```bash
curl "http://localhost:8005/api/v1/disponibilidad/mttr?mtbf_horas=720&mttr_horas=0.72"
```

**Argumento:**
1. **Las réplicas mejoran más**, porque convierten la indisponibilidad de `ms-pagos` de 0,2 % en 0,0004 % (la elevan al cuadrado). Reducir el MTTR a la mitad solo la divide entre 2.
2. **Pero las réplicas solo valen si las fallas son independientes.** Si ambas réplicas comparten la misma base de datos, la misma zona o la misma pasarela caída, fallan juntas y `1-(1-A)^n` deja de ser válida. Reducir el MTTR (alertas, despliegue automático, *runbooks*) mejora **todas** las fallas, incluidas las correlacionadas. La recomendación es replicar `ms-pagos` en zonas distintas **y** trabajar el MTTR.

## 4. (c) MTBF efectivo de la cadena

Con MTBF individual de 2 000 h por servicio y 5 servicios en serie:

| Fórmula | Resultado |
|---|---|
| `MTBF/n` = 2 000 / 5 | **400 h ≈ 16,67 días** |

```bash
curl -X POST http://localhost:8005/api/v1/mtbf/serie -H "Content-Type: application/json" \
  -d '{"mtbf_individual_horas":2000,"servicios":5}'
```

En serie, cualquier falla tumba la cadena, así que las fallas se suman: cinco servicios fallan cinco veces más seguido que uno. Supone fallas independientes y una tasa de falla constante.

## 5. (d) Presupuesto de error para el SLO propuesto

**SLO propuesto para la cadena de compra: 99,5 %.**

| Fórmula | Fracción | Minutos/mes |
|---|---|---|
| `1-SLO` = 1 − 0,995 | 0,005 | **216 min** (3 h 36 min) |

```bash
curl -X POST http://localhost:8005/api/v1/presupuesto-error -H "Content-Type: application/json" \
  -d '{"slo":0.995}'
```

**Justificación:**
- Con la arquitectura actual (237,10 min de caída al mes) **no se cumple** este SLO: se gasta más que los 216 minutos permitidos.
- Con dos réplicas de `ms-pagos` (151,18 min) **sí se cumple**, y sobran unos 65 minutos de presupuesto para despliegues y experimentos.
- Por eso el SLO de 99,5 % sirve de **argumento para financiar la réplica** de `ms-pagos`. No propongo 99,9 % (43,2 min): exigiría replicar toda la cadena.