#
# Archivo: __init__.py (Entrenamiento/01_Supervisado)
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Conecta las tareas del paradigma Supervisado (Clasificacion / Regresion) con
# Core.modelos_supervisados (catalogo de estimadores) y
# Core.entrenamiento_base (flujo comun: cargar dataset, evaluar, guardar).
#
# `tarea` llega desde Core.rutas con tilde ("Clasificación", "Regresión": son
# las claves de TAXONOMIA[paradigma]["tareas"], se usan tal cual en las
# llamadas a rutas.*). Aqui adentro se traduce a la clave sin tilde que usa
# Core.modelos_supervisados (misma que el nombre de carpeta en disco).
#
from __future__ import annotations

from Core import submodulo

entrenamiento_base = submodulo("04_entrenamiento.entrenamiento_base")
catalogo = submodulo("01_catalogos.modelos_supervisados")

_TAREA_INTERNA = {"Clasificación": "Clasificacion", "Regresión": "Regresion"}
_ES_CLASIFICACION = {"Clasificacion": True, "Regresion": False}


def _tarea_interna(tarea: str) -> str:
    interna = _TAREA_INTERNA.get(tarea, tarea)
    if interna not in _ES_CLASIFICACION:
        raise ValueError(f"Tarea desconocida para Supervisado: {tarea!r}")
    return interna


# Modelos disponibles para la tarea (nombres del catalogo de Core.modelos_supervisados).
def modelos_disponibles(tarea: str) -> list[str]:
    return catalogo.modelos(_tarea_interna(tarea))


# Entrena un modelo puntual: paradigma/tarea/objetivo/modelo -> resumen (ver
# Core.entrenamiento_base.entrenar_supervisado).
def entrenar(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    interna = _tarea_interna(tarea)
    fabrica = catalogo.fabrica(interna, modelo)
    return entrenamiento_base.entrenar_supervisado(
        paradigma, tarea, objetivo, modelo, fabrica, _ES_CLASIFICACION[interna])
