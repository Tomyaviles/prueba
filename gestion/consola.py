"""Interfaz de consola: pide datos, llama al servicio y muestra los resultados."""

from gestion.modelo import TIPOS, ErrorDeNegocio, Estado, FiltroSolicitud


class MenuConsola:

    def __init__(self, servicio):
        self._servicio = servicio
        # para agregar una opcion alcanza con sumarla aca
        self._opciones = {
            "1": ("Registrar solicitud", self.registrar_solicitud),
            "2": ("Cambiar estado de solicitud", self.cambiar_estado),
            "3": ("Asignar responsable", self.asignar_responsable),
            "4": ("Buscar / filtrar solicitudes", self.buscar),
            "5": ("Reporte", self.mostrar_reporte),
            "6": ("Eliminar solicitud", self.eliminar),
        }

    def iniciar(self):
        while True:
            self._mostrar_menu()
            opcion = input("Opcion: ")
            if opcion == "0":
                print("Chau!")
                break
            if opcion not in self._opciones:
                print("Opcion incorrecta")
                continue
            _, accion = self._opciones[opcion]
            try:
                accion()
            except ErrorDeNegocio as error:
                print(error)

    def _mostrar_menu(self):
        print("")
        print("===== SISTEMA DE SOLICITUDES ACADEMICAS =====")
        for numero, (titulo, _) in self._opciones.items():
            print(f"{numero}. {titulo}")
        print("0. Salir")

    # --- acciones del menu ---

    def registrar_solicitud(self):
        print("--- Registrar solicitud ---")
        legajo = input("Legajo del estudiante: ")
        estudiante = self._servicio.buscar_estudiante(legajo)
        if estudiante is None:
            estudiante = self._registrar_estudiante(legajo)
            if estudiante is None:
                return
        tipo = self._pedir_tipo()
        if tipo is None:
            return
        descripcion = input("Descripcion: ")
        solicitud = self._servicio.registrar_solicitud(estudiante, tipo, descripcion)
        print(f"Solicitud registrada con ID {solicitud.id} - Prioridad: {solicitud.prioridad.nombre}")

    def cambiar_estado(self):
        print("--- Cambiar estado ---")
        solicitud = self._pedir_solicitud()
        if solicitud is None:
            return
        print("Estado actual: " + solicitud.estado.nombre)
        print(", ".join(f"{estado.value}={estado.nombre}" for estado in Estado))
        codigo = input("Nuevo estado: ").upper()
        self._servicio.cambiar_estado(solicitud, codigo)
        print("Estado actualizado a " + solicitud.estado.nombre)

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

    def buscar(self):
        print("--- Buscar solicitudes (Enter para omitir un filtro) ---")
        filtro = FiltroSolicitud(
            estado=input("Estado (P/E/R/C/X): ").upper(),
            tipo=input("Tipo (texto): "),
            prioridad=input("Prioridad (1/2/3): "),
            responsable=input("ID responsable: "),
        )
        encontradas = self._servicio.filtrar(filtro)
        if not encontradas:
            print("No se encontraron solicitudes")
            return
        print(f"{len(encontradas)} solicitud(es) encontrada(s):")
        for solicitud in encontradas:
            self._mostrar_solicitud(solicitud)

    def mostrar_reporte(self):
        print("--- Reporte de solicitudes ---")
        reporte = self._servicio.generar_reporte()
        print(f"Total de solicitudes: {reporte.total}")
        print("Por estado:")
        for estado, cantidad in reporte.cantidad_por_estado.items():
            print(f"  {estado.nombre}: {cantidad}")
        urgentes = reporte.urgentes_sin_atender
        if urgentes:
            ids = ", ".join(f"#{s.id}" for s in urgentes)
            print(f"ALERTA: {len(urgentes)} solicitud(es) de prioridad alta sin responsable: {ids}")
        if reporte.total > 0:
            print(f"Porcentaje resueltas/cerradas: {round(reporte.porcentaje_finalizadas, 1)}%")

    def eliminar(self):
        print("--- Eliminar solicitud ---")
        solicitud = self._pedir_solicitud()
        if solicitud is None:
            return
        confirmacion = input("Seguro que desea eliminarla? (s/n): ")
        if confirmacion == "s":
            self._servicio.eliminar_solicitud(solicitud)
            print("Solicitud eliminada")

    # --- auxiliares ---

    def _registrar_estudiante(self, legajo):
        respuesta = input("El estudiante no existe. Desea registrarlo? (s/n): ")
        if respuesta.lower() != "s":
            print("Operacion cancelada")
            return None
        nombre = input("Nombre: ")
        apellido = input("Apellido: ")
        email = input("Email: ")
        carrera = input("Carrera: ")
        return self._servicio.crear_estudiante(legajo, nombre, apellido, email, carrera)

    def _pedir_tipo(self):
        print("Tipos de solicitud:")
        for numero, tipo in enumerate(TIPOS, start=1):
            print(f"{numero}. {tipo}")
        numero = self._pedir_numero("Tipo: ")
        if numero is None:
            return None
        return self._servicio.tipo_por_numero(numero)

    def _pedir_solicitud(self):
        id_solicitud = self._pedir_numero("ID de la solicitud: ")
        if id_solicitud is None:
            return None
        return self._servicio.obtener_solicitud(id_solicitud)

    def _pedir_numero(self, mensaje):
        try:
            return int(input(mensaje))
        except ValueError:
            print("Debe ingresar un numero")
            return None

    def _mostrar_solicitud(self, solicitud):
        estudiante = self._servicio.nombre_del_estudiante(solicitud.legajo)
        responsable = self._servicio.nombre_del_responsable(solicitud.id_responsable)
        print(f"#{solicitud.id} | {solicitud.fecha} | {estudiante} ({solicitud.legajo}) | {solicitud.tipo} | "
              f"{solicitud.prioridad.nombre} | {solicitud.estado.nombre} | {responsable}")
        print("    " + solicitud.descripcion)
