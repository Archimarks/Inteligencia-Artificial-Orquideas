#
# Archivo: modelos_supervisados.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Catalogo de estimadores para las tareas supervisadas (Clasificacion / Regresion).
# Cada entrada es una fabrica sin argumentos (callable -> estimador sin entrenar);
# se evalua recien al llamar entrenar(), asi que perfiles.requerido() ya esta
# fijado y kwargs_boost()/device_torch() reparten la GPU que corresponda.
#
# Escalado: knn, svm/svr, ridge/elastic_net, regresion_logistica y mlp comparan
# distancias o penalizan coeficientes, asi que van envueltos en
# Pipeline(StandardScaler, modelo) -- si no, una feature en escala grande (p.ej.
# ALTURA_PICO, en el orden de 1e5-1e6) domina por completo a una en escala chica
# (p.ej. TIEMPO_RETENCION_MINUTOS). Arboles/boosting (random_forest, extra_trees,
# gradient_boosting, xgboost, lightgbm, catboost) y naive_bayes no lo necesitan.
# perfiles.dispositivo_de() y visualizacion_estilo._estimador_base() ya sabian desarmar
# un Pipeline (miran ".steps"), asi que no hace falta tocar nada mas para que el
# resto del pipeline (grafico de importancia, registro de GPU/CPU) siga andando.
#
# Balanceo de clases: los objetivos de clasificacion vienen desbalanceados
# (Clasificacion/METABOLITO tiene 32000+ clases, muchas con pocas decenas de
# muestras) y la metrica con la que se rankea es f1_macro, que pesa todas las
# clases por igual -- entrenar sin balancear favorece a las clases mayoritarias
# y castiga esa metrica. Se activa class_weight="balanced" (o el equivalente de
# cada libreria) en todo clasificador que lo soporte sin necesitar sample_weight
# aparte; xgboost no tiene una opcion multiclase equivalente y se deja tal cual.
#
# Nota de escala: SVM y KNN (distancia par-a-par) y el GradientBoosting de
# scikit-learn (secuencial, sin GPU) se vuelven poco practicos por encima de un
# par de cientos de miles de filas -- Clasificacion/METABOLITO (~965K) y
# Clasificacion/ACTIVIDAD_BIOLOGICA (~2.5M) los van a dejar corriendo mucho
# tiempo. No se quitan del catalogo (la eleccion de que entrenar es del menu),
# pero es la limitacion esperada, no un error.
#
from __future__ import annotations

from typing import Callable

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    ExtraTreesClassifier, ExtraTreesRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    RandomForestClassifier, RandomForestRegressor,
)
from sklearn.linear_model import ElasticNet, LogisticRegression, Ridge
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR

from .. import submodulo

config = submodulo("00_fundamentos.config")
perfiles = submodulo("00_fundamentos.perfiles")

_N_JOBS = -1
# Mas arboles que el default (100) de scikit-learn: mejor promedio sin cambiar
# el costo por arbol; con n_jobs=-1 se reparten entre nucleos igual que antes.
_N_ESTIMADORES_BOSQUE = 250
# Mismo espiritu para los boosting: mas rondas, con sub-muestreo de filas/columnas
# por ronda (subsample/colsample) para que compense el riesgo de sobreajuste de
# tener mas rondas.
_N_ESTIMADORES_BOOST = 300
_SUBMUESTREO_BOOST = 0.8


def _escalado(modelo) -> Callable[[], object]:
    return lambda: make_pipeline(StandardScaler(), modelo())


def _xgb_clasificador():
    from xgboost import XGBClassifier
    return XGBClassifier(random_state=config.SEMILLA, n_jobs=_N_JOBS,
                          eval_metric="mlogloss", n_estimators=_N_ESTIMADORES_BOOST,
                          subsample=_SUBMUESTREO_BOOST, colsample_bytree=_SUBMUESTREO_BOOST,
                          **perfiles.kwargs_boost("xgboost"))


def _xgb_regresor():
    from xgboost import XGBRegressor
    return XGBRegressor(random_state=config.SEMILLA, n_jobs=_N_JOBS,
                         n_estimators=_N_ESTIMADORES_BOOST,
                         subsample=_SUBMUESTREO_BOOST, colsample_bytree=_SUBMUESTREO_BOOST,
                         **perfiles.kwargs_boost("xgboost"))


def _lgbm_clasificador():
    from lightgbm import LGBMClassifier
    return LGBMClassifier(random_state=config.SEMILLA, n_jobs=_N_JOBS, verbosity=-1,
                          n_estimators=_N_ESTIMADORES_BOOST, subsample=_SUBMUESTREO_BOOST,
                          colsample_bytree=_SUBMUESTREO_BOOST, class_weight="balanced")


def _lgbm_regresor():
    from lightgbm import LGBMRegressor
    return LGBMRegressor(random_state=config.SEMILLA, n_jobs=_N_JOBS, verbosity=-1,
                         n_estimators=_N_ESTIMADORES_BOOST, subsample=_SUBMUESTREO_BOOST,
                         colsample_bytree=_SUBMUESTREO_BOOST)


