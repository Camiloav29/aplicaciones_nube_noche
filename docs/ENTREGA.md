# Entrega del Parcial · Corte 1

## Fecha límite

**Martes 10 de noviembre de 2026, 21:00 (hora de Bogotá, UTC-5).**
Se califica el último commit de la rama `main` anterior a esa hora.

## Cómo se entrega

El repositorio es público, pero solo el docente escribe en `main`. Cada estudiante trabaja así:

1. Hace un **fork** de `cleangel196809/aplicaciones_nube_noche`.
2. Crea una rama por acción: `feat/A04-ms-pedidos`, `feat/A07-config-repo`, etc.
3. Trabaja dentro de la carpeta que indica su ficha (no edita las carpetas de otros).
4. Abre un **Pull Request** hacia `main` con el título `[A04] ms-pedidos · Nombre Apellido` y la plantilla que aparece por defecto.
5. Otro integrante revisa el PR (al menos un comentario sustantivo y una aprobación) y el docente lo integra.
6. El docente puede, en cambio, agregar a los estudiantes como colaboradores; en ese caso se mantienen las ramas y los PR.

Las comprobaciones automáticas de `scripts/verificar_estructura.sh` se ejecutan en cada PR.

## Calendario sugerido (hitos de equipo, no se califican por separado)

| Fecha | Hito |
|---|---|
| Mar 3 nov | Sorteo en clase con la ruleta. Cada estudiante lee sus dos fichas y [`CONVENCIONES.md`](CONVENCIONES.md) |
| Jue 5 nov | PR en borrador con el esqueleto de cada servicio levantando en su puerto con `/health` |
| Sáb 7 nov | Contratos congelados: cualquier cambio de endpoint se acuerda por issue |
| Dom 8 nov | Primera integración con `docker compose up` y `scripts/e2e.sh` |
| Lun 9 nov | Correcciones, README, capturas y evidencia |
| **Mar 10 nov, 21:00** | **Entrega** |

## Qué debe contener la entrega

- El código y la documentación de las dos acciones de cada estudiante, en las rutas de su ficha.
- Para cada servicio: `pyproject.toml`, `uv.lock`, `Dockerfile`, `README.md` con instrucciones de ejecución, y carpeta `tests/`.
- Ningún archivo `.env` ni credenciales. Solo `.env.example`.
- La carpeta `.venv` **no** se versiona.

## Sustentación

Después de la entrega, cada estudiante sustenta individualmente durante 10 minutos (la fecha y la hora las fija el docente en el aula virtual). Incluye un cambio en vivo: por ejemplo, cambiar `pagina_tamano_maximo` por entorno y mostrar el efecto sin recompilar.

## Integridad académica

El servicio es suyo. Se evalúa el criterio de arquitectura, no la copia del código del docente ni de un compañero. Puede consultar la documentación oficial y las presentaciones del curso; todo lo que entregue debe poder explicarlo y modificarlo en la sustentación.

## Nota sobre el peso en la nota

Este parcial corresponde al **Corte 1, 15 % de la nota total**, según indicación del docente. Si en el aula virtual el corte se divide en parcial y taller acumulativo, el docente ajusta la ponderación aquí.
