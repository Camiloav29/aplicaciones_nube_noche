# A09 · Balanceador de carga del lado del cliente

| Dato | Valor |
|---|---|
| Tipo | Plataforma: algoritmo de balanceo propio |
| Carpeta | `plataforma/balanceador/` |
| Dificultad | 4 puntos · paquete **P5** (con A05) |
| Semana | 4 |
| Provee a | `ms-pedidos` (A04) y `bff-web` (A05) |
| Consume | el `Protocol` `Resolvedor` de `CONVENCIONES.md` (la implementación real es de A08) |

## Contexto del cliente

«La carga debe repartirse de forma **medible** entre las réplicas», y una réplica cuya comprobación de salud falle debe **dejar de recibir tráfico sin reiniciar el consumidor y sin editar ningún archivo**. El objetivo del trabajo es que **el algoritmo sea suyo** y que pueda explicar cada decisión.

**Prohibido** usar una biblioteca de balanceo ya hecha.

## Qué debe construir

Un paquete Python copiable (`pyproject.toml`, `uv.lock`, tests) con:

| Elemento | Detalle |
|---|---|
| `BalanceadorPonderado` | Round robin ponderado por **crédito**: en cada elección suma el peso de cada instancia a su crédito, elige la de mayor crédito y le resta la suma total de pesos. Debe repartir **exactamente** en proporción a los pesos en cada ciclo |
| `BalanceadorMenosConexiones` | Elige la instancia con menos peticiones activas. Se usa con `async with balanceador.elegir() as instancia:` (suma al entrar, resta al salir, **incluso si hay excepción**) |
| Expulsión activa | `reportar_fallo(instancia)`: si una instancia falla N veces seguidas (N configurable), se retira de la lista local **sin esperar al TTL** |
| Acceso concurrente | Estado protegido con `asyncio.Lock` |
| Errores | `SinInstanciasSanas` cuando no hay instancias |
| Desacoplamiento | Recibe un `Resolvedor` (Protocol); se prueba con un resolvedor **simulado**, sin Consul |

## Evidencia exigida

`scripts/medir_reparto.sh` (o `.py`) que haga 12 peticiones o más a un consumidor y muestre el reparto con `sort | uniq -c`:

```
 6 8002     # peso 3
 3 8012     # peso 2 -> proporción = pesos 6:4:2 en 12 peticiones
 3 8022     # peso 1
```

(Ajuste los pesos a su demostración: lo importante es que el reparto **no sea uniforme** cuando los pesos difieren y que coincida con ellos.) Además, la demostración de que al detener una réplica el consumidor sigue respondiendo `200`.

## Documento `plataforma/balanceador/README.md`

- Justificación del algoritmo elegido frente a round robin simple, menos conexiones, menor latencia, hash consistente y aleatorio de dos opciones (cuándo conviene cada uno).
- Por qué el balanceo del lado del cliente ahorra un salto de red y qué cuesta (lógica replicada en cada cliente).
- Por qué las **sesiones pegajosas** contradicen el factor VI.
- Cómo se integra en `ms-pedidos` y en `bff-web` (ejemplo de 10 líneas).

## Criterios de aceptación y puntaje (30)

| # | Criterio | Puntos |
|---|---|---|
| 1 | Ponderado por crédito correcto: en un ciclo completo el reparto coincide **exactamente** con los pesos | 8 |
| 2 | Menos conexiones con adquisición y liberación seguras (también ante excepciones) | 5 |
| 3 | Concurrencia: `asyncio.Lock` y una prueba con `asyncio.gather` de 100 elecciones que mantiene la proporción | 4 |
| 4 | Expulsión activa tras N fallos y reincorporación cuando el resolvedor vuelve a listarla | 3 |
| 5 | Interfaz desacoplada (`Resolvedor` como `Protocol`) y `SinInstanciasSanas` | 2 |
| 6 | Evidencia del reparto con `uniq -c` y script reproducible | 4 |
| 7 | `README` con la justificación del algoritmo y la integración | 3 |
| 8 | Tipado completo (`mypy` sin errores) y configuración (N de fallos, algoritmo) desde el entorno | 1 |

## Preguntas de sustentación

1. ¿Por qué el round robin simple es el valor por defecto correcto y cuándo se justifica salir de él?
2. ¿Por qué con HTTP/2 y gRPC el balanceo de capa 4 se degrada y qué ventaja da el balanceo del lado del cliente?
3. Sin `asyncio.Lock`, ¿qué falla con 100 corrutinas pidiendo `siguiente()` a la vez?

## Extensión opcional

Aleatorio de dos opciones comparado con el ponderado en 1 000 peticiones generadas con `locust`.
