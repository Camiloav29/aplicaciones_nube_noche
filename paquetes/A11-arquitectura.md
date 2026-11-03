# A11 · Arquitectura: C4, UML y decisiones (ADR)

| Dato | Valor |
|---|---|
| Tipo | Documentación de la arquitectura objetivo y de implementación |
| Carpeta | `docs/arquitectura/` |
| Dificultad | 3 puntos · paquete **P2** (con A03) |
| Semanas | 1, 2, 3 y 4 |
| Provee a | todo el grupo y al docente (revisión de arquitectura) |
| Consume | las fichas y el código que entreguen los demás (para evitar que diverjan) |

## Contexto del cliente

El syllabus exige relacionar la solución con un modelamiento previo en UML (indicador 1.4) y derivar la arquitectura **de lo que el cliente pide**, no del modelo de datos (indicador 1.3). Cuando la arquitectura objetivo y la de implementación divergen, **la verdad del sistema está en la segunda**; por eso este trabajo termina con una revisión cruzada contra el código final.

## Qué debe entregar

Use **Mermaid** (se renderiza en GitHub) y escriba cada pieza en su archivo:

| Archivo | Contenido |
|---|---|
| `C4-1-contexto.md` | Sistema MercadoAndino, actores (cliente web, app móvil, operador) y sistemas externos |
| `C4-2-contenedores.md` | Un contenedor por microservicio con puerto, **tipo** (core, compuesto, API, perimetral) y su base de datos; Consul; `config-repo` |
| `C4-3-componentes-ms-pedidos.md` | Componentes internos de `ms-pedidos`: router, servicio, repositorios, clientes `httpx`, manejadores de errores |
| `UML-componentes.md` | Componentes e **interfaces** (`ICatalogo`, `IInventario`, `IPagos`, `IPedidos`) como contratos |
| `UML-secuencia-compra.md` | Tres secuencias de `POST /bff/v1/compras`: **feliz**, **pago rechazado con compensación** y **dependencia caída** (`503`) |
| `UML-despliegue.md` | Nodos y contenedores del Compose, incluidas las **tres réplicas** de `ms-inventario` y Consul |
| `clasificacion-servicios.md` | La **tabla de decisión** de la semana 2 aplicada a cada servicio, con la justificación de cada respuesta |
| `trazabilidad.md` | Cadena *requerimiento → caso de uso → capacidad de negocio → contexto delimitado → servicio → API* para los cinco requerimientos de `ENUNCIADO.md`, y la tabla de **doce factores** (I, III, IV, VI, IX, XI) con la evidencia concreta en el repositorio |
| `glosario.md` | Lenguaje del dominio y los contextos delimitados: por qué *Producto* significa cosas distintas en catálogo y en pedidos |
| `adr/ADR-001-monorepo.md` | Monorepo didáctico frente a un repositorio por servicio (factor I) |
| `adr/ADR-002-descubrimiento.md` | Consul con balanceo del lado del cliente frente al `Service` de Kubernetes (lado del servidor); incluye CAP |
| `adr/ADR-003-comunicacion.md` | REST con `httpx` frente a gRPC y mensajería, y orquestación frente a coreografía para la saga |

Cada ADR sigue el formato: **contexto, decisión, alternativas consideradas, consecuencias (lo que se gana y lo que se paga)**.

## Reglas

1. **Consistencia:** puertos, nombres de servicios, rutas y códigos de estado deben coincidir con `CONVENCIONES.md` y con el código final. Antes de la entrega haga una **revisión cruzada** y deje en `trazabilidad.md` la lista de divergencias que encontró y cómo se cerraron.
2. Los diagramas deben leerse sin su explicación: títulos, leyendas de tipo de servicio y flechas con verbo (por ejemplo «reserva unidades», `HTTP POST /api/v1/existencias/{sku}/reservas`).
3. Si los diagramas muestran algo que el código no hace, es un defecto del documento.

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | C4 niveles 1 a 3 correctos, legibles y coherentes con puertos, tipos y servicios | 7 |
| 2 | Clasificación de servicios con la tabla de decisión **justificada** pregunta por pregunta | 5 |
| 3 | UML de secuencia: flujo feliz, compensación por pago rechazado y dependencia caída; UML de componentes y de despliegue | 6 |
| 4 | Tres ADR con alternativas y consecuencias argumentadas | 5 |
| 5 | Trazabilidad requerimiento→servicio y tabla de doce factores con evidencia real del repositorio, más glosario | 4 |
| 6 | Revisión cruzada final contra el código: divergencias detectadas y cerradas | 3 |

## Preguntas de sustentación

1. ¿Qué responde cada nivel de C4 y a qué audiencia?
2. Aplique la tabla de decisión a `ms-pedidos`: ¿por qué no es core ni API?
3. ¿Por qué un monolito bien modularizado puede ser mejor que microservicios mal cortados, y qué señales dicen que **no** corresponde usar microservicios?
