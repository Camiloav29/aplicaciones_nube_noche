# Rúbrica del Parcial · Corte 1

Total: **100 puntos**. Nota del parcial = `puntos / 20` (0,0 a 5,0). El parcial vale el **15 % de la nota total**.

| Componente | Puntos | Quién |
|---|---|---|
| Acción 1 del paquete (ficha en `paquetes/`) | 30 | Individual |
| Acción 2 del paquete (ficha en `paquetes/`) | 30 | Individual |
| Sustentación oral y cambio en vivo | 15 | Individual |
| Integración de la plataforma (`scripts/e2e.sh`) | 15 | Grupo |
| Calidad del repositorio y trabajo colaborativo | 10 | Grupo |

## Por qué las dos acciones valen lo mismo

Cada paquete suma **7 puntos de dificultad** (por ejemplo, la acción más pesada, `ms-pedidos` con 5, se empareja con la más liviana, `config-repo` con 2). Por eso las dos acciones puntúan 30 cada una: la carga total de cada estudiante es equivalente.

## Acciones (60 puntos)

Cada ficha de [`paquetes/`](../paquetes/) trae su propia lista de **criterios de aceptación con puntaje** que suma exactamente 30. Se califica contra el estado de la rama `main` a la hora límite.

Niveles de logro por criterio (se aplican al puntaje del criterio):

| Nivel | Fracción del puntaje | Descripción |
|---|---|---|
| Completo | 100 % | Cumple el criterio y hay evidencia reproducible (prueba, salida de `curl`, captura) |
| Parcial | 50 % | Cumple en el caso principal, pero falla un caso límite o no hay evidencia |
| Insuficiente | 0 % | No cumple, o cumple solo por casualidad (valor fijo en el código, prueba que no verifica nada) |

## Sustentación (15 puntos)

Cada estudiante dispone de 10 minutos con el docente, sin ayuda de compañeros.

| Criterio | Puntos | Qué se observa |
|---|---|---|
| Dominio conceptual | 6 | Responde las preguntas de sustentación de sus dos fichas con las ideas de las semanas 1 a 4 |
| Justificación de decisiones | 5 | Explica por qué eligió ese diseño y qué cambiaría si la carga se multiplicara por diez |
| Cambio en vivo | 4 | Modifica un valor de configuración o una regla pequeña y demuestra el efecto **sin recompilar** ni tocar otros servicios |

Quien no puede explicar su código no obtiene los puntos de las acciones asociadas a ese código, aunque funcione: la sustentación verifica autoría.

## Integración del grupo (15 puntos)

Se ejecuta `scripts/e2e.sh` sobre `main`. Cada verificación aprobada aporta `15 / total_de_verificaciones` puntos. Si la plataforma no arranca con `docker compose up`, esta parte vale 0.

## Calidad del repositorio y colaboración (10 puntos)

| Criterio | Puntos |
|---|---|
| Historial: al menos 5 commits con mensaje claro por integrante, repartidos en más de un día | 3 |
| Pull Requests: cada PR revisado por otro integrante antes de integrarse | 3 |
| `README` raíz actualizado con instrucciones de ejecución verificadas, y sin credenciales ni archivos `.env` versionados | 2 |
| Bitácora de integración (`docs/E2E.md`) con los problemas encontrados y cómo se resolvieron | 2 |

## Reglas generales de calificación

1. Se toma el último commit de `main` anterior a **martes 10 de noviembre de 2026, 21:00 (Bogotá)**. Los cambios posteriores no se valoran.
2. Una credencial versionada resta el 100 % de los puntos del criterio "Configuración" de la ficha correspondiente (y debe rotarse: borrar el archivo no la elimina del historial).
3. Una acción cuya lógica es copia de otro compañero o de una fuente externa sin explicación no puntúa en los criterios de contrato ni de reglas de negocio.
4. Las extensiones opcionales no suman puntos: sirven de práctica y de material para la sustentación.
