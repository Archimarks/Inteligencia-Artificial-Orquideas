"""Entrada/salida de JSON, YAML y tablas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


class _Codificador(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return None if np.isnan(o) else float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (Path,)):
            return str(o)
        if isinstance(o, (pd.Timestamp,)):
            return o.isoformat()
        return super().default(o)


def guardar_json(obj: Any, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, cls=_Codificador), encoding="utf-8")


def leer_json(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def guardar_yaml(obj: Any, p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(obj, allow_unicode=True, sort_keys=False), encoding="utf-8")


def leer_yaml(p: Path) -> Any:
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def guardar_tabla(df: pd.DataFrame, p: Path, index: bool = False) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, sep=";", index=index, encoding="utf-8-sig")
