# Sistema de Gestion de Solicitudes Academicas - v1
# TODO: ordenar esto algun dia

import json
import os
from datetime import datetime

from gestion.modelo import (TIPOS, LARGO_MINIMO_DESCRIPCION, Estado, Estudiante, FiltroSolicitud,
                            Responsable, Solicitud, calcular_prioridad)

ARCHIVO = "datos.json"

RESPONSABLES_INICIALES = [
    Responsable(1, "Laura Gomez", "Alumnado"),
    Responsable(2, "Martin Ruiz", "Secretaria Academica"),
    Responsable(3, "Sofia Herrera", "Tesoreria"),
    Responsable(4, "Diego Paz", "Bedelia"),
]


def guardar(estudiantes, responsables, solicitudes):
    d = {
        "estudiantes": [e.a_dict() for e in estudiantes],
        "responsables": [r.a_dict() for r in responsables],
        "solicitudes": [s.a_dict() for s in solicitudes],
    }
    with open(ARCHIVO, "w") as f:
        json.dump(d, f, indent=2)


def cargar():
    # si no existe el archivo lo creo con los responsables
    if not os.path.exists(ARCHIVO):
        responsables = list(RESPONSABLES_INICIALES)
        guardar([], responsables, [])
        return [], responsables, []
    try:
        f = open(ARCHIVO, "r")
        d = json.load(f)
        f.close()
        return ([Estudiante.desde_dict(e) for e in d["estudiantes"]],
                [Responsable.desde_dict(r) for r in d["responsables"]],
                [Solicitud.desde_dict(s) for s in d["solicitudes"]])
    except:
        print("error")
        return [], [], []