def _catboost_clasificador():
    from catboost import CatBoostClassifier
    return CatBoostClassifier(random_state=config.SEMILLA, verbose=False,
                              iterations=_N_ESTIMADORES_BOOST, bootstrap_type="Bernoulli",
                              subsample=_SUBMUESTREO_BOOST,
                              auto_class_weights="Balanced",
                              **perfiles.kwargs_boost("catboost"))


def _catboost_regresor():
    from catboost import CatBoostRegressor
    return CatBoostRegressor(random_state=config.SEMILLA, verbose=False,
                             iterations=_N_ESTIMADORES_BOOST, bootstrap_type="Bernoulli",
                             subsample=_SUBMUESTREO_BOOST,
                             **perfiles.kwargs_boost("catboost"))


def _mlp_clasificador():
    from .torch_modelos import MLPClasificador
    return MLPClasificador(device=perfiles.device_torch())


def _mlp_regresor():
    from .torch_modelos import MLPRegresor
    return MLPRegresor(device=perfiles.device_torch())


# nombre -> fabrica (sin argumentos).
CLASIFICACION: dict[str, Callable[[], object]] = {
    # n_jobs no va aca: scikit-learn >= 1.8 lo dejo sin efecto en LogisticRegression
    # (se va en 1.10) y avisa con FutureWarning si se lo pasa.
    "regresion_logistica": _escalado(lambda: LogisticRegression(
        random_state=config.SEMILLA, max_iter=1000, class_weight="balanced")),
    "knn": _escalado(lambda: KNeighborsClassifier(n_jobs=_N_JOBS)),
    # SVC(probability=True) esta deprecado desde scikit-learn 1.9 (se va en 1.11);
    # el propio aviso de la libreria recomienda este reemplazo para seguir
    # teniendo predict_proba (lo necesitan la curva ROC y precision-recall).
    "svm": _escalado(lambda: CalibratedClassifierCV(
        SVC(random_state=config.SEMILLA, class_weight="balanced"),
        ensemble=False, n_jobs=_N_JOBS)),
    "naive_bayes": lambda: GaussianNB(),
    "random_forest": lambda: RandomForestClassifier(
        random_state=config.SEMILLA, n_jobs=_N_JOBS, n_estimators=_N_ESTIMADORES_BOSQUE,
        class_weight="balanced"),
    "extra_trees": lambda: ExtraTreesClassifier(
        random_state=config.SEMILLA, n_jobs=_N_JOBS, n_estimators=_N_ESTIMADORES_BOSQUE,
        class_weight="balanced"),
    "gradient_boosting": lambda: GradientBoostingClassifier(random_state=config.SEMILLA),
    "xgboost": _xgb_clasificador,
    "lightgbm": _lgbm_clasificador,
    "catboost": _catboost_clasificador,
    "mlp": _escalado(_mlp_clasificador),
}

REGRESION: dict[str, Callable[[], object]] = {
    "ridge": _escalado(lambda: Ridge(random_state=config.SEMILLA)),
    "elastic_net": _escalado(lambda: ElasticNet(random_state=config.SEMILLA)),
    "knn": _escalado(lambda: KNeighborsRegressor(n_jobs=_N_JOBS)),
    "svr": _escalado(lambda: SVR()),
    "random_forest": lambda: RandomForestRegressor(
        random_state=config.SEMILLA, n_jobs=_N_JOBS, n_estimators=_N_ESTIMADORES_BOSQUE),
    "extra_trees": lambda: ExtraTreesRegressor(
        random_state=config.SEMILLA, n_jobs=_N_JOBS, n_estimators=_N_ESTIMADORES_BOSQUE),
    "gradient_boosting": lambda: GradientBoostingRegressor(random_state=config.SEMILLA),
    "xgboost": _xgb_regresor,
    "lightgbm": _lgbm_regresor,
    "catboost": _catboost_regresor,
    "mlp": _escalado(_mlp_regresor),
}


# Algoritmos que escalan mal con la cantidad de filas (ver nota de escala mas
# arriba): entrenamiento_base.py los entrena sobre una submuestra por encima de
# config.LIMITE_FILAS_MODELOS_LENTOS en vez de colgarse con el dataset completo.
# Se entrenan siempre (tambien sin GPU): entrenamiento_base.py cronometra cada
# modelo, asi que si alguno tarda de mas queda a la vista en vez de ocultarlo.
MODELOS_LENTOS: frozenset[str] = frozenset({"svm", "svr", "knn", "gradient_boosting"})


def modelos(tarea: str) -> list[str]:
    catalogo = CLASIFICACION if tarea == "Clasificacion" else REGRESION
    return list(catalogo)


def fabrica(tarea: str, nombre: str) -> Callable[[], object]:
    catalogo = CLASIFICACION if tarea == "Clasificacion" else REGRESION
    if nombre not in catalogo:
        raise ValueError(f"Modelo desconocido para {tarea}: {nombre!r}. "
                         f"Opciones: {list(catalogo)}")
    return catalogo[nombre]
