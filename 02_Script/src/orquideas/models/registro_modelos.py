"""Catalogo de modelos configurables por nombre desde YAML.

Cada modelo se envuelve en un Pipeline (imputacion -> escalado opcional -> seleccion de variables -> estimador),
de modo que toda transformacion aprendida se ajusta solo con los datos de entrenamiento de cada particion.

Modelos con GPU (ver utils/gpu.py): `xgboost` (una GPU por modelo; las particiones se reparten entre todas las GPU)
y `catboost` (todas las GPU seleccionadas en cada modelo). Sin GPU ambos se entrenan en CPU con el mismo codigo.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif, mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

ESCALAR = {"logistica", "knn"}
MODELOS_GPU = {"xgboost", "catboost"}


class XGBoostGPU(ClassifierMixin, BaseEstimator):
    """XGBoost con reetiquetado interno (las particiones pueden no contener todas las clases) y dispositivo
    configurable. Tras entrenar, el modelo se pasa a CPU para que el archivo guardado funcione en cualquier equipo."""

    def __init__(self, gpu: int | None = None, semilla: int = 0, n_jobs: int = -1, balancear: bool = True,
                 parametros: dict[str, Any] | None = None):
        self.gpu = gpu
        self.semilla = semilla
        self.n_jobs = n_jobs
        self.balancear = balancear
        self.parametros = parametros

    def fit(self, X, y, sample_weight=None):
        from xgboost import XGBClassifier
        self.le_ = LabelEncoder().fit(y)
        self.classes_ = self.le_.classes_
        yy = self.le_.transform(y)
        if len(self.classes_) == 1:
            self.modelo_ = None
            self.n_features_in_ = X.shape[1]
            self.feature_importances_ = np.zeros(X.shape[1])
            return self
        w = compute_sample_weight("balanced", yy) if self.balancear else None
        if sample_weight is not None:
            w = np.asarray(sample_weight) if w is None else w * np.asarray(sample_weight)
        p = dict(n_estimators=400, learning_rate=0.05, max_depth=6, subsample=0.8, colsample_bytree=0.8,
                 tree_method="hist")
        p.update(self.parametros or {})
        dispositivo = f"cuda:{self.gpu}" if self.gpu is not None else "cpu"
        self.modelo_ = XGBClassifier(device=dispositivo, random_state=self.semilla, n_jobs=self.n_jobs, **p)
        self.modelo_.fit(X, yy, sample_weight=w)
        self.modelo_.set_params(device="cpu")
        self.n_features_in_ = X.shape[1]
        self.feature_importances_ = self.modelo_.feature_importances_
        return self

    def predict_proba(self, X):
        if self.modelo_ is None:
            return np.ones((len(X), 1))
        return self.modelo_.predict_proba(X)

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(1)]


class CatBoostGPU(ClassifierMixin, BaseEstimator):
    """CatBoost con todas las GPU indicadas a la vez (devices='0:1'); si una particion de entrenamiento tiene una
    sola clase (frecuente en multietiqueta) devuelve esa clase en vez de fallar."""

    def __init__(self, gpus: list[int] | None = None, semilla: int = 0, n_jobs: int = -1,
                 parametros: dict[str, Any] | None = None):
        self.gpus = gpus
        self.semilla = semilla
        self.n_jobs = n_jobs
        self.parametros = parametros

    def parametros_catboost(self) -> dict[str, Any]:
        p = dict(iterations=500, learning_rate=0.08, depth=6, auto_class_weights="Balanced", verbose=0,
                 allow_writing_files=False, random_seed=self.semilla, thread_count=self.n_jobs)
        p.update(self.parametros or {})
        if self.gpus:
            p.update(task_type="GPU", devices=":".join(str(g) for g in self.gpus))
        return p

    def fit(self, X, y, sample_weight=None):
        from catboost import CatBoostClassifier
        self.classes_ = np.unique(y)
        self.n_features_in_ = X.shape[1]
        if len(self.classes_) == 1:
            self.modelo_ = None
            self.feature_importances_ = np.zeros(X.shape[1])
            return self
        self.modelo_ = CatBoostClassifier(**self.parametros_catboost())
        self.modelo_.fit(X, y, sample_weight=sample_weight)
        self.feature_importances_ = np.asarray(self.modelo_.get_feature_importance(), dtype=float)
        return self

    def predict_proba(self, X):
        if self.modelo_ is None:
            return np.ones((len(X), 1))
        p = self.modelo_.predict_proba(X)
        orden = [list(self.modelo_.classes_).index(c) for c in self.classes_]   # mismas columnas que classes_
        return p[:, orden]

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(1)]


def _lightgbm(semilla: int, n_jobs: int, **kw: Any):
    from lightgbm import LGBMClassifier
    base = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10, subsample=0.8,
                subsample_freq=1, colsample_bytree=0.8, class_weight="balanced", verbose=-1)
    base.update(kw)
    return LGBMClassifier(random_state=semilla, n_jobs=n_jobs, **base)


def estimador(nombre: str, semilla: int, n_jobs: int, multietiqueta: bool = False, gpus: list[int] | None = None,
              **kw: Any):
    """Instancia el estimador `nombre` con los hiperparametros `kw`; `gpus` = indices de GPU para este ajuste."""
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
    elif nombre == "xgboost":
        est = XGBoostGPU(gpu=gpus[0] if gpus else None, semilla=semilla, n_jobs=n_jobs, parametros=kw or None)
    elif nombre == "catboost":
        est = CatBoostGPU(gpus=gpus, semilla=semilla, n_jobs=n_jobs, parametros=kw or None)
    elif nombre == "knn":
        p = dict(n_neighbors=7, weights="distance")
        p.update(kw)
        est = KNeighborsClassifier(n_jobs=n_jobs, **p)
    else:
        raise ValueError(f"Modelo desconocido '{nombre}'. Disponibles: {sorted(MODELOS)}")
    # RF, ExtraTrees, KNN y Dummy aceptan Y multietiqueta de forma nativa; el resto se envuelve
    if multietiqueta and nombre in {"logistica", "hist_gradient_boosting", "lightgbm", "xgboost", "catboost"}:
        est = MultiOutputClassifier(est, n_jobs=n_jobs if nombre in {"logistica", "hist_gradient_boosting"} else 1)
    return est


MODELOS = ["baseline_mayoritaria", "baseline_prior", "baseline_estratificada", "logistica", "random_forest",
           "extra_trees", "hist_gradient_boosting", "lightgbm", "xgboost", "catboost", "knn"]


def construir_pipeline(nombre: str, semilla: int, n_jobs: int, multietiqueta: bool = False,
                       seleccion: dict[str, Any] | None = None, hiperparametros: dict[str, Any] | None = None,
                       n_variables: int | None = None, gpus: list[int] | None = None) -> Pipeline:
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
    pasos.append(("modelo", estimador(nombre, semilla, n_jobs, multietiqueta,
                                      gpus if nombre in MODELOS_GPU else None, **(hiperparametros or {}))))
    return Pipeline(pasos)