class Sistema:

    def __init__(self):
        self.estudiantes, self.responsables, self.solicitudes = cargar()

    def guardar(self):
        guardar(self.estudiantes, self.responsables, self.solicitudes)

    def menu(self):
        while True:
            print("")
            print("===== SISTEMA DE SOLICITUDES ACADEMICAS =====")
            print("1. Registrar solicitud")
            print("2. Cambiar estado de solicitud")
            print("3. Asignar responsable")
            print("4. Buscar / filtrar solicitudes")
            print("5. Reporte")
            print("6. Eliminar solicitud")
            print("0. Salir")
            op = input("Opcion: ")
            if op == "1":
                self.reg_sol()
            elif op == "2":
                self.cambiar_estado()
            elif op == "3":
                self.asignar()
            elif op == "4":
                self.buscar()
            elif op == "5":
                self.reporte()
            elif op == "6":
                self.eliminar()
            elif op == "0":
                print("Chau!")
                break
            else:
                print("Opcion incorrecta")

    def buscar_estudiante(self, leg):
        for e in self.estudiantes:
            if e.legajo == leg:
                return e
        return None

    def buscar_solicitud(self, id):
        for s in self.solicitudes:
            if s.id == id:
                return s
        return None

    def buscar_responsable(self, id):
        for r in self.responsables:
            if r.id == id:
                return r
        return None

    def pedir_id_solicitud(self):
        try:
            return int(input("ID de la solicitud: "))
        except:
            print("error")
            return None

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
        s = Solicitud(
            id=len(self.solicitudes) + 1,
            legajo=leg,
            tipo=tipo,
            descripcion=desc,
            prioridad=calcular_prioridad(tipo, desc),
            fecha=datetime.now().strftime("%d/%m/%Y"),
        )
        self.agregar(s)
        print("Solicitud registrada con ID " + str(s.id) + " - Prioridad: " + s.prioridad.nombre)

    def registrar_estudiante(self, leg):
        r = input("El estudiante no existe. Desea registrarlo? (s/n): ")
        if r != "s" and r != "S":
            print("Operacion cancelada")
            return None
        n = input("Nombre: ")
        a = input("Apellido: ")
        em = input("Email: ")
        c = input("Carrera: ")
        if leg == "" or n == "" or a == "":
            print("Datos invalidos")
            return None
        if not "@" in em:
            print("Email invalido")
            return None
        est = Estudiante(leg, n, a, em, c)
        self.estudiantes.append(est)
        return est

    def pedir_tipo(self):
        print("Tipos de solicitud:")
        for i in range(len(TIPOS)):
            print(str(i + 1) + ". " + TIPOS[i])
        try:
            t = int(input("Tipo: "))
        except:
            print("error")
            return None
        if t < 1 or t > len(TIPOS):
            print("Tipo invalido")
            return None
        return TIPOS[t - 1]

    def pedir_descripcion(self):
        desc = input("Descripcion: ")
        if len(desc) < LARGO_MINIMO_DESCRIPCION:
            print("La descripcion debe tener al menos " + str(LARGO_MINIMO_DESCRIPCION) + " caracteres")
            return None
        return desc

    def agregar(self, solicitud):
        self.solicitudes.append(solicitud)
        self.guardar()

    def cambiar_estado(self):
        print("--- Cambiar estado ---")
        id = self.pedir_id_solicitud()
        if id == None:
            return
        s = self.buscar_solicitud(id)
        if s == None:
            print("No existe la solicitud")
            return
        print("Estado actual: " + s.estado.nombre)
        print("P=Pendiente, E=En proceso, R=Resuelta, C=Cerrada, X=Rechazada")
        n = input("Nuevo estado: ").upper()
        nuevo = Estado.desde_codigo(n)
        if not s.puede_pasar_a(nuevo):
            nombre_nuevo = nuevo.nombre if nuevo else "?"
            print("Transicion no permitida de " + s.estado.nombre + " a " + nombre_nuevo)
            return
        if nuevo == Estado.EN_PROCESO and s.id_responsable == None:
            print("No se puede pasar a En proceso sin responsable asignado")
            return
        s.estado = nuevo
        self.guardar()
        print("Estado actualizado a " + nuevo.nombre)

    def asignar(self):
        print("--- Asignar responsable ---")
        id = self.pedir_id_solicitud()
        if id == None:
            return
        s = self.buscar_solicitud(id)
        if s == None:
            print("No existe la solicitud")
            return
        if s.esta_finalizada():
            print("No se puede asignar responsable a una solicitud finalizada")
            return
        for r in self.responsables:
            print(str(r.id) + " - " + r.nombre + " (" + r.area + ")")
        try:
            rid = int(input("ID del responsable: "))
        except:
            print("error")
            return
        r = self.buscar_responsable(rid)
        if r == None:
            print("Responsable inexistente")
            return
        s.id_responsable = rid
        self.guardar()
        print("Responsable " + r.nombre + " asignado a la solicitud " + str(id))

    def buscar(self):
        print("--- Buscar solicitudes (Enter para omitir un filtro) ---")
        filtro = FiltroSolicitud(
            estado=input("Estado (P/E/R/C/X): ").upper(),
            tipo=input("Tipo (texto): "),
            prioridad=input("Prioridad (1/2/3): "),
            responsable=input("ID responsable: "),
        )
        res = self.filtrar(filtro)
        if len(res) == 0:
            print("No se encontraron solicitudes")
        else:
            print(str(len(res)) + " solicitud(es) encontrada(s):")
            for s in res:
                resp = "Sin asignar"
                x = self.buscar_responsable(s.id_responsable)
                if x != None:
                    resp = x.nombre
                est = self.buscar_estudiante(s.legajo)
                nombre = est.nombre_completo if est else "?"
                print("#" + str(s.id) + " | " + s.fecha + " | " + nombre + " (" + s.legajo + ") | " + s.tipo + " | " + s.prioridad.nombre + " | " + s.estado.nombre + " | " + resp)
                print("    " + s.descripcion)

    def filtrar(self, filtro):
        return [s for s in self.solicitudes if filtro.acepta(s)]

    def reporte(self):
        print("--- Reporte de solicitudes ---")
        sols = self.solicitudes
        print("Total de solicitudes: " + str(len(sols)))
        cantidad = {estado: 0 for estado in Estado}
        for s in sols:
            cantidad[s.estado] += 1
        print("Por estado:")
        for estado in Estado:
            print("  " + estado.nombre + ": " + str(cantidad[estado]))
        # alertas
        al = [s for s in sols if s.es_urgente_sin_atender()]
        if len(al) > 0:
            print("ALERTA: " + str(len(al)) + " solicitud(es) de prioridad alta sin responsable: " + ", ".join(["#" + str(s.id) for s in al]))
        if len(sols) > 0:
            pct = (cantidad[Estado.RESUELTA] + cantidad[Estado.CERRADA]) * 100 / len(sols)
            print("Porcentaje resueltas/cerradas: " + str(round(pct, 1)) + "%")

    def eliminar(self):
        print("--- Eliminar solicitud ---")
        id = self.pedir_id_solicitud()
        if id == None:
            return
        s = self.buscar_solicitud(id)
        if s == None:
            print("No existe la solicitud")
            return
        c = input("Seguro que desea eliminarla? (s/n): ")
        if c == "s":
            self.solicitudes.remove(s)
            self.guardar()
            print("Solicitud eliminada")


if __name__ == "__main__":
    s = Sistema()
    s.menu()
