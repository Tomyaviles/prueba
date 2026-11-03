# Sistema de Gestion de Solicitudes Academicas - v1
# TODO: ordenar esto algun dia

import json
import os
from datetime import datetime

ARCHIVO = "datos.json"


def guardar(d):
    with open(ARCHIVO, "w") as f:
        json.dump(d, f, indent=2)


def cargar():
    # si no existe el archivo lo creo con los responsables
    if not os.path.exists(ARCHIVO):
        d = {
            "estudiantes": [],
            "responsables": [
                {"id": 1, "nombre": "Laura Gomez", "area": "Alumnado"},
                {"id": 2, "nombre": "Martin Ruiz", "area": "Secretaria Academica"},
                {"id": 3, "nombre": "Sofia Herrera", "area": "Tesoreria"},
                {"id": 4, "nombre": "Diego Paz", "area": "Bedelia"},
            ],
            "solicitudes": [],
        }
        guardar(d)
        return d
    try:
        f = open(ARCHIVO, "r")
        d = json.load(f)
        f.close()
        return d
    except:
        print("error")
        return {"estudiantes": [], "responsables": [], "solicitudes": []}


def nom_est(e):
    if e == "P":
        return "Pendiente"
    elif e == "E":
        return "En proceso"
    elif e == "R":
        return "Resuelta"
    elif e == "C":
        return "Cerrada"
    elif e == "X":
        return "Rechazada"
    else:
        return "?"


def nom_prio(p):
    if p == 1:
        return "Baja"
    if p == 2:
        return "Media"
    if p == 3:
        return "Alta"
    return "?"


def calcular_prioridad(tipo, desc):
    if tipo == "Reclamo de nota":
        p = 3
    elif tipo == "Equivalencia":
        p = 2
    elif tipo == "Cambio de comision":
        p = 2
    elif tipo == "Certificado":
        p = 1
    else:
        p = 1
    if "urgente" in desc.lower():
        p = 3
    return p


