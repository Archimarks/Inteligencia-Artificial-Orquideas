"""Lectura de los archivos de lote (xlsx, xls, csv, tsv) a una estructura comun: tabla de senales con los atributos
estandar y matriz de intensidades por muestra."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import quimica as q
from .curacion import Hoja, Lote

ATRIBUTOS_TEXTO = ["id", "nombre", "nombre_ms1", "etiqueta", "formula", "aducto", "modo", "nivel", "superclase", "clase", "subclase",
                   "clase2", "cas", "kegg", "hmdb", "pubchem", "chebi", "metlin", "lipidmaps", "inchikey", "inchikey2d", "inchi",
                   "smiles", "chemspider", "mwdb", "pmdb", "nist", "sinonimo", "plataforma", "fuente_anot"]
ATRIBUTOS_NUM = ["mz", "rt", "masa", "q3", "ri", "puntaje", "error_ppm"]
_SUFIJO_MUESTRA = re.compile(r"(\.mzML|\.mzXML|\.CDF|\.cdf|\.d|\.raw)?\s*Peak (height|area)\s*$", re.I)


@dataclass
class TablaLote:
    """Resultado de leer una hoja: una fila por senal y una columna de intensidad por muestra."""
    hoja: Hoja
    senales: pd.DataFrame
    valores: pd.DataFrame                    # mismas filas que `senales`, columnas = codigo de muestra
    contexto_muestra: dict[str, str] = field(default_factory=dict)  # codigo -> texto para las reglas
    avisos: list[str] = field(default_factory=list)


def limpiar_codigo_muestra(c: object) -> str:
    s = str(c).strip()
    s = _SUFIJO_MUESTRA.sub("", s).strip()
    return s


def _leer_crudo(ruta: Path, hoja: object) -> pd.DataFrame:
    if ruta.suffix.lower() == ".csv":
        return pd.read_csv(ruta, header=None, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig",
                           low_memory=False)
    with open(ruta, "rb") as fh:
        firma = fh.read(8)
    if not firma.startswith((b"PK", b"\xd0\xcf\x11\xe0")):  # texto con extension .xls (separado por tabuladores)
        return pd.read_csv(ruta, sep="\t", header=None, dtype=str, keep_default_na=False, na_values=[""], low_memory=False)
    return pd.read_excel(ruta, sheet_name=hoja, header=None, dtype=object)


def _unicos(nombres: list[str]) -> list[str]:
    vistos: dict[str, int] = {}
    out = []
    for n in nombres:
        if n in vistos:
            vistos[n] += 1
            out.append(f"{n}.{vistos[n]}")
        else:
            vistos[n] = 0
            out.append(n)
    return out


def _texto(v: object) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def _numero(v: object) -> float:
    """Convierte celdas a numero; acepta 'media±DE' (toma la media) y cadenas con espacios."""
    if v is None:
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = str(v).strip().replace("−", "-")
    if not s or s in ("-", "--", "/", "nan", "NA", "N/A"):
        return np.nan
    s = re.split(r"[±+](?=\s*\d)", s)[0] if "±" in s else s
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return np.nan


def _tabla_desde_crudo(crudo: pd.DataFrame, h: Hoja) -> tuple[pd.DataFrame, dict[str, dict[str, str]], list[str]]:
    """Convierte la hoja cruda en un DataFrame con nombres de columna; devuelve tambien metadatos por columna."""
    cab = [_texto(x) for x in crudo.iloc[h.cabecera].tolist()]
    inicio = h.cabecera + 1
    if h.fila_muestras is not None:
        fila = [_texto(x) for x in crudo.iloc[h.fila_muestras].tolist()]
        cab = [f if (f and (not c or c.lower() in ("nan",) or re.match(r"^(relative content|average relative)", c, re.I) or c == "")) else c
               for c, f in zip(cab, fila)]
        inicio = max(inicio, h.fila_muestras + 1)
    cab = [c if c else f"col_{j}" for j, c in enumerate(cab)]
    cab = _unicos(cab)
    meta: dict[str, dict[str, str]] = {}
    for attr, fila_meta in h.filas_meta.items():
        valores = [_texto(x) for x in crudo.iloc[fila_meta].tolist()]
        for c, v in zip(cab, valores):
            meta.setdefault(c, {})[attr] = v
    df = crudo.iloc[inicio:].copy()
    df.columns = cab
    df = df.reset_index(drop=True)
    return df, meta, cab


def _extraer(df: pd.DataFrame, h: Hoja, cols: dict[str, str], avisos: list[str], etiqueta: str) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for attr in ATRIBUTOS_TEXTO + ATRIBUTOS_NUM:
        col = cols.get(attr)
        if col is None:
            out[attr] = np.nan if attr in ATRIBUTOS_NUM else ""
            continue
        if col not in df.columns:
            norm = lambda x: re.sub(r"\s+", " ", x).strip().lower()
            alt = [c for c in df.columns if norm(c) == norm(col)]
            if not alt:
                avisos.append(f"{etiqueta}: no existe la columna '{col}' (atributo {attr})")
                out[attr] = np.nan if attr in ATRIBUTOS_NUM else ""
                continue
            col = alt[0]
        out[attr] = df[col].map(_numero) if attr in ATRIBUTOS_NUM else df[col].map(_texto)
    return out


def leer_hoja(base: Path, lote: Lote, h: Hoja, libro: dict[object, pd.DataFrame]) -> TablaLote:
    ruta = base / lote.archivo
    avisos: list[str] = []

    def crudo_de(nombre: object) -> pd.DataFrame:
        if nombre not in libro:
            libro[nombre] = _leer_crudo(ruta, nombre)
        return libro[nombre]

    partes_s, partes_v = [], []
    meta_total: dict[str, dict[str, str]] = {}
    for nombre in [h.hoja] + list(h.combinar):
        df, meta, cab = _tabla_desde_crudo(crudo_de(nombre), h)
        meta_total.update(meta)
        etiqueta = f"BAT{lote.id:04d}[{nombre}]"
        mapeadas = {v for v in h.cols.values()}
        rx, ex = re.compile(h.muestras), re.compile(h.excluir)
        cols_m = [c for c in df.columns if c not in mapeadas and rx.search(limpiar_codigo_muestra(c)) and not ex.search(c)]
        if not cols_m:
            avisos.append(f"{etiqueta}: ninguna columna de muestra coincide con {h.muestras!r}")
        for col, patron in h.saltar_si.items():
            if col in df.columns:
                df = df[~df[col].astype(str).str.strip().str.match(patron)]
        if h.filtro:
            col, patron = h.filtro
            df = df[df[col].astype(str).str.contains(patron, regex=True, na=False)]
        s = _extraer(df, h, h.cols, avisos, etiqueta)
        v = df[cols_m].apply(lambda c: c.map(_numero)).astype(float)
        v.columns = [limpiar_codigo_muestra(c) for c in cols_m]
        v = v.T.groupby(level=0).first().T if v.columns.duplicated().any() else v
        # filas totalmente vacias (separadores, notas al pie)
        vacias = (s["nombre"].eq("") & s["id"].eq("") & s["mz"].isna() & s["masa"].isna()) & v.isna().all(axis=1)
        s, v = s[~vacias], v[~vacias]
        s = s.assign(_hoja=str(nombre))
        partes_s.append(s)
        partes_v.append(v)
    senales = pd.concat(partes_s, ignore_index=True)
    valores = pd.concat(partes_v, ignore_index=True)
    if h.combinar:  # mismas senales repetidas en varias hojas: una fila por ID con todas las muestras disponibles
        clave = senales["id"].where(senales["id"].ne(""), senales["nombre"])
        valores = valores.groupby(clave.values).first()
        senales = senales.groupby(clave.values).first().loc[valores.index].reset_index(drop=True)
        valores = valores.reset_index(drop=True)
    if h.anotar_desde:
        senales = _anotar(senales, h, crudo_de, avisos, lote)
    contexto = {c: c + ("|" + "|".join(meta_total[c].values()) if c in meta_total else "") for c in valores.columns}
    # meta por columna se indexa por el nombre original; reconstruir con el codigo limpio
    if meta_total:
        limp = {limpiar_codigo_muestra(k): v for k, v in meta_total.items()}
        contexto = {c: c + ("|" + "|".join(limp[c].values()) if c in limp else "") for c in valores.columns}
    return TablaLote(h, senales.reset_index(drop=True), valores.reset_index(drop=True), contexto, avisos)


def _anotar(senales: pd.DataFrame, h: Hoja, crudo_de, avisos: list[str], lote: Lote) -> pd.DataFrame:
    partes = []
    for nombre in h.anotar_desde:
        cab = 0 if nombre == "SIRIUS" else h.cabecera
        hh = Hoja(nombre, cab, dict(h.cols_anotacion))
        df, _, _ = _tabla_desde_crudo(crudo_de(nombre), hh)
        partes.append(_extraer(df, hh, hh.cols, avisos, f"BAT{lote.id:04d}[{nombre}]"))
    an = pd.concat(partes, ignore_index=True)
    an = an[an["id"].ne("")]
    if h.clave_anotacion_modo:
        an["_modo"] = an["modo"].map(q.modo_desde_texto)
        an = an.drop_duplicates(["id", "_modo"])
        modo_hoja = q.modo_desde_texto(h.modo)
        claves = list(zip(senales["id"], [modo_hoja] * len(senales)))
        idx = {(i, m): k for k, (i, m) in enumerate(zip(an["id"], an["_modo"]))}
    else:
        an = an.drop_duplicates("id")
        claves = list(senales["id"])
        idx = {i: k for k, i in enumerate(an["id"])}
    pos = [idx.get(c) for c in claves]
    for attr in ATRIBUTOS_TEXTO + ATRIBUTOS_NUM:
        if attr in ("id", "modo") or attr not in an.columns:
            continue
        nuevos = [an[attr].iloc[p] if p is not None else (np.nan if attr in ATRIBUTOS_NUM else "") for p in pos]
        if attr in ATRIBUTOS_NUM:
            senales[attr] = senales[attr].where(senales[attr].notna(), pd.Series(nuevos, index=senales.index, dtype=float))
        else:
            actual = senales[attr].astype(str)
            senales[attr] = actual.where(actual.ne(""), pd.Series(nuevos, index=senales.index).fillna("").astype(str))
    return senales


def leer_lote(base: Path, lote: Lote) -> list[TablaLote]:
    libro: dict[object, pd.DataFrame] = {}
    tablas = [leer_hoja(base, lote, h, libro) for h in lote.hojas]
    if lote.metadatos_hoja:
        nombre, clave = lote.metadatos_hoja
        md = pd.read_excel(base / lote.archivo, sheet_name=nombre, dtype=str)
        md["_k"] = md[clave].astype(str).str.replace(r"\.d$", "", regex=True)
        cols = ["ATTRIBUTE_Sample_Type", "ATTRIBUTE_Cultivar", "ATTRIBUTE_Location", "ATTRIBUTE_Replicate"]
        texto = {r["_k"]: "|".join(_texto(r[c]) for c in cols) for _, r in md.iterrows()}
        for t in tablas:
            t.contexto_muestra = {c: c + ("|" + texto[c] if c in texto else "") for c in t.valores.columns}
    return tablas
