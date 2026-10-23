"""Huellas digitales (SHA-256) de archivos de entrada para trazabilidad."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .rutas import asegurar_dir, ruta


def sha256_archivo(p: Path, bloque: int = 1 << 22) -> str:
    """SHA-256 con cache por (ruta, tamano, fecha de modificacion) para no releer 500 MB en cada ejecucion."""
    st = p.stat()
    cache_f = asegurar_dir(ruta("salidas", "cache")) / "huellas.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    clave = f"{p.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    if clave in cache:
        return cache[clave]
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(bloque), b""):
            h.update(chunk)
    cache[clave] = h.hexdigest()
    cache_f.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return cache[clave]


def huellas_datos() -> dict[str, str]:
    """Huella de cada CSV de 01_Datos/Base."""
    base = ruta("datos", "base")
    return {str(p.relative_to(base)).replace("\\", "/"): sha256_archivo(p) for p in sorted(base.rglob("*.csv"))}
