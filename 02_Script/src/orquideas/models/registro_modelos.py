"""Catalogo de modelos configurables por nombre desde YAML.

Cada modelo se envuelve en un Pipeline (imputacion -> escalado opcional -> seleccion de variables -> estimador),
de modo que toda transformacion aprendida se ajusta solo con los datos de entrenamiento de cada particion.
"""
from __future__ import annotations

from typing import Any

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ESCALAR = {"logistica", "knn"}


def _lightgbm(semilla: int, n_jobs: int, **kw: Any):
    from lightgbm import LGBMClassifier
    base = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10, subsample=0.8,
                subsample_freq=1, colsample_bytree=0.8, class_weight="balanced", verbose=-1)
    base.update(kw)
    return LGBMClassifier(random_state=semilla, n_jobs=n_jobs, **base)


def estimador(nombre: str, semilla: int, n_jobs: int, multietiqueta: bool = False, **kw: Any):
    """Instancia el estimador `nombre` con los hiperparametros `kw`."""
    if nombre == "baseline_mayoritaria":
        est = DummyClassifier(strategy="most_frequent")
    elif nombre == "baseline_prior":
        est = DummyClassifier(strategy="prior")
    elif nombre == "baseline_estratificada":
        est = DummyClassifier(strategy="stratified", random_state=semilla)
    elif nombre == "logistica":
        p = dict(C=1.0, max_iter=3000, class_weight="balanced")
        p.update(kw)
        est = LogisticRegression(random_state=semilla, **p)
    elif nombre == "random_forest":
        p = dict(n_estimators=400, min_samples_leaf=2, class_weight="balanced_subsample", max_features="sqrt")
        p.update(kw)
        est = RandomForestClassifier(random_state=semilla, n_jobs=n_jobs, **p)
    elif nombre == "extra_trees":
        p = dict(n_estimators=400, min_samples_leaf=2, class_weight="balanced_subsample")
        p.update(kw)
        est = ExtraTreesClassifier(random_state=semilla, n_jobs=n_jobs, **p)
    elif nombre == "hist_gradient_boosting":
        p = dict(max_iter=300, learning_rate=0.06, class_weight="balanced", early_stopping=False)
        p.update(kw)
        est = HistGradientBoostingClassifier(random_state=semilla, **p)
    elif nombre == "lightgbm":
        est = _lightgbm(semilla, 1 if multietiqueta else n_jobs, **kw)
    elif nombre == "knn":
        p = dict(n_neighbors=7, weights="distance")
        p.update(kw)
        est = KNeighborsClassifier(n_jobs=n_jobs, **p)
    else:
        raise ValueError(f"Modelo desconocido '{nombre}'. Disponibles: {sorted(MODELOS)}")
    # RF, ExtraTrees, KNN y Dummy aceptan Y multietiqueta de forma nativa; el resto se envuelve
    if multietiqueta and nombre in {"logistica", "hist_gradient_boosting", "lightgbm"}:
        est = MultiOutputClassifier(est, n_jobs=n_jobs if nombre != "lightgbm" else 1)
    return est


MODELOS = ["baseline_mayoritaria", "baseline_prior", "baseline_estratificada", "logistica", "random_forest",
           "extra_trees", "hist_gradient_boosting", "lightgbm", "knn"]


def construir_pipeline(nombre: str, semilla: int, n_jobs: int, multietiqueta: bool = False,
                       seleccion: dict[str, Any] | None = None, hiperparametros: dict[str, Any] | None = None,
                       n_variables: int | None = None) -> Pipeline:
    pasos: list[tuple[str, Any]] = [("imputar", SimpleImputer(strategy="median")),
                                    ("varianza", VarianceThreshold(0.0))]
    if nombre in ESCALAR:
        pasos.append(("escalar", StandardScaler()))
    if seleccion and seleccion.get("metodo") not in (None, "ninguna") and not multietiqueta \
            and not nombre.startswith("baseline"):
        func = {"anova": f_classif, "informacion_mutua": mutual_info_classif}[seleccion["metodo"]]
        k = seleccion.get("k", 30)
        k = "all" if n_variables is not None and k >= n_variables else k
        pasos.append(("seleccion", SelectKBest(func, k=k)))
    pasos.append(("modelo", estimador(nombre, semilla, n_jobs, multietiqueta, **(hiperparametros or {}))))
    return Pipeline(pasos)
