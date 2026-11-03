# Pruebas unitarias de las reglas de negocio, sin consola ni archivo.
# Usan RepositorioEnMemoria en lugar del JSON.
#
# Para correrlas: python -m unittest discover tests -v

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from gestion.modelo import ErrorDeNegocio, Estado, FiltroSolicitud, Prioridad, Responsable, calcular_prioridad
from gestion.repositorio import RepositorioEnMemoria
from gestion.servicio import ServicioSolicitudes

RESPONSABLES = [Responsable(1, "Laura Gomez", "Alumnado"), Responsable(2, "Martin Ruiz", "Secretaria Academica")]


class BaseServicio(unittest.TestCase):

    def setUp(self):
        self.repositorio = RepositorioEnMemoria(responsables=RESPONSABLES)
        self.servicio = ServicioSolicitudes(self.repositorio, obtener_fecha=lambda: "01/11/2026")
        self.ana = self.servicio.crear_estudiante("1001", "Ana", "Lopez", "ana@mail.com", "TUP")

    def nueva_solicitud(self, tipo="Certificado", descripcion="Certificado de alumno regular"):
        return self.servicio.registrar_solicitud(self.ana, tipo, descripcion)


class TestPrioridad(unittest.TestCase):

    def test_prioridad_segun_tipo(self):
        esperadas = {
            "Certificado": Prioridad.BAJA,
            "Equivalencia": Prioridad.MEDIA,
            "Reclamo de nota": Prioridad.ALTA,
            "Cambio de comision": Prioridad.MEDIA,
            "Otro": Prioridad.BAJA,
        }
        for tipo, prioridad in esperadas.items():
            with self.subTest(tipo=tipo):
                self.assertEqual(calcular_prioridad(tipo, "texto cualquiera"), prioridad)

    def test_urgente_pasa_a_alta_sin_importar_mayusculas(self):
        self.assertEqual(calcular_prioridad("Certificado", "Lo necesito URGENTE"), Prioridad.ALTA)


class TestRegistro(BaseServicio):

    def test_registra_con_estado_pendiente_y_sin_responsable(self):
        solicitud = self.nueva_solicitud()
        self.assertEqual(solicitud.id, 1)
        self.assertEqual(solicitud.estado, Estado.PENDIENTE)
        self.assertIsNone(solicitud.id_responsable)
        self.assertEqual(solicitud.fecha, "01/11/2026")

    def test_id_no_se_repite_despues_de_eliminar(self):
        primera = self.nueva_solicitud()
        segunda = self.nueva_solicitud()
        tercera = self.nueva_solicitud()
        self.servicio.eliminar_solicitud(segunda)
        nueva = self.nueva_solicitud()
        self.assertEqual(nueva.id, 4)
        ids = [s.id for s in self.repositorio.listar_solicitudes()]
        self.assertEqual(ids, [primera.id, tercera.id, nueva.id])

    def test_descripcion_corta(self):
        with self.assertRaisesRegex(ErrorDeNegocio, "al menos 10"):
            self.nueva_solicitud(descripcion="corta")
        self.assertEqual(self.repositorio.listar_solicitudes(), [])

    def test_estudiante_nuevo_se_guarda_con_su_primera_solicitud(self):
        self.assertIsNone(self.repositorio.buscar_estudiante("1001"))
        self.nueva_solicitud()
        self.assertEqual(self.repositorio.buscar_estudiante("1001"), self.ana)

    def test_estudiante_nuevo_no_se_guarda_si_la_solicitud_falla(self):
        juan = self.servicio.crear_estudiante("2002", "Juan", "Perez", "juan@mail.com", "TUP")
        with self.assertRaises(ErrorDeNegocio):
            self.servicio.registrar_solicitud(juan, "Certificado", "corta")
        self.assertIsNone(self.repositorio.buscar_estudiante("2002"))

    def test_estudiante_con_datos_vacios(self):
        with self.assertRaisesRegex(ErrorDeNegocio, "Datos invalidos"):
            self.servicio.crear_estudiante("2002", "", "Perez", "juan@mail.com", "TUP")

    def test_email_sin_arroba(self):
        with self.assertRaisesRegex(ErrorDeNegocio, "Email invalido"):
            self.servicio.crear_estudiante("2002", "Juan", "Perez", "juanmail.com", "TUP")

    def test_tipo_fuera_de_rango(self):
        for numero in (0, 6, -1):
            with self.subTest(numero=numero):
                with self.assertRaisesRegex(ErrorDeNegocio, "Tipo invalido"):
                    self.servicio.tipo_por_numero(numero)


