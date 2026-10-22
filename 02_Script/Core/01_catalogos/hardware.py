#
# Archivo: hardware.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Escaneo del equipo: CPU, RAM y GPUs. Lo usa el menu "Utilizar perfil" para
# mostrar de que hardware se dispone antes de la prueba de rendimiento.
#
from __future__ import annotations

import platform
from dataclasses import dataclass, field

import psutil

from .. import submodulo

registro = submodulo("00_fundamentos.registro")
_log = registro.obtener()


# Una GPU CUDA detectada.
@dataclass
class GPU:
    indice: int
    nombre: str
    memoria_gb: float


# Resumen del equipo.
@dataclass
class Equipo:
    cpu_nombre: str
    cpu_nucleos_fisicos: int
    cpu_nucleos_logicos: int
    ram_total_gb: float
    ram_disponible_gb: float
    cuda_disponible: bool
    gpus: list[GPU] = field(default_factory=list)


# Escanea el equipo y devuelve un Equipo. torch se importa aca dentro para no
# pagar su arranque salvo cuando se abre el menu de perfil.

def escanear() -> Equipo:
    memoria = psutil.virtual_memory()

    cuda = False
    gpus: list[GPU] = []

    try:
        import torch

        _log.info("[DETECCIÓN GPU]")
        _log.info("  PyTorch:          %s", torch.__version__)
        _log.info("  CUDA PyTorch:     %s", torch.version.cuda)
        _log.info("  CUDA disponible:  %s", torch.cuda.is_available())
        _log.info("  GPU detectadas:   %s", torch.cuda.device_count())

        if torch.cuda.is_available():
            cantidad = torch.cuda.device_count()

            for i in range(cantidad):
                propiedades = torch.cuda.get_device_properties(i)

                gpu = GPU(
                    indice=i,
                    nombre=propiedades.name,
                    memoria_gb=round(
                        propiedades.total_memory / (1024 ** 3),
                        1,
                    ),
                )

                gpus.append(gpu)

                _log.info("  GPU %d: %s (%.1f GB)", i, gpu.nombre, gpu.memoria_gb)

            cuda = len(gpus) > 0

        else:
            _log.warning("  [AVISO] PyTorch no puede utilizar CUDA.")

            if torch.version.cuda is None:
                _log.warning("  [AVISO] Esta instalación de PyTorch no incluye CUDA.")

    except ImportError:
        _log.error("[ERROR] PyTorch no está instalado.")
        _log.error("       Instala PyTorch para utilizar las GPU CUDA.")

    except Exception as e:
        _log.error("[ERROR DETECTANDO GPU]")
        _log.error("  %s: %s", type(e).__name__, e)

    return Equipo(
        cpu_nombre=(
            platform.processor()
            or platform.machine()
            or "desconocida"
        ),
        cpu_nucleos_fisicos=psutil.cpu_count(logical=False) or 0,
        cpu_nucleos_logicos=psutil.cpu_count(logical=True) or 0,
        ram_total_gb=round(memoria.total / (1024 ** 3), 1),
        ram_disponible_gb=round(memoria.available / (1024 ** 3), 1),
        cuda_disponible=cuda,
        gpus=gpus,
    )