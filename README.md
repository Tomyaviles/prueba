# Sistema de Gestion de Solicitudes Academicas

TPI de Metodologia de Sistemas II - UTN TUP a distancia.

Sistema de consola para registrar solicitudes de estudiantes, clasificarlas por tipo, prioridad y estado, asignarles un responsable, buscarlas y sacar un reporte.

El trabajo parte de una version inicial que funciona pero tiene problemas de diseño (tag `estado-inicial`). Sobre esa version hicimos un diagnostico, la refactorizamos sin cambiar su comportamiento, corregimos los errores encontrados y revisamos el resultado (tag `estado-refactorizado`).

## Tecnologias

- Python 3.8 o superior, solo libreria estandar
- `unittest` para las pruebas
- Los datos se guardan en `datos.json`, que se crea solo la primera vez que se ejecuta

## Como usarlo

```
git clone https://github.com/francosiri96/TPI-de-Metodologia-de-Sistemas.git
cd TPI-de-Metodologia-de-Sistemas
python solicitudes.py
```

Para correr las pruebas:

```
python -m unittest discover tests -v
```

Para ver la version inicial: `git checkout estado-inicial`.

## Estructura

```
solicitudes.py          punto de entrada
gestion/
  modelo.py             Estado, Prioridad, Estudiante, Responsable, Solicitud, FiltroSolicitud
  repositorio.py        acceso a los datos (interfaz Repositorio e implementacion JSON)
  servicio.py           reglas de negocio
  consola.py            menu e interaccion con el usuario
tests/
  test_comportamiento.py  pruebas de caja negra (entrada en casos/, salida esperada en esperado/)
  test_servicio.py        pruebas unitarias de las reglas
  test_repositorio.py     pruebas del guardado en JSON
docs/
  diagnostico.md        calidad externa e interna, 12 code smells
  refactoring.md        SOLID, Clean Code y los 5 refactorings con antes/despues
  pruebas.md            estrategia de pruebas y verificacion del comportamiento
  code-review.md        checklist, observaciones, correcciones y criterios de aceptacion
  decisiones.md         decisiones tecnicas
  evidencias/           salidas de las pruebas y del analisis estatico
```

## Entidades

- Estudiante: legajo, nombre, apellido, email, carrera
- Responsable: id, nombre, area (vienen precargados)
- Solicitud: id, estudiante, tipo, descripcion, prioridad, estado, responsable, fecha
- Estado: Pendiente, En proceso, Resuelta, Cerrada, Rechazada

## Funcionalidades

1. Registrar solicitud (si el estudiante no existe se lo da de alta; la prioridad se calcula sola segun el tipo)
2. Cambiar estado
3. Asignar responsable
4. Buscar / filtrar solicitudes por estado, tipo, prioridad o responsable
5. Reporte por estado, con alerta de solicitudes urgentes sin responsable
6. Eliminar solicitud

## Reglas

- Prioridad: Reclamo de nota es Alta, Equivalencia y Cambio de comision son Media, Certificado y Otro son Baja. Si la descripcion dice "urgente" pasa a Alta.
- Cambios de estado permitidos: Pendiente a En proceso (tiene que tener responsable), Pendiente a Rechazada, En proceso a Resuelta, En proceso a Rechazada, Resuelta a Cerrada.
- No se puede asignar responsable a una solicitud Cerrada o Rechazada.
- La descripcion tiene que tener al menos 10 caracteres y el email tiene que tener "@".
- El estudiante nuevo se guarda junto con su primera solicitud; si la solicitud no se puede registrar, el estudiante tampoco queda guardado.

## Etapas y tags

| Tag | Que contiene |
|---|---|
| `estado-inicial` | Version base, con los problemas a diagnosticar |
| `etapa-diagnostico` | Calidad externa e interna y 12 code smells documentados |
| `etapa-refactoring` | Los 5 refactorings terminados, con el mismo comportamiento que la version inicial |
| `etapa-pruebas` | Pruebas unitarias y correccion de los errores encontrados |
| `etapa-docs` | Documentacion de refactoring, pruebas, code review y decisiones |
| `estado-refactorizado` | Version final |

Los datos de prueba son inventados.
