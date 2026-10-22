#
# Archivo: __init__.py (Entrenamiento)
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Punto de entrada del codigo de entrenamiento por paradigma.
#
# Cada paradigma vive en su propia carpeta bajo Entrenamiento/ (mismo nombre
# que TAXONOMIA[paradigma]["carpeta_codigo"] en Core.rutas, ej. "01_Supervisado")
# y expone dos funciones:
#     modelos_disponibles(tarea: str) -> list[str]
#     entrenar(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict
#
# para(paradigma) importa dinamicamente esa carpeta (el nombre empieza con un
# digito, por eso el import es via importlib y no una sentencia `import` literal)
# y devuelve el modulo, que ya cumple esa interfaz.
#
from __future__ import annotations

import importlib
from functools import lru_cache
from types import ModuleType

from Core import submodulo

rutas = submodulo("00_fundamentos.rutas")


@lru_cache(maxsize=None)
def para(paradigma: str) -> ModuleType:
    carpeta = rutas.carpeta_codigo(paradigma)
    nombre_modulo = f"Entrenamiento.{carpeta.name}"
    try:
        return importlib.import_module(nombre_modulo)
    except ModuleNotFoundError as exc:
        # Solo se traduce a "falta el paradigma" si lo que no se encontro es
        # el propio paquete del paradigma; si el paquete existe pero un import
        # interno suyo fallo (ej. una dependencia no instalada), se deja ver
        # el error real en vez de enmascararlo.
        if exc.name == nombre_modulo:
            raise rutas.RutaError(
                f"Paradigma {paradigma!r} aun no tiene codigo de entrenamiento "
                f"(falta Entrenamiento/{carpeta.name}/).") from exc
        raise
