import copy

import numpy as np
import pandas as pd
import pytest

from src.config.esquema import ErrorConfiguracion, cargar_config, listar_configs, validar
from src.data.catalogos import ARCHIVOS_FIJADOS, ruta_archivo
from src.features import fuentes
from src.features.conjuntos import Conjunto


def _cfg(prefijo: str) -> dict:
    return copy.deepcopy(cargar_config([p for p in listar_configs() if p.stem.startswith(prefijo)][0]))


def test_cada_yaml_declara_los_archivos_que_usa():
    for p in listar_configs():
        c = cargar_config(p)
        declarados = set(fuentes.archivos_configurados(c))
        usados = set(fuentes.columnas_origen(c))
        assert usados, p.name
        assert usados <= declarados, f"{p.name}: faltan en datos_entrenamiento.archivos {usados - declarados}"


def test_columnas_origen_por_rol():
    co = fuentes.columnas_origen(_cfg("M05"))
    assert co["dataset"]["y"] == ["ID_FAMILIA"]
    assert co["dataset"]["grupos"] == ["ID_ARTICULO"]
    assert "ID_CLASE_QUIMICA" in co["dataset"]["X"]
    co = fuentes.columnas_origen(_cfg("M09"))
    assert co["metabolitos"]["X"] == ["FORMULA_MOLECULAR"] and co["clases_quim"]["y"] == ["ID_CLASE_QUIMICA"]


def test_columna_de_variable():
    assert fuentes.columna_de_variable("ID_FAMILIA_6") == "ID_FAMILIA"
    assert fuentes.columna_de_variable("ID_SUPERCLASE_QUIMICA_3") == "ID_SUPERCLASE_QUIMICA"
    assert fuentes.columna_de_variable("clase_240") == "ID_CLASE_QUIMICA"
    assert fuentes.columna_de_variable("superclase_otras") == "ID_SUPERCLASE_QUIMICA"
    assert fuentes.columna_de_variable("dbe") == "FORMULA_MOLECULAR"
    assert fuentes.columna_de_variable("H_C") == "FORMULA_MOLECULAR"


def _conjunto() -> Conjunto:
    X = pd.DataFrame(np.ones((4, 4)), columns=["dbe", "n_C", "ID_SUPERCLASE_QUIMICA_1", "ID_SUPERCLASE_QUIMICA_2"])
    return Conjunto("prueba", X, pd.Series([1, 2, 1, 2], name="ID_ADUCTO"), pd.Series(list("aabb"), name="ID_ARTICULO"),
                    "multiclase", {}, pd.DataFrame(index=X.index))


def test_seleccion_de_variables_por_columna_de_origen_y_comodin():
    cfg = {"id": "X", "datos_entrenamiento": {"variables": {"excluir": ["ID_SUPERCLASE_QUIMICA"]}}}
    conj = _conjunto()
    assert fuentes.seleccionar_variables(conj, cfg) == ["ID_SUPERCLASE_QUIMICA_1", "ID_SUPERCLASE_QUIMICA_2"]
    assert list(conj.X.columns) == ["dbe", "n_C"]
    conj = _conjunto()
    fuentes.seleccionar_variables(conj, {"id": "X", "datos_entrenamiento": {"variables": {"incluir": ["n_*"]}}})
    assert list(conj.X.columns) == ["n_C"]
    with pytest.raises(ErrorConfiguracion, match="ninguna variable"):
        fuentes.seleccionar_variables(_conjunto(), {"id": "X", "datos_entrenamiento": {"variables": {"incluir": ["zzz"]}}})


def test_sin_seleccion_no_cambia_nada():
    conj = _conjunto()
    assert fuentes.seleccionar_variables(conj, {"id": "X"}) == []
    assert conj.X.shape[1] == 4


def test_validacion_del_bloque():
    c = _cfg("M05")
    c["datos_entrenamiento"]["archivos"]["inventado"] = "x.csv"
    with pytest.raises(ErrorConfiguracion, match="inventado"):
        validar(c, "<config>")
    c = _cfg("M05")
    c["datos_entrenamiento"]["variables"]["excluir"] = "ID_FAMILIA"
    with pytest.raises(ErrorConfiguracion, match="lista"):
        validar(c, "<config>")


def test_fijar_archivos_cambia_la_ruta_y_se_restablece(tmp_path):
    c = _cfg("M05")
    original = ruta_archivo("dataset")
    c["datos_entrenamiento"]["archivos"]["dataset"] = str(tmp_path / "otro.csv")
    try:
        fuentes.fijar_archivos(c)
        assert ruta_archivo("dataset") == tmp_path / "otro.csv"
    finally:
        fuentes.fijar_archivos(_cfg("M05"))
    assert ruta_archivo("dataset") == original and not ARCHIVOS_FIJADOS


def test_describir_y_texto():
    c = _cfg("M10")
    d = fuentes.describir(c, _conjunto(), [])
    assert {a["nombre"] for a in d["archivos"]} >= {"dataset"}
    t = fuentes.texto(d)
    assert "Archivo dataset" in t and "FORMULA_MOLECULAR" in t and "Variables de entrada usadas" in t
    assert "| `dbe` |" in fuentes.markdown(d)
