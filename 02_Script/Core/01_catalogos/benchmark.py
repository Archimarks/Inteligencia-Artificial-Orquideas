#
# Archivo: benchmark.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Prueba de rendimiento del equipo: comprueba que CPU, RAM y cada GPU responden
# y rinden por encima de un minimo. El menu "Utilizar perfil" la corre y no deja
# elegir perfil si algo falla.
#
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .. import submodulo

config = submodulo("00_fundamentos.config")


# Resultado de probar un componente.
@dataclass
class Prueba:
    componente: str
    detalle: str
    ok: bool


# Multiplicacion de matrices en CPU: mide GFLOP/s.
def _prueba_cpu() -> Prueba:
    n = 2000
    a = np.random.rand(n, n)
    b = np.random.rand(n, n)
    inicio = time.perf_counter()
    for _ in range(3):
        a @ b
    segundos = (time.perf_counter() - inicio) / 3
    gflops = 2 * n ** 3 / segundos / 1e9
    return Prueba("CPU", f"{gflops:.0f} GFLOP/s ({segundos * 1000:.0f} ms/matmul {n}x{n})",
                  segundos < config.BENCH_CPU_MAX_SEG)


# Escritura repetida sobre un bloque grande: mide ancho de banda de RAM.
def _prueba_ram() -> Prueba:
    elementos = config.BENCH_RAM_MB * 1024 * 1024 // 8
    bloque = np.zeros(elementos, dtype=np.float64)
    inicio = time.perf_counter()
    for _ in range(5):
        bloque += 1.0
    segundos = (time.perf_counter() - inicio) / 5
    gbs = (bloque.nbytes / 1e9) / segundos
    return Prueba("RAM", f"{gbs:.1f} GB/s ({bloque.nbytes / 1e6:.0f} MB)",
                  gbs > config.BENCH_RAM_MIN_GBS)


# Multiplicacion de matrices en una GPU concreta: comprueba que responde.
def _prueba_gpu(indice: int) -> Prueba:
    try:
        import torch

        dispositivo = torch.device(f"cuda:{indice}")
        n = 3000
        a = torch.rand(n, n, device=dispositivo)
        b = torch.rand(n, n, device=dispositivo)
        torch.cuda.synchronize(dispositivo)
        inicio = time.perf_counter()
        for _ in range(5):
            a @ b
        torch.cuda.synchronize(dispositivo)
        segundos = (time.perf_counter() - inicio) / 5
        gflops = 2 * n ** 3 / segundos / 1e9
        nombre = torch.cuda.get_device_name(indice)
        del a, b
        torch.cuda.empty_cache()
        return Prueba(f"GPU {indice}", f"{nombre} - {gflops:.0f} GFLOP/s", True)
    except Exception as exc:
        return Prueba(f"GPU {indice}", f"fallo: {exc}", False)


# Corre todas las pruebas (CPU, RAM y cada GPU del equipo).
def ejecutar(equipo) -> list[Prueba]:
    pruebas = [_prueba_cpu(), _prueba_ram()]
    for gpu in equipo.gpus:
        pruebas.append(_prueba_gpu(gpu.indice))
    return pruebas
