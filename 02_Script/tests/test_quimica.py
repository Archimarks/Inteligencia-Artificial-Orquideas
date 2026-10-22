import math

import pandas as pd

from orquideas.features.quimica import descriptores, matriz_descriptores, parsear_formula


def test_parseo_basico():
    assert parsear_formula("C6H12O6") == {"C": 6, "H": 12, "O": 6}
    assert parsear_formula("C10H16N5O13P3") == {"C": 10, "H": 16, "N": 5, "O": 13, "P": 3}


def test_hidratos_y_sales():
    assert parsear_formula("C6H12O6.H2O") == {"C": 6, "H": 14, "O": 7}


def test_formulas_invalidas():
    for f in ["", None, "XYZ", "C27H41D3O3", "(C6H10O5)n", "H2O"]:
        assert parsear_formula(f) is None


def test_dbe_y_masa():
    assert descriptores("C6H6")["dbe"] == 4
    assert descriptores("C8H10N4O2")["dbe"] == 6          # cafeina
    assert math.isclose(descriptores("C6H12O6")["masa_formula"], 180.06339, abs_tol=1e-3)


def test_matriz_con_nan():
    m = matriz_descriptores(pd.Series(["C6H6", "basura", "C2H6O"]))
    assert m.shape[0] == 3 and m.iloc[1].isna().all() and m.iloc[0].notna().all()
