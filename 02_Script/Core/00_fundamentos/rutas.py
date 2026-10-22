#
# Archivo: rutas.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Raices del proyecto y tabla canonica paradigma -> tarea -> objetivo.
#
# De aca sale:
#     - que paradigmas/tareas/objetivos existen (Supervisado arma sus datos
#       en memoria desde las tablas fuente; No supervisado usa los CSV 04_
#       en las tareas compatibles), y
#     - la carpeta donde se guardan los artefactos
#       (03_Resultados/Models/<paradigma>/<tarea>/<objetivo>/<modelo>/).
#
from __future__ import annotations

from pathlib import Path

# Core/00_fundamentos/ -> Core/ -> 02_Script/ -> raiz del proyecto.
RAIZ: Path = Path(__file__).resolve().parents[3]
SCRIPT: Path = RAIZ / "02_Script"
DATOS: Path = RAIZ / "01_Datos"
RESULTADOS: Path = RAIZ / "03_Resultados"
MODELS: Path = RESULTADOS / "Models"


# Tabla canonica. `objetivos` vacio () = tarea sin implementar; ("",) = un unico
# dataset directamente en la carpeta de la tarea (sin nivel de objetivo).
def _tarea(datos: str, objetivos: tuple[str, ...] = ()) -> dict:
    return {"datos": datos, "resultados": datos, "objetivos": objetivos}


TAXONOMIA: dict[str, dict] = {
    "Supervisado": {
        "carpeta_codigo": "01_Supervisado",
        "datos": "01_Supervisado",
        "resultados": "01_Supervisado",
        "tareas": {
            # Orden METABOLITO primero, ACTIVIDAD_BIOLOGICA despues: es el orden
            # en el que se entrena (ver plan_entrenamiento), a pedido del usuario.
            "Clasificación": _tarea("Clasificacion", ("METABOLITO", "ACTIVIDAD_BIOLOGICA")),
            # Regresion/METABOLITO no predice identidad (eso es Clasificacion):
            # predice ALTURA_PICO (abundancia), ver Core.construir_dataset.
            "Regresión": _tarea("Regresion", ("METABOLITO", "ACTIVIDAD_BIOLOGICA")),
        },
    },
    "No supervisado": {
        "carpeta_codigo": "02_No_supervisado",
        "datos": "02_No supervisado",
        "resultados": "02_No supervisado",
        "tareas": {
            "Clustering": _tarea(
                "Clustering",
                ("PATRONES_QUIMICOS", "CALIDAD_BATCH", "CALIDAD_MUESTRA",
                 "METABOLITOS_SIN_CLASE"),
            ),
            "Reducción de dimensionalidad": _tarea(
                "Reduccion de dimensionalidad",
                ("PATRONES_QUIMICOS", "CALIDAD_BATCH", "CALIDAD_MUESTRA",
                 "METABOLITOS_SIN_CLASE"),
            ),
            "Detección de anomalías": _tarea(
                "Deteccion de anomalias",
                ("PATRONES_QUIMICOS", "CALIDAD_BATCH", "CALIDAD_MUESTRA",
                 "METABOLITOS_SIN_CLASE"),
            ),
            "Reglas de asociación": _tarea("Reglas de asociacion", ("PATRONES_QUIMICOS",)),
            # Secuencia = metabolitos de una muestra en orden de elucion
            # cromatografica (RT), representados por su clase quimica -- ver
            # Core.construir_dataset_no_supervisado.construir_secuencias().
            "Cadenas de Markov": _tarea("Cadenas de Markov", ("PATRONES_QUIMICOS",)),
        },
    },
    "Semi-supervisado": {
        "carpeta_codigo": "03_Semi_supervisado",
        "datos": "03_Semi-supervisado",
        "resultados": "03_Semi-supervisado",
        "tareas": {
            "Clasificación": _tarea("Clasificacion"),
            "Regresión": _tarea("Regresion"),
            "Deep semi-supervisado": _tarea("Deep semi-supervisado"),
        },
    },
    "Auto-supervisado": {
        "carpeta_codigo": "04_Auto_supervisado",
        "datos": "04_Auto-supervisado",
        "resultados": "04_Auto-supervisado",
        "tareas": {
            "Representación contrastiva": _tarea("Representacion contrastiva"),
            "Representación no contrastiva": _tarea("Representacion no contrastiva"),
            "Predicción enmascarada": _tarea("Prediccion enmascarada"),
            "Tareas pretexto": _tarea("Tareas pretexto"),
            "Autoencoders": _tarea("Autoencoders"),
        },
    },
    "Por refuerzo": {
        "carpeta_codigo": "05_Por_refuerzo",
        "datos": "05_Por refuerzo",
        "resultados": "05_Por refuerzo",
        "tareas": {
            "Basado en valor": _tarea("Basado en valor"),
            "Basado en política": _tarea("Basado en politica"),
            "Actor-Crítico": _tarea("Actor-Critico"),
            "Basado en modelo": _tarea("Basado en modelo"),
        },
    },
}

# Paradigma, tarea u objetivo que no existe en TAXONOMIA.
class RutaError(ValueError):
    pass


