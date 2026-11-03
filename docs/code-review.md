# Code review

**Versión revisada:** commit `a8214a8` (tag `etapa-pruebas`), es decir, el código ya refactorizado y con los errores del diagnóstico corregidos.
**Alcance:** `solicitudes.py`, `gestion/`, `tests/`, el README y el historial de commits.
**Herramientas de apoyo:** `pyflakes` (código sin usar, nombres no definidos) y `radon` (complejidad y mantenibilidad). Salida en [evidencias/analisis_estatico.txt](evidencias/analisis_estatico.txt).

## 1. Checklist técnico

Cada ítem se marca como **Cumple**, **Cumple con observaciones** o **No cumple**. Las observaciones están numeradas en la sección 2.

### Diseño y responsabilidades

| # | Criterio | Resultado |
|---|---|---|
| D1 | Cada clase tiene una sola responsabilidad (SRP) | Cumple |
| D2 | Agregar un estado, tipo u opción de menú no obliga a modificar lógica existente (OCP) | Cumple |
| D3 | Las subclases se pueden usar en lugar de la clase base sin romper nada (LSP) | Cumple |
| D4 | Las interfaces exponen solo lo que el cliente necesita (ISP) | Cumple con observaciones (O3) |
| D5 | La lógica depende de abstracciones y no del archivo (DIP) | Cumple |
| D6 | No hay dependencias circulares entre módulos | Cumple |
| D7 | Las reglas de negocio están en el servicio o el modelo, no en la consola | Cumple con observaciones (O1) |

### Legibilidad y Clean Code

| # | Criterio | Resultado |
|---|---|---|
| L1 | Los nombres dicen qué guardan o qué hacen, sin abreviaturas de una letra | Cumple |
| L2 | Ninguna función supera complejidad 10 | Cumple (máximo 9) |
| L3 | No hay magic strings ni magic numbers en la lógica | Cumple |
| L4 | No hay código muerto ni imports sin usar (`pyflakes` sin advertencias) | Cumple |
| L5 | No hay código duplicado | Cumple |
| L6 | Los comentarios explican el porqué, no el qué | Cumple |
| L7 | Hay anotaciones de tipo en las funciones públicas | No cumple (O7) |

### Manejo de errores

| # | Criterio | Resultado |
|---|---|---|
| E1 | No hay `except:` sin tipo ni `except ...: pass` | Cumple |
| E2 | Los errores del usuario muestran un mensaje que dice qué hacer | Cumple con observaciones (O5) |
| E3 | Un error al leer los datos no provoca pérdida de información | Cumple |
| E4 | Una falla durante la escritura no deja el archivo corrupto | No cumple (O4) |
| E5 | Las validaciones están en el servicio y no dependen de que la consola las haga antes | No cumple (O1, O2) |

### Pruebas

| # | Criterio | Resultado |
|---|---|---|
| P1 | Hay pruebas que verifican el comportamiento externo | Cumple (9 de caja negra) |
| P2 | Las reglas de negocio tienen pruebas unitarias | Cumple |
| P3 | Cada corrección de un error tiene una prueba que lo reproduce | Cumple |
| P4 | Las pruebas no dependen de la fecha ni de archivos reales | Cumple |
| P5 | Se mide la cobertura | No cumple (O8) |

### Repositorio y documentación

| # | Criterio | Resultado |
|---|---|---|
| R1 | Cada commit hace una sola cosa y el mensaje dice cuál | Cumple |
| R2 | Existen los tags de cada etapa | Cumple (`etapa-docs` y `estado-refactorizado` se crean con la documentación) |
| R3 | El README describe la versión actual | No cumple (O6) |
| R4 | `datos.json` y archivos generados no se suben al repositorio | Cumple con observaciones (O4) |

## 2. Observaciones

Severidad: **Alta** = puede perder datos o dejar el sistema en un estado incorrecto. **Media** = una regla que se puede saltear o un mensaje confuso. **Baja** = mejora de prolijidad.

### O1. El servicio confía en que la consola valide el tipo (Media)

**Dónde:** `ServicioSolicitudes.registrar_solicitud`.
**Observación:** el servicio no verifica que el tipo exista. Hoy la consola siempre pasa un tipo válido porque lo obtiene con `tipo_por_numero`. Pero si mañana se usa el servicio desde otra interfaz, se puede registrar una solicitud de tipo "Pedido de beca", que además recibe prioridad Baja sin que nadie lo decida.
**Feedback:** la regla tiene que estar donde está la lógica, no depender de quién la llama. Es justamente lo que buscábamos al separar las capas.
**Acción:** validar `tipo in TIPOS` en el servicio. Prueba: `test_tipo_inexistente`.
**Estado:** Corregido en `2acd1e6`.

### O2. Un estado inexistente en el filtro no avisa (Baja)

**Dónde:** `FiltroSolicitud.validar`.
**Observación:** después de la corrección `135e71c`, la prioridad y el responsable inválidos avisan, pero el estado no. Buscar por estado `Z` responde "No se encontraron solicitudes", como si fuera una búsqueda válida sin resultados.
**Feedback:** es el mismo problema que el Smell 7, a menor escala. Conviene que los cuatro filtros se comporten igual.
**Acción:** validar el estado con `Estado.desde_codigo`. Prueba: `test_filtro_con_estado_inexistente`.
**Estado:** Corregido en `2acd1e6`.

### O3. La interfaz `Repositorio` expone `guardar()` (Media)

