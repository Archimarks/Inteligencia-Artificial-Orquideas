"""Registro estructurado: la consola muestra el avance (INFO) y el archivo de la ejecucion guarda ademas el detalle
(DEBUG: archivos, columnas y lista completa de variables)."""
from __future__ import annotations

import logging
from pathlib import Path

_FMT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def obtener_logger(nombre: str = "orquideas", archivo: Path | None = None) -> logging.Logger:
    log = logging.getLogger(nombre)
    log.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in log.handlers):
        h = logging.StreamHandler()
        h.setLevel(logging.INFO)
        h.setFormatter(logging.Formatter(_FMT, "%H:%M:%S"))
        log.addHandler(h)
    if archivo is not None:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(archivo, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FMT))
        log.addHandler(fh)
    log.propagate = False
    return log


def cerrar_archivos(log: logging.Logger) -> None:
    for h in list(log.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            log.removeHandler(h)
