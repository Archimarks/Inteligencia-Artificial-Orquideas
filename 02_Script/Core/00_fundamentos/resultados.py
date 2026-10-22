#
# Archivo: resultados.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Guardado de artefactos de entrenamiento bajo 03_Resultados/Models.
#
# Por entrenamiento se escribe, en <objetivo>/<modelo>/:
#     modelo.joblib   preprocesador.joblib (si aplica)   resumen.json
#     diagnostico.csv (si aplica)   entrenamiento.log   graficos/
# Y una fila por modelo en el leaderboard del objetivo:
#     <objetivo>/_leaderboard.csv
#
# En entrenamiento paralelo (Core.ejecutor) los workers difieren la escritura
# del leaderboard y el proceso padre lo reconstruye de una, sin carreras.
#
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

_diferido: bool = False
_log = logging.getLogger(__name__)


def _leer_leaderboard(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(ruta)
    except pd.errors.EmptyDataError:
        _log.warning(
            "El leaderboard existente está vacío y se reconstruirá: %s", ruta)
        return pd.DataFrame()


# Marca de tiempo AAAAMMDD_HHMMSS (informativa, va dentro de resumen.json).
def marca_tiempo() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# Prepara la carpeta de resultados de un entrenamiento (Supervisado y No
# supervisado comparten esta logica): la crea si falta y vacia su contenido
# previo. Se vacia el CONTENIDO pero no se borra la carpeta en si: en Windows,
# borrar y recrear el directorio deja carreras (Defender) que rompen escrituras
# posteriores.
def preparar_carpeta(carpeta: str | Path) -> Path:
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    for previo in carpeta.iterdir():
        if previo.is_dir():
            shutil.rmtree(previo, ignore_errors=True)
        else:
            previo.unlink(missing_ok=True)
    return carpeta


# Serializa un artefacto entrenado con joblib. `nombre` permite guardar
# transformadores auxiliares además del modelo principal. Devuelve la ruta.
def guardar_modelo(modelo: Any, carpeta: str | Path,
                   nombre: str = "modelo.joblib") -> Path:
    ruta = Path(carpeta) / nombre
    joblib.dump(modelo, ruta)
    return ruta


# Escribe datos como JSON legible (UTF-8, indentado).
def guardar_json(datos: dict, ruta: str | Path) -> Path:
    ruta = Path(ruta)
    ruta.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return ruta


# Activa/desactiva el modo diferido: mientras esta activo, actualizar_leaderboard
# no hace nada (lo reconstruye el padre). Es estado por-proceso.
def diferir_leaderboard(activo: bool = True) -> None:
    global _diferido
    _diferido = activo


# Fila del leaderboard a partir de un resumen de entrenamiento.
def fila_leaderboard(resumen: dict) -> dict:
    return {
        "modelo": resumen["modelo"],
        "dataset": resumen.get("dataset"),
        "archivo_fuente": resumen.get("archivo_fuente"),
        "dispositivo": resumen.get("dispositivo", "cpu"),
        "validacion": resumen["validacion"],
        "n_filas": resumen["n_filas"],
        "n_filas_dataset": resumen.get("n_filas_dataset", resumen["n_filas"]),
        "n_features": resumen["n_features"],
        "duracion_total_seg": resumen.get("duracion_total_seg"),
        "marca_tiempo": resumen["marca_tiempo"],
        **resumen["metricas"],
    }


# Deja una unica fila por modelo en el _leaderboard.csv del objetivo: si el
# modelo ya estaba, se reemplaza. No hace nada en modo diferido.
def actualizar_leaderboard(carpeta_objetivo: str | Path, fila: dict) -> Path | None:
    if _diferido:
        return None
    ruta = Path(carpeta_objetivo) / "_leaderboard.csv"
    previo = _leer_leaderboard(ruta)
    if not previo.empty and "modelo" in previo.columns:
        previo = previo[previo["modelo"] != fila["modelo"]]
    combinado = pd.concat([previo, pd.DataFrame([fila])], ignore_index=True)
    combinado.to_csv(ruta, index=False)
    return ruta


# Reescribe el _leaderboard.csv del objetivo: reemplaza las filas de los modelos
# recien entrenados y conserva las del resto. Lo llama el padre tras el paralelo.
def reconstruir_leaderboard(carpeta_objetivo: str | Path, resumenes: list[dict],
                            modelos_fallidos: list[str] | None = None) -> Path:
    ruta = Path(carpeta_objetivo) / "_leaderboard.csv"
    previo = _leer_leaderboard(ruta)
    nuevos = {r["modelo"] for r in resumenes} | set(modelos_fallidos or ())
    if not previo.empty and "modelo" in previo.columns:
        previo = previo[~previo["modelo"].isin(nuevos)]
    filas = pd.DataFrame([fila_leaderboard(r) for r in resumenes])
    pd.concat([previo, filas], ignore_index=True).to_csv(ruta, index=False)
    return ruta
