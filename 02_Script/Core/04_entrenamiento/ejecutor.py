#
# Archivo: ejecutor.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Entrena varios modelos A LA VEZ, usando TODO el equipo (no se turnan):
#   - los modelos que aceptan GPU (xgboost, catboost) se fijan a una GPU del
#     perfil, con un candado por GPU para que no se pisen (a lo sumo uno por GPU
#     al mismo tiempo);
#   - el resto (scikit-learn, lightgbm) corre en varios procesos de CPU.
# Todo en un unico pool de procesos: mientras las GPU entrenan sus modelos, la
# CPU entrena los suyos en paralelo.
#
# Cada worker es un proceso aislado (loky): fija su propio perfil y difiere la
# escritura del leaderboard; el proceso padre lo reconstruye al final.
#
from __future__ import annotations

import os
import json
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from joblib import Parallel, delayed

from .. import submodulo

perfiles = submodulo("00_fundamentos.perfiles")
registro = submodulo("00_fundamentos.registro")
resultados = submodulo("00_fundamentos.resultados")
rutas = submodulo("00_fundamentos.rutas")

# Modelos que corren en GPU: los boosting con soporte CUDA y los hechos a mano en
# PyTorch (sufijo _gpu).
_MODELOS_GPU = {"xgboost", "catboost"}


def _usa_gpu(modelo: str) -> bool:
    return modelo in _MODELOS_GPU or "_gpu" in modelo

# Espera maxima por el candado de una GPU antes de asumir que quedo huerfano.
_TIMEOUT_CANDADO_SEG = 900


