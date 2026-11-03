# Pruebas del repositorio JSON sobre una carpeta temporal.
#
# Para correrlas: python -m unittest discover tests -v

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from gestion.modelo import Estado, Estudiante, Prioridad, Solicitud
from gestion.repositorio import ErrorDeDatos, RepositorioJSON


class TestRepositorioJSON(unittest.TestCase):

    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.carpeta.name, "datos.json")

    def tearDown(self):
        self.carpeta.cleanup()

    def test_primera_vez_crea_archivo_con_responsables(self):
        repositorio = RepositorioJSON(self.ruta)
        repositorio.cargar()
        self.assertTrue(os.path.exists(self.ruta))
        self.assertEqual(len(repositorio.listar_responsables()), 4)

    def test_lo_guardado_se_recupera(self):
        repositorio = RepositorioJSON(self.ruta)
        repositorio.cargar()
        repositorio.agregar_estudiante(Estudiante("1001", "Ana", "Lopez", "ana@mail.com", "TUP"))
        repositorio.agregar_solicitud(Solicitud(1, "1001", "Certificado", "Certificado de alumno regular",
                                                Prioridad.BAJA, "01/11/2026", Estado.EN_PROCESO, 2))

        otro = RepositorioJSON(self.ruta)
        otro.cargar()
        solicitud = otro.buscar_solicitud(1)
        self.assertEqual(solicitud.estado, Estado.EN_PROCESO)
        self.assertEqual(solicitud.id_responsable, 2)
        self.assertEqual(otro.buscar_estudiante("1001").nombre_completo, "Ana Lopez")

    def test_lee_archivo_de_la_version_inicial(self):
        # la version inicial guardaba ademas "nombre_est" dentro de cada solicitud
        datos = {
            "estudiantes": [{"legajo": "1001", "nombre": "Ana", "apellido": "Lopez",
                             "email": "ana@mail.com", "carrera": "TUP"}],
            "responsables": [{"id": 1, "nombre": "Laura Gomez", "area": "Alumnado"}],
            "solicitudes": [{"id": 1, "legajo": "1001", "nombre_est": "Ana Lopez", "tipo": "Reclamo de nota",
                             "desc": "Reclamo por nota del parcial", "prioridad": 3, "estado": "P",
                             "resp": None, "fecha": "25/10/2026"}],
        }
        with open(self.ruta, "w") as archivo:
            json.dump(datos, archivo)
        repositorio = RepositorioJSON(self.ruta)
        repositorio.cargar()
        self.assertEqual(repositorio.buscar_solicitud(1).prioridad, Prioridad.ALTA)

    def test_cambio_de_estado_queda_guardado(self):
        repositorio = RepositorioJSON(self.ruta)
        repositorio.cargar()
        solicitud = Solicitud(1, "1001", "Certificado", "Certificado de alumno regular",
                              Prioridad.BAJA, "01/11/2026")
        repositorio.agregar_solicitud(solicitud)
        solicitud.estado = Estado.RECHAZADA
        repositorio.actualizar_solicitud(solicitud)

        otro = RepositorioJSON(self.ruta)
        otro.cargar()
        self.assertEqual(otro.buscar_solicitud(1).estado, Estado.RECHAZADA)
        self.assertFalse(os.path.exists(self.ruta + ".tmp"))

    def test_archivo_danado(self):
        with open(self.ruta, "w") as archivo:
            archivo.write("{esto no es json")
        with self.assertRaises(ErrorDeDatos):
            RepositorioJSON(self.ruta).cargar()


if __name__ == "__main__":
    unittest.main()
