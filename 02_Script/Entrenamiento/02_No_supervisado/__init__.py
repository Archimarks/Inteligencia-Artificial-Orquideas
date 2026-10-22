#
# Archivo: __init__.py (Entrenamiento/02_No_supervisado)
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Conecta las 5 tareas del paradigma No supervisado con Core.no_supervisado
# (flujo comun: cargar dataset, entrenar, evaluar, guardar) y
# Core.modelos_no_supervisados (catalogo de estimadores de Clustering,
# Reduccion de dimensionalidad y Deteccion de anomalias -- Reglas de
# asociacion y Cadenas de Markov no son un estimador de scikit-learn, cada una
# tiene un unico "modelo": apriori y markov_orden_1 respectivamente).
#
# `tarea` llega desde Core.rutas con tilde ("Clustering", "Reducción de
# dimensionalidad", ...): son las claves de TAXONOMIA[paradigma]["tareas"], se
# usan tal cual en las llamadas a rutas.*. rutas.tarea_interna() la traduce a
# la clave sin tilde que usan Core.modelos_no_supervisados y las carpetas en
# disco (unica fuente de verdad: TAXONOMIA["No supervisado"]["tareas"][x]["datos"]).
#
from __future__ import annotations

from Core import submodulo

cadena_markov = submodulo("05_markov.cadena_markov")
catalogo = submodulo("01_catalogos.modelos_no_supervisados")
no_supervisado = submodulo("04_entrenamiento.no_supervisado")
rutas = submodulo("00_fundamentos.rutas")

_PARADIGMA = "No supervisado"

_ENTRENAR = {
    "Clustering": no_supervisado.entrenar_clustering,
    "Reduccion de dimensionalidad": no_supervisado.entrenar_reduccion,
    "Deteccion de anomalias": no_supervisado.entrenar_anomalias,
    "Reglas de asociacion": no_supervisado.entrenar_reglas,
    "Cadenas de Markov": cadena_markov.entrenar,
}

# Tareas sin catalogo de estimadores (un unico algoritmo posible, ver arriba).
_MODELO_UNICO = {"Reglas de asociacion": "apriori", "Cadenas de Markov": "markov_orden_1"}


# Modelos disponibles para la tarea.
def modelos_disponibles(tarea: str) -> list[str]:
    interna = rutas.tarea_interna(_PARADIGMA, tarea)
    if interna in _MODELO_UNICO:
        return [_MODELO_UNICO[interna]]
    return catalogo.modelos(interna)


# Entrena un modelo puntual: paradigma/tarea/objetivo/modelo -> resumen.
def entrenar(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    interna = rutas.tarea_interna(_PARADIGMA, tarea)
    if interna not in _ENTRENAR:
        raise ValueError(f"Tarea desconocida para {_PARADIGMA}: {tarea!r}")
    return _ENTRENAR[interna](paradigma, tarea, objetivo, modelo)
