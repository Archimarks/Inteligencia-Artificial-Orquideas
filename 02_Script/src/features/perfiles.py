"""Perfiles quimicos por muestra y por unidad agregada.

Las intensidades (ALTURA_PICO) no son comparables entre lotes (plataformas, detectores y normalizaciones
distintas), por lo que los perfiles se construyen con **presencia** de metabolitos identificados: la composicion
de una muestra es la fraccion de sus metabolitos que pertenece a cada superclase o clase quimica. Es un dato
composicional, por eso se transforma con log-cociente centrado (CLR) antes de modelar.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from ..data.dataset import identificados, muestras_biologicas, vista_quimica

ATRIBUTOS_MUESTRA = [
    "ID_ARTICULO", "ID_BATCH", "ID_REINO", "ID_FILO", "ID_CLASE_TAXONOMICA", "ID_ORDEN", "ID_FAMILIA", "ID_GENERO",
    "ID_ESPECIE", "ID_TIPO_MUESTRA", "ID_PARTE_ESTUDIADA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION",
    "ID_COLUMNA_CROMATOGRAFICA",
]
# plataforma analitica (columnas presentes en el Dataset.csv generado por `construir-dataset`; opcionales)
ATRIBUTOS_PLATAFORMA = ["ID_TECNICA_SEPARACION", "ID_INSTRUMENTO", "ID_ANALIZADOR"]
NIVEL_QUIMICO = {"superclase": "ID_SUPERCLASE_QUIMICA", "clase": "ID_CLASE_QUIMICA"}


@lru_cache(maxsize=1)
def tabla_muestras() -> pd.DataFrame:
    """Una fila por muestra (ID_MUESTRA > 0) con sus atributos, modos adquiridos y numero de senales."""
    df = vista_quimica()
    df = df[df["ID_MUESTRA"] > 0]
    cols = ATRIBUTOS_MUESTRA + [c for c in ATRIBUTOS_PLATAFORMA if c in df.columns]
    meta = df.groupby("ID_MUESTRA", sort=True)[cols].first()
    modos = df.groupby("ID_MUESTRA")["ID_MODO_IONIZACION"].agg(lambda s: tuple(sorted(set(s) - {0})))
    meta["MODOS"] = modos.map(lambda t: "+".join(map(str, t)) if t else "0")
    meta["N_SENALES"] = df.groupby("ID_MUESTRA").size()
    ide = identificados(df)
    meta["N_IDENTIFICADOS"] = ide.groupby("ID_MUESTRA")["ID_METABOLITO"].nunique().reindex(meta.index).fillna(0).astype(int)
    return meta


@lru_cache(maxsize=1)
def presencias() -> pd.DataFrame:
    """Pares unicos (muestra biologica, metabolito identificado) con su clasificacion quimica."""
    df = muestras_biologicas(identificados())
    df = df[df["ID_MUESTRA"] > 0]
    cols = ["ID_MUESTRA", "ID_METABOLITO", "ID_SUPERCLASE_QUIMICA", "ID_CLASE_QUIMICA"]
    return df[cols].drop_duplicates(["ID_MUESTRA", "ID_METABOLITO"]).reset_index(drop=True)


def clr(conteos: pd.DataFrame, pseudo: float = 0.5) -> pd.DataFrame:
    """Transformacion log-cociente centrada con pseudoconteo para ceros."""
    x = np.log(conteos.to_numpy(dtype=float) + pseudo)
    return pd.DataFrame(x - x.mean(axis=1, keepdims=True), index=conteos.index, columns=conteos.columns)


def categorias_frecuentes(nivel: str, min_articulos: int, max_categorias: int | None) -> list[int]:
    """Categorias quimicas presentes en al menos `min_articulos` articulos (evita variables de un solo estudio)."""
    col = NIVEL_QUIMICO[nivel]
    p = presencias().merge(tabla_muestras()[["ID_ARTICULO"]], left_on="ID_MUESTRA", right_index=True)
    p = p[p[col] > 0]
    n_art = p.groupby(col)["ID_ARTICULO"].nunique()
    n_obs = p.groupby(col).size()
    cats = n_art[n_art >= min_articulos].index
    orden = n_obs.loc[cats].sort_values(ascending=False).index.tolist()
    return orden[:max_categorias] if max_categorias else orden


def conteos_por_muestra(nivel: str = "superclase", min_articulos: int = 3, max_categorias: int | None = None) -> pd.DataFrame:
    """Matriz muestras x categoria quimica con el numero de metabolitos distintos; incluye columna 'otras'."""
    col = NIVEL_QUIMICO[nivel]
    cats = categorias_frecuentes(nivel, min_articulos, max_categorias)
    p = presencias()
    p = p[p[col] > 0]
    c = pd.crosstab(p["ID_MUESTRA"], p[col])
    otras = c.drop(columns=[k for k in cats if k in c.columns]).sum(axis=1)
    c = c.reindex(columns=cats, fill_value=0)
    c.columns = [f"{nivel}_{k}" for k in c.columns]
    c[f"{nivel}_otras"] = otras
    return c


def perfil_muestras(nivel: str = "superclase", transformacion: str = "clr", min_metabolitos: int = 20,
                    min_articulos: int = 3, max_categorias: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(X, meta) por muestra biologica con al menos `min_metabolitos` metabolitos clasificados."""
    c = conteos_por_muestra(nivel, min_articulos, max_categorias)
    c = c[c.sum(axis=1) >= min_metabolitos]
    X = transformar(c, transformacion)
    meta = tabla_muestras().loc[X.index]
    return X, meta


