"""Acceso a los datos. El resto del sistema depende de Repositorio, no del archivo JSON."""

import json
import os
from abc import ABC, abstractmethod

from gestion.modelo import Estudiante, Responsable, Solicitud

RESPONSABLES_INICIALES = [
    Responsable(1, "Laura Gomez", "Alumnado"),
    Responsable(2, "Martin Ruiz", "Secretaria Academica"),
    Responsable(3, "Sofia Herrera", "Tesoreria"),
    Responsable(4, "Diego Paz", "Bedelia"),
]


class ErrorDeDatos(Exception):
    """No se pudieron leer los datos guardados."""


class Repositorio(ABC):

    @abstractmethod
    def buscar_estudiante(self, legajo): ...

    @abstractmethod
    def agregar_estudiante(self, estudiante): ...

    @abstractmethod
    def listar_responsables(self): ...

    @abstractmethod
    def buscar_responsable(self, id_responsable): ...

    @abstractmethod
    def listar_solicitudes(self): ...

    @abstractmethod
    def buscar_solicitud(self, id_solicitud): ...

    @abstractmethod
    def agregar_solicitud(self, solicitud): ...

    @abstractmethod
    def eliminar_solicitud(self, solicitud): ...

    @abstractmethod
    def siguiente_id_solicitud(self): ...

    @abstractmethod
    def guardar(self):
        """Hace permanentes los cambios hechos sobre los objetos."""


class RepositorioEnMemoria(Repositorio):
    """Guarda todo en listas. Se usa en las pruebas unitarias y es la base del repositorio JSON."""

    def __init__(self, estudiantes=None, responsables=None, solicitudes=None):
        self._estudiantes = list(estudiantes or [])
        self._responsables = list(responsables or [])
        self._solicitudes = list(solicitudes or [])

    def buscar_estudiante(self, legajo):
        return next((e for e in self._estudiantes if e.legajo == legajo), None)

    def agregar_estudiante(self, estudiante):
        self._estudiantes.append(estudiante)

    def listar_responsables(self):
        return list(self._responsables)

    def buscar_responsable(self, id_responsable):
        return next((r for r in self._responsables if r.id == id_responsable), None)

    def listar_solicitudes(self):
        return list(self._solicitudes)

    def buscar_solicitud(self, id_solicitud):
        return next((s for s in self._solicitudes if s.id == id_solicitud), None)

    def agregar_solicitud(self, solicitud):
        self._solicitudes.append(solicitud)
        self.guardar()

    def eliminar_solicitud(self, solicitud):
        self._solicitudes.remove(solicitud)
        self.guardar()

    def siguiente_id_solicitud(self):
        return len(self._solicitudes) + 1

    def guardar(self):
        pass


class RepositorioJSON(RepositorioEnMemoria):
    """Mantiene los datos en memoria y los escribe en un archivo JSON en cada cambio."""

    def __init__(self, ruta):
        super().__init__()
        self._ruta = ruta

    def cargar(self):
        """Lee el archivo. Si no existe lo crea con los responsables iniciales."""
        if not os.path.exists(self._ruta):
            self._responsables = list(RESPONSABLES_INICIALES)
            self.guardar()
            return
        try:
            with open(self._ruta, "r") as archivo:
                datos = json.load(archivo)
            estudiantes = [Estudiante.desde_dict(e) for e in datos["estudiantes"]]
            responsables = [Responsable.desde_dict(r) for r in datos["responsables"]]
            solicitudes = [Solicitud.desde_dict(s) for s in datos["solicitudes"]]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise ErrorDeDatos(f"No se pudo leer {self._ruta}: {error}") from error
        self._estudiantes = estudiantes
        self._responsables = responsables
        self._solicitudes = solicitudes

    def guardar(self):
        datos = {
            "estudiantes": [e.a_dict() for e in self._estudiantes],
            "responsables": [r.a_dict() for r in self._responsables],
            "solicitudes": [s.a_dict() for s in self._solicitudes],
        }
        with open(self._ruta, "w") as archivo:
            json.dump(datos, archivo, indent=2)
