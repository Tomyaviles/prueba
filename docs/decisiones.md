# Decisiones técnicas

Registro de las decisiones de diseño que tomamos, qué alternativas había y por qué elegimos cada una.

## DT1. Escribir las pruebas antes de refactorizar

**Decisión:** antes de tocar una línea del código grabamos la salida completa de la versión inicial para 8 escenarios (commit `16f742d`).
**Alternativa:** escribir pruebas unitarias primero.
**Por qué:** en la versión inicial no se podía probar ninguna regla sin pasar por `input()` y `print()`. La única forma de tener una red de seguridad era probar el programa entero desde afuera. Las pruebas unitarias se escribieron después, cuando la refactorización ya las hacía posibles.

## DT2. Un refactoring por commit, sin cambiar comportamiento

**Decisión:** cada commit de refactoring tenía que pasar las pruebas con los resultados esperados originales. Las correcciones de errores se hicieron **después** y en commits separados.
**Alternativa:** corregir los errores a medida que aparecían durante la refactorización.
**Por qué:** si en un mismo commit se mezclan refactoring y corrección, cuando cambia la salida no se sabe si fue a propósito o si el refactoring rompió algo. Separándolos, una prueba que falla en un commit de refactoring siempre es un error nuestro.

## DT3. Separar en modelo, repositorio, servicio y consola

**Decisión:** cuatro módulos dentro del paquete `gestion/`, con dependencias en un solo sentido.
**Alternativas:** dejar todo en un archivo pero con varias clases, o usar una arquitectura más completa (por ejemplo, un caso de uso por clase).
**Por qué:** un solo archivo con varias clases resolvía SRP pero seguía siendo difícil de navegar. Una clase por caso de uso hubiera sido demasiado para 6 operaciones simples. Cuatro módulos es lo mínimo que separa las tres razones de cambio del Smell 1 (interfaz, reglas y persistencia) más el modelo que comparten.

## DT4. Mantener el formato de `datos.json`

**Decisión:** el archivo usa las mismas claves que la versión inicial (`desc`, `resp`, estados como letras, prioridades como números). Lo único que se sacó es `nombre_est`, que se ignora al leer.
**Alternativa:** un formato nuevo con nombres más claros (`descripcion`, `id_responsable`, `"PENDIENTE"`).
**Por qué:** un usuario que ya tiene datos cargados con la versión inicial tiene que poder seguir usándolos. Los nombres claros están en las clases (`Solicitud.descripcion`, `Solicitud.id_responsable`) y la traducción se hace en un solo lugar, en `a_dict` y `desde_dict`.

## DT5. Excepción de negocio en lugar de valores de retorno

**Decisión:** las reglas lanzan `ErrorDeNegocio` con el mensaje para el usuario, y la consola lo muestra en un solo lugar.
**Alternativa:** devolver `None` o un código de error, como hacía la versión inicial con `return` después de cada `print`.
**Por qué:** con valores de retorno, cada llamada tiene que acordarse de revisarlos y el servicio tiene que saber qué mostrar. Con la excepción, el servicio no imprime nada, y si una regla falla es imposible que el error pase de largo.

## DT6. Herencia entre `RepositorioJSON` y `RepositorioEnMemoria`

**Decisión:** el repositorio JSON hereda del de memoria y solo agrega la carga y la escritura del archivo.
**Alternativa:** dos implementaciones independientes de `Repositorio`.
**Por qué:** la lógica de búsqueda es la misma en los dos casos; lo único que cambia es si se escribe a disco. Con la herencia, las pruebas unitarias (que usan memoria) ejercitan el mismo código de búsqueda que usa el programa. Cumple LSP porque la subclase no cambia el significado de ningún método, solo agrega la persistencia.

## DT7. Solo la librería estándar de Python

**Decisión:** no agregar dependencias para el sistema ni para las pruebas (`unittest` en lugar de `pytest`).
**Por qué:** la versión inicial se ejecutaba con un `python solicitudes.py` sin instalar nada, y quisimos mantenerlo así. `radon` y `pyflakes` se usaron solo para el análisis y no son necesarios para ejecutar ni probar.

## DT8. Corregir solo los errores con evidencia

**Decisión:** solo cambiamos el comportamiento externo donde había un error demostrable (IDs repetidos, estudiante fantasma, filtros ignorados, pérdida de datos) o una observación del code review.
**Alternativa:** aprovechar para mejorar la interfaz (mensajes, colores, menús).
**Por qué:** el objetivo del trabajo es la calidad interna. Cada cambio visible necesita una justificación y una prueba, y agregar mejoras de interfaz hubiera mezclado ese objetivo con otro.