class Sistema:

    def __init__(self):
        self.d = cargar()
        self.tipos = ["Certificado", "Equivalencia", "Reclamo de nota", "Cambio de comision", "Otro"]

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
        for e in self.d["estudiantes"]:
            if e["legajo"] == leg:
                return e
        return None

    def buscar_solicitud(self, id):
        for s in self.d["solicitudes"]:
            if s["id"] == id:
                return s
        return None

    def buscar_responsable(self, id):
        for r in self.d["responsables"]:
            if r["id"] == id:
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
        p = calcular_prioridad(tipo, desc)
        id = len(self.d["solicitudes"]) + 1
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.agregar(id, leg, est["nombre"], est["apellido"], tipo, desc, p, "P", None, fecha)
        print("Solicitud registrada con ID " + str(id) + " - Prioridad: " + nom_prio(p))

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
        est = {"legajo": leg, "nombre": n, "apellido": a, "email": em, "carrera": c}
        self.d["estudiantes"].append(est)
        return est

    def pedir_tipo(self):
        print("Tipos de solicitud:")
        for i in range(len(self.tipos)):
            print(str(i + 1) + ". " + self.tipos[i])
        try:
            t = int(input("Tipo: "))
        except:
            print("error")
            return None
        if t < 1 or t > 5:
            print("Tipo invalido")
            return None
        return self.tipos[t - 1]

    def pedir_descripcion(self):
        desc = input("Descripcion: ")
        if len(desc) < 10:
            print("La descripcion debe tener al menos 10 caracteres")
            return None
        return desc

    def agregar(self, id, leg, nom, ape, tipo, desc, prio, est, resp, fecha):
        s = {
            "id": id,
            "legajo": leg,
            "nombre_est": nom + " " + ape,
            "tipo": tipo,
            "desc": desc,
            "prioridad": prio,
            "estado": est,
            "resp": resp,
            "fecha": fecha,
        }
        self.d["solicitudes"].append(s)
        guardar(self.d)

    def cambiar_estado(self):
        print("--- Cambiar estado ---")
        id = self.pedir_id_solicitud()
        if id == None:
            return
        s = self.buscar_solicitud(id)
        if s == None:
            print("No existe la solicitud")
            return
        print("Estado actual: " + nom_est(s["estado"]))
        print("P=Pendiente, E=En proceso, R=Resuelta, C=Cerrada, X=Rechazada")
        n = input("Nuevo estado: ").upper()
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
        if ok:
            s["estado"] = n
            guardar(self.d)
            print("Estado actualizado a " + nom_est(n))
        else:
            print("Transicion no permitida de " + nom_est(s["estado"]) + " a " + nom_est(n))

    def asignar(self):
        print("--- Asignar responsable ---")
        id = self.pedir_id_solicitud()
        if id == None:
            return
        s = self.buscar_solicitud(id)
        if s == None:
            print("No existe la solicitud")
            return
        if s["estado"] == "C" or s["estado"] == "X":
            print("No se puede asignar responsable a una solicitud finalizada")
            return
        for r in self.d["responsables"]:
            print(str(r["id"]) + " - " + r["nombre"] + " (" + r["area"] + ")")
        try:
            rid = int(input("ID del responsable: "))
        except:
            print("error")
            return
        r = self.buscar_responsable(rid)
        if r == None:
            print("Responsable inexistente")
            return
        s["resp"] = rid
        guardar(self.d)
        print("Responsable " + r["nombre"] + " asignado a la solicitud " + str(id))

    def buscar(self):
        print("--- Buscar solicitudes (Enter para omitir un filtro) ---")
        e = input("Estado (P/E/R/C/X): ").upper()
        t = input("Tipo (texto): ")
        p = input("Prioridad (1/2/3): ")
        r = input("ID responsable: ")
        res = self.filtrar(e, t, p, r)
        if len(res) == 0:
            print("No se encontraron solicitudes")
        else:
            print(str(len(res)) + " solicitud(es) encontrada(s):")
            for s in res:
                resp = "Sin asignar"
                x = self.buscar_responsable(s["resp"])
                if x != None:
                    resp = x["nombre"]
                print("#" + str(s["id"]) + " | " + s["fecha"] + " | " + s["nombre_est"] + " (" + s["legajo"] + ") | " + s["tipo"] + " | " + nom_prio(s["prioridad"]) + " | " + nom_est(s["estado"]) + " | " + resp)
                print("    " + s["desc"])

    def filtrar(self, e, t, p, r):
        lst = []
        for s in self.d["solicitudes"]:
            if e != "" and s["estado"] != e:
                continue
            if t != "" and t.lower() not in s["tipo"].lower():
                continue
            if p != "":
                try:
                    if s["prioridad"] != int(p):
                        continue
                except:
                    pass
            if r != "":
                try:
                    if s["resp"] != int(r):
                        continue
                except:
                    pass
            lst.append(s)
        return lst

    def reporte(self):
        print("--- Reporte de solicitudes ---")
        sols = self.d["solicitudes"]
        print("Total de solicitudes: " + str(len(sols)))
        p = 0
        e = 0
        r = 0
        c = 0
        x = 0
        for s in sols:
            if s["estado"] == "P":
                p = p + 1
            elif s["estado"] == "E":
                e = e + 1
            elif s["estado"] == "R":
                r = r + 1
            elif s["estado"] == "C":
                c = c + 1
            elif s["estado"] == "X":
                x = x + 1
        print("Por estado:")
        print("  Pendiente: " + str(p))
        print("  En proceso: " + str(e))
        print("  Resuelta: " + str(r))
        print("  Cerrada: " + str(c))
        print("  Rechazada: " + str(x))
        # alertas
        al = []
        for s in sols:
            if s["prioridad"] == 3 and s["resp"] == None and s["estado"] == "P":
                al.append(s)
        if len(al) > 0:
            print("ALERTA: " + str(len(al)) + " solicitud(es) de prioridad alta sin responsable: " + ", ".join(["#" + str(s["id"]) for s in al]))
        if len(sols) > 0:
            pct = (r + c) * 100 / len(sols)
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
            self.d["solicitudes"].remove(s)
            guardar(self.d)
            print("Solicitud eliminada")


if __name__ == "__main__":
    s = Sistema()
    s.menu()
