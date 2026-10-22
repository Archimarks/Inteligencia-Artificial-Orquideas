#
# Archivo: perfiles.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Perfil de hardware de la sesion: que dispositivos usar para entrenar.
#
# Se elige desde el menu ("Utilizar perfil") despues de analizar el equipo y
# pasar la prueba de rendimiento. Sin perfil activo no se permite entrenar
# (Core.entrenamiento_base y la interfaz lo verifican). El estado es de sesion:
# al reiniciar hay que volver a elegirlo.
#
# Que usa GPU cuando el perfil la incluye:
#     - xgboost  (device=cuda:N)   -> requiere xgboost 2.1.x y GPU compute >= 6.0
#     - catboost (task_type=GPU)
#     - torch    (deep learning, a futuro)
# scikit-learn (random_forest, knn, svm, ridge, ...) y el wheel de pip de
# lightgbm son solo CPU: no hay forma de acelerarlos con GPU en este entorno.
#
from __future__ import annotations

from dataclasses import dataclass


# Perfil elegido.
#     dispositivos: indices de GPU a usar; lista vacia = solo CPU.
#     n_jobs: hilos para los modelos de scikit-learn (-1 = todos).
@dataclass
class Perfil:
    nombre: str
    dispositivos: list[int]
    n_jobs: int = -1

    @property
    def usa_gpu(self) -> bool:
        return bool(self.dispositivos)


_activo: Perfil | None = None
_turno: int = 0


# Perfil activo, o None si todavia no se eligio.
def activo() -> Perfil | None:
    return _activo


# Fija el perfil activo de la sesion.
def establecer(perfil: Perfil) -> None:
    global _activo, _turno
    _activo = perfil
    _turno = 0


# Devuelve el perfil activo o lanza si no hay ninguno.
def requerido() -> Perfil:
    if _activo is None:
        raise RuntimeError(
            "No hay perfil de hardware. Usa el menu 'Utilizar perfil' antes de entrenar.")
    return _activo


# Siguiente GPU del perfil, en rotacion (reparte modelos entre varias GPU).
def _siguiente_gpu() -> int:
    global _turno
    dispositivos = _activo.dispositivos
    gpu = dispositivos[_turno % len(dispositivos)]
    _turno += 1
    return gpu


# True si la GPU tiene capacidad de computo suficiente para XGBoost (>= 6.0).
def _gpu_apta_xgboost(indice: int) -> bool:
    try:
        import torch

        mayor, _ = torch.cuda.get_device_capability(indice)
        return mayor >= 6
    except Exception:
        return False


# Dispositivo torch para los modelos hechos a mano ("cuda:N" repartido entre las
# GPU del perfil, o "cpu").
def device_torch() -> str:
    if _activo is None or not _activo.usa_gpu:
        return "cpu"
    return f"cuda:{_siguiente_gpu()}"


# kwargs de GPU para el constructor de una libreria de boosting.
# Devuelve {} (CPU) si el perfil es CPU o la libreria/GPU no lo soporta aqui.
def kwargs_boost(libreria: str) -> dict:
    if _activo is None or not _activo.usa_gpu:
        return {}
    gpu = _siguiente_gpu()
    if libreria == "xgboost":
        return {"device": f"cuda:{gpu}"} if _gpu_apta_xgboost(gpu) else {}
    if libreria == "catboost":
        return {"task_type": "GPU", "devices": str(gpu)}
    return {}


# Dispositivo real de un estimador ya construido: "cuda:N" o "cpu".
# Sirve para registrar en el log y en resumen.json donde corrio cada modelo.
def dispositivo_de(estimador) -> str:
    pasos = getattr(estimador, "steps", None)
    nucleo = pasos[-1][1] if pasos else estimador
    params = nucleo.get_params() if hasattr(nucleo, "get_params") else {}
    device = str(params.get("device") or "")
    if device.startswith("cuda"):
        return device
    if params.get("task_type") == "GPU":
        return f"cuda:{params.get('devices', '0')}"
    return "cpu"
