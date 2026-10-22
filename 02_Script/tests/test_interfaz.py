"""Interfaz de consola: seleccion de modelos, ajustes del modo rapido y pantalla de entrenamiento (sin entrenar)."""
from orquideas.config.esquema import cargar_config, listar_configs
from orquideas.interfaz import consola


def _cfgs():
    c = [cargar_config(p) for p in listar_configs()]
    c.sort(key=lambda x: (consola._categoria(x["id"])[0], x["id"]))
    return c


def test_seleccion():
    cfgs = _cfgs()
    ids = lambda s: [c["id"].split("_")[0] for c in consola._interpretar_seleccion(s, cfgs)]  # noqa: E731
    assert len(consola._interpretar_seleccion("todos", cfgs)) == len(cfgs)
    assert ids("E") == ["M18"]
    assert ids("M05 m01") == ["M01", "M05"]                 # orden de la tabla, IDs sin distinguir mayusculas
    assert ids("1-3") == ["M01", "M08", "M09"]
    assert ids("xyz") == []


def test_ajustes_modo_rapido_y_algoritmos():
    cfg = cargar_config([p for p in listar_configs() if p.stem.startswith("M05")][0])
    aj = consola._ajustes(cfg, {"rapido": True, "algoritmos": ["xgboost"]})
    assert aj["evaluation"]["n_permutations"] == 0
    assert [m["nombre"] for m in aj["modelos"]] == ["baseline_mayoritaria", "baseline_estratificada", "xgboost"]
    assert consola._ajustes(cfg, {"rapido": False, "algoritmos": [m["nombre"] for m in cfg["modelos"]]}) is None


def test_pantalla_entrenamiento_sin_entrenar(monkeypatch):
    llamadas = []

    def falso(id_exp, etiqueta=None, ajustes=None):
        llamadas.append((id_exp, ajustes))
        return {"id_experimento": id_exp, "estado": "completado", "veredicto": "senal debil", "mejor_modelo": "xgboost",
                "metrica_principal": "balanced_accuracy", "valor_mejor": 0.5, "valor_baseline": 0.3}

    import orquideas.pipeline.ejecutor as ej
    import orquideas.pipeline.interpretacion as it
    monkeypatch.setattr(ej, "ejecutar_experimento", falso)
    # no tocar 03_Resultados ni 05_Documentacion durante la prueba
    monkeypatch.setattr(it, "guia_modelos", lambda df: None)
    monkeypatch.setattr(it, "resumen_ejecutivo", lambda df: None)
    monkeypatch.setattr(consola.Confirm, "ask", classmethod(lambda cls, *a, **k: False))
    cfgs = [c for c in _cfgs() if c["id"].startswith(("M01", "M18"))]
    consola.entrenar(cfgs, {"rapido": True, "algoritmos": ["xgboost"]})
    assert [x[0] for x in llamadas] == ["M01_modo_ionizacion", "M18_patrones_quimicos"]
    assert llamadas[1][1]["patrones"]["n_nulos"] == 50
