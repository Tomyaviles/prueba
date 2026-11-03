# Refactoring, SOLID y Clean Code

Versión base: tag `estado-inicial` (un solo archivo `solicitudes.py` de 356 líneas).
Versión final: tag `estado-refactorizado`. La refactorización propiamente dicha termina en el tag `etapa-refactoring`.

Regla que seguimos en todo el proceso: **un refactoring por commit y las 8 pruebas de caja negra tienen que pasar sin tocar los resultados esperados**. Si una prueba fallaba, el refactoring estaba mal y se corregía antes de commitear. La evidencia de las pruebas corridas en cada commit está en [evidencias/pruebas_por_commit.txt](evidencias/pruebas_por_commit.txt).

## 1. Estructura antes y después

**Antes:** todo en `solicitudes.py`. La clase `Sistema` lee del teclado, valida, aplica las reglas, arma los textos y escribe el archivo.

**Después:**

```
solicitudes.py          punto de entrada: arma las piezas y arranca el menu (28 lineas)
gestion/
  modelo.py             Estado, Prioridad, Estudiante, Responsable, Solicitud, FiltroSolicitud
  repositorio.py        Repositorio (interfaz), RepositorioEnMemoria, RepositorioJSON
  servicio.py           ServicioSolicitudes: reglas de negocio, sin input() ni print()
  consola.py            MenuConsola: input() y print(), sin reglas de negocio
```

Las dependencias van en un solo sentido:

```
consola  -->  servicio  -->  Repositorio (interfaz)  <--  RepositorioJSON
   \             |
    +------>  modelo  <------------------------------------+
```

`solicitudes.py` es el único lugar que conoce las clases concretas: crea el `RepositorioJSON`, se lo pasa al `ServicioSolicitudes` y el servicio se lo pasa al `MenuConsola`.

## 2. Aplicación de SOLID (Etapa 4)

| Principio | Problema en la versión inicial | Qué hicimos | Dónde |
|---|---|---|---|
| **SRP** | `Sistema` tenía 3 motivos para cambiar: la interfaz, las reglas y la persistencia (Smell 1). | Una clase por responsabilidad: `MenuConsola` solo habla con el usuario, `ServicioSolicitudes` solo aplica reglas, `RepositorioJSON` solo lee y escribe. | Refactorings 4 y 5 |
| **OCP** | Los estados estaban repetidos en 4 cadenas de if/elif (Smell 6). Agregar un estado obligaba a modificar las 4. | Tablas `TRANSICIONES`, `NOMBRES_ESTADO` y `PRIORIDAD_POR_TIPO`. El menú también es una tabla (`self._opciones`). Para agregar un estado, un tipo o una opción del menú se agrega una entrada, sin tocar la lógica. | Refactoring 2 y 5 |
| **LSP** | No había jerarquías. | `RepositorioJSON` hereda de `RepositorioEnMemoria` y solo redefine `_persistir()`. Se puede usar cualquiera de los dos donde el servicio espera un `Repositorio`: las pruebas unitarias usan el de memoria y el programa usa el JSON, con las mismas reglas. | Refactoring 4 |
| **ISP** | No aplicaba en la versión inicial. | La interfaz `Repositorio` tiene solo las operaciones que usa el servicio. La consola no ve el repositorio. Evaluamos partirla en lectura y escritura, pero hay un solo cliente que usa todos los métodos, así que partirla no aportaba nada. | Refactoring 4 |
| **DIP** | La lógica dependía directamente de `json.dump` y de `open(ARCHIVO)` (Smell 10). | `ServicioSolicitudes` recibe un `Repositorio` (clase abstracta) en el constructor y no sabe que existe un archivo. También recibe la función que da la fecha, para poder fijarla en las pruebas. | Refactoring 4 y 5 |

## 3. Clean Code aplicado

