"""Sistema de Gestion de Solicitudes Academicas.

Punto de entrada: arma las piezas (repositorio, servicio y consola) y arranca el menu.
"""

from gestion.consola import MenuConsola
from gestion.repositorio import ErrorDeDatos, RepositorioJSON
from gestion.servicio import ServicioSolicitudes

ARCHIVO = "datos.json"


def main():
    repositorio = RepositorioJSON(ARCHIVO)
    try:
        repositorio.cargar()
    except ErrorDeDatos:
        print("error")
    MenuConsola(ServicioSolicitudes(repositorio)).iniciar()


if __name__ == "__main__":
    main()
