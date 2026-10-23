"""Deteccion de GPU NVIDIA y politica de uso para el entrenamiento.

Se detectan todas las GPU con `nvidia-smi` (incluido con el controlador NVIDIA en Windows y Linux; no requiere
librerias adicionales). La configuracion `hardware` de config_global.yaml decide cuales usar:

    hardware:
      usar_gpu: auto      # auto = usar GPU si hay alguna | si = exigir GPU | no = solo CPU
      gpus: todas         # todas | lista de indices, p. ej. [0, 1]

Uso por modelo:
- CatBoost entrena cada modelo con todas las GPU seleccionadas a la vez (devices="0:1").
- XGBoost usa una GPU por modelo; las particiones de la validacion cruzada (y las permutaciones) se reparten entre
  todas las GPU y se entrenan en paralelo, una por GPU.
- LightGBM (wheel de pip), Random Forest, regresion logistica y KNN se entrenan en CPU con todos los nucleos.
`CUDA_VISIBLE_DEVICES` se respeta si esta definida.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from functools import lru_cache
from typing import Any

from .rutas import config_global


class ErrorGPU(RuntimeError):
    """Se exigio GPU (usar_gpu: si) y no hay ninguna disponible."""


def _consultar_nvidia_smi() -> list[dict[str, Any]]:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return []
    campos = ["index", "name", "memory.total", "compute_cap", "driver_version"]
    for intento in (campos, campos[:3] + campos[4:]):   # compute_cap no existe en controladores antiguos
        try:
            out = subprocess.run([exe, f"--query-gpu={','.join(intento)}", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            return []
        if out.returncode == 0 and out.stdout.strip():
            gpus = []
            for linea in out.stdout.strip().splitlines():
                v = [x.strip() for x in linea.split(",")]
                d = dict(zip(intento, v))
                gpus.append({"indice": int(d["index"]), "nombre": d["name"],
                             "memoria_mb": int(float(d["memory.total"])) if d["memory.total"].replace(".", "").isdigit() else None,
                             "compute_capability": d.get("compute_cap"), "driver": d.get("driver_version")})
            return gpus
    return []


@lru_cache(maxsize=1)
def detectar_gpus() -> list[dict[str, Any]]:
    """Todas las GPU NVIDIA visibles para este proceso."""
    gpus = _consultar_nvidia_smi()
    visibles = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visibles is not None and visibles.strip() != "":
        permitidas = [int(x) for x in visibles.split(",") if x.strip().lstrip("-").isdigit() and int(x) >= 0]
        gpus = [g for g in gpus if g["indice"] in permitidas]
        # CUDA renumera las GPU visibles desde 0
        gpus = [{**g, "indice_fisico": g["indice"], "indice": i} for i, g in enumerate(gpus)]
    return gpus


_GPUS_SESION: list[int] | None = None


def establecer_gpus_sesion(indices: list[int] | None) -> None:
    """Fija las GPU de esta sesion (la interfaz lo usa tras elegir la maquina); None vuelve a config_global.yaml."""
    global _GPUS_SESION
    _GPUS_SESION = None if indices is None else list(indices)


def seleccionar_gpus(hardware: dict[str, Any] | None = None, detectadas: list[dict[str, Any]] | None = None) -> list[int]:
    """Indices de GPU que se usaran para entrenar: la eleccion de la sesion (interfaz) o config_global.yaml."""
    if hardware is None and detectadas is None and _GPUS_SESION is not None:
        return list(_GPUS_SESION)
    hw = hardware if hardware is not None else config_global().get("hardware", {})
    detectadas = detectar_gpus() if detectadas is None else detectadas
    modo = str(hw.get("usar_gpu", "auto")).lower()
    if modo in ("no", "false", "0", "cpu"):
        return []
    indices = [g["indice"] for g in detectadas]
    pedidas = hw.get("gpus", "todas")
    if isinstance(pedidas, list):
        indices = [i for i in indices if i in pedidas]
    if not indices and modo in ("si", "true", "1", "gpu"):
        raise ErrorGPU("config_global.yaml exige GPU (hardware.usar_gpu: si) pero no se detecto ninguna GPU NVIDIA "
                       "con nvidia-smi. Instale el controlador NVIDIA o use usar_gpu: auto.")
    return indices


def resumen_hardware() -> dict[str, Any]:
    return {"cpu_nucleos": os.cpu_count(), "gpus": detectar_gpus(), "gpus_usadas": seleccionar_gpus()}



def nombre_cpu() -> str:
    if platform.system() == "Windows":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as fh:
            for linea in fh:
                if linea.lower().startswith("model name"):
                    return linea.split(":", 1)[1].strip()
    except OSError:
        pass
    if platform.system() == "Darwin":
        try:
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True,
                                  timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or platform.machine() or "desconocido"


def memoria_ram_gb() -> tuple[float | None, float | None]:
    """(total, disponible) en GB, sin dependencias externas."""
    try:
        if platform.system() == "Windows":
            import ctypes

            class _Estado(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            e = _Estado()
            e.dwLength = ctypes.sizeof(_Estado)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))
            return round(e.ullTotalPhys / 2**30, 1), round(e.ullAvailPhys / 2**30, 1)
        info = {}
        with open("/proc/meminfo", encoding="utf-8") as fh:
            for linea in fh:
                k, v = linea.split(":", 1)
                info[k] = int(v.split()[0])
        return round(info["MemTotal"] / 2**20, 1), round(info.get("MemAvailable", 0) / 2**20, 1)
    except Exception:  # noqa: BLE001
        return None, None


def probar_gpu(indice: int) -> tuple[bool, str]:
    """Entrena un XGBoost diminuto en la GPU `indice` para comprobar que CUDA funciona de verdad."""
    import importlib.util
    if importlib.util.find_spec("xgboost") is None:
        return False, "xgboost no instalado"
    try:
        import warnings

        import numpy as np
        from xgboost import XGBClassifier
        rng = np.random.default_rng(0)
        X = rng.normal(size=(2000, 10))
        y = (X[:, 0] > 0).astype(int)
        t = time.time()
        # XGBoost no falla si no puede usar la GPU: avisa y sigue en CPU. Se registran los avisos y se comprueba
        # el dispositivo que realmente uso.
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            m = XGBClassifier(n_estimators=20, device=f"cuda:{indice}", tree_method="hist").fit(X, y)
        textos = " ".join(str(a.message) for a in avisos)
        import json
        dispositivo = json.loads(m.get_booster().save_config())["learner"]["generic_param"].get("device", "")
        for clave in ("not compiled with CUDA", "No visible GPU", "setting device to CPU", "Falling back"):
            if clave.lower() in textos.lower():
                return False, f"XGBoost no pudo usar la GPU ({clave})"
        if not str(dispositivo).startswith("cuda"):
            return False, f"XGBoost entreno en '{dispositivo}', no en la GPU"
        return True, f"XGBoost en {dispositivo} OK ({time.time() - t:.1f} s)"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e).splitlines()[0][:90]}"


def descripcion_equipo() -> dict[str, Any]:
    total, libre = memoria_ram_gb()
    return {"cpu": nombre_cpu(), "nucleos_logicos": os.cpu_count(), "ram_total_gb": total, "ram_libre_gb": libre,
            "sistema": f"{platform.system()} {platform.release()}", "python": platform.python_version(),
            "gpus": detectar_gpus()}
