import copy

import pytest

from src.config.esquema import ErrorConfiguracion, cargar_config, listar_configs, validar, verificar_fuga


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
    from src.utils.rutas import carpeta_modelo, ruta_global, ruta_modelo
    assert carpeta_modelo("M01_modo_ionizacion") == "M01_Modo_Ionizacion"
    assert ruta_modelo("M01_modo_ionizacion", "metricas").parts[-3:] == ("Models", "M01_Modo_Ionizacion", "metricas")
    assert ruta_global().parts[-2:] == ("03_Resultados", "Global")


def test_puntero_lfs_detectado(tmp_path):
    from src.data.catalogos import ErrorDatos, verificar_archivo_datos
    p = tmp_path / "Dataset.csv"
    p.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 123\n")
    with pytest.raises(ErrorDatos, match="LFS"):
        verificar_archivo_datos(p)
    with pytest.raises(ErrorDatos, match="No existe"):
        verificar_archivo_datos(tmp_path / "no.csv")


def test_main_sin_argumentos_no_interactivo(capsys):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("main_orq", Path(__file__).resolve().parents[1] / "main.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.main(["listar"]) == 0
    assert "M01_modo_ionizacion" in capsys.readouterr().out
