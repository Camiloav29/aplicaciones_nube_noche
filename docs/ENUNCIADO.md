# Enunciado del Parcial · Corte 1

**Lenguajes de Programación para Aplicaciones de Nube** · código 1534 · periodo VII
**Valor:** 15 % de la nota total (Corte 1) · **Entrega:** martes 10 de noviembre de 2026, 21:00 (Bogotá)

## 1. Contexto del cliente

MercadoAndino vende productos de despensa por canal web y móvil. En temporada de promociones el monolito actual se cae: cuando el catálogo colapsa, también cae la facturación. El cliente pide una plataforma de microservicios que:

1. Muestre el catálogo filtrado por categoría y la disponibilidad real de cada producto.
2. **No venda lo que no tiene**: reserve el inventario antes de confirmar un pedido.
3. Haga la compra en **un solo paso** desde la app móvil.
4. Escale de forma horizontal sin editar direcciones en ningún archivo.
5. Demuestre con números qué disponibilidad percibe realmente el cliente.

## 2. Objetivo

Construir de forma incremental la arquitectura de implementación de MercadoAndino aplicando lo visto en las semanas 1 a 4: microservicios con FastAPI y Pydantic v2, arquitectura en capas, configuración externalizada con Git, comunicación entre servicios con `httpx`, BFF, idempotencia y saga, cálculo de disponibilidad y MTBF, y registro, descubrimiento y balanceo de carga con Consul.

## 3. Alcance temático (solo semanas 1 a 4)

| Semana | Tema evaluado en este parcial |
|---|---|
| 1 | Definición de microservicio, contexto delimitado, taxonomía core/compuesto/API, FastAPI, esquemas Pydantic, códigos de estado, `/health`, `uv` |
| 2 | Capas (router, servicio, repositorio), `pydantic-settings` con fallo temprano, patrón repositorio con `Protocol`, excepciones de dominio, Git como repositorio de configuración, versionado |
| 3 | Cliente `httpx` único en el `lifespan`, cuatro timeouts, `asyncio.gather`, traducción de fallos (409/502/503/504), idempotencia, saga, BFF, disponibilidad en serie y en paralelo, MTBF, presupuesto de error |
| 4 | Consul (registro, renovación, expiración, cancelación), comprobaciones de salud, resolvedor con caché y TTL, modo degradado, balanceo del lado del cliente, apagado elegante |

**Fuera de alcance:** gateway perimetral (semana 7), mensajería asíncrona (semana 6), resiliencia con cortocircuito (semana 5), Kubernetes y observabilidad completa (semanas 7 y 8). Puede mencionarlos en las ADR como trabajo futuro, pero no se evalúan.

## 4. Qué debe entregar el grupo

Una plataforma que arranque con un solo comando (`docker compose up`) y que pase el recorrido `scripts/e2e.sh`. Está compuesta por las 12 acciones descritas en [`paquetes/`](../paquetes/):

| ID | Acción | Tipo | Ubicación |
|---|---|---|---|
| A01 | `ms-catalogo` | API core | `servicios/ms-catalogo/` |
| A02 | `ms-inventario` | API core | `servicios/ms-inventario/` |
| A03 | `ms-pagos` | API core con llamadas salientes | `servicios/ms-pagos/` |
| A04 | `ms-pedidos` | API compuesta (orquestador) | `servicios/ms-pedidos/` |
| A05 | `bff-web` | API de canal | `servicios/bff-web/` |
| A06 | `ms-confiabilidad` | API core sin estado | `servicios/ms-confiabilidad/` |
| A07 | `config-repo` | Configuración en Git | `config-repo/` |
| A08 | Consul y descubrimiento | Plataforma | `plataforma/consul/`, `plataforma/descubrimiento/` |
| A09 | Balanceador de carga | Plataforma | `plataforma/balanceador/` |
| A10 | Pruebas y CI | Calidad | `tests/`, `.github/workflows/` |
| A11 | Arquitectura (C4, UML, ADR) | Documentación | `docs/arquitectura/` |
| A12 | Integración E2E y Docker Compose | Plataforma | `docker-compose.yml`, `scripts/`, `docs/E2E.md` |

## 5. Reparto

Los seis estudiantes reciben un paquete de dos acciones por **ruleta** (ver `ruleta/index.html`). Los paquetes están balanceados en dificultad, de modo que ningún estudiante parte con ventaja. Quien termine antes debe apoyar la integración del grupo, pero la nota individual solo cuenta sus dos acciones.

## 6. Reglas de trabajo

- Python 3.13, FastAPI, Pydantic v2, `uv` y `httpx`, las versiones de referencia del curso.
- **Prohibido:** la biblioteca `requests`, crear un `AsyncClient` dentro de una ruta, llamadas salientes sin timeout, credenciales en el repositorio, importar FastAPI en `servicios/`, y usar una biblioteca de balanceo ya hecha.
- Cada acción se entrega por Pull Request (ver [`ENTREGA.md`](ENTREGA.md)).
- Las convenciones comunes (puertos, formato de error, nombres de variables, datos semilla) están en [`CONVENCIONES.md`](CONVENCIONES.md). Si dos servicios discrepan, manda ese documento.
- Las dependencias entre acciones se resuelven con **contratos**, no esperando al compañero: cada ficha dice qué provee y qué consume.

## 7. Evaluación

100 puntos: 60 individuales (30 por acción), 15 de sustentación y 25 de equipo. Detalle en [`RUBRICA.md`](RUBRICA.md). La nota del parcial es `puntos / 20` (escala de 0,0 a 5,0).