| Aspecto | Antes | Después |
|---|---|---|
| Nombres | `d`, `x`, `al`, `enc`, `e`/`t`/`p`/`r`, `c` con dos significados (Smell 8) | `estudiante`, `solicitud`, `urgentes`, `id_responsable`, `FiltroSolicitud(estado, tipo, prioridad, responsable)` |
| Funciones | `reg_sol` de 58 líneas con 7 tareas, complejidad 20 (Smell 2) | La función más compleja tiene complejidad 9 y el promedio bajó de 8,4 a 2,3 (ver sección 6) |
| Manejo de errores | `except:` vacío en 8 lugares y `pass` en `filtrar` (Smell 7) | Se capturan excepciones concretas (`ValueError`, `OSError`, `json.JSONDecodeError`). Las reglas lanzan `ErrorDeNegocio` con el mensaje para el usuario y la consola lo muestra en un solo lugar (`MenuConsola.iniciar`). |
| Magic values | `"P"`, `"X"`, `3`, `t > 5` (Smell 5) | `Estado.PENDIENTE`, `Prioridad.ALTA`, `len(TIPOS)`, `LARGO_MINIMO_DESCRIPCION` |
| Tipos primitivos | Diccionarios con claves de texto (Smell 9) | Clases `Solicitud`, `Estudiante` y `Responsable` con métodos propios (`esta_finalizada`, `puede_pasar_a`, `nombre_completo`) |
| Código muerto | `cont = 0` (Smell 11) | Eliminado |
| Duplicación | 5 copias del guardado y 3 de la búsqueda por ID (Smell 4) | Un solo `_persistir()` y un solo `buscar_solicitud()` |

## 4. Refactorings aplicados (Etapa 5)

### Refactoring 1: Extract Method

**Commit:** `e4f75dd`. **Smells:** 2, 4 y 11.

Se extrajeron a métodos propios el guardado del archivo (repetido 5 veces), las búsquedas por ID y las partes de `reg_sol`. En el mismo commit se eliminó la variable `cont`, que no se usaba.

**Antes** (`reg_sol`, el cálculo de prioridad estaba en el medio del método):

```python
        desc = input("Descripcion: ")
        if len(desc) < 10:
            print("La descripcion debe tener al menos 10 caracteres")
            return
        # calculo de prioridad
        if tipo == "Reclamo de nota":
            p = 3
        elif tipo == "Equivalencia":
            p = 2
        ...
        if "urgente" in desc.lower():
            p = 3
        id = len(self.d["solicitudes"]) + 1
```

**Después:**

```python
    def reg_sol(self):
        print("--- Registrar solicitud ---")
        leg = input("Legajo del estudiante: ")
        est = self.buscar_estudiante(leg)
        if est == None:
            est = self.registrar_estudiante(leg)
            if est == None:
                return
        tipo = self.pedir_tipo()
        if tipo == None:
            return
        desc = self.pedir_descripcion()
        if desc == None:
            return
        p = calcular_prioridad(tipo, desc)
        ...
```

Y el guardado, que estaba copiado en 5 lugares:

```python
# antes, en agregar, cambiar_estado, asignar, eliminar y cargar
        f = open(ARCHIVO, "w")
        json.dump(self.d, f, indent=2)
        f.close()

# despues
def guardar(d):
    with open(ARCHIVO, "w") as f:
        json.dump(d, f, indent=2)
```

Además de sacar la duplicación, el `with` cierra el archivo aunque `json.dump` falle.

---

### Refactoring 2: Replace Conditional with Table y Enum

**Commit:** `5199939`. **Smells:** 5 y 6. **Principio:** OCP.

**Antes** (transiciones):

```python
        ok = False
        if s["estado"] == "P":
            if n == "E":
                if s["resp"] == None:
                    print("No se puede pasar a En proceso sin responsable asignado")
                    return
                ok = True
            elif n == "X":
                ok = True
        elif s["estado"] == "E":
            if n == "R" or n == "X":
                ok = True
        elif s["estado"] == "R":
            if n == "C":
                ok = True
```

**Después** (en la versión final está en `gestion/modelo.py`):

```python
TRANSICIONES = {
    Estado.PENDIENTE: {Estado.EN_PROCESO, Estado.RECHAZADA},
    Estado.EN_PROCESO: {Estado.RESUELTA, Estado.RECHAZADA},
    Estado.RESUELTA: {Estado.CERRADA},
    Estado.CERRADA: set(),
    Estado.RECHAZADA: set(),
}

    def puede_pasar_a(self, nuevo_estado):
        return nuevo_estado in TRANSICIONES[self.estado]
```