class TestTransiciones(BaseServicio):

    PERMITIDAS = {
        Estado.PENDIENTE: {Estado.EN_PROCESO, Estado.RECHAZADA},
        Estado.EN_PROCESO: {Estado.RESUELTA, Estado.RECHAZADA},
        Estado.RESUELTA: {Estado.CERRADA},
        Estado.CERRADA: set(),
        Estado.RECHAZADA: set(),
    }

    def test_todas_las_combinaciones(self):
        # recorre los 25 pares (actual, nuevo) y compara con la tabla del README
        for actual in Estado:
            for nuevo in Estado:
                with self.subTest(actual=actual, nuevo=nuevo):
                    solicitud = self.nueva_solicitud()
                    solicitud.estado = actual
                    solicitud.id_responsable = 1
                    if nuevo in self.PERMITIDAS[actual]:
                        self.servicio.cambiar_estado(solicitud, nuevo.value)
                        self.assertEqual(solicitud.estado, nuevo)
                    else:
                        with self.assertRaisesRegex(ErrorDeNegocio, "Transicion no permitida"):
                            self.servicio.cambiar_estado(solicitud, nuevo.value)
                        self.assertEqual(solicitud.estado, actual)

    def test_en_proceso_requiere_responsable(self):
        solicitud = self.nueva_solicitud()
        with self.assertRaisesRegex(ErrorDeNegocio, "sin responsable"):
            self.servicio.cambiar_estado(solicitud, "E")
        self.assertEqual(solicitud.estado, Estado.PENDIENTE)

    def test_codigo_inexistente(self):
        solicitud = self.nueva_solicitud()
        with self.assertRaisesRegex(ErrorDeNegocio, "de Pendiente a \\?"):
            self.servicio.cambiar_estado(solicitud, "Z")


class TestAsignacion(BaseServicio):

    def test_asigna_responsable(self):
        solicitud = self.nueva_solicitud()
        responsable = self.servicio.asignar_responsable(solicitud, 2)
        self.assertEqual(responsable.nombre, "Martin Ruiz")
        self.assertEqual(solicitud.id_responsable, 2)

    def test_responsable_inexistente(self):
        solicitud = self.nueva_solicitud()
        with self.assertRaisesRegex(ErrorDeNegocio, "Responsable inexistente"):
            self.servicio.asignar_responsable(solicitud, 99)
        self.assertIsNone(solicitud.id_responsable)

    def test_no_se_asigna_a_finalizadas(self):
        for estado in (Estado.CERRADA, Estado.RECHAZADA):
            with self.subTest(estado=estado):
                solicitud = self.nueva_solicitud()
                solicitud.estado = estado
                with self.assertRaisesRegex(ErrorDeNegocio, "finalizada"):
                    self.servicio.asignar_responsable(solicitud, 1)


class TestBusquedaYReporte(BaseServicio):

    def setUp(self):
        super().setUp()
        self.reclamo = self.nueva_solicitud("Reclamo de nota", "Reclamo por nota del parcial")
        self.certificado = self.nueva_solicitud("Certificado", "Certificado de alumno regular")
        self.servicio.asignar_responsable(self.certificado, 1)
        self.servicio.cambiar_estado(self.certificado, "E")
        self.servicio.cambiar_estado(self.certificado, "R")

    def test_filtro_vacio_devuelve_todas(self):
        self.assertEqual(len(self.servicio.filtrar(FiltroSolicitud())), 2)

    def test_filtros_combinados(self):
        self.assertEqual(self.servicio.filtrar(FiltroSolicitud(estado="R")), [self.certificado])
        self.assertEqual(self.servicio.filtrar(FiltroSolicitud(tipo="RECLAMO")), [self.reclamo])
        self.assertEqual(self.servicio.filtrar(FiltroSolicitud(prioridad="3")), [self.reclamo])
        self.assertEqual(self.servicio.filtrar(FiltroSolicitud(responsable="1")), [self.certificado])
        self.assertEqual(self.servicio.filtrar(FiltroSolicitud(estado="P", prioridad="1")), [])

    def test_filtro_con_texto_donde_va_un_numero(self):
        with self.assertRaisesRegex(ErrorDeNegocio, "Prioridad invalida"):
            self.servicio.filtrar(FiltroSolicitud(prioridad="alta"))
        with self.assertRaisesRegex(ErrorDeNegocio, "ID de responsable invalido"):
            self.servicio.filtrar(FiltroSolicitud(responsable="Laura"))

    def test_reporte(self):
        reporte = self.servicio.generar_reporte()
        self.assertEqual(reporte.total, 2)
        self.assertEqual(reporte.cantidad_por_estado[Estado.PENDIENTE], 1)
        self.assertEqual(reporte.cantidad_por_estado[Estado.RESUELTA], 1)
        self.assertEqual(reporte.urgentes_sin_atender, [self.reclamo])
        self.assertEqual(reporte.porcentaje_finalizadas, 50.0)

    def test_reporte_sin_solicitudes(self):
        servicio = ServicioSolicitudes(RepositorioEnMemoria())
        reporte = servicio.generar_reporte()
        self.assertEqual(reporte.total, 0)
        self.assertEqual(reporte.porcentaje_finalizadas, 0.0)


if __name__ == "__main__":
    unittest.main()
