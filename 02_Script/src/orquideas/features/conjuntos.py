"""Constructores de conjuntos de modelado (unidad de analisis, X, y, grupos y covariables instrumentales).

Cada constructor devuelve un `Conjunto`. La unidad de analisis se elige segun la pregunta:
- propiedades de un compuesto (superclase, clase, modo, aducto, actividad de un metabolito): unidad = metabolito
  (o metabolito x articulo), variables = descriptores de la formula.
- atributos de una muestra (taxonomia, parte, tipo, cultivo, extraccion, columna): unidad = muestra biologica,
  variables = perfil composicional (CLR) por superclase/clase quimica.
- presencia de metabolitos y actividades de especies: unidad = grupo de muestras / especie x articulo.
Los grupos (para validacion cruzada) son el articulo, o la formula cuando la unidad es el compuesto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

from ..data.catalogos import cargar_catalogo, mapa_etiquetas
from ..data.dataset import identificados
from .perfiles import (ATRIBUTOS_MUESTRA, agregar, conteos_por_muestra, matriz_presencia, perfil_muestras, tabla_muestras,
                       transformar)
from .quimica import matriz_descriptores

CATALOGO_DE = {
    "ID_FILO": "filos", "ID_CLASE_TAXONOMICA": "clases_tax", "ID_ORDEN": "ordenes", "ID_FAMILIA": "familias",
    "ID_GENERO": "generos", "ID_ESPECIE": "especies", "ID_TIPO_MUESTRA": "tipos_muestra", "ID_PARTE_ESTUDIADA": "partes",
    "ID_TIPO_CULTIVO": "cultivos", "ID_METODO_EXTRACCION": "metodos", "ID_COLUMNA_CROMATOGRAFICA": "columnas",
    "ID_MODO_IONIZACION": "modos", "ID_SUPERCLASE_QUIMICA": "superclases", "ID_CLASE_QUIMICA": "clases_quim",
    "ID_ADUCTO": "aductos", "ID_ACTIVIDAD_BIOLOGICA": "actividades", "ID_METABOLITO": "metabolitos", "ID_REINO": "reinos",
}


@dataclass
class Conjunto:
    nombre: str
    X: pd.DataFrame
    y: pd.Series | pd.DataFrame
    grupos: pd.Series
    tipo: str                                   # multiclase | multietiqueta
    etiquetas: dict[Any, str]                   # codigo de clase/etiqueta -> nombre legible
    meta: pd.DataFrame
    X_instrumental: pd.DataFrame | None = None  # covariables de plataforma para el control de confusion
    pesos: pd.Series | None = None
    notas: list[str] = field(default_factory=list)


def _one_hot(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    partes = []
    for c in cols:
        d = pd.get_dummies(df[c].astype(str), prefix=c, dtype=float)
        partes.append(d)
    return pd.concat(partes, axis=1) if partes else pd.DataFrame(index=df.index)


def _etiquetas(col: str) -> dict[int, str]:
    return mapa_etiquetas(CATALOGO_DE[col]) if col in CATALOGO_DE else {}


def _pesos_por_grupo(grupos: pd.Series) -> pd.Series:
    """Peso 1/n_unidades del grupo, normalizado a media 1: cada articulo pesa lo mismo."""
    w = 1.0 / grupos.map(grupos.value_counts())
    return w / w.mean()


# ---------------------------------------------------------------------------------------------------------------------
# Unidad = compuesto
# ---------------------------------------------------------------------------------------------------------------------
def metabolito_quimica(objetivo: str = "ID_SUPERCLASE_QUIMICA", **_: Any) -> Conjunto:
    """Metabolitos identificados (catalogo) con formula interpretable; y = superclase o clase quimica."""
    met = cargar_catalogo("metabolitos")
    cq = cargar_catalogo("clases_quim")[["ID_CLASE_QUIMICA", "ID_SUPERCLASE_QUIMICA"]]
    observados = identificados()["ID_METABOLITO"].unique()
    m = met[met["ID_METABOLITO"].isin(observados) & (met["ID_CLASE_QUIMICA"] > 0)].merge(cq, on="ID_CLASE_QUIMICA")
    X = matriz_descriptores(m["FORMULA_MOLECULAR"])
    ok = X.notna().all(axis=1)
    m, X = m[ok].reset_index(drop=True), X[ok].reset_index(drop=True)
    return Conjunto(
        nombre=f"metabolito_quimica[{objetivo}]", X=X, y=m[objetivo].rename(objetivo),
        grupos=m["FORMULA_MOLECULAR"].astype(str).rename("FORMULA"), tipo="multiclase", etiquetas=_etiquetas(objetivo),
        meta=m[["ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR", "ID_CLASE_QUIMICA", "ID_SUPERCLASE_QUIMICA"]],
        notas=["Grupos = formula molecular: los isomeros comparten formula y nunca quedan repartidos entre entrenamiento "
               "y prueba. Las formulas deuteradas (estandares internos) y las no interpretables se excluyen."])


def _anotaciones_articulo() -> pd.DataFrame:
    df = identificados()
    cols = ["ID_ARTICULO", "ID_METABOLITO", "ID_MODO_IONIZACION", "ID_ADUCTO", "ID_SUPERCLASE_QUIMICA", "FORMULA_MOLECULAR"]
    return df[cols].drop_duplicates()


def metabolito_modo(incluir_superclase: bool = True, **_: Any) -> Conjunto:
    """(articulo, metabolito) observado en un solo modo ESI, en articulos que adquirieron ambos modos."""
    a = _anotaciones_articulo()
    a = a[a["ID_MODO_IONIZACION"].isin([1, 2])]
    modos_art = a.groupby("ID_ARTICULO")["ID_MODO_IONIZACION"].nunique()
    a = a[a["ID_ARTICULO"].isin(modos_art[modos_art == 2].index)]
    u = a.groupby(["ID_ARTICULO", "ID_METABOLITO"]).agg(
        n_modos=("ID_MODO_IONIZACION", "nunique"), ID_MODO_IONIZACION=("ID_MODO_IONIZACION", "first"),
        ID_SUPERCLASE_QUIMICA=("ID_SUPERCLASE_QUIMICA", "first"), FORMULA_MOLECULAR=("FORMULA_MOLECULAR", "first")).reset_index()
    n_ambos = int((u["n_modos"] == 2).sum())
    u = u[u["n_modos"] == 1].reset_index(drop=True)
    X = matriz_descriptores(u["FORMULA_MOLECULAR"])
    if incluir_superclase:
        X = pd.concat([X, _one_hot(u, ["ID_SUPERCLASE_QUIMICA"])], axis=1)
    ok = X.notna().all(axis=1)
    u, X = u[ok].reset_index(drop=True), X[ok].reset_index(drop=True)
    return Conjunto(
        nombre="metabolito_modo", X=X, y=u["ID_MODO_IONIZACION"], grupos=u["ID_ARTICULO"], tipo="multiclase",
        etiquetas=_etiquetas("ID_MODO_IONIZACION"), meta=u[["ID_ARTICULO", "ID_METABOLITO", "FORMULA_MOLECULAR"]],
        notas=[f"Solo articulos con adquisicion en ESI+ y ESI-; se excluyen {n_ambos} pares detectados en ambos modos. "
               "No se usan m/z, aducto ni RT (codifican el modo). EI (GC-MS) no se incluye: depende de la plataforma, "
               "no del compuesto."])


def metabolito_aducto(max_clases: int = 15, incluir_superclase: bool = True, **_: Any) -> Conjunto:
    """(articulo, metabolito, aducto) con aducto informado; y = aducto; X = formula + modo (+ superclase)."""
    a = _anotaciones_articulo()
    a = a[(a["ID_ADUCTO"] > 0) & a["ID_MODO_IONIZACION"].isin([1, 2])].reset_index(drop=True)
    top = a.groupby("ID_ADUCTO")["ID_ARTICULO"].nunique().sort_values(ascending=False).head(max_clases).index
    a = a[a["ID_ADUCTO"].isin(top)].reset_index(drop=True)
    X = pd.concat([matriz_descriptores(a["FORMULA_MOLECULAR"]), _one_hot(a, ["ID_MODO_IONIZACION"])], axis=1)
    if incluir_superclase:
        X = pd.concat([X, _one_hot(a, ["ID_SUPERCLASE_QUIMICA"])], axis=1)
    ok = X.notna().all(axis=1)
    a, X = a[ok].reset_index(drop=True), X[ok].reset_index(drop=True)
    return Conjunto(
        nombre="metabolito_aducto", X=X, y=a["ID_ADUCTO"], grupos=a["ID_ARTICULO"], tipo="multiclase",
        etiquetas=_etiquetas("ID_ADUCTO"), meta=a[["ID_ARTICULO", "ID_METABOLITO", "FORMULA_MOLECULAR", "ID_MODO_IONIZACION"]],
        X_instrumental=_one_hot(a, ["ID_MODO_IONIZACION"]),
        notas=[f"Se modelan los {len(top)} aductos informados en mas articulos. m/z queda excluida: m/z - masa = masa del "
               "aducto (fuga directa). El control instrumental usa solo el modo de ionizacion."])


def actividad_metabolito(min_positivos: int = 10, incluir_superclase: bool = True, **_: Any) -> Conjunto:
    """Metabolitos con actividad registrada (literatura); y multietiqueta = actividades con >= min_positivos."""
    r = cargar_catalogo("registro_actividades")
    r = r[(r["ID_METABOLITO"] > 1) & (r["ID_ACTIVIDAD_BIOLOGICA"] > 0)]
    Y = pd.crosstab(r["ID_METABOLITO"], r["ID_ACTIVIDAD_BIOLOGICA"]).clip(upper=1)
    Y = Y.loc[:, Y.sum() >= min_positivos]
    Y = Y[Y.sum(axis=1) > 0]
    met = cargar_catalogo("metabolitos").set_index("ID_METABOLITO").loc[Y.index]
    cq = cargar_catalogo("clases_quim").set_index("ID_CLASE_QUIMICA")["ID_SUPERCLASE_QUIMICA"]
    met["ID_SUPERCLASE_QUIMICA"] = met["ID_CLASE_QUIMICA"].map(cq).fillna(0).astype(int)
    X = matriz_descriptores(met["FORMULA_MOLECULAR"])
    if incluir_superclase:
        X = pd.concat([X, _one_hot(met, ["ID_SUPERCLASE_QUIMICA"])], axis=1)
    ok = X.notna().all(axis=1)
    X, Y, met = X[ok], Y[ok], met[ok]
    return Conjunto(
        nombre="actividad_metabolito", X=X.reset_index(drop=True), y=Y.reset_index(drop=True),
        grupos=met["FORMULA_MOLECULAR"].astype(str).reset_index(drop=True), tipo="multietiqueta",
        etiquetas=_etiquetas("ID_ACTIVIDAD_BIOLOGICA"),
        meta=met.reset_index()[["ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR"]],
        notas=["Etiquetas positivas-no etiquetadas (PU): una actividad no registrada no significa inactividad. Solo hay "
               "metabolitos con alguna actividad citada, de modo que el modelo aprende que actividad, no si es activo."])


# ---------------------------------------------------------------------------------------------------------------------
# Unidad = muestra o grupo de muestras
# ---------------------------------------------------------------------------------------------------------------------
INSTRUMENTALES = ["ID_COLUMNA_CROMATOGRAFICA", "MODOS"]


def _instrumental(meta: pd.DataFrame, excluir: str | None = None) -> pd.DataFrame:
    cols = [c for c in INSTRUMENTALES if c != excluir]
    Xi = _one_hot(meta, cols)
    Xi["log_n_identificados"] = np.log1p(meta["N_IDENTIFICADOS"].astype(float))
    Xi["log_n_senales"] = np.log1p(meta["N_SENALES"].astype(float))
    return Xi


def perfil_muestra(objetivo: str, nivel: str = "superclase", transformacion: str = "clr", min_metabolitos: int = 20,
                   min_articulos_categoria: int = 3, max_categorias: int | None = None, agregar_por: list[str] | None = None,
                   ponderar_por_grupo: bool = True, **_: Any) -> Conjunto:
    """Perfil composicional por muestra (o grupo de muestras) -> atributo de muestra `objetivo`."""
    if agregar_por:
        c = conteos_por_muestra(nivel, min_articulos_categoria, max_categorias)
        meta = tabla_muestras().loc[c.index]
        c, meta = agregar(c, meta, agregar_por)
        c = c[c.sum(axis=1) >= min_metabolitos]
        meta = meta.loc[c.index]
        X = transformar(c, transformacion)
    else:
        X, meta = perfil_muestras(nivel, transformacion, min_metabolitos, min_articulos_categoria, max_categorias)
    y = meta[objetivo]
    ok = y > 0
    X, meta, y = X[ok], meta[ok], y[ok]
    grupos = meta["ID_ARTICULO"]
    return Conjunto(
        nombre=f"perfil_muestra[{objetivo}|{nivel}]", X=X.reset_index(drop=True), y=y.reset_index(drop=True),
        grupos=grupos.reset_index(drop=True), tipo="multiclase", etiquetas=_etiquetas(objetivo),
        meta=meta.reset_index(), X_instrumental=_instrumental(meta, objetivo).reset_index(drop=True),
        pesos=_pesos_por_grupo(grupos.reset_index(drop=True)) if ponderar_por_grupo else None,
        notas=[f"Perfil = numero de metabolitos identificados por {nivel} quimica (categorias presentes en >= "
               f"{min_articulos_categoria} articulos + 'otras'), transformado con {transformacion}. Se excluyen muestras "
               f"con < {min_metabolitos} metabolitos clasificados, QC, blancos y objetivo 'No especificado'."])


def presencia_metabolitos(agregar_por: list[str] | None = None, min_articulos: int = 5, max_metabolitos: int = 60,
                          predictores: list[str] | None = None, min_identificados: int = 20, **_: Any) -> Conjunto:
    """Grupos de muestras (lote x especie x parte x tipo x cultivo x metodo) -> presencia de metabolitos frecuentes."""
    por = agregar_por or ["ID_BATCH", "ID_ESPECIE", "ID_PARTE_ESTUDIADA", "ID_TIPO_MUESTRA", "ID_TIPO_CULTIVO",
                          "ID_METODO_EXTRACCION"]
    predictores = predictores or ["ID_CLASE_TAXONOMICA", "ID_ORDEN", "ID_FAMILIA", "ID_PARTE_ESTUDIADA", "ID_TIPO_MUESTRA",
                                  "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION"]
    meta = tabla_muestras()
    meta = meta[(meta["N_IDENTIFICADOS"] >= min_identificados) & ~meta["ID_TIPO_MUESTRA"].isin([9, 10])]
    Y = matriz_presencia(meta, por, min_articulos, max_metabolitos)
    clave = meta[por].astype(str).agg("|".join, axis=1)
    m = meta.assign(_clave=clave).groupby("_clave").agg(
        {**{k: "first" for k in ATRIBUTOS_MUESTRA}, "N_IDENTIFICADOS": "sum", "N_SENALES": "sum",
         "MODOS": lambda s: "+".join(sorted(set("+".join(s).split("+"))))})
    m = m.loc[m.index.intersection(Y.index)]
    Y = Y.loc[m.index]
    X = _one_hot(m, predictores)
    return Conjunto(
        nombre="presencia_metabolitos", X=X.reset_index(drop=True), y=Y.reset_index(drop=True).astype(int),
        grupos=m["ID_ARTICULO"].reset_index(drop=True), tipo="multietiqueta", etiquetas=_etiquetas("ID_METABOLITO"),
        meta=m.reset_index(), X_instrumental=_instrumental(m).reset_index(drop=True),
        notas=[f"Etiquetas = {Y.shape[1]} metabolitos presentes en >= {min_articulos} articulos. Un metabolito ausente "
               "puede no estar en la biblioteca del laboratorio: la presencia mezcla quimica de la planta y cobertura "
               "de la biblioteca (por eso se compara con un control que solo usa la plataforma)."])


def actividad_especie(nivel: str = "superclase", min_positivos: int = 8, min_metabolitos: int = 20,
                      min_articulos_categoria: int = 3, max_categorias: int | None = None, **_: Any) -> Conjunto:
    """(articulo, especie) con perfil quimico -> actividades registradas para esa especie en ese articulo."""
    c = conteos_por_muestra(nivel, min_articulos_categoria, max_categorias)
    meta = tabla_muestras().loc[c.index]
    meta = meta[meta["ID_ESPECIE"] > 0]
    c, meta = agregar(c.loc[meta.index], meta, ["ID_ARTICULO", "ID_ESPECIE"])
    c = c[c.sum(axis=1) >= min_metabolitos]
    meta = meta.loc[c.index]
    r = cargar_catalogo("registro_actividades")
    r = r[(r["ID_ACTIVIDAD_BIOLOGICA"] > 0) & (r["ID_ESPECIE"] > 0)]
    r_clave = r["ID_ARTICULO"].astype(str) + "|" + r["ID_ESPECIE"].astype(str)
    Y = pd.crosstab(r_clave, r["ID_ACTIVIDAD_BIOLOGICA"]).clip(upper=1).reindex(meta.index, fill_value=0)
    Y = Y.loc[:, Y.sum() >= min_positivos]
    con = Y.sum(axis=1) > 0
    X = transformar(c[con], "clr")
    Y, meta = Y[con], meta[con]
    return Conjunto(
        nombre=f"actividad_especie[{nivel}]", X=X.reset_index(drop=True), y=Y.reset_index(drop=True).astype(int),
        grupos=meta["ID_ARTICULO"].reset_index(drop=True), tipo="multietiqueta",
        etiquetas=_etiquetas("ID_ACTIVIDAD_BIOLOGICA"), meta=meta.reset_index(),
        X_instrumental=_instrumental(meta).reset_index(drop=True),
        notas=["Unidad = especie x articulo (casi siempre una por articulo). Actividades mayoritariamente bibliograficas: "
               "positivos sin negativos verificados (PU). Solo se incluyen especies con alguna actividad registrada."])


CONSTRUCTORES: dict[str, Callable[..., Conjunto]] = {
    "metabolito_quimica": metabolito_quimica,
    "metabolito_modo": metabolito_modo,
    "metabolito_aducto": metabolito_aducto,
    "actividad_metabolito": actividad_metabolito,
    "perfil_muestra": perfil_muestra,
    "presencia_metabolitos": presencia_metabolitos,
    "actividad_especie": actividad_especie,
}


def construir(nombre: str, parametros: dict[str, Any]) -> Conjunto:
    if nombre not in CONSTRUCTORES:
        raise ValueError(f"Conjunto desconocido '{nombre}'. Disponibles: {sorted(CONSTRUCTORES)}")
    return CONSTRUCTORES[nombre](**parametros)
