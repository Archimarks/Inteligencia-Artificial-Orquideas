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


# --- bloque estructurado: supervisado / no supervisado ---------------------------------------------------------------
def test_yaml_supervisado_y_no_supervisado():
    for p in listar_configs():
        c = cargar_config(p)
        de = c["datos_entrenamiento"]
        if c["tarea"] == "supervisado":
            assert de["tipo_aprendizaje"] == "supervisado" and de["objetivo"] and de["grupos_validacion"], p.name
            assert fuentes._computado(c, "y") == [de["objetivo"]], p.name
        else:
            assert de["tipo_aprendizaje"] == "no_supervisado" and "objetivo" not in de, p.name
        assert not fuentes.avisos_declaracion(c), p.name


def test_objetivo_se_toma_de_datos_entrenamiento():
    c = _cfg("M05")
    assert c["conjunto"]["parametros"]["objetivo"] == "ID_FAMILIA" == c["datos_entrenamiento"]["objetivo"]
    crudo = copy.deepcopy(c)
    crudo["datos_entrenamiento"]["objetivo"] = "ID_ORDEN"
    crudo["conjunto"]["parametros"].pop("objetivo")
    for a in crudo["datos_entrenamiento"]["archivos"].values():
        if "objetivo" in a:
            a["objetivo"] = ["ID_ORDEN"]
    validar(crudo, "<config>")
    assert crudo["conjunto"]["parametros"]["objetivo"] == "ID_ORDEN"


@pytest.mark.parametrize("cambio, mensaje", [
    (lambda de: de.__setitem__("objetivo", "ID_ORDEN"), "contradice|usa"),
    (lambda de: de.__setitem__("tipo_aprendizaje", "no_supervisado"), "no corresponde"),
    (lambda de: de.pop("objetivo"), "falta datos_entrenamiento.objetivo"),
    (lambda de: de["archivos"]["dataset"]["entrada"].append("ID_ADUCTO"), "no sabe usar"),
    (lambda de: de["archivos"]["dataset"].__setitem__("factores_contraste", ["ID_ORDEN"]), "no aplica"),
])
def test_errores_supervisado(cambio, mensaje):
    c = _cfg("M05")
    cambio(c["datos_entrenamiento"])
    with pytest.raises(ErrorConfiguracion, match=mensaje):
        validar(c, "<config>")


def test_no_supervisado_sin_objetivo():
    c = _cfg("M18")
    c["datos_entrenamiento"]["objetivo"] = "ID_FAMILIA"
    with pytest.raises(ErrorConfiguracion, match="no tiene variable objetivo"):
        validar(c, "<config>")


def _perfil() -> Conjunto:
    X = pd.DataFrame(np.ones((4, 3)), columns=["clase_1", "clase_2", "clase_otras"])
    Xi = pd.DataFrame(np.ones((4, 3)), columns=["ID_INSTRUMENTO_3", "MODOS_1", "log_n_senales"])
    return Conjunto("p", X, pd.Series([1, 2, 1, 2], name="ID_FAMILIA"), pd.Series(list("aabb"), name="ID_ARTICULO"),
                    "multiclase", {}, pd.DataFrame(index=X.index), X_instrumental=Xi)


def test_quitar_columnas_de_entrada_y_control():
    c = _cfg("M05")
    ds = c["datos_entrenamiento"]["archivos"]["dataset"]
    ds["control_instrumental"].remove("ID_INSTRUMENTO")
    conj = _perfil()
    assert fuentes.aplicar_declaracion(conj, c) == []
    assert list(conj.X_instrumental.columns) == ["MODOS_1", "log_n_senales"]
    ds["entrada"].remove("ID_METABOLITO")   # estructural: no genera variables propias
    with pytest.raises(ErrorConfiguracion, match="necesita"):
        fuentes.aplicar_declaracion(_perfil(), c)
    ds["entrada"] = ["ID_METABOLITO"]       # quitar ID_CLASE_QUIMICA deja X vacia
    with pytest.raises(ErrorConfiguracion, match="ninguna variable"):
        fuentes.aplicar_declaracion(_perfil(), c)


def test_quitar_superclase_de_entrada():
    c = _cfg("M10")
    c["datos_entrenamiento"]["archivos"]["dataset"]["entrada"].remove("ID_SUPERCLASE_QUIMICA")
    validar(c, "<config>")
    conj = _conjunto()
    assert fuentes.aplicar_declaracion(conj, c) == ["ID_SUPERCLASE_QUIMICA_1", "ID_SUPERCLASE_QUIMICA_2"]
    assert "ID_SUPERCLASE_QUIMICA" not in fuentes.roles_efectivos(c)["dataset"]["X"]


def test_escribir_yaml_es_idempotente_y_conserva_cambios(tmp_path):
    origen = [p for p in listar_configs() if p.stem.startswith("M10")][0]
    destino = tmp_path / origen.name
    texto = origen.read_text(encoding="utf-8").replace(
        "entrada: [FORMULA_MOLECULAR, ID_MODO_IONIZACION, ID_SUPERCLASE_QUIMICA]",
        "entrada: [FORMULA_MOLECULAR, ID_MODO_IONIZACION]")
    destino.write_text(texto, encoding="utf-8")
    cfg = cargar_config(destino)
    assert not fuentes.escribir_yaml(destino, cfg)
    assert "entrada: [FORMULA_MOLECULAR, ID_MODO_IONIZACION]\n" in destino.read_text(encoding="utf-8")
    assert fuentes.escribir_yaml(destino, cfg, completo=True)
    assert "ID_SUPERCLASE_QUIMICA]" in destino.read_text(encoding="utf-8")
    cargar_config(destino)
