#
# Archivo: registro.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Logging centralizado. Un unico logger "ia" que siempre escribe a consola;
# cada entrenamiento le engancha ademas un archivo entrenamiento.log en su
# carpeta de resultados mientras dura, y lo desengancha al terminar.
#
from __future__ import annotations

import logging
import sys
from pathlib import Path

_NOMBRE = "ia"
_FORMATO = "%(asctime)s  %(levelname)-7s  %(message)s"
_FECHA_CONSOLA = "%H:%M:%S"
_logger: logging.Logger | None = None


# Devuelve el logger del proyecto, configurandolo la primera vez.
def obtener() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    log = logging.getLogger(_NOMBRE)
    log.setLevel(logging.INFO)
    log.propagate = False
    if not log.handlers:
        consola = logging.StreamHandler(sys.stdout)
        consola.setFormatter(logging.Formatter(_FORMATO, _FECHA_CONSOLA))
        log.addHandler(consola)

    _logger = log
    return log


# Engancha un archivo de log al logger y devuelve el handler creado.
def agregar_archivo(ruta: str | Path) -> logging.FileHandler:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(ruta, encoding="utf-8")
    handler.setFormatter(logging.Formatter(_FORMATO))
    obtener().addHandler(handler)
    return handler


# Desengancha y cierra un handler previamente devuelto por agregar_archivo.
def quitar_archivo(handler: logging.Handler | None) -> None:
    if handler is None:
        return
    obtener().removeHandler(handler)
    handler.close()
