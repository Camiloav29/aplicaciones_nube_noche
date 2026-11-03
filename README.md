# Aplicaciones en la Nube (noche) · Parcial del Corte 1 · MercadoAndino

**Asignatura:** Lenguajes de Programación para Aplicaciones de Nube (código 1534, periodo VII)
**Programa:** Tecnología en Desarrollo de Software y Aplicativos Móviles · Politécnico Internacional I.E.S.
**Docente:** Edgar Humberto Angel Millán
**Alcance:** semanas 1 a 4 de las presentaciones del curso
**Valor:** Corte 1 · 15 % de la nota total
**Entrega:** **martes 10 de noviembre de 2026, 21:00 (hora de Bogotá, UTC-5)**

> Este repositorio reemplaza al README anterior del repositorio. Aquí vive **todo** el parcial: el enunciado, los contratos de las APIs, la rúbrica, la ruleta de asignación y, cuando ustedes entreguen, el código.

## Qué se construye

La plataforma **MercadoAndino**, el caso guía del curso, como un conjunto de microservicios FastAPI que se descubren por Consul, se balancean del lado del cliente y se despliegan con Docker Compose:

```
Cliente ─► bff-web :8080 (API) ─► ms-pedidos :8003 (compuesto) ─► ms-catalogo   :8001 (core)
                                                               ├─► ms-inventario :8002 / 8012 / 8022 (core, 3 réplicas)
                                                               └─► ms-pagos      :8004 (core)
                 ms-confiabilidad :8005 (core, calculadora de disponibilidad y MTBF)
                 Consul :8500 (registro) · config-repo (configuración por perfil, en Git)
```

El `gateway :8000` pertenece a la semana 7 y **no** se construye en este parcial.

## Cómo se reparte el trabajo

Hay **12 acciones** (A01 a A12): seis APIs y seis tareas de plataforma, calidad y documentación. Se agrupan en **6 paquetes de 2 acciones con la misma carga (7 puntos de dificultad)** y se asignan a los 6 estudiantes con la **ruleta** (`ruleta/index.html`). Cada estudiante responde por sus dos acciones y las sustenta.

| Paquete | Acciones | Carga |
|---|---|---|
| P1 | A04 `ms-pedidos` (5) + A07 `config-repo` (2) | 7 |
| P2 | A03 `ms-pagos` (4) + A11 Arquitectura C4/UML/ADR (3) | 7 |
| P3 | A02 `ms-inventario` (3) + A08 Consul y descubrimiento (4) | 7 |
| P4 | A01 `ms-catalogo` (3) + A12 Integración E2E y Docker Compose (4) | 7 |
| P5 | A05 `bff-web` (3) + A09 Balanceador de carga (4) | 7 |
| P6 | A06 `ms-confiabilidad` (3) + A10 Pruebas y CI (4) | 7 |

El resultado del sorteo se registra en [`docs/ASIGNACIONES.md`](docs/ASIGNACIONES.md).

## Mapa del repositorio

| Ruta | Contenido |
|---|---|
| [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md) | Enunciado completo, alcance temático y fechas (versión Word: [`docs/Parcial_Corte1_MercadoAndino.docx`](docs/Parcial_Corte1_MercadoAndino.docx)) |
| [`docs/CONVENCIONES.md`](docs/CONVENCIONES.md) | Reglas comunes: puertos, errores, configuración, datos semilla, interfaces compartidas |
| [`docs/RUBRICA.md`](docs/RUBRICA.md) | Cómo se calcula la nota (100 puntos) |
| [`docs/ENTREGA.md`](docs/ENTREGA.md) | Cómo entregar (fork + Pull Request), hitos y sustentación |
| [`paquetes/`](paquetes/) | Una ficha por acción: contrato, reglas, requisitos y criterios con puntaje |
| `ruleta/index.html` | Ruleta de asignación (abrir en el navegador; funciona sin conexión) |
| `servicios/` | Aquí van `ms-catalogo`, `ms-inventario`, `ms-pagos`, `ms-pedidos`, `bff-web`, `ms-confiabilidad` |
| `plataforma/` | `descubrimiento/` (A08) y `balanceador/` (A09); `consul/` (A08) |
| `config-repo/` | Configuración por servicio y perfil (A07) |
| `docs/arquitectura/` | C4, UML y ADR (A11) |
| `tests/` | Pruebas transversales (A10) |
| `scripts/` | `verificar_estructura.sh` (reglas automáticas) y los scripts E2E (A12) |

## Regla de oro

Cada servicio es **suyo**: se evalúa el criterio de arquitectura, no la copia del código del docente. En la sustentación cada estudiante debe poder explicar y modificar en vivo lo que entregó.

> Este repositorio es público. Por eso **no contiene soluciones de referencia**, solo los enunciados y los contratos.
