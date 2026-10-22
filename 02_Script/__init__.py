#
# Paquete: 02_Script
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Codigo del pipeline. Se agrega a sys.path desde main.py, de modo que los
# subpaquetes se importan directo: from Core import rutas, import Entrenamiento
# (y Entrenamiento.para(paradigma) para el modulo de cada paradigma).
#
# Subpaquetes:
#     Core            Codigo general (rutas, carga de datos, logging, artefactos).
#     Interfaz        Interaccion con el usuario (por ahora, consola).
#     Entrenamiento   Codigo de entrenamiento por paradigma/tarea.
#
