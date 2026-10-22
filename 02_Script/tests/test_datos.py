"""Pruebas de integridad sobre los datos reales de 01_Datos/Base (se omiten si no estan disponibles)."""
from conftest import requiere_datos


@requiere_datos
def test_sin_huerfanos_en_catalogos():
    from orquideas.data.relaciones import verificar_fks_catalogos
    t = verificar_fks_catalogos()
    assert int(t["huerfanos"].sum()) == 0


@requiere_datos
def test_vista_quimica_sin_replicas():
    from orquideas.data.dataset import cargar_dataset, vista_quimica
    assert len(vista_quimica()) < len(cargar_dataset())
    assert "ID_ACTIVIDAD_BIOLOGICA" not in vista_quimica().columns


@requiere_datos
def test_conjuntos_sin_variables_prohibidas():
    from orquideas.config.esquema import PROHIBIDAS_SIEMPRE
    from orquideas.features.conjuntos import construir
    for nombre, par in [("metabolito_modo", {}), ("perfil_muestra", {"objetivo": "ID_FAMILIA"}),
                        ("presencia_metabolitos", {})]:
        c = construir(nombre, par)
        assert len(c.X) == len(c.y) == len(c.grupos)
        assert not c.X.isna().any().any()
        malas = [col for col in c.X.columns for p in PROHIBIDAS_SIEMPRE if col.startswith(p)]
        assert not malas
        if "objetivo" in par:
            assert not any(col.startswith(par["objetivo"]) for col in c.X.columns)
            assert not any(col.startswith(par["objetivo"]) for col in c.X_instrumental.columns)