# Procesos para los modelos de CPU (deja nucleos para el paralelismo interno).
def _procesos_cpu() -> int:
    return max(2, (os.cpu_count() or 4) // 3)


# Toma un candado exclusivo de la GPU `indice` (spin sobre un archivo). Si el
# candado lleva demasiado tiempo tomado se asume huerfano y se fuerza.
def _tomar_candado(indice: int):
    ruta = Path(tempfile.gettempdir()) / f"ia_gpu_{indice}.lock"
    inicio = time.time()
    while True:
        try:
            return os.open(str(ruta), os.O_CREAT | os.O_EXCL | os.O_RDWR), ruta
        except FileExistsError:
            if time.time() - inicio > _TIMEOUT_CANDADO_SEG:
                try:
                    ruta.unlink()
                except OSError:
                    pass
            time.sleep(0.3)


def _soltar_candado(fd: int, ruta: Path) -> None:
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        ruta.unlink()
    except OSError:
        pass


# Proceso worker aislado: fija el perfil del dispositivo que le toca, toma
# el candado si es GPU, y entrena un modelo. Devuelve el resumen o un dict "error".
def _worker(paradigma: str, tarea: str, objetivo: str, modelo: str,
            dispositivos: list[int]) -> dict:
    from Core import submodulo
    _perf = submodulo("00_fundamentos.perfiles")
    _res = submodulo("00_fundamentos.resultados")
    from Entrenamiento import para

    _perf.establecer(_perf.Perfil(f"worker {dispositivos or 'cpu'}", list(dispositivos)))
    _res.diferir_leaderboard(True)

    candado = _tomar_candado(dispositivos[0]) if dispositivos else None
    try:
        return para(paradigma).entrenar(paradigma, tarea, objetivo, modelo)
    except Exception as exc:
        return {"error": str(exc), "tipo_error": type(exc).__name__,
                "traceback": traceback.format_exc(),
                "modelo": modelo, "tarea": tarea, "objetivo": objetivo}
    finally:
        if candado is not None:
            _soltar_candado(*candado)


# Entrena todos los modelos de cada (tarea, objetivo) de `combos` a la vez,
# repartidos entre GPU(s) y CPU. Reconstruye el leaderboard de cada objetivo al
# final. Devuelve resultados completados y fallidos; los fallos se guardan para
# que la interfaz y los informes globales expliquen el estado de cada modelo.
def entrenar_plan(paradigma: str, combos: list[tuple[str, str]],
                  modelos_de: Callable[[str], list[str]]) -> list[dict]:
    perfil = perfiles.requerido()
    gpus = list(perfil.dispositivos)
    log = registro.obtener()

    tareas_gpu: list[tuple] = []
    tareas_cpu: list[tuple] = []
    turno = 0
    for tarea, objetivo in combos:
        for modelo in modelos_de(tarea):
            if gpus and _usa_gpu(modelo):
                tareas_gpu.append((paradigma, tarea, objetivo, modelo,
                                   [gpus[turno % len(gpus)]]))
                turno += 1
            else:
                tareas_cpu.append((paradigma, tarea, objetivo, modelo, []))

    # GPU primero: arrancan enseguida y su candado limita la concurrencia por tarjeta.
    tareas = tareas_gpu + tareas_cpu
    n_procesos = (len(gpus) or 0) + _procesos_cpu()
    log.info("Paralelo: %d modelos en GPU %s + %d en CPU, %d procesos, todo a la vez",
             len(tareas_gpu), gpus or "-", len(tareas_cpu), n_procesos)

    salida = Parallel(n_jobs=n_procesos, backend="loky")(
        delayed(_worker)(*tarea) for tarea in tareas)

    resumenes = [r for r in salida if r and "error" not in r]
    for r in salida:
        if r and "error" in r:
            recomendacion = (
                "DBSCAN no encontró estructura de densidad evaluable con las "
                "configuraciones probadas. Compare KMeans/Agglomerative; revise "
                "cobertura, dimensionalidad y métrica de distancia antes de ajustar "
                "epsilon."
                if r["modelo"] == "dbscan" and r["tarea"] == "Clustering" else
                "Revise error.log para el traceback completo. Compruebe los datos, "
                "parámetros y dependencias indicados en el mensaje.")
            carpeta = rutas.carpeta_resultados(
                paradigma, r["tarea"], r["objetivo"], r["modelo"])
            resultados.preparar_carpeta(carpeta)
            fallo = {
                "estado": "FALLIDO",
                "paradigma": paradigma,
                "tarea": r["tarea"],
                "objetivo": r["objetivo"],
                "modelo": r["modelo"],
                "archivo_fuente": (
                    "04_Dataset_Patrones_Quimicos_Unificado.csv"
                    if r["objetivo"] == "PATRONES_QUIMICOS"
                    and (rutas.DATOS / "Dataset" /
                         "04_Dataset_Patrones_Quimicos_Unificado.csv").is_file()
                    else None
                ),
                "tipo_error": r.get("tipo_error", "Error"),
                "error": r["error"],
                "recomendacion": recomendacion,
                "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
                "traceback": r.get("traceback", ""),
                "directorio_resultados": str(carpeta.relative_to(rutas.RAIZ)),
            }
            (carpeta / "error.json").write_text(
                json.dumps(fallo, ensure_ascii=False, indent=2), encoding="utf-8")
            (carpeta / "error.log").write_text(
                f"{fallo['fecha']} | {fallo['tipo_error']}: {fallo['error']}\n\n"
                f"{fallo['traceback']}", encoding="utf-8")
            r["estado"] = "FALLIDO"
            r["archivo_fuente"] = fallo["archivo_fuente"]
            r["recomendacion"] = recomendacion
            r["directorio_resultados"] = fallo["directorio_resultados"]
            log.error(
                "Modelo '%s' (%s/%s) falló [%s]. Detalle: %s. Resultado: %s",
                r["modelo"], r["tarea"], r["objetivo"], fallo["tipo_error"],
                r["error"].rstrip(". "), carpeta / "error.json")

    for tarea, objetivo in combos:
        del_combo = [r for r in resumenes
                     if r["tarea"] == tarea and r["objetivo"] == objetivo]
        resultados.reconstruir_leaderboard(
            rutas.carpeta_objetivo_resultados(paradigma, tarea, objetivo), del_combo,
            modelos_fallidos=[
                r["modelo"] for r in salida
                if r and "error" in r and r["tarea"] == tarea and r["objetivo"] == objetivo
            ])

    return resumenes + [r for r in salida if r and "error" in r]
