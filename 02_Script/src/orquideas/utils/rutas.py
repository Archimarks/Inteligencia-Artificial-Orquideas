"""Resolucion centralizada de rutas (compatible con Windows mediante pathlib)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parents[3]          # .../02_Script
CONFIG_DIR = SCRIPT_DIR / "config"


@lru_cache(maxsize=1)
def config_rutas() -> dict[str, Any]:
    with open(CONFIG_DIR / "rutas.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def config_global() -> dict[str, Any]:
    with open(CONFIG_DIR / "config_global.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def raiz_proyecto() -> Path:
    raiz = config_rutas().get("raiz_proyecto", "auto")
    return SCRIPT_DIR.parent if raiz in (None, "auto") else Path(raiz)


def ruta(seccion: str, clave: str) -> Path:
    """Devuelve la ruta absoluta configurada en rutas.yaml (seccion.clave)."""
    valor = config_rutas()[seccion][clave]
    p = Path(valor)
    return p if p.is_absolute() else raiz_proyecto() / p


def asegurar_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p
