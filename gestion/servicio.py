"""Reglas de negocio. No lee del teclado ni imprime: recibe datos y devuelve resultados o lanza ErrorDeNegocio."""

from dataclasses import dataclass
from datetime import datetime

from gestion.modelo import (LARGO_MINIMO_DESCRIPCION, TIPOS, ErrorDeNegocio, Estado, Estudiante,
                            Solicitud, calcular_prioridad)


def fecha_de_hoy():
    return datetime.now().strftime("%d/%m/%Y")


@dataclass
class Reporte:
    total: int
    cantidad_por_estado: dict
    urgentes_sin_atender: list
    porcentaje_finalizadas: float


class ServicioSolicitudes:

    def __init__(self, repositorio, obtener_fecha=fecha_de_hoy):
        self._repositorio = repositorio
        self._obtener_fecha = obtener_fecha

    # --- estudiantes ---

    def buscar_estudiante(self, legajo):
        return self._repositorio.buscar_estudiante(legajo)

    def crear_estudiante(self, legajo, nombre, apellido, email, carrera):
        """Valida los datos y arma el estudiante. Se guarda recien cuando se registra su solicitud."""
        if not legajo or not nombre or not apellido:
            raise ErrorDeNegocio("Datos invalidos")
        if "@" not in email:
            raise ErrorDeNegocio("Email invalido")
        return Estudiante(legajo, nombre, apellido, email, carrera)

    def nombre_del_estudiante(self, legajo):
        estudiante = self._repositorio.buscar_estudiante(legajo)
        return estudiante.nombre_completo if estudiante else "?"

    # --- solicitudes ---

    def tipo_por_numero(self, numero):
        if numero < 1 or numero > len(TIPOS):
            raise ErrorDeNegocio("Tipo invalido")
        return TIPOS[numero - 1]

    def validar_descripcion(self, descripcion):
        if len(descripcion) < LARGO_MINIMO_DESCRIPCION:
            raise ErrorDeNegocio(f"La descripcion debe tener al menos {LARGO_MINIMO_DESCRIPCION} caracteres")

    def registrar_solicitud(self, estudiante, tipo, descripcion):
        if tipo not in TIPOS:
            raise ErrorDeNegocio("Tipo invalido")
        self.validar_descripcion(descripcion)
        if self._repositorio.buscar_estudiante(estudiante.legajo) is None:
            self._repositorio.agregar_estudiante(estudiante)
        solicitud = Solicitud(
            id=self._repositorio.siguiente_id_solicitud(),
            legajo=estudiante.legajo,
            tipo=tipo,
            descripcion=descripcion,
            prioridad=calcular_prioridad(tipo, descripcion),
            fecha=self._obtener_fecha(),
        )
        self._repositorio.agregar_solicitud(solicitud)
        return solicitud

    def obtener_solicitud(self, id_solicitud):
        solicitud = self._repositorio.buscar_solicitud(id_solicitud)
        if solicitud is None:
            raise ErrorDeNegocio("No existe la solicitud")
        return solicitud

    def cambiar_estado(self, solicitud, codigo_estado):
        nuevo_estado = Estado.desde_codigo(codigo_estado)
        if not solicitud.puede_pasar_a(nuevo_estado):
            nombre_nuevo = nuevo_estado.nombre if nuevo_estado else "?"
            raise ErrorDeNegocio(f"Transicion no permitida de {solicitud.estado.nombre} a {nombre_nuevo}")
        if nuevo_estado == Estado.EN_PROCESO and solicitud.id_responsable is None:
            raise ErrorDeNegocio("No se puede pasar a En proceso sin responsable asignado")
        solicitud.estado = nuevo_estado
        self._repositorio.actualizar_solicitud(solicitud)

    def verificar_que_admite_responsable(self, solicitud):
        if solicitud.esta_finalizada():
            raise ErrorDeNegocio("No se puede asignar responsable a una solicitud finalizada")

    def asignar_responsable(self, solicitud, id_responsable):
        self.verificar_que_admite_responsable(solicitud)
        responsable = self._repositorio.buscar_responsable(id_responsable)
        if responsable is None:
            raise ErrorDeNegocio("Responsable inexistente")
        solicitud.id_responsable = responsable.id
        self._repositorio.actualizar_solicitud(solicitud)
        return responsable

    def eliminar_solicitud(self, solicitud):
        self._repositorio.eliminar_solicitud(solicitud)

    def filtrar(self, filtro):
        filtro.validar()
        return [s for s in self._repositorio.listar_solicitudes() if filtro.acepta(s)]

    # --- responsables y reporte ---

    def listar_responsables(self):
        return self._repositorio.listar_responsables()

    def nombre_del_responsable(self, id_responsable):
        responsable = self._repositorio.buscar_responsable(id_responsable)
        return responsable.nombre if responsable else "Sin asignar"

    def generar_reporte(self):
        solicitudes = self._repositorio.listar_solicitudes()
        cantidad_por_estado = {estado: 0 for estado in Estado}
        for solicitud in solicitudes:
            cantidad_por_estado[solicitud.estado] += 1
        finalizadas_ok = cantidad_por_estado[Estado.RESUELTA] + cantidad_por_estado[Estado.CERRADA]
        porcentaje = finalizadas_ok * 100 / len(solicitudes) if solicitudes else 0.0
        return Reporte(
            total=len(solicitudes),
            cantidad_por_estado=cantidad_por_estado,
            urgentes_sin_atender=[s for s in solicitudes if s.es_urgente_sin_atender()],
            porcentaje_finalizadas=porcentaje,
        )
