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
import shutil
import subprocess
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


def seleccionar_gpus(hardware: dict[str, Any] | None = None, detectadas: list[dict[str, Any]] | None = None) -> list[int]:
    """Indices de GPU que se usaran para entrenar, segun config_global.yaml (hardware)."""
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
