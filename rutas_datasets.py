#
# Archivo: rutas_datasets.py
#
# Modulo standalone de referencia: rutas de los dos datasets fuente y las
# variables objetivo (Y) que se arman a partir de ellos. No depende de
# 02_Script/ ni se importa desde ahi -- es solo una referencia rapida.
#
from __future__ import annotations

from pathlib import Path

DIR_BASE = Path(__file__).resolve().parent / "01_Datos" / "Dataset"

# --- Datasets fuente ---------------------------------------------------
RUTA_ACTIVIDAD_BIOLOGICA = DIR_BASE / "01_Dataset_Actividad_biologica.csv"
RUTA_METABOLITO_IDENTIFICADOS = DIR_BASE / "03_Dataset_Metabolito_Identificados.csv"
RUTA_PATRONES_QUIMICOS = DIR_BASE / "04_Dataset_Patrones_Quimicos.csv"
RUTA_INFORME_CALIDAD_BATCH = DIR_BASE / "04_Informe_Calidad_Por_Batch.csv"
RUTA_INFORME_CALIDAD_MUESTRA = DIR_BASE / "04_Informe_Calidad_Por_Muestra.csv"
RUTA_METABOLITOS_SIN_CLASE = DIR_BASE / "04_Metabolitos_Sin_Clase_Quimica.csv"

# --- Variables objetivo (Y) ---------------------------------------------
# Cada entrada: paradigma/tarea -> (dataset fuente, columna(s) de origen, descripcion).
VARIABLES_OBJETIVO = {
    "Clasificacion/METABOLITO": {
        "dataset": RUTA_METABOLITO_IDENTIFICADOS,
        "columna_origen": "ID_METABOLITO",
        "descripcion": (
            "Nombre del metabolito (texto, via catalogo de metabolitos). "
            "Excluye filas con ID_METABOLITO=1 (no identificado)."
        ),
    },
    "Clasificacion/ACTIVIDAD_BIOLOGICA": {
        "dataset": RUTA_ACTIVIDAD_BIOLOGICA,
        "columna_origen": "ID_ACTIVIDAD",
        "descripcion": "Nombre de la actividad biologica (texto, via catalogo de actividades).",
    },
    "Regresion/METABOLITO": {
        "dataset": RUTA_METABOLITO_IDENTIFICADOS,
        "columna_origen": "ALTURA_PICO",
        "descripcion": (
            "log1p(ALTURA_PICO): abundancia del pico cromatografico en escala "
            "logaritmica (la distribucion original es practicamente log-normal)."
        ),
    },
    "Regresion/ACTIVIDAD_BIOLOGICA": {
        "dataset": RUTA_ACTIVIDAD_BIOLOGICA,
        "columna_origen": "VALOR_ACTIVIDAD",
        "descripcion": (
            "Valor numerico de la actividad biologica. Solo filas con "
            "VALOR_ACTIVIDAD no vacio (~139 mil de 2.47 millones)."
        ),
    },
    "Clasificacion/PATRON_QUIMICO": {
        "dataset": RUTA_PATRONES_QUIMICOS,
        "columna_origen": "CLASE_QUIMICA",
        "descripcion": (
            "Clase quimica asignada al metabolito. Usar solo filas con "
            "ESTADO_CLASIFICACION_QUIMICA='Clasificado'."
        ),
    },
    "Clasificacion/ESTADO_COBERTURA_BATCH": {
        "dataset": RUTA_INFORME_CALIDAD_BATCH,
        "columna_origen": "ESTADO_COBERTURA",
        "descripcion": "Estado de cobertura de clasificacion quimica para el batch.",
    },
    "Regresion/COBERTURA_CLASIFICACION_BATCH": {
        "dataset": RUTA_INFORME_CALIDAD_BATCH,
        "columna_origen": "COBERTURA_CLASIFICACION_PCT",
        "descripcion": "Porcentaje de cobertura de clasificacion quimica para el batch.",
    },
    "Clasificacion/ESTADO_COBERTURA_MUESTRA": {
        "dataset": RUTA_INFORME_CALIDAD_MUESTRA,
        "columna_origen": "ESTADO_COBERTURA",
        "descripcion": "Estado de cobertura de clasificacion quimica para la muestra.",
    },
    "Regresion/COBERTURA_CLASIFICACION_MUESTRA": {
        "dataset": RUTA_INFORME_CALIDAD_MUESTRA,
        "columna_origen": "COBERTURA_CLASIFICACION_PCT",
        "descripcion": "Porcentaje de cobertura de clasificacion quimica para la muestra.",
    },
    "Clasificacion/ESTADO_SUGERENCIA_METABOLITO": {
        "dataset": RUTA_METABOLITOS_SIN_CLASE,
        "columna_origen": "ESTADO_SUGERENCIA",
        "descripcion": (
            "Estado de la sugerencia de clase. No representa una clase quimica "
            "confirmada; para eso se requiere validacion independiente."
        ),
    },
}
