"""Estrategias de particion y filtrado de clases evaluables.

Regla central: las unidades de un mismo grupo (articulo o formula) nunca se reparten entre entrenamiento y prueba.
Una clase solo es evaluable si aparece en al menos `min_groups_per_class` grupos: si aparece en un unico articulo,
predecirla en validacion agrupada es imposible por construccion, y en validacion no agrupada el modelo aprenderia
la firma del articulo, no la de la clase.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, StratifiedGroupKFold, StratifiedKFold, KFold


@dataclass
class FiltroClases:
    conservadas: list[Any]
    descartadas: pd.DataFrame        # clase, n_unidades, n_grupos, motivo
    mascara: np.ndarray


def filtrar_clases(y: pd.Series, grupos: pd.Series, min_grupos: int, min_unidades: int,
                   max_clases: int | None = None) -> FiltroClases:
    t = pd.DataFrame({"y": y.values, "g": grupos.values})
    res = t.groupby("y").agg(n_unidades=("g", "size"), n_grupos=("g", "nunique")).sort_values("n_unidades", ascending=False)
    ok = (res["n_grupos"] >= min_grupos) & (res["n_unidades"] >= min_unidades)
    motivo = np.where(res["n_grupos"] < min_grupos, f"< {min_grupos} grupos",
                      np.where(res["n_unidades"] < min_unidades, f"< {min_unidades} unidades", ""))
    res["motivo"] = motivo
    conservadas = res.index[ok].tolist()
    if max_clases and len(conservadas) > max_clases:
        sobran = conservadas[max_clases:]
        res.loc[sobran, "motivo"] = f"fuera de las {max_clases} clases mas frecuentes"
        conservadas = conservadas[:max_clases]
    desc = res[~res.index.isin(conservadas)].reset_index().rename(columns={"y": "clase"})
    return FiltroClases(conservadas, desc, t["y"].isin(conservadas).to_numpy())


def filtrar_etiquetas(Y: pd.DataFrame, grupos: pd.Series, min_grupos: int, min_unidades: int) -> FiltroClases:
    """Multietiqueta: conserva etiquetas positivas en >= min_grupos grupos y >= min_unidades unidades,
    y con al menos una unidad negativa."""
    filas = []
    for c in Y.columns:
        pos = Y[c].to_numpy() == 1
        filas.append({"clase": c, "n_unidades": int(pos.sum()), "n_grupos": int(grupos[pos].nunique()),
                      "n_negativos": int((~pos).sum())})
    res = pd.DataFrame(filas)
    ok = (res["n_grupos"] >= min_grupos) & (res["n_unidades"] >= min_unidades) & (res["n_negativos"] > 0)
    res["motivo"] = np.where(ok, "", np.where(res["n_grupos"] < min_grupos, f"< {min_grupos} grupos",
                                              np.where(res["n_negativos"] == 0, "sin negativos", f"< {min_unidades} unidades")))
    conservadas = res.loc[ok, "clase"].tolist()
    mascara = Y[conservadas].sum(axis=1).to_numpy() > 0 if conservadas else np.zeros(len(Y), bool)
    return FiltroClases(conservadas, res[~ok].reset_index(drop=True), np.ones(len(Y), bool) if conservadas else mascara)


def particiones(estrategia: str, y: np.ndarray, grupos: np.ndarray, n_splits: int, semilla: int,
                multietiqueta: bool = False) -> list[tuple[np.ndarray, np.ndarray]]:
    """Devuelve la lista de (indices_entrenamiento, indices_prueba)."""
    n_grupos = len(np.unique(grupos))
    X0 = np.zeros(len(grupos))
    if estrategia == "group_kfold":
        k = min(n_splits, n_grupos)
        if multietiqueta:
            sp: Any = GroupKFold(n_splits=k, shuffle=True, random_state=semilla)
            it: Iterator = sp.split(X0, None, grupos)
        else:
            # StratifiedGroupKFold equilibra las clases entre particiones; si alguna clase tiene menos grupos que
            # particiones, scikit-learn avisa pero sigue siendo una particion agrupada valida.
            sp = StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=semilla)
            it = sp.split(X0, y, grupos)
    elif estrategia == "leave_one_group_out":
        it = LeaveOneGroupOut().split(X0, y, grupos)
    elif estrategia == "stratified_kfold":
        if multietiqueta:
            it = KFold(n_splits=n_splits, shuffle=True, random_state=semilla).split(X0)
        else:
            k = int(min(n_splits, pd.Series(y).value_counts().min()))
            it = StratifiedKFold(n_splits=max(k, 2), shuffle=True, random_state=semilla).split(X0, y)
    else:
        raise ValueError(f"Estrategia de particion desconocida: {estrategia}")
    out = [(tr, te) for tr, te in it]
    for tr, te in out:
        if estrategia != "stratified_kfold":
            assert not set(grupos[tr]) & set(grupos[te]), "Fuga: un grupo aparece en entrenamiento y prueba"
    return out
