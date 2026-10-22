import numpy as np
import pandas as pd

from orquideas.features.perfiles import clr


def test_clr_centrado_e_invariante_a_escala():
    c = pd.DataFrame([[1, 2, 7], [10, 20, 70]], columns=list("abc"))
    x = clr(c, pseudo=0)
    assert np.allclose(x.sum(axis=1), 0)
    assert np.allclose(x.iloc[0], x.iloc[1])
