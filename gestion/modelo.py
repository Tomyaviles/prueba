"""Clases del dominio: estados, prioridades, estudiantes, responsables y solicitudes."""

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional


class ErrorDeNegocio(Exception):
    """Una regla del sistema no se cumple. El mensaje es el que ve el usuario."""


class Estado(Enum):
    PENDIENTE = "P"
    EN_PROCESO = "E"
    RESUELTA = "R"
    CERRADA = "C"
    RECHAZADA = "X"

    @property
    def nombre(self):
        return NOMBRES_ESTADO[self]

    @classmethod
    def desde_codigo(cls, codigo):
        """Devuelve el estado de esa letra, o None si la letra no corresponde a ninguno."""
        try:
            return cls(codigo)
        except ValueError:
            return None


NOMBRES_ESTADO = {
    Estado.PENDIENTE: "Pendiente",
    Estado.EN_PROCESO: "En proceso",
    Estado.RESUELTA: "Resuelta",
    Estado.CERRADA: "Cerrada",
    Estado.RECHAZADA: "Rechazada",
}

# a que estados se puede pasar desde cada estado
TRANSICIONES = {
    Estado.PENDIENTE: {Estado.EN_PROCESO, Estado.RECHAZADA},
    Estado.EN_PROCESO: {Estado.RESUELTA, Estado.RECHAZADA},
    Estado.RESUELTA: {Estado.CERRADA},
    Estado.CERRADA: set(),
    Estado.RECHAZADA: set(),
}

ESTADOS_FINALES = {Estado.CERRADA, Estado.RECHAZADA}


class Prioridad(IntEnum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3

    @property
    def nombre(self):
        return self.name.capitalize()


# el orden de este diccionario es el orden en que se muestran los tipos
PRIORIDAD_POR_TIPO = {
    "Certificado": Prioridad.BAJA,
    "Equivalencia": Prioridad.MEDIA,
    "Reclamo de nota": Prioridad.ALTA,
    "Cambio de comision": Prioridad.MEDIA,
    "Otro": Prioridad.BAJA,
}

TIPOS = list(PRIORIDAD_POR_TIPO)
PALABRA_URGENTE = "urgente"
LARGO_MINIMO_DESCRIPCION = 10


def calcular_prioridad(tipo, descripcion):
    if PALABRA_URGENTE in descripcion.lower():
        return Prioridad.ALTA
    return PRIORIDAD_POR_TIPO.get(tipo, Prioridad.BAJA)


@dataclass
class Estudiante:
    legajo: str
    nombre: str
    apellido: str
    email: str
    carrera: str

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def a_dict(self):
        return {"legajo": self.legajo, "nombre": self.nombre, "apellido": self.apellido,
                "email": self.email, "carrera": self.carrera}

    @classmethod
    def desde_dict(cls, datos):
        return cls(datos["legajo"], datos["nombre"], datos["apellido"], datos["email"], datos["carrera"])


@dataclass
class Responsable:
    id: int
    nombre: str
    area: str

    def a_dict(self):
        return {"id": self.id, "nombre": self.nombre, "area": self.area}

    @classmethod
    def desde_dict(cls, datos):
        return cls(datos["id"], datos["nombre"], datos["area"])


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

    def esta_finalizada(self):
        return self.estado in ESTADOS_FINALES

    def puede_pasar_a(self, nuevo_estado):
        return nuevo_estado in TRANSICIONES[self.estado]

    def es_urgente_sin_atender(self):
        return (self.prioridad == Prioridad.ALTA and self.id_responsable is None
                and self.estado == Estado.PENDIENTE)

    # las claves del archivo son las mismas que usaba la version inicial,
    # asi un datos.json viejo se sigue pudiendo leer
    def a_dict(self):
        return {
            "id": self.id,
            "legajo": self.legajo,
            "tipo": self.tipo,
            "desc": self.descripcion,
            "prioridad": int(self.prioridad),
            "estado": self.estado.value,
            "resp": self.id_responsable,
            "fecha": self.fecha,
        }

    @classmethod
    def desde_dict(cls, datos):
        return cls(
            id=datos["id"],
            legajo=datos["legajo"],
            tipo=datos["tipo"],
            descripcion=datos["desc"],
            prioridad=Prioridad(datos["prioridad"]),
            fecha=datos["fecha"],
            estado=Estado(datos["estado"]),
            id_responsable=datos["resp"],
        )


@dataclass
class FiltroSolicitud:
    """Criterios de busqueda tal como los escribe el usuario. Un campo vacio no filtra."""
    estado: str = ""
    tipo: str = ""
    prioridad: str = ""
    responsable: str = ""

    def validar(self):
        if self.prioridad and not self.prioridad.isdigit():
            raise ErrorDeNegocio("Prioridad invalida")
        if self.responsable and not self.responsable.isdigit():
            raise ErrorDeNegocio("ID de responsable invalido")

    def acepta(self, solicitud):
        if self.estado and solicitud.estado.value != self.estado:
            return False
        if self.tipo and self.tipo.lower() not in solicitud.tipo.lower():
            return False
        if self.prioridad and solicitud.prioridad != int(self.prioridad):
            return False
        if self.responsable and solicitud.id_responsable != int(self.responsable):
            return False
        return True
