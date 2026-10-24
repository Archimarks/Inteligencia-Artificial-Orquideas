"""Paralelismo: plan de ranuras, reparto de experimentos y resultados identicos a la ejecucion en serie."""
import os
import time

import numpy as np
import pytest

from src.evaluation.validacion import particiones
from src.tasks import supervisado
from src.utils import paralelo
from src.utils.paralelo import Ranura, ejecutar_experimentos, plan_ranuras


def test_auto_una_ranura_por_gpu_y_otra_de_cpu():
    r = plan_ranuras("auto", gpus=[0, 1], total_nucleos=8)
    assert [x.nombre for x in r] == ["GPU 0", "GPU 1", "CPU"]
    assert [x.gpus for x in r] == [(0,), (1,), ()]
    assert sum(x.nucleos for x in r) == 8 and r[2].nucleos >= r[0].nucleos


def test_auto_sin_gpu_o_pocos_nucleos():
    assert len(plan_ranuras("auto", gpus=[], total_nucleos=16)) == 1
    r = plan_ranuras("auto", gpus=[0, 1], total_nucleos=4)   # no alcanza para una ranura de CPU
    assert [x.nombre for x in r] == ["GPU 0", "GPU 1"]


def test_numero_fijo_y_secuencial():
    r = plan_ranuras(4, gpus=[0, 1], total_nucleos=8)
    assert [x.gpus for x in r] == [(0,), (1,), (), (0,)]
    assert len({x.nombre for x in r}) == 4 and sum(x.nucleos for x in r) == 8
    uno = plan_ranuras(1, gpus=[0, 1], total_nucleos=8)
    assert len(uno) == 1 and uno[0].gpus == (0, 1) and uno[0].nucleos == 8
    assert len(plan_ranuras(32, gpus=[], total_nucleos=3)) == 3


def _falso(identificador, etiqueta, ajustes, ranura):
    time.sleep(0.2)
    return {"id_experimento": identificador, "estado": "completado", "run_id": identificador,
            "_ranura": ranura.nombre, "_pid": os.getpid(), "_gpus": ranura.gpus}


def test_experimentos_en_procesos_paralelos():
    ranuras = [Ranura("GPU 0", (0,), 1), Ranura("CPU", (), 1)]
    vistos = []
    r = ejecutar_experimentos(["A", "B", "C"], ranuras=ranuras, trabajador=_falso, al_terminar=vistos.append)
    assert [x["id_experimento"] for x in r] == ["A", "B", "C"]
    assert len(vistos) == 3
    assert {x["_ranura"] for x in r} == {"GPU 0", "CPU"}
    assert all(x["_pid"] != os.getpid() for x in r)


def _datos(multi=False):
    rng = np.random.default_rng(1)
    n = 160
    g = np.repeat(np.arange(16), n // 16).astype(str)
    X = rng.normal(size=(n, 6))
    if multi:
        y = (X[:, :3] + rng.normal(scale=0.5, size=(n, 3)) > 0).astype(int)
        estr = y.argmax(1)
    else:
        y = (X[:, 0] + X[:, 1] > 0).astype(int) + (X[:, 2] > 1).astype(int)
        estr = y
    splits = particiones("group_kfold", estr, g, 4, 0, multi)
    return X, y, splits, (y.shape[1] if multi else 3)


@pytest.mark.parametrize("nombre", ["logistica", "random_forest", "xgboost"])
def test_particiones_en_paralelo_dan_lo_mismo(nombre):
    pytest.importorskip("xgboost") if nombre == "xgboost" else None
    X, y, splits, k = _datos()
    cols = [f"v{i}" for i in range(X.shape[1])]
    a = supervisado.validar_cruzado(nombre, {}, X, y, None, splits, "multiclase", k, 0, 2, None, cols, gpus=[],
                                    paralelo=False)
    b = supervisado.validar_cruzado(nombre, {}, X, y, None, splits, "multiclase", k, 0, 2, None, cols, gpus=[],
                                    paralelo=True)
    np.testing.assert_allclose(a[0], b[0], atol=1e-10)


@pytest.mark.parametrize("multi", [False, True])
def test_permutaciones_en_paralelo_dan_lo_mismo(monkeypatch, multi):
    X, y, splits, k = _datos(multi)
    tipo = "multietiqueta" if multi else "multiclase"
    principal = "average_precision_macro" if multi else "balanced_accuracy"
    cols = [f"v{i}" for i in range(X.shape[1])]
    monkeypatch.setattr(supervisado, "seleccionar_gpus", lambda: [])
    args = ("random_forest", {"hiperparametros": {"n_estimators": 30}}, X, y, None, splits, tipo, k, 0, 2, None, cols, 4,
            principal)
    monkeypatch.setattr(supervisado, "paralelo_interno", lambda: False)
    serie = supervisado.permutaciones(*args)
    monkeypatch.setattr(supervisado, "paralelo_interno", lambda: True)
    par = supervisado.permutaciones(*args)
    np.testing.assert_allclose(serie, par)


def test_cola_de_dispositivos_reparte_sin_repetir():
    import threading
    cola = paralelo.ColaDispositivos([[0], [1], []])
    en_uso, errores = [], []
    candado = threading.Lock()

    def tarea():
        with cola.tomar() as d:
            with candado:
                if d in en_uso:
                    errores.append(d)
                en_uso.append(d)
            time.sleep(0.01)
            with candado:
                en_uso.remove(d)
    hilos = [threading.Thread(target=tarea) for _ in range(12)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert not errores
