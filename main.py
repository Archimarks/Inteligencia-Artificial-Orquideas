#!/usr/bin/env python3
#
# Archivo: main.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Punto de entrada unico del proyecto.
#
# Abre la interfaz de consola (02_Script/Interfaz/), un menu desde el que se
# elige que entrenar y se lanza. La opcion principal es iniciar un entrenamiento:
# paradigma -> tarea -> objetivo -> modelo.
#
# Estructura del codigo (bajo 02_Script/):
#     Core/           codigo general: rutas de los datasets, carga de datos,
#                     logging y guardado de artefactos.
#     Interfaz/       interaccion con el usuario (por ahora, consola).
#     Entrenamiento/  codigo de entrenamiento por paradigma/tarea.
#
# Flujo de datos:
#     entrada supervisada   <- tablas fuente de 01_Datos/Dataset/
#     entrada no supervisada <- 01_Datos/Dataset/04_Dataset_Patrones_Quimicos.csv
#     salida                 -> 03_Resultados/Models/<paradigma>/<tarea>/<objetivo>/<modelo>/<marca_tiempo>/
#
# Uso:
#     python main.py
#
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "02_Script"
if str(_SCRIPT) not in sys.path:
    sys.path.insert(0, str(_SCRIPT))


# Verifica las dependencias antes de importar los módulos de la aplicación.
def _verificar_dependencias() -> None:
    from Core import submodulo

    submodulo("00_fundamentos.dependencias").verificar_e_instalar()


# Lanza la interfaz y devuelve su codigo de salida al proceso.
# El import va aca dentro: 02_Script recien esta en sys.path despues del bloque de arriba.
def main() -> int:
    _verificar_dependencias()
    from Interfaz import ejecutar

    return ejecutar()


if __name__ == "__main__":
    raise SystemExit(main())