Lo mismo con la prioridad: la cadena de 10 líneas de if/elif pasó a ser el diccionario `PRIORIDAD_POR_TIPO` y la función quedó así:

```python
def calcular_prioridad(tipo, descripcion):
    if PALABRA_URGENTE in descripcion.lower():
        return Prioridad.ALTA
    return PRIORIDAD_POR_TIPO.get(tipo, Prioridad.BAJA)
```

La lista de tipos ahora sale del mismo diccionario (`TIPOS = list(PRIORIDAD_POR_TIPO)`), así que el `t > 5` escrito a mano pasó a ser `len(TIPOS)`. Agregar un tipo nuevo es agregar una línea.

---

### Refactoring 3: Introduce Parameter Object

**Commit:** `2484a67`. **Smells:** 3, 9 y 12.

**Antes:**

```python
    def agregar(self, id, leg, nom, ape, tipo, desc, prio, est, resp, fecha):

        self.agregar(id, leg, est["nombre"], est["apellido"], tipo, desc, p, "P", None, fecha)

    def filtrar(self, e, t, p, r):
```

**Después:**

```python
@dataclass
class Solicitud:
    id: int
    legajo: str
    tipo: str
    descripcion: str
    prioridad: Prioridad
    fecha: str
    estado: Estado = Estado.PENDIENTE
    id_responsable: Optional[int] = None

@dataclass
class FiltroSolicitud:
    estado: str = ""
    tipo: str = ""
    prioridad: str = ""
    responsable: str = ""

    def acepta(self, solicitud): ...
```

`agregar` pasó a recibir un solo objeto `Solicitud`, y `estado` y `responsable` dejaron de ser parámetros porque tienen valor por defecto. `filtrar(e, t, p, r)` pasó a recibir un `FiltroSolicitud`, y la lógica de cada filtro quedó dentro del objeto, en `acepta()`.

En este paso también se sacó el campo `nombre_est` de la solicitud (Smell 12). El nombre se busca en el estudiante por legajo. Las claves que se guardan en el JSON son las mismas de la versión inicial, así que un `datos.json` viejo se sigue pudiendo leer (lo verifica la prueba `test_lee_archivo_de_la_version_inicial`).

---

### Refactoring 4: Move Method (persistencia al repositorio)

**Commit:** `5a4ac2b`. **Smells:** 1, 4 y 10. **Principios:** DIP y LSP.

Se movieron `cargar`, `guardar` y las búsquedas a `gestion/repositorio.py`, detrás de una clase abstracta:

```python
class Repositorio(ABC):
    @abstractmethod
    def buscar_estudiante(self, legajo): ...
    @abstractmethod
    def buscar_solicitud(self, id_solicitud): ...
    @abstractmethod
    def agregar_solicitud(self, solicitud): ...
    ...

class RepositorioEnMemoria(Repositorio): ...      # para las pruebas
class RepositorioJSON(RepositorioEnMemoria): ...  # lee y escribe datos.json
```

**Antes:** `Sistema.__init__` llamaba a `cargar()`, que leía el archivo directamente, y cada operación escribía el JSON por su cuenta.

**Después:**

```python
def main():
    repositorio = RepositorioJSON(ARCHIVO)
    ...
    MenuConsola(ServicioSolicitudes(repositorio)).iniciar()
```

Para pasar a una base de datos alcanza con escribir otra clase que implemente `Repositorio` y cambiar esta línea. El resto del sistema no se entera.

---

### Refactoring 5: Move Method (reglas al servicio, entrada y salida a la consola)

**Commit:** `1ae8882`. **Smells:** 1, 2, 7 y 8. **Principio:** SRP.

Cada método de `Sistema` se partió en dos: lo que habla con el usuario fue a `MenuConsola` y la regla fue a `ServicioSolicitudes`. En este mismo paso se renombraron las variables y se reemplazaron los `except:` por excepciones concretas.

**Antes** (`asignar`, todo mezclado):

