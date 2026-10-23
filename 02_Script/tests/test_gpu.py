"""Seleccion de GPU y reparto de particiones (sin GPU real: se simulan las detectadas)."""
import numpy as np
import pytest

from src.models.registro_modelos import XGBoostGPU, construir_pipeline
from src.tasks.supervisado import asignar_gpus
from src.utils.gpu import ErrorGPU, seleccionar_gpus

DOS = [{"indice": 0, "nombre": "GPU A"}, {"indice": 1, "nombre": "GPU B"}]


def test_usa_todas_las_gpu_detectadas():
    assert seleccionar_gpus({"usar_gpu": "auto", "gpus": "todas"}, DOS) == [0, 1]


def test_lista_y_cpu():
    assert seleccionar_gpus({"usar_gpu": "auto", "gpus": [1]}, DOS) == [1]
    assert seleccionar_gpus({"usar_gpu": "no"}, DOS) == []
    assert seleccionar_gpus({"usar_gpu": "auto"}, []) == []


def test_exigir_gpu_sin_gpu_falla():
    with pytest.raises(ErrorGPU):
        seleccionar_gpus({"usar_gpu": "si"}, [])


def test_reparto_de_particiones():
    assert asignar_gpus("xgboost", 5, [0, 1]) == [[0], [1], [0], [1], [0]]
    assert asignar_gpus("catboost", 3, [0, 1]) == [[0, 1]] * 3
    assert asignar_gpus("random_forest", 2, [0, 1]) == [None, None]
    assert asignar_gpus("xgboost", 2, []) == [None, None]


def test_catboost_configura_todas_las_gpu():
    pipe = construir_pipeline("catboost", 0, 1, gpus=[0, 1])
    p = pipe.steps[-1][1].parametros_catboost()
    assert p["task_type"] == "GPU" and p["devices"] == "0:1"


def test_catboost_cpu_una_sola_clase_y_multietiqueta():
    from src.models.registro_modelos import CatBoostGPU
    X = np.random.default_rng(0).normal(size=(40, 3))
    m = CatBoostGPU(parametros={"iterations": 10}).fit(X, np.zeros(40, int))
    assert m.predict_proba(X).shape == (40, 1)
    pipe = construir_pipeline("catboost", 0, 1, multietiqueta=True, hiperparametros={"iterations": 10})
    Y = np.c_[(X[:, 0] > 0).astype(int), np.zeros(40, int)]
    pipe.fit(X, Y)
    assert len(pipe.predict_proba(X)) == 2


def test_xgboost_cpu_con_clases_no_contiguas():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(120, 4))
    y = np.repeat([2, 5, 9], 40)                       # etiquetas no contiguas, como en una particion
    X[:, 0] += y
    m = XGBoostGPU(gpu=None, parametros={"n_estimators": 20}).fit(X, y)
    assert list(m.classes_) == [2, 5, 9]
    assert m.predict_proba(X).shape == (120, 3)
    assert (m.predict(X) == y).mean() > 0.9


@pytest.mark.parametrize("multi", [False, True])
def test_todos_los_modelos_entrenan(multi):
    from src.models.registro_modelos import MODELOS
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 4))
    y = np.c_[(X[:, 0] > 0), (X[:, 1] > 0)].astype(int) if multi else (X[:, 0] > 0).astype(int) + (X[:, 1] > 1)
    rapidos = {"random_forest": {"n_estimators": 10}, "extra_trees": {"n_estimators": 10}, "lightgbm": {"n_estimators": 10},
               "xgboost": {"n_estimators": 10}, "catboost": {"iterations": 10}, "hist_gradient_boosting": {"max_iter": 10}}
    for nombre in MODELOS:
        pipe = construir_pipeline(nombre, 0, 1, multietiqueta=multi, hiperparametros=rapidos.get(nombre), n_variables=4)
        pipe.fit(X, y)
        assert pipe.predict_proba(X) is not None, nombre