**Dónde:** `Repositorio.guardar`, usado por `ServicioSolicitudes.cambiar_estado` y `asignar_responsable`.
**Observación:** el servicio modificaba la solicitud y después llamaba a `guardar()`, un método que solo tiene sentido para un archivo: "escribí todo de nuevo". Con una base de datos no existe ese concepto; lo que se hace es actualizar un registro.
**Feedback:** la interfaz filtra un detalle de la implementación JSON. Eso va contra DIP: la abstracción depende del detalle.
**Acción:** reemplazar `guardar()` por `actualizar_solicitud(solicitud)` en la interfaz. La escritura del archivo queda como método privado de la implementación (`_persistir`). Prueba: `test_cambio_de_estado_queda_guardado`.
**Estado:** Corregido en `a91b0f0`.

### O4. La escritura del JSON no es atómica (Alta)

**Dónde:** `RepositorioJSON._persistir` (antes `guardar`).
**Observación:** `open(ruta, "w")` vacía el archivo antes de escribir. Si el programa se corta en ese momento (se cierra la consola, se corta la luz), `datos.json` queda vacío o a medias y se pierde todo.
**Feedback:** la corrección `a8214a8` evita pisar un archivo dañado, pero no evita que el propio sistema lo dañe.
**Acción:** escribir en `datos.json.tmp` y reemplazar con `os.replace`, que es una operación atómica. Se agregó `datos.json.tmp` al `.gitignore`.
**Estado:** Corregido en `a91b0f0`.

### O5. El mensaje "error" no dice qué pasó (Baja)

**Dónde:** `MenuConsola._pedir_numero`.
**Observación:** si se escriben letras donde va un número, el sistema responde solo `error`. Lo mantuvimos durante la refactorización para no cambiar el comportamiento, pero es el único mensaje que no le dice al usuario qué hizo mal.
**Acción:** cambiarlo por `Debe ingresar un numero`. Cambia la salida esperada en 3 casos de prueba (5 líneas).
**Estado:** Corregido en `b28e282`.

### O6. El README describe la versión inicial (Media)

**Observación:** dice "Versión actual: estado inicial", no menciona la estructura en módulos ni cómo correr las pruebas.
**Acción:** actualizar el README con la estructura, las pruebas, la tabla de etapas y los enlaces a `/docs`.
**Estado:** Corregido en el commit de documentación (tag `etapa-docs`).

### O7. No hay anotaciones de tipo (Baja)

**Observación:** solo los `dataclass` del modelo tienen tipos. El servicio y el repositorio no los tienen, así que un editor no puede avisar si se pasa un `str` donde va un `int`.
**Decisión:** no se corrige en este trabajo. No afecta el comportamiento, y agregarlas en todo el código es un cambio grande que no aporta a los objetivos de la materia. Queda como mejora pendiente.
**Estado:** Aceptado como pendiente.

### O8. No se mide la cobertura (Baja)

**Observación:** sabemos qué cubre cada prueba porque las escribimos, pero no tenemos un número.
**Decisión:** pendiente. Usar `coverage` agregaría una dependencia externa, y hasta ahora el proyecto solo usa la librería estándar.
**Estado:** Aceptado como pendiente.

### Observaciones que se consideraron y se descartaron

- **Los responsables están fijos en el código** (`RESPONSABLES_INICIALES`). Es así en la versión inicial y la consigna no pide administrarlos. No es un problema de calidad sino de alcance.
- **La fecha se guarda como texto `dd/mm/aaaa`**, lo que impide ordenar por fecha. Pasarla a `date` cambiaría el formato del archivo y rompería la compatibilidad con los datos de la versión inicial. Se deja anotado en mejoras futuras.
- **El repositorio devuelve los mismos objetos que guarda**, así que alguien podría modificar una solicitud sin llamar a `actualizar_solicitud`. En este sistema el único que modifica es el servicio y siempre lo llama. Si hubiera más clientes, convendría devolver copias.

## 3. Resumen

| | Cantidad |
|---|---|
| Ítems del checklist | 28 |
| Cumple | 19 |
| Cumple con observaciones | 4 |
| No cumple | 5 |
| Observaciones registradas | 8 |
| Corregidas | 6 (O1 a O6) |
| Aceptadas como pendientes | 2 (O7 y O8) |

Después de las correcciones se volvió a aplicar el checklist sobre la versión final: E4, E5 y R3 pasan a **Cumple**, y D4, D7, E2 y R4 a **Cumple** también. Quedan en **No cumple** L7 y P5, que corresponden a las observaciones aceptadas como pendientes.

## 4. Criterios de aceptación técnica

Para considerar terminada la versión final se tienen que cumplir todos estos criterios:

| Criterio | Cómo se verifica | Resultado |
|---|---|---|
| Todas las pruebas pasan | `python -m unittest discover tests` | 37 de 37 OK |
| La refactorización no cambió el comportamiento | Pruebas de caja negra originales sobre cada commit de refactoring | OK en los 5 ([evidencias](evidencias/pruebas_por_commit.txt)) |
| Cada cambio de salida es intencional y está documentado | Diff de `tests/esperado` contra la versión inicial | 6 cambios, todos en la tabla de [pruebas.md](pruebas.md) |
| Sin advertencias de análisis estático | `pyflakes solicitudes.py gestion tests` | Sin salida |
| Ninguna función con complejidad mayor a 10 | `radon cc` | Máximo 9 |
| Los 12 smells del diagnóstico están resueltos | Tabla de [refactoring.md](refactoring.md#5-relación-entre-smells-y-refactorings) | 12 de 12 |
| Se leen los datos de la versión inicial | `test_lee_archivo_de_la_version_inicial` | OK |
| No quedan observaciones de severidad Alta o Media abiertas | Sección 2 | Ninguna abierta |