# --- navegacion de la taxonomia -------------------------------------
def _nodo(paradigma: str, tarea: str) -> tuple[dict, dict]:
    if paradigma not in TAXONOMIA:
        raise RutaError(f"Paradigma desconocido: {paradigma!r}. Opciones: {listar_paradigmas()}")
    par = TAXONOMIA[paradigma]
    if tarea not in par["tareas"]:
        raise RutaError(f"Tarea desconocida para {paradigma}: {tarea!r}. Opciones: {listar_tareas(paradigma)}")
    return par, par["tareas"][tarea]


# Nombres humanos de los paradigmas soportados -- solo los que tienen codigo
# de verdad bajo 02_Script/Entrenamiento/ (con __init__.py), no toda la
# TAXONOMIA: listar algo que despues rutas.carpeta_codigo() no puede resolver
# no sirve de nada.
def listar_paradigmas() -> list[str]:
    return [p for p in TAXONOMIA if (carpeta_codigo(p) / "__init__.py").is_file()]


# Nombres humanos de las tareas de un paradigma.
def listar_tareas(paradigma: str) -> list[str]:
    if paradigma not in TAXONOMIA:
        raise RutaError(f"Paradigma desconocido: {paradigma!r}. Opciones: {listar_paradigmas()}")
    return list(TAXONOMIA[paradigma]["tareas"])


# Nombre interno sin tilde de una tarea (igual a su carpeta en disco) a partir
# del nombre con tilde de TAXONOMIA -- unica fuente de verdad para traducir
# entre "Reducción de dimensionalidad" (como la ve rutas.*) y "Reduccion de
# dimensionalidad" (como la usan los catalogos de modelos y las carpetas).
def tarea_interna(paradigma: str, tarea: str) -> str:
    _, t = _nodo(paradigma, tarea)
    return t["datos"]


# Carpeta de codigo del paradigma bajo 02_Script/Entrenamiento/ (ej. '01_Supervisado').
def carpeta_codigo(paradigma: str) -> Path:
    if paradigma not in TAXONOMIA:
        raise RutaError(f"Paradigma desconocido: {paradigma!r}. Opciones: {listar_paradigmas()}")
    return SCRIPT / "Entrenamiento" / TAXONOMIA[paradigma]["carpeta_codigo"]


# --- objetivos / plan -------------------------------------------------
# Objetivos declarados de paradigma/tarea (los que Core.dataset_en_memoria
# sabe construir). Para tareas sin nivel de objetivo devuelve [""].
def listar_objetivos(paradigma: str, tarea: str) -> list[str]:
    _, t = _nodo(paradigma, tarea)
    return list(t["objetivos"])


# Paradigmas con al menos un objetivo declarado.
def paradigmas_con_datos() -> list[str]:
    return [p for p in listar_paradigmas()
            if any(listar_objetivos(p, t) for t in listar_tareas(p))]


# Pares (tarea, objetivo) de un paradigma con dataset.csv en disco, agrupados
# por OBJETIVO (todas las tareas de un objetivo antes de pasar al siguiente) en
# vez de por tarea -- a pedido del usuario, para que termine primero todo lo de
# un objetivo (p.ej. METABOLITO: Clasificacion y Regresion) antes de arrancar
# con el siguiente. El orden de los objetivos es el de aparicion en TAXONOMIA.
def plan_entrenamiento(paradigma: str) -> list[tuple[str, str]]:
    tareas = listar_tareas(paradigma)
    disponibles = {t: listar_objetivos(paradigma, t) for t in tareas}
    if paradigma == "No supervisado":
        carpeta_dataset = DATOS / "Dataset"
        archivos = {
            "PATRONES_QUIMICOS": (
                "04_Dataset_Patrones_Quimicos_Unificado.csv",
                "04_Dataset_Patrones_Quimicos.csv",
            ),
            "CALIDAD_BATCH": ("04_Informe_Calidad_Por_Batch.csv",),
            "CALIDAD_MUESTRA": ("04_Informe_Calidad_Por_Muestra.csv",),
            "METABOLITOS_SIN_CLASE": ("04_Metabolitos_Sin_Clase_Quimica.csv",),
        }
        disponibles = {
            tarea: [
                objetivo for objetivo in objetivos
                if any((carpeta_dataset / nombre).is_file()
                       for nombre in archivos.get(objetivo, ()))
            ]
            for tarea, objetivos in disponibles.items()
        }
    orden_objetivos: list[str] = []
    for objetivos in disponibles.values():
        for o in objetivos:
            if o not in orden_objetivos:
                orden_objetivos.append(o)
    return [(t, o) for o in orden_objetivos for t in tareas if o in disponibles[t]]


# Carpeta 03_Resultados/Models/<paradigma>/<tarea>/<objetivo>/ (creada si falta).
# Ahi vive el _leaderboard.csv compartido por todos los modelos.
def carpeta_objetivo_resultados(paradigma: str, tarea: str, objetivo: str) -> Path:
    par, t = _nodo(paradigma, tarea)
    carpeta = MODELS / par["resultados"] / t["resultados"] / objetivo
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


# Carpeta de artefactos del modelo: .../<objetivo>/<modelo>/  (una por modelo, se
# sobreescribe al reentrenar). NO crea el directorio: eso lo hace quien entrena.
def carpeta_resultados(paradigma: str, tarea: str, objetivo: str, modelo: str) -> Path:
    return carpeta_objetivo_resultados(paradigma, tarea, objetivo) / modelo
