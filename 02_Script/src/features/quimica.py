"""Descriptores elementales derivados de la formula molecular.

Se usan como variables de entrada para predecir propiedades del compuesto (superclase, clase, modo, aducto,
actividad) sin depender de la anotacion del laboratorio. No se usan m/z ni masa del aducto: m/z - masa codifica
directamente el aducto y el modo (fuga de informacion).
"""
from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
import pandas as pd

MASA_ISOTOPO = {  # masa monoisotopica del isotopo mas abundante
    "C": 12.0, "H": 1.0078250319, "N": 14.0030740052, "O": 15.9949146221, "P": 30.97376151, "S": 31.97207069,
    "F": 18.99840320, "Cl": 34.96885271, "Br": 78.9183376, "I": 126.904468, "Si": 27.9769265327, "Na": 22.98976966,
    "K": 38.9637069, "B": 11.0093055, "Se": 79.9165218, "Fe": 55.9349421, "Mg": 23.98504187, "Ca": 39.9625912,
    "Cu": 62.9296011, "Zn": 63.9291466, "Co": 58.9332002, "As": 74.9215964, "Al": 26.98153841, "Mn": 54.9380496,
}
TETRAVALENTES = {"C", "Si"}
MONOVALENTES = {"H", "F", "Cl", "Br", "I", "Na", "K"}
TRIVALENTES = {"N", "P", "B", "As"}
ELEMENTOS_BASE = ["C", "H", "N", "O", "P", "S", "F", "Cl", "Br", "I"]
_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)")
_LIMPIA = re.compile(r"[\s\[\]+\-]|(?<=\d)\.(?=\d)")


@lru_cache(maxsize=200_000)
def parsear_formula(formula: str) -> dict[str, int] | None:
    """'C6H12O6' -> {'C': 6, 'H': 12, 'O': 6}. Devuelve None si la formula no es interpretable.

    Acepta hidratos/sales separados por '.' (se suman) y descarta cargas (+/-) y corchetes.
    """
    if not isinstance(formula, str) or not formula.strip():
        return None
    f = formula.strip()
    if "(" in f or "*" in f:  # formulas de polimeros o con grupos repetidos no se expanden
        return None
    cuenta: dict[str, int] = {}
    for parte in f.split("."):
        parte = _LIMPIA.sub("", parte)
        mult = 1
        m = re.match(r"^(\d+)(.*)$", parte)
        if m:
            mult, parte = int(m.group(1)), m.group(2)
        pos = 0
        for el, n in _TOKEN.findall(parte):
            if el not in MASA_ISOTOPO:
                return None
            cuenta[el] = cuenta.get(el, 0) + mult * (int(n) if n else 1)
            pos += len(el) + len(n)
        if pos != len(parte):
            return None
    return cuenta if cuenta.get("C", 0) > 0 else None


def descriptores(formula: str) -> dict[str, float] | None:
    c = parsear_formula(formula)
    if c is None:
        return None
    d: dict[str, float] = {f"n_{e}": float(c.get(e, 0)) for e in ELEMENTOS_BASE}
    otros = sum(v for k, v in c.items() if k not in ELEMENTOS_BASE)
    d["n_otros"] = float(otros)
    nC = c.get("C", 0)
    # Dobles enlaces equivalentes: 1 + sum(n_i (v_i - 2)) / 2; O y S divalentes no contribuyen
    dbe = 1 + sum(n for el, n in c.items() if el in TETRAVALENTES) \
        - sum(n for el, n in c.items() if el in MONOVALENTES) / 2 + sum(n for el, n in c.items() if el in TRIVALENTES) / 2
    d["dbe"] = dbe
    d["masa_formula"] = sum(MASA_ISOTOPO[el] * n for el, n in c.items())
    d["n_atomos_pesados"] = float(sum(n for el, n in c.items() if el != "H"))
    for e in ["H", "O", "N", "S", "P"]:
        d[f"{e}_C"] = c.get(e, 0) / nC
    d["dbe_C"] = dbe / nC
    d["heteroatomos"] = float(sum(n for el, n in c.items() if el not in ("C", "H")))
    d["halogenado"] = float(any(c.get(e, 0) for e in ("F", "Cl", "Br", "I")))
    # Indice de aromaticidad modificado (Koch y Dittmar 2006)
    den = nC - 0.5 * c.get("O", 0) - c.get("S", 0) - c.get("N", 0) - c.get("P", 0)
    num = 1 + nC - 0.5 * c.get("O", 0) - c.get("S", 0) - 0.5 * (c.get("H", 0) + c.get("N", 0) + c.get("P", 0))
    d["ai_mod"] = float(np.clip(num / den, 0, 1)) if den > 0 else 0.0
    d["regla_nitrogeno_par"] = float(round(d["masa_formula"]) % 2 == 0)
    return d


def matriz_descriptores(formulas: pd.Series) -> pd.DataFrame:
    """Descriptores para una serie de formulas; filas no interpretables quedan con NaN."""
    unicas = formulas.fillna("").astype(str).unique()
    tabla = {f: descriptores(f) for f in unicas}
    cols = list(next((v for v in tabla.values() if v), descriptores("CH4")).keys())
    filas = [tabla[f] if tabla[f] else dict.fromkeys(cols, np.nan) for f in formulas.fillna("").astype(str)]
    return pd.DataFrame(filas, index=formulas.index, columns=cols)
