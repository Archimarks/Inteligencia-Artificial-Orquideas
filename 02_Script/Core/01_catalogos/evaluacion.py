#
# Archivo: evaluacion.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Evaluacion generica de un estimador supervisado, independiente del algoritmo.
#
# Estrategia, en orden de preferencia segun el tamano de los datos:
#     1. Holdout estratificado (>= MIN_FILAS_HOLDOUT filas y clases con soporte).
#     2. Validacion cruzada k-fold (estratificada en clasificacion), con
#        predicciones obtenidas por cross_val_predict.
#     3. Sin validacion: predicciones y metricas sobre los datos de entrenamiento.
#
# Devuelve un objeto Evaluacion con: metricas, texto de la validacion, el
# estimador re-entrenado con TODAS las filas, y las predicciones del conjunto
# evaluado (y_true / y_pred / y_score) para que Core.visualizacion dibuje.
#
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    mean_absolute_error, r2_score, root_mean_squared_error,
)
from sklearn.model_selection import (
    KFold, StratifiedKFold, cross_val_predict, train_test_split,
)

from .. import submodulo

config = submodulo("00_fundamentos.config")


# Resultado de evaluar un estimador.
#     estimador   : re-entrenado con todas las filas (lo que se guarda).
#     y_true/y_pred: objetivo real y predicho del conjunto evaluado.
#     y_score     : probabilidades / puntajes de decision si el modelo los da, si no None.
#     origen_pred : "holdout" | "cv" | "entrenamiento".
@dataclass
class Evaluacion:
    metricas: dict
    validacion: str
    estimador: Any
    y_true: np.ndarray
    y_pred: np.ndarray
    y_score: np.ndarray | None
    origen_pred: str


# Metricas de clasificacion a partir de (verdaderos, predichos).
def metricas_clasificacion(y_true, y_pred) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


# Metricas de regresion a partir de (verdaderos, predichos).
def metricas_regresion(y_true, y_pred) -> dict[str, float]:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
    }


# Texto descriptivo de una particion holdout segun config.PROPORCION_PRUEBA.
def _texto_holdout(estratificado: bool) -> str:
    entren = int((1 - config.PROPORCION_PRUEBA) * 100)
    prueba = int(config.PROPORCION_PRUEBA * 100)
    sufijo = " estratificado" if estratificado else ""
    return f"holdout {entren}/{prueba}{sufijo}"


# Probabilidades o puntajes de decision de un estimador ya entrenado (None si no aplica).
def _scores(estimador, X) -> np.ndarray | None:
    for metodo in ("predict_proba", "decision_function"):
        if hasattr(estimador, metodo):
            try:
                return np.asarray(getattr(estimador, metodo)(X))
            except Exception:
                pass
    return None


# Predicciones out-of-fold por validacion cruzada. Si con_proba=True intenta
# UNA sola pasada con method="predict_proba" y deriva la clase predicha con
# argmax (valido: y ya viene codificado 0..k-1 por LabelEncoder, asi que la
# columna j de predict_proba es exactamente la clase j, y todo el catalogo de
# clasificadores del proyecto predice por argmax de sus probabilidades) --
# evita una segunda pasada de cross_val_predict (el doble de folds entrenados)
# solo para tener las probabilidades. Si predict_proba no es viable (el modelo
# no la da, o algun fold no ve todas las clases), cae a una pasada con
# method="predict" (mismo costo que antes, sin probabilidades).
def _predicciones_cv(estimador, X, y, cv, con_proba: bool) -> tuple[np.ndarray, np.ndarray | None]:
    if con_proba:
        try:
            proba = np.asarray(cross_val_predict(clone(estimador), X, y, cv=cv, method="predict_proba"))
            return np.argmax(proba, axis=1), proba
        except Exception:
            pass
    return cross_val_predict(clone(estimador), X, y, cv=cv), None


# Evalua el estimador con la mejor estrategia posible y lo re-entrena con todo.
def evaluar(estimador, X, y, es_clasificacion: bool, log) -> Evaluacion:
    n = len(y)
    conteo = Counter(y) if es_clasificacion else None
    min_clase = min(conteo.values()) if conteo else None
    y = np.asarray(y)

    y_score: np.ndarray | None = None

    if es_clasificacion and n >= config.MIN_FILAS_HOLDOUT \
            and min_clase >= config.MIN_EJEMPLARES_CLASE_HOLDOUT:
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=config.PROPORCION_PRUEBA,
            random_state=config.SEMILLA, stratify=y)
        parcial = clone(estimador)
        parcial.fit(X_tr, y_tr)
        y_true, y_pred = y_te, parcial.predict(X_te)
        y_score = _scores(parcial, X_te)
        validacion, origen = _texto_holdout(True), "holdout"

    elif not es_clasificacion and n >= config.MIN_FILAS_HOLDOUT:
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=config.PROPORCION_PRUEBA, random_state=config.SEMILLA)
        parcial = clone(estimador)
        parcial.fit(X_tr, y_tr)
        y_true, y_pred = y_te, parcial.predict(X_te)
        validacion, origen = _texto_holdout(False), "holdout"

    elif es_clasificacion and min_clase >= 2:
        k = min(config.MAX_FOLDS, min_clase)
        cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=config.SEMILLA)
        y_true = y
        y_pred, y_score = _predicciones_cv(estimador, X, y, cv, len(conteo) <= config.MAX_CLASES_ROC)
        validacion, origen = f"validacion cruzada {k}-fold estratificada", "cv"

    elif es_clasificacion and n >= config.MIN_FILAS_CV:
        # Alguna clase tiene una sola muestra: no se puede estratificar. KFold
        # normal como ultimo recurso; las clases raras cuentan como error, que es honesto.
        k = min(config.MAX_FOLDS, n // 2)
        cv = KFold(n_splits=k, shuffle=True, random_state=config.SEMILLA)
        y_true = y
        y_pred, y_score = _predicciones_cv(estimador, X, y, cv, len(conteo) <= config.MAX_CLASES_ROC)
        validacion, origen = f"validacion cruzada {k}-fold (no estratificada)", "cv"

    elif not es_clasificacion and n >= config.MIN_FILAS_CV:
        k = min(config.MAX_FOLDS, n // 2)
        cv = KFold(n_splits=k, shuffle=True, random_state=config.SEMILLA)
        y_true = y
        y_pred = cross_val_predict(clone(estimador), X, y, cv=cv)
        validacion, origen = f"validacion cruzada {k}-fold", "cv"

    else:
        log.warning("Datos insuficientes para validar (%d filas): se reportan metricas "
                    "de entrenamiento, son optimistas.", n)
        parcial = clone(estimador)
        parcial.fit(X, y)
        y_true, y_pred = y, parcial.predict(X)
        y_score = _scores(parcial, X)
        validacion, origen = "sin validacion (metricas de entrenamiento)", "entrenamiento"

    metricas = (metricas_clasificacion(y_true, y_pred) if es_clasificacion
                else metricas_regresion(y_true, y_pred))

    final = clone(estimador)
    final.fit(X, y)

    return Evaluacion(
        metricas=metricas,
        validacion=validacion,
        estimador=final,
        y_true=np.asarray(y_true),
        y_pred=np.asarray(y_pred),
        y_score=y_score,
        origen_pred=origen,
    )
