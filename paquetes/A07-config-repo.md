# A07 · `config-repo` — Git como repositorio de configuración

| Dato | Valor |
|---|---|
| Tipo | Configuración externalizada (factor III) |
| Carpeta | `config-repo/` |
| Dificultad | 2 puntos · paquete **P1** (con A04) |
| Semana | 2 |
| Provee a | los seis servicios y a A12 (Compose) |
| Consume | las clases `Configuracion` de cada servicio (para mantener las claves coherentes) |

## Contexto del cliente

Operaciones necesita que cada servicio corra en cuatro entornos (`local`, `dev`, `test`, `prod`) **sin recompilar ni editar código**. La configuración se versiona en Git para tener historial auditable, revisión por Pull Request, reversión inmediata y trazabilidad línea por línea.

## Qué debe contener

```
config-repo/
├── ms-catalogo/        default.yaml  dev.yaml  test.yaml  prod.yaml
├── ms-inventario/      default.yaml  dev.yaml  prod.yaml
├── ms-pagos/           default.yaml  dev.yaml  prod.yaml
├── ms-pedidos/         default.yaml  dev.yaml  test.yaml  prod.yaml
├── bff-web/            default.yaml  dev.yaml  prod.yaml
├── ms-confiabilidad/   default.yaml  dev.yaml  prod.yaml
├── cargar_config.py    # cargador con precedencia (ver abajo)
├── tests/              # pruebas del cargador
├── .env.example
├── .gitignore          # incluye .env y .venv/
└── README.md           # tabla de claves: clave, tipo, dueño, descripción
```

Decisión del curso: **carpetas por entorno** (se comparan con `diff` y se promueven copiando el valor validado de `dev` a `prod`).

## Perfiles (referencia de la semana 2)

| Perfil | Base de datos | `nivel_log` | `docs_habilitada` |
|---|---|---|---|
| `local` | SQLite en archivo / memoria | `DEBUG` | `true` |
| `dev` | PostgreSQL compartido | `DEBUG` | `true` |
| `test` | PostgreSQL efímero | `INFO` | `true` |
| `prod` | PostgreSQL con réplica | `WARNING` | **`false`** |

Valores extra por servicio (ejemplos): `pagina_tamano_maximo`, `tipo_repositorio`, `modo_descubrimiento` (`estatico` en `local`, `consul` en `dev` y `prod`), `monto_maximo` (pagos), `reserva_maxima_unidades` (inventario).

## El cargador

`cargar_config.py --servicio ms-catalogo --perfil prod` lee `default.yaml`, luego el archivo del perfil, aplica las variables de entorno ya presentes (que **ganan**) y los secretos montados en `/run/secrets/<nombre>` (que ganan sobre todo), y **imprime** las líneas `export CATALOGO_NIVEL_LOG=WARNING` que consumen los scripts de A12. Precedencia, de menor a mayor: defectos → perfil → entorno → secretos.

## Reglas

1. **Ningún secreto en el repositorio**, aunque fuera privado: la URL de base de datos con credenciales llega por `/run/secrets`; `prod.yaml` lo dice en un comentario.
2. Las claves de cada YAML son exactamente los campos de la `Configuracion` del servicio (sin prefijo; el cargador agrega el prefijo `CATALOGO_`, etc.). Un script de verificación debe detectar claves desconocidas.
3. Un `README` con la tabla de claves: **clave, tipo, dueño y descripción**.
4. Si un secreto llegara al historial, la respuesta correcta es **rotar la credencial**, no reescribir el historial (documéntelo).

## Evidencia de Git que se espera ver

- Al menos 6 commits con mensajes claros.
- Un Pull Request que modifique un `prod.yaml` y sea **revisado por otro integrante** antes de integrarse.
- Un `git revert` de un cambio defectuoso a `prod.yaml`, con el hash del commit y el del revert escritos en el `README` (sección «Reversión»).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Estructura y perfiles correctos para los seis servicios (valores de la tabla, `docs_habilitada: false` en `prod`) | 8 |
| 2 | Las claves coinciden con los campos de `Configuracion` de cada servicio (verificación automática incluida) | 5 |
| 3 | Cargador con la precedencia correcta, **probado** con pytest (defecto < perfil < entorno < secreto) | 7 |
| 4 | Ausencia de secretos, `.gitignore` con `.env`, `.env.example` | 3 |
| 5 | `README` con la tabla de claves (clave, tipo, dueño, descripción) y la política de rotación | 4 |
| 6 | Historial Git, Pull Request revisado y `git revert` evidenciados | 3 |

## Preguntas de sustentación

1. ¿Qué cambia si la configuración vive en el código y hay que desplegar en cuatro entornos?
2. ¿Por qué un secreto que llegó a Git está comprometido aunque se borre?
3. Con `INVENTARIO_PAGINA_TAMANO_MAXIMO=0` en el entorno, ¿qué debe ocurrir al arrancar `ms-inventario` y por qué?
