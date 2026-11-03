# Pruebas y verificación del comportamiento

## 1. Cómo correrlas

```
python -m unittest discover tests -v
```

Usan solo la librería estándar de Python. Resultado sobre la versión final: **37 pruebas, todas OK** ([evidencias/pruebas_final.txt](evidencias/pruebas_final.txt)).

## 2. Estrategia

Usamos dos tipos de prueba, cada una con un objetivo distinto.

### Pruebas de caja negra (`tests/test_comportamiento.py`)

Se escribieron **antes de tocar el código** (commit `16f742d`, sobre la versión inicial). Cada caso es un archivo en `tests/casos/` con lo que escribiría un usuario en el teclado. La prueba ejecuta `solicitudes.py`, le pasa esa entrada y compara todo lo que imprime contra `tests/esperado/`. La fecha se reemplaza por `<fecha>` para que el resultado no dependa del día.

Como comparan la salida completa, cualquier cambio en un mensaje, en un orden o en un cálculo hace fallar la prueba. Por eso sirven como red de seguridad para refactorizar: si después de un refactoring siguen pasando con los resultados grabados de la versión inicial, el comportamiento externo no cambió.

| Caso | Qué cubre |
|---|---|
| `registro_y_prioridad` | Alta de estudiante, los 5 tipos, prioridad automática y la palabra "urgente" |
| `validaciones` | Cancelar el alta, datos vacíos, email sin @, tipo no numérico, tipo fuera de rango, descripción corta |
| `transiciones_estado` | Transiciones permitidas y no permitidas, En proceso sin responsable, estado en minúscula |
| `asignar_responsable` | ID no numérico, solicitud inexistente, responsable inexistente, reasignar, asignar a una finalizada |
| `buscar` | Cada filtro por separado, combinados, sin filtros y sin resultados |
| `reporte` | Conteo por estado, alerta de urgentes sin responsable y porcentaje de finalizadas |
| `eliminar` | ID inválido, solicitud inexistente, cancelar, confirmar y registrar después de eliminar |
| `persistencia` | Dos ejecuciones sobre el mismo `datos.json`: la segunda ve lo que hizo la primera |
| `archivo_danado_no_se_pisa` | Se agregó en la corrección 4: con un `datos.json` dañado el programa avisa y no lo modifica |

### Pruebas unitarias (`tests/test_servicio.py` y `tests/test_repositorio.py`)

Se agregaron después de la refactorización (commit `968db19`), porque antes no se podían escribir: las reglas solo eran accesibles a través de `input()` y `print()`. Prueban el servicio con `RepositorioEnMemoria`, sin consola ni archivo, y con una fecha fija.

| Grupo | Qué verifica |
|---|---|
| `TestPrioridad` | Prioridad de cada tipo y "urgente" en mayúsculas |
| `TestRegistro` | Estado inicial, IDs que no se repiten, alta del estudiante junto con su solicitud, validaciones |
| `TestTransiciones` | **Los 25 pares** (estado actual, estado nuevo) contra la tabla de reglas del README, En proceso sin responsable, código inexistente |
| `TestAsignacion` | Asignación correcta, responsable inexistente, solicitudes cerradas y rechazadas |
| `TestBusquedaYReporte` | Filtros solos y combinados, filtros inválidos, cálculo del reporte, reporte vacío |
| `TestRepositorioJSON` | Creación del archivo la primera vez, guardar y volver a leer, leer un archivo de la versión inicial, archivo dañado, escritura sin dejar el `.tmp` |

La prueba de las 25 transiciones vale la pena destacarla: con las pruebas de caja negra solo se cubrían algunos caminos, y esta recorre todas las combinaciones posibles.

## 3. Cómo se verificó que la refactorización no alteró el comportamiento

1. Antes de empezar se grabaron los resultados esperados con la versión inicial (commit `16f742d`).
2. Se hizo un refactoring por commit y se corrieron las 8 pruebas de caja negra antes de cada commit.
3. Ningún commit de refactoring modificó `tests/esperado/`. Se puede comprobar con:

   ```
   git diff 16f742d etapa-refactoring -- tests/esperado
   ```

   que no muestra ninguna diferencia.
4. Al terminar, volvimos a correr las pruebas originales sobre cada uno de los 5 commits, para dejar la evidencia: [evidencias/pruebas_por_commit.txt](evidencias/pruebas_por_commit.txt). Los 6 resultados (versión inicial más los 5 refactorings) dan OK.
5. Además se comprobó a mano que un `datos.json` generado por la versión inicial se lee bien con la versión nueva. Después eso quedó como prueba automática (`test_lee_archivo_de_la_version_inicial`).

## 4. Cambios de comportamiento intencionales

Después de la refactorización (tag `etapa-refactoring`) corregimos errores encontrados en el diagnóstico y en el code review. Estos commits **sí cambian la salida**, y en cada uno se actualizó el resultado esperado en el mismo commit, para que el cambio quede explícito en el historial. El diff completo está en [evidencias/cambios_de_salida.txt](evidencias/cambios_de_salida.txt).

| Commit | Error en la versión inicial | Antes | Después |
|---|---|---|---|
| `6f047e7` | El ID se calculaba como cantidad + 1 | Con 3 solicitudes, si se borra la #2, la siguiente recibe el ID 3 y queda repetido | Recibe el ID 4 (mayor ID + 1) |
| `30268b8` | El estudiante se agregaba antes de validar la solicitud (Smell 2) | Si la solicitud fallaba, el estudiante quedaba cargado y la próxima vez no se preguntaba por él | El estudiante se guarda recién cuando su solicitud se registra |
| `135e71c` | Filtro con texto donde va un número (Smell 7) | `alta` en prioridad ignoraba el filtro y mostraba todas las solicitudes | Muestra `Prioridad invalida` |
| `a8214a8` | `datos.json` dañado (Smell 7) | Imprimía `error`, arrancaba vacío y en el primer guardado borraba los datos | Explica el problema, termina y no toca el archivo |
| `2acd1e6` | Sin validación en el servicio (code review) | Un estado inexistente en el filtro devolvía "No se encontraron solicitudes" | Muestra `Estado invalido` |
| `b28e282` | Mensaje poco claro (code review) | `error` | `Debe ingresar un numero` |

En el caso `validaciones` hubo que cambiar también la entrada (`tests/casos/validaciones.txt`): como ahora el sistema vuelve a preguntar por el estudiante en cada intento, el caso tiene que cargar sus datos de nuevo. Al final se agregó un intento que confirma que el estudiante 2002 no quedó guardado.

Ninguno de estos cambios quita funcionalidad. En todos, el sistema pasa de hacer algo incorrecto en silencio a hacer lo correcto o avisar.

## 5. Límites de las pruebas

- La consola (`MenuConsola`) no tiene pruebas unitarias propias. Está cubierta por las pruebas de caja negra, que pasan por todas sus opciones.
- No se probó el sistema con muchos datos ni con dos personas usándolo al mismo tiempo sobre el mismo archivo.
- No medimos cobertura con una herramienta (por ejemplo `coverage`). Queda como mejora pendiente.
