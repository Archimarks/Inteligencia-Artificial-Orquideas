"""Carga tipada de Dataset.csv con cache en Parquet y vistas sin duplicacion.

Unidad de observacion de Dataset.csv: una senal (caracteristica espectral o metabolito) medida en una
muestra de un lote, con su intensidad (ALTURA_PICO). Cuando una muestra tiene varias medidas de actividad
biologica, la misma senal aparece una vez por cada medida (columnas ID_ACTIVIDAD_BIOLOGICA, VALOR_ACTIVIDAD,
UNIDAD_ACTIVIDAD). `vista_quimica()` elimina esa replicacion para los analisis quimicos.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from ..utils.huella import sha256_archivo
from ..utils.registro import obtener_logger
from ..utils.rutas import asegurar_dir, config_global, ruta
from .catalogos import ErrorDatos

COLUMNAS_ESPERADAS = [
    "ID_ARTICULO", "ID_BATCH", "ID_MUESTRA", "ID_REINO", "ID_FILO", "ID_CLASE_TAXONOMICA", "ID_ORDEN", "ID_FAMILIA",
    "ID_GENERO", "ID_ESPECIE", "ID_TIPO_MUESTRA", "ID_PARTE_ESTUDIADA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION",
    "ID_COLUMNA_CROMATOGRAFICA", "ID_MODO_IONIZACION", "ID_NIVEL_IDENTIFICACION", "ID_SUPERCLASE_QUIMICA",
    "ID_CLASE_QUIMICA", "ID_ADUCTO", "ID_METABOLITO", "ID_ACTIVIDAD_BIOLOGICA", "FORMULA_MOLECULAR",
    "MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS", "ALTURA_PICO", "VALOR_ACTIVIDAD",
    "UNIDAD_ACTIVIDAD",
]
_NUM = ["MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS", "ALTURA_PICO", "VALOR_ACTIVIDAD"]
_TXT = ["FORMULA_MOLECULAR", "UNIDAD_ACTIVIDAD"]
log = obtener_logger()


def _dtypes() -> dict[str, str]:
    d = {c: "int32" for c in COLUMNAS_ESPERADAS if c.startswith("ID_")}
    d.update({c: "float64" for c in _NUM})
    d.update({c: "string" for c in _TXT})
    return d


@lru_cache(maxsize=1)
def cargar_dataset() -> pd.DataFrame:
    """Lee Dataset.csv (con cache Parquet indexada por la huella SHA-256 del archivo)."""
    p = ruta("datos", "dataset")
    if not p.exists():
        raise ErrorDatos(f"No existe Dataset.csv en {p}")
    huella = sha256_archivo(p)
    cache = asegurar_dir(ruta("salidas", "cache")) / f"dataset_{huella[:16]}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    log.info("Leyendo Dataset.csv (primera vez; se guardara cache Parquet)...")
    cab = pd.read_csv(p, sep=config_global()["datos"]["separador"], nrows=0).columns.tolist()
    faltan = [c for c in COLUMNAS_ESPERADAS if c not in cab]
    if faltan:
        raise ErrorDatos(f"Dataset.csv no contiene las columnas esperadas: {faltan}")
    df = pd.read_csv(p, sep=";", dtype=_dtypes(), keep_default_na=False, na_values={c: [""] for c in _NUM})
    for c in _TXT:
        df[c] = df[c].fillna("").astype("string")
    df.to_parquet(cache, index=False)
    return df


@lru_cache(maxsize=1)
def vista_quimica() -> pd.DataFrame:
    """Dataset sin la replicacion por medidas de actividad (una fila por senal x muestra).

    En Dataset.csv, una muestra con k medidas experimentales repite cada senal k veces de forma consecutiva.
    k se toma del registro de actividades (filas con ID_MUESTRA > 0); se conserva la primera de cada bloque.
    La comparacion por (actividad, valor) no sirve porque dos ensayos distintos pueden tener el mismo valor.
    """
    from .catalogos import cargar_catalogo
    df = cargar_dataset()
    drop = ["ID_ACTIVIDAD_BIOLOGICA", "VALOR_ACTIVIDAD", "UNIDAD_ACTIVIDAD"]
    reg = cargar_catalogo("registro_actividades")
    k = reg[reg["ID_MUESTRA"] > 0].groupby("ID_MUESTRA").size()
    con_act = (df["ID_ACTIVIDAD_BIOLOGICA"] != 0) & df["ID_MUESTRA"].isin(k.index)
    if not con_act.any():
        return df.drop(columns=drop)
    sub = df.loc[con_act, ["ID_MUESTRA"]]
    pos = sub.groupby("ID_MUESTRA").cumcount()
    kk = sub["ID_MUESTRA"].map(k)
    conservar = pd.Series(True, index=df.index)
    conservar.loc[sub.index] = (pos % kk) == 0
    return df.loc[conservar].drop(columns=drop).reset_index(drop=True)


def identificados(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Filas con metabolito identificado (ID_METABOLITO > 1 y nivel MSI aceptado)."""
    df = vista_quimica() if df is None else df
    niveles = config_global()["datos"]["niveles_identificados"]
    return df[(df["ID_METABOLITO"] > 1) & df["ID_NIVEL_IDENTIFICACION"].isin(niveles)]


def muestras_biologicas(df: pd.DataFrame) -> pd.DataFrame:
    """Excluye QC y blancos (tipos configurados en config_global)."""
    excl = config_global()["datos"]["tipos_muestra_excluidos"]
    return df[~df["ID_TIPO_MUESTRA"].isin(excl)]
