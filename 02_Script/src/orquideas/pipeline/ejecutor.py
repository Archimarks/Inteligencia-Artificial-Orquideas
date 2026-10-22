"""Ejecucion reproducible de un experimento: run id, carpetas, manifiesto, huellas, registro e informe."""
from __future__ import annotations

import platform
import random
import subprocess
import sys
import time
import traceback
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config.esquema import ErrorConfiguracion, buscar_config, cargar_config, verificar_fuga
from ..utils.es import guardar_json, guardar_yaml, leer_json
from ..utils.huella import huellas_datos
from ..utils.registro import cerrar_archivos, obtener_logger
from ..utils.gpu import resumen_hardware
from ..utils.rutas import asegurar_dir, raiz_proyecto, ruta, ruta_modelo
from . import interpretacion

PAQUETES = ["pandas", "numpy", "scikit-learn", "scipy", "lightgbm", "xgboost", "catboost", "mlxtend", "networkx", "umap-learn", "matplotlib",
            "seaborn", "pyarrow", "PyYAML", "joblib", "statsmodels"]


def versiones() -> dict[str, str]:
    out = {"python": sys.version.split()[0], "plataforma": platform.platform()}
    for p in PAQUETES:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = "no instalado"
    return out


def _commit_git() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=raiz_proyecto(), capture_output=True, text=True,
                              timeout=5).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def preparar_salidas(cfg: dict[str, Any], run_id: str) -> dict[str, Path]:
    """Carpetas de la ejecucion dentro de 03_Resultados/Models/<Modelo>/ (una subcarpeta <run_id> en cada una)."""
    dirs = {
        "ejecucion": ruta_modelo(cfg["id"], "ejecuciones") / run_id,
        "auditoria": ruta_modelo(cfg["id"], "auditoria_datos") / run_id,
        "metricas": ruta_modelo(cfg["id"], "metricas") / run_id,
        "predicciones": ruta_modelo(cfg["id"], "predicciones") / run_id,
        "graficas": ruta_modelo(cfg["id"], "graficas") / run_id,
        "modelo": ruta_modelo(cfg["id"], "modelo_entrenado") / run_id,
        "informes": ruta_modelo(cfg["id"], "informes"),
    }
    # tablas de datos del modelo (distribucion de clases, descartes) -> auditoria; tablas de hallazgos (M18) -> metricas
    dirs["tablas"] = dirs["auditoria"] if cfg["tarea"] == "supervisado" else dirs["metricas"]
    if dirs["ejecucion"].exists() and not cfg["outputs"].get("overwrite", False):
        raise FileExistsError(f"La ejecucion {run_id} ya existe y overwrite=false")
    for d in dirs.values():
        asegurar_dir(d)
    return dirs


def ejecutar_experimento(identificador: str | Path, etiqueta: str | None = None) -> dict[str, Any]:
    p = Path(identificador) if str(identificador).endswith(".yaml") else buscar_config(str(identificador))
    cfg = cargar_config(p)
    inicio = datetime.now()
    run_id = f"{inicio:%Y%m%d-%H%M%S}_{cfg['id']}_{cfg['_huella'][:8]}" + (f"_{etiqueta}" if etiqueta else "")
    salida = preparar_salidas(cfg, run_id)
    log = obtener_logger(f"orquideas.{run_id}", salida["ejecucion"] / "ejecucion.log")
    random.seed(cfg["semilla"])
    np.random.seed(cfg["semilla"])
    log.info(f"Ejecucion {run_id} | {cfg['nombre']}")
    hw = resumen_hardware()
    log.info(f"Hardware: {hw['cpu_nucleos']} nucleos CPU; GPU detectadas: {len(hw['gpus'])}"
             + "".join(f" | GPU {g['indice']}: {g['nombre']} ({g['memoria_mb']} MB)" for g in hw["gpus"])
             + f"; GPU usadas para entrenar: {hw['gpus_usadas'] or 'ninguna'}")
    guardar_yaml({k: v for k, v in cfg.items() if not k.startswith("_")}, salida["ejecucion"] / "config_resuelta.yaml")
    manifiesto: dict[str, Any] = {
        "run_id": run_id, "id_experimento": cfg["id"], "nombre": cfg["nombre"], "archivo_config": cfg["_archivo"],
        "huella_config": cfg["_huella"], "inicio": inicio.isoformat(timespec="seconds"), "semilla": cfg["semilla"],
        "huellas_datos": huellas_datos(), "versiones": versiones(), "commit_git": _commit_git(),
        "hardware": resumen_hardware(),
        "salidas": {k: str(v) for k, v in salida.items()},
    }
    t0 = time.time()
    try:
        if cfg["tarea"] == "supervisado":
            from ..features.conjuntos import construir
            from ..tasks import supervisado
            conj = construir(cfg["conjunto"]["nombre"], cfg["conjunto"].get("parametros", {}))
            verificar_fuga(cfg, list(conj.X.columns),
                           list(conj.X_instrumental.columns) if conj.X_instrumental is not None else None)
            resultado = supervisado.ejecutar(conj, cfg, salida, log)
        else:
            from ..tasks import patrones
            resultado = patrones.ejecutar(cfg, salida, log)
        manifiesto["estado"] = resultado.get("estado", "completado")
    except ErrorConfiguracion:
        raise
    except Exception as e:  # noqa: BLE001
        log.error(traceback.format_exc())
        resultado = {"estado": "error", "motivo": f"{type(e).__name__}: {e}"}
        manifiesto["estado"] = "error"
    manifiesto["fin"] = datetime.now().isoformat(timespec="seconds")
    manifiesto["segundos"] = round(time.time() - t0, 1)
    resultado["run_id"] = run_id
    resultado["id_experimento"] = cfg["id"]
    guardar_json(resultado, salida["ejecucion"] / "resultado.json")
    guardar_json(manifiesto, salida["ejecucion"] / "manifiesto.json")
    interpretacion.escribir_informe(cfg, resultado, manifiesto, salida)
    log.info(f"Estado: {manifiesto['estado']} ({manifiesto['segundos']} s). Informe: {salida['ejecucion'] / 'informe.md'}")
    cerrar_archivos(log)
    return resultado


def ultimas_ejecuciones() -> pd.DataFrame:
    """Ultima ejecucion de cada experimento (segun la fecha de inicio del run id)."""
    filas = []
    for d in sorted(ruta("salidas", "modelos").glob("*/ejecuciones/*/resultado.json")):
        r = interpretacion.completar(leer_json(d), d.parent)
        man = leer_json(d.parent / "manifiesto.json")
        filas.append({**r, "inicio": man.get("inicio"), "_dir": str(d.parent)})
    if not filas:
        return pd.DataFrame()
    df = pd.DataFrame(filas).sort_values("inicio")
    return df.groupby("id_experimento").tail(1).sort_values("id_experimento").reset_index(drop=True)
