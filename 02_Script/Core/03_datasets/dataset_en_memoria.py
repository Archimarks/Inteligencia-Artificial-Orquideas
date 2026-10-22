#
# Archivo: dataset_en_memoria.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Punto unico de entrada para pedir el Dataset de un paradigma/tarea/objetivo.
# Los datasets supervisados se arman en memoria desde las tablas fuente; el
# flujo no supervisado prepara cada CSV 04_ para las tareas compatibles.
# El dataset de patrones se genera si falta o quedo desactualizado.
#
# cargar() cachea por proceso (paradigma, tarea, objetivo): si el mismo
# combo se pide dos veces en la misma corrida (p.ej. la vista previa del plan
# y despues el entrenamiento en el proceso padre), no se rehace el trabajo.
# Cada worker de Core.ejecutor es un proceso aparte (loky), por lo que se
# reconstruye una vez por modelo.
#
from __future__ import annotations

from .. import submodulo

datos = submodulo("01_catalogos.datos")
rutas = submodulo("00_fundamentos.rutas")

_CACHE: dict[tuple[str, str, str], datos.Dataset] = {}


def _construir(paradigma: str, tarea: str, objetivo: str) -> datos.Dataset:
    interna = rutas.tarea_interna(paradigma, tarea)

    if paradigma == "Supervisado":
        from .. import submodulo
        cd = submodulo("02_etl.construir_dataset")
        constructor = {
            ("Clasificacion", "METABOLITO"): cd.construir_metabolito,
            ("Clasificacion", "ACTIVIDAD_BIOLOGICA"): cd.construir_actividad_clasificacion,
            ("Regresion", "METABOLITO"): cd.construir_metabolito_regresion,
            ("Regresion", "ACTIVIDAD_BIOLOGICA"): cd.construir_actividad_regresion,
        }.get((interna, objetivo))

    elif paradigma == "No supervisado":
        from . import construir_dataset_no_supervisado as cdns
        if objetivo == "PATRONES_QUIMICOS":
            constructor = {
                "Clustering": cdns.construir_perfil_continuo,
                "Reduccion de dimensionalidad": cdns.construir_perfil_continuo,
                "Deteccion de anomalias": cdns.construir_perfil_continuo,
                "Reglas de asociacion": cdns.construir_perfil_binario,
                "Cadenas de Markov": cdns.construir_secuencias,
            }.get(interna)
        elif interna in {
                "Clustering", "Reduccion de dimensionalidad",
                "Deteccion de anomalias"}:
            constructor = lambda: cdns.construir_dataset_04(objetivo)
        else:
            constructor = None

    else:
        constructor = None

    if constructor is None:
        raise rutas.RutaError(f"No hay ETL en memoria para {paradigma}/{tarea}/{objetivo!r}.")
    return constructor()


# Dataset de paradigma/tarea/objetivo, armado en memoria (cacheado por
# proceso). `requiere_objetivo` solo aplica al chequeo que ya hace cada
# constructor -- se ignora aca, queda por simetria con Core.datos.desde_texto.
def cargar(paradigma: str, tarea: str, objetivo: str, requiere_objetivo: bool = True) -> datos.Dataset:
    clave = (paradigma, tarea, objetivo)
    if clave not in _CACHE:
        _CACHE[clave] = _construir(paradigma, tarea, objetivo)
    return _CACHE[clave]
