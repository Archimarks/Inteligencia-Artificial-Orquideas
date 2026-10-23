"""Prueba de extremo a extremo del flujo supervisado con datos sinteticos (no usa 01_Datos)."""
import logging

import numpy as np
import pandas as pd

from src.features.conjuntos import Conjunto
from src.tasks import supervisado


def _cfg():
    return {"id": "TEST", "semilla": 0, "n_jobs": 1,
            "split": {"strategy": "group_kfold", "n_splits": 4, "group_column": "G", "min_groups_per_class": 2,
                      "min_samples_per_class": 5},
            "evaluation": {"permutation_test": True, "n_permutations": 3, "confounding_control": True,
                           "evaluacion_optimista": True},
            "outputs": {"save_model": True, "save_predictions": True, "save_plots": False},
            "modelos": [{"nombre": "baseline_mayoritaria"}, {"nombre": "logistica"}]}


def _salida(tmp_path):
    d = {k: tmp_path / k for k in ["metricas", "predicciones", "graficas", "modelo", "tablas", "auditoria", "informes"]}
    for v in d.values():
        v.mkdir()
    return d


def test_senal_detectada(tmp_path):
    rng = np.random.default_rng(0)
    n = 240
    y = rng.integers(0, 2, n)
    X = pd.DataFrame({"x1": y * 2 + rng.normal(0, 0.5, n), "x2": rng.normal(size=n)})
    g = pd.Series(np.repeat(np.arange(12), 20), name="G")
    c = Conjunto("sint", X, pd.Series(y), g, "multiclase", {0: "A", 1: "B"}, pd.DataFrame({"i": range(n)}),
                 X_instrumental=pd.DataFrame({"ruido": rng.normal(size=n)}))
    r = supervisado.ejecutar(c, _cfg(), _salida(tmp_path), logging.getLogger("t"))
    assert r["estado"] == "completado"
    assert r["mejor_modelo"] == "logistica"
    assert r["valor_mejor"] > 0.9 > r["valor_control_instrumental"]
    assert (tmp_path / "modelo" / "modelo.joblib").exists()


def test_no_viable_si_clase_en_un_grupo(tmp_path):
    n = 60
    y = pd.Series([0] * 30 + [1] * 30)
    g = pd.Series([0] * 30 + [1] * 30, name="G")      # cada clase en un solo grupo
    c = Conjunto("sint", pd.DataFrame({"x": np.arange(n, dtype=float)}), y, g, "multiclase", {}, pd.DataFrame(index=range(n)))
    r = supervisado.ejecutar(c, _cfg(), _salida(tmp_path), logging.getLogger("t"))
    assert r["estado"] == "no_viable"


def test_multietiqueta(tmp_path):
    rng = np.random.default_rng(1)
    n = 200
    X = pd.DataFrame(rng.normal(size=(n, 3)), columns=list("abc"))
    Y = pd.DataFrame({"e1": (X["a"] > 0).astype(int), "e2": (X["b"] > 0.5).astype(int)})
    g = pd.Series(np.repeat(np.arange(10), 20), name="G")
    cfg = _cfg()
    cfg["modelos"] = [{"nombre": "baseline_prior"}, {"nombre": "random_forest", "hiperparametros": {"n_estimators": 50}}]
    c = Conjunto("sint", X, Y, g, "multietiqueta", {}, pd.DataFrame(index=range(n)))
    r = supervisado.ejecutar(c, cfg, _salida(tmp_path), logging.getLogger("t"))
    assert r["estado"] == "completado" and r["valor_mejor"] > r["valor_baseline"]
