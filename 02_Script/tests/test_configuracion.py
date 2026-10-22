import copy

import pytest

from orquideas.config.esquema import ErrorConfiguracion, cargar_config, listar_configs, validar, verificar_fuga


def test_todas_las_configs_validas():
    rutas = listar_configs()
    assert len(rutas) >= 18
    for p in rutas:
        cargar_config(p)


def _base():
    return copy.deepcopy(cargar_config([p for p in listar_configs() if p.stem.startswith("M05")][0]))


def test_sin_baseline_falla():
    c = _base()
    c["modelos"] = [{"nombre": "random_forest"}]
    with pytest.raises(ErrorConfiguracion, match="baseline"):
        validar(c, "<config>")


def test_modelo_desconocido_falla():
    c = _base()
    c["modelos"].append({"nombre": "red_magica"})
    with pytest.raises(ErrorConfiguracion, match="red_magica"):
        validar(c, "<config>")


def test_split_sin_grupos_rechazado():
    c = _base()
    c["split"]["strategy"] = "stratified_kfold"
    with pytest.raises(ErrorConfiguracion, match="fuga"):
        validar(c, "<config>")


def test_deteccion_fuga():
    c = _base()
    with pytest.raises(ErrorConfiguracion, match="Fuga"):
        verificar_fuga(c, ["clase_1", "ID_FAMILIA_3"])
    with pytest.raises(ErrorConfiguracion, match="Fuga"):
        verificar_fuga(c, ["RELACION_MASA_CARGA"])
    verificar_fuga(c, ["clase_1", "clase_otras"])


def test_carpetas_por_modelo():
    from orquideas.utils.rutas import carpeta_modelo, ruta_global, ruta_modelo
    assert carpeta_modelo("M01_modo_ionizacion") == "M01_Modo_Ionizacion"
    assert ruta_modelo("M01_modo_ionizacion", "metricas").parts[-3:] == ("Models", "M01_Modo_Ionizacion", "metricas")
    assert ruta_global().parts[-2:] == ("03_Resultados", "Global")
