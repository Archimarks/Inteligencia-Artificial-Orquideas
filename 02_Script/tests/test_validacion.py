import numpy as np
import pandas as pd
import pytest

from src.evaluation.validacion import filtrar_clases, filtrar_etiquetas, particiones


def test_filtrar_clases_por_grupos():
    y = pd.Series(["a"] * 20 + ["b"] * 20 + ["c"] * 20)
    g = pd.Series([1] * 10 + [2] * 10 + [3] * 20 + [4] * 10 + [5] * 10)   # b vive en un solo grupo
    f = filtrar_clases(y, g, min_grupos=2, min_unidades=5)
    assert set(f.conservadas) == {"a", "c"}
    assert f.descartadas["clase"].tolist() == ["b"]
    assert f.mascara.sum() == 40


def test_filtrar_etiquetas_sin_negativos():
    Y = pd.DataFrame({"x": [1] * 10, "y": [1, 0] * 5})
    f = filtrar_etiquetas(Y, pd.Series(range(10)), min_grupos=2, min_unidades=2)
    assert f.conservadas == ["y"]


@pytest.mark.parametrize("estrategia", ["group_kfold", "leave_one_group_out"])
def test_particiones_sin_fuga(estrategia):
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(12), 10).astype(str)
    y = rng.integers(0, 3, len(g))
    for tr, te in particiones(estrategia, y, g, 5, 0):
        assert not set(g[tr]) & set(g[te])


def test_particiones_multietiqueta():
    g = np.repeat(np.arange(8), 5).astype(str)
    sp = particiones("group_kfold", np.zeros(len(g)), g, 4, 0, multietiqueta=True)
    assert len(sp) == 4
    assert sorted(np.concatenate([te for _, te in sp]).tolist()) == list(range(len(g)))
