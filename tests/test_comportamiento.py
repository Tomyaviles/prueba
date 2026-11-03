# Pruebas de caja negra: le pasamos al programa las entradas de tests/casos/
# y comparamos lo que imprime con tests/esperado/.
# Si el archivo esperado no existe, se graba con la salida actual.
#
# Para correrlas: python -m unittest discover tests -v

import os
import re
import subprocess
import sys
import tempfile
import unittest

CARPETA = os.path.dirname(os.path.abspath(__file__))
PROGRAMA = os.path.join(CARPETA, "..", "solicitudes.py")


def correr(caso, carpeta_datos):
    with open(os.path.join(CARPETA, "casos", caso + ".txt"), encoding="utf-8") as f:
        entrada = f.read()
    resultado = subprocess.run([sys.executable, PROGRAMA], input=entrada, capture_output=True,
                               text=True, encoding="utf-8", cwd=carpeta_datos)
    # la fecha cambia segun el dia, la reemplazo para poder comparar
    return re.sub(r"\d{2}/\d{2}/\d{4}", "<fecha>", resultado.stdout)


class TestComportamiento(unittest.TestCase):
    maxDiff = None

    def comparar(self, nombre, salida):
        ruta = os.path.join(CARPETA, "esperado", nombre + ".txt")
        if not os.path.exists(ruta):
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(salida)
        with open(ruta, encoding="utf-8") as f:
            self.assertEqual(f.read(), salida)

    def probar_caso(self, caso):
        with tempfile.TemporaryDirectory() as carpeta_datos:
            self.comparar(caso, correr(caso, carpeta_datos))

    def test_registro_y_prioridad(self):
        self.probar_caso("registro_y_prioridad")

    def test_validaciones(self):
        self.probar_caso("validaciones")

    def test_transiciones_estado(self):
        self.probar_caso("transiciones_estado")

    def test_asignar_responsable(self):
        self.probar_caso("asignar_responsable")

    def test_buscar(self):
        self.probar_caso("buscar")

    def test_reporte(self):
        self.probar_caso("reporte")

    def test_eliminar(self):
        self.probar_caso("eliminar")

    def test_archivo_danado_no_se_pisa(self):
        with tempfile.TemporaryDirectory() as carpeta_datos:
            ruta = os.path.join(carpeta_datos, "datos.json")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("{esto no es json")
            salida = correr("registro_y_prioridad", carpeta_datos)
            self.assertIn("No se pudo leer datos.json", salida)
            with open(ruta, encoding="utf-8") as f:
                self.assertEqual(f.read(), "{esto no es json")

    def test_persistencia(self):
        # dos ejecuciones sobre el mismo datos.json: la segunda tiene que ver lo de la primera
        with tempfile.TemporaryDirectory() as carpeta_datos:
            salida = correr("persistencia_1", carpeta_datos) + correr("persistencia_2", carpeta_datos)
            self.comparar("persistencia", salida)


if __name__ == "__main__":
    unittest.main()