```python
    def asignar(self):
        print("--- Asignar responsable ---")
        try:
            id = int(input("ID de la solicitud: "))
        except:
            print("error")
            return
        ...
        if s["estado"] == "C" or s["estado"] == "X":
            print("No se puede asignar responsable a una solicitud finalizada")
            return
        ...
        f = open(ARCHIVO, "w")
        json.dump(self.d, f, indent=2)
        f.close()
        print("Responsable " + nombre + " asignado a la solicitud " + str(id))
```

**Después**, la regla en el servicio (sin `input` ni `print`):

```python
    def asignar_responsable(self, solicitud, id_responsable):
        self.verificar_que_admite_responsable(solicitud)
        responsable = self._repositorio.buscar_responsable(id_responsable)
        if responsable is None:
            raise ErrorDeNegocio("Responsable inexistente")
        solicitud.id_responsable = responsable.id
        self._repositorio.actualizar_solicitud(solicitud)
        return responsable
```

y la interacción en la consola:

```python
    def asignar_responsable(self):
        print("--- Asignar responsable ---")
        solicitud = self._pedir_solicitud()
        if solicitud is None:
            return
        self._servicio.verificar_que_admite_responsable(solicitud)
        for responsable in self._servicio.listar_responsables():
            print(f"{responsable.id} - {responsable.nombre} ({responsable.area})")
        id_responsable = self._pedir_numero("ID del responsable: ")
        if id_responsable is None:
            return
        responsable = self._servicio.asignar_responsable(solicitud, id_responsable)
        print(f"Responsable {responsable.nombre} asignado a la solicitud {solicitud.id}")
```

Los errores de negocio se muestran en un solo lugar, en el bucle del menú:

```python
            try:
                accion()
            except ErrorDeNegocio as error:
                print(error)
```

La consecuencia más importante es que ahora las reglas se pueden probar sin simular a un usuario escribiendo en el teclado. Antes de este paso era imposible (lo dice el impacto del Smell 1). Las pruebas unitarias de [tests/test_servicio.py](../tests/test_servicio.py) se escribieron justamente después de este commit.

## 5. Relación entre smells y refactorings

| Smell | Prioridad | Resuelto en |
|---|---|---|
| 1. God Class | Alta | Refactorings 4 y 5 |
| 2. Long Method | Alta | Refactorings 1 y 5, corrección del error del estudiante (`30268b8`) |
| 3. Long Parameter List | Media | Refactoring 3 |
| 4. Código duplicado | Alta | Refactorings 1 y 4 |
| 5. Magic strings / numbers | Media | Refactoring 2 |
| 6. Cadenas de if/elif | Media | Refactoring 2 |
| 7. Excepciones silenciosas | Alta | Refactoring 5 y correcciones `135e71c` y `a8214a8` |
| 8. Nombres pobres | Media | Refactoring 5 |
| 9. Primitive Obsession | Alta | Refactorings 2 y 3 |
| 10. Acoplamiento al archivo | Media | Refactoring 4 |
| 11. Código muerto | Baja | Refactoring 1 |
| 12. Datos duplicados | Media | Refactoring 3 |

Los 12 smells quedaron resueltos. El orden siguió la prioridad del diagnóstico, salvo los de prioridad Alta 1 y 7, que necesitaban que antes existieran las clases del modelo (refactorings 2 y 3) para poder mover las reglas a algún lugar.

## 6. Métricas antes y después

Medido con `radon` (salida completa en [evidencias/analisis_estatico.txt](evidencias/analisis_estatico.txt)).

| Métrica | Inicial | Final |
|---|---|---|
| Complejidad ciclomática promedio | 8,4 (B) | 2,3 (A) |
| Función más compleja | `reg_sol`: 20 (C) | `FiltroSolicitud.acepta`: 9 (B) |
| Funciones con complejidad C (11 a 20) | 5 | 0 |
| Índice de mantenibilidad | 15,3 (un solo archivo) | entre 39,9 y 47,1 por módulo |
| Líneas totales | 356 | 651 |

Hay más líneas que al principio. Era esperable: aparecen clases, docstrings y separación en archivos. Lo que bajó es la complejidad de cada parte, que es lo que hace falta entender para modificar algo.
