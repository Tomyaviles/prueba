"""Sistema de Gestion de Solicitudes Academicas.

Punto de entrada: arma las piezas (repositorio, servicio y consola) y arranca el menu.
"""

import sys

from gestion.consola import MenuConsola
from gestion.repositorio import ErrorDeDatos, RepositorioJSON
from gestion.servicio import ServicioSolicitudes

ARCHIVO = "datos.json"


def main():
    repositorio = RepositorioJSON(ARCHIVO)
    try:
        repositorio.cargar()
    except ErrorDeDatos as error:
        # no se sigue: si se arrancara vacio, el primer guardado borraria los datos del archivo
        print(error)
        print("Revise el archivo o muevalo a otra carpeta para empezar de cero.")
        sys.exit(1)
    MenuConsola(ServicioSolicitudes(repositorio)).iniciar()


if __name__ == "__main__":
    main()