def transformar(c: pd.DataFrame, transformacion: str) -> pd.DataFrame:
    if transformacion == "clr":
        return clr(c)
    if transformacion == "fraccion":
        return c.div(c.sum(axis=1).replace(0, 1), axis=0)
    if transformacion == "conteo":
        return c.astype(float)
    raise ValueError(f"Transformacion desconocida: {transformacion}")


def agregar(conteos: pd.DataFrame, meta: pd.DataFrame, por: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Suma los conteos de las muestras que comparten los atributos `por` (reduce la pseudorreplicacion)."""
    clave = meta[por].astype(str).agg("|".join, axis=1)
    c = conteos.groupby(clave).sum()
    m = meta.groupby(clave).agg({**{k: "first" for k in meta.columns if k not in ("N_SENALES", "N_IDENTIFICADOS", "MODOS")},
                                 "N_SENALES": "sum", "N_IDENTIFICADOS": "sum",
                                 "MODOS": lambda s: "+".join(sorted(set("+".join(s).split("+"))))})
    m["N_MUESTRAS"] = clave.value_counts().reindex(m.index)
    return c, m.loc[c.index]


def matriz_presencia(meta: pd.DataFrame, por: list[str], min_articulos: int = 5, max_metabolitos: int | None = None
                     ) -> pd.DataFrame:
    """Unidades (agregadas por `por`) x metabolitos presentes en >= `min_articulos` articulos (0/1)."""
    p = presencias().merge(meta[por], left_on="ID_MUESTRA", right_index=True)
    p = p.merge(tabla_muestras()[["ID_ARTICULO"]].rename(columns={"ID_ARTICULO": "_ART"}), left_on="ID_MUESTRA", right_index=True)
    n_art = p.groupby("ID_METABOLITO")["_ART"].nunique()
    mets = n_art[n_art >= min_articulos].sort_values(ascending=False)
    if max_metabolitos:
        mets = mets.head(max_metabolitos)
    p = p[p["ID_METABOLITO"].isin(mets.index)]
    clave = p[por].astype(str).agg("|".join, axis=1)
    m = pd.crosstab(clave, p["ID_METABOLITO"]).clip(upper=1).astype(np.uint8)
    return m.reindex(columns=mets.index, fill_value=0)
