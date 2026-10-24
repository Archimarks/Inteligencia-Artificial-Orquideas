"""Construye las 40 tablas de 01_Datos/Dataset a partir de los lotes (01_Datos/Data/Batch) y la curacion de los
articulos (`curacion.py`, `referencias.py`).

Convenciones: separador ';', UTF-8 (catalogos con BOM, Dataset.csv sin BOM), todas las columnas ID_* enteras y el
ID 0 significa "No especificado". En 07_Metabolitos el ID 1 es "Senal no identificada". Las intensidades iguales a
0, vacias o con el marcador de no detectado del laboratorio no se guardan (no detectado).
"""
from __future__ import annotations

import csv
import math
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from . import quimica as q
from . import referencias as ref
from .curacion import (ACT_ESPECIE, ACT_METABOLITO, ARTICULOS, ESPECIES_ARTICULO, LOTES, MEDICIONES, Lote,
                       interpretar_muestra)
from .lectores import TablaLote, leer_lote

NE = "No especificado"
ND = "No disponible"

# ------------------------------------------------------------------------------------------------ esquema de salida
ARCHIVOS: dict[str, tuple[str, list[str]]] = {
    "articulos": ("01_Trazabilidad/01_Articulos.csv", ["ID_ARTICULO", "CODIGO_ARTICULO", "ARCHIVO_ARTICULO", "TITULO", "AUTOR_PRINCIPAL", "REVISTA", "ANIO_PUBLICACION", "DOI", "ENFOQUE_METABOLOMICO", "TIPO_FUENTE", "OBJETIVO", "REPOSITORIO_DATOS", "DATOS_CRUDOS", "N_BATCHES", "N_ESPECIES", "DESCRIPCION"]),
    "batches": ("01_Trazabilidad/02_Batches.csv", ["ID_BATCH", "ID_ARTICULO", "CODIGO_BATCH", "ARCHIVO_BATCH", "HOJAS_UTILIZADAS", "MODOS_IONIZACION", "ID_TECNICA_SEPARACION", "ID_COLUMNA_CROMATOGRAFICA", "ID_INSTRUMENTO", "ID_MODO_ADQUISICION", "ID_TIPO_INTENSIDAD", "FASE_MOVIL", "FLUJO", "VOLTAJE_CAPILAR", "TEMPERATURA_FUENTE", "N_MUESTRAS", "N_SENALES", "N_SENALES_ANOTADAS", "N_INTENSIDADES", "DESCRIPCION"]),
    "reinos": ("02_Taxonomia/01_Reinos.csv", ["ID_REINO", "REINO", "DESCRIPCION"]),
    "filos": ("02_Taxonomia/02_Filos.csv", ["ID_FILO", "ID_REINO", "FILO", "DESCRIPCION"]),
    "clases_tax": ("02_Taxonomia/03_Clases_taxonomicas.csv", ["ID_CLASE_TAXONOMICA", "ID_FILO", "CLASE_TAXONOMICA", "DESCRIPCION"]),
    "ordenes": ("02_Taxonomia/04_Ordenes.csv", ["ID_ORDEN", "ID_CLASE_TAXONOMICA", "ORDEN", "DESCRIPCION"]),
    "familias": ("02_Taxonomia/05_Familias.csv", ["ID_FAMILIA", "ID_ORDEN", "FAMILIA", "DESCRIPCION"]),
    "generos": ("02_Taxonomia/06_Generos.csv", ["ID_GENERO", "ID_FAMILIA", "GENERO", "DESCRIPCION"]),
    "especies": ("02_Taxonomia/07_Especies.csv", ["ID_ESPECIE", "ID_GENERO", "NOMBRE_CIENTIFICO", "AUTORIDAD", "NOMBRE_COMUN", "ES_ORQUIDEA", "DESCRIPCION"]),
    "ubicaciones": ("03_Geografia/01_Ubicaciones.csv", ["ID_UBICACION", "PAIS", "REGION", "LOCALIDAD", "LATITUD", "LONGITUD", "ALTITUD_M", "DESCRIPCION"]),
    "tipos_muestra": ("04_Muestra/01_Tipos_muestra.csv", ["ID_TIPO_MUESTRA", "TIPO_MUESTRA", "DESCRIPCION"]),
    "partes": ("04_Muestra/02_Partes_planta_estudiadas.csv", ["ID_PARTE_ESTUDIADA", "PARTE_PLANTA_ESTUDIADA", "DESCRIPCION"]),
    "cultivos": ("04_Muestra/03_Tipos_cultivo.csv", ["ID_TIPO_CULTIVO", "TIPO_CULTIVO", "DESCRIPCION"]),
    "metodos": ("04_Muestra/04_Metodos_extraccion.csv", ["ID_METODO_EXTRACCION", "METODO_EXTRACCION", "ID_SOLVENTE", "COMPOSICION_SOLVENTE", "TECNICA_EXTRACCION", "DESCRIPCION"]),
    "solventes": ("04_Muestra/05_Solventes.csv", ["ID_SOLVENTE", "SOLVENTE", "FORMULA", "INDICE_POLARIDAD", "DESCRIPCION"]),
    "modos": ("05_Plataforma_analitica/01_Modos_ionizacion.csv", ["ID_MODO_IONIZACION", "MODO_IONIZACION", "DESCRIPCION"]),
    "tecnicas": ("05_Plataforma_analitica/02_Tecnicas_separacion.csv", ["ID_TECNICA_SEPARACION", "TECNICA_SEPARACION", "DESCRIPCION"]),
    "columnas": ("05_Plataforma_analitica/03_Columnas_cromatograficas.csv", ["ID_COLUMNA_CROMATOGRAFICA", "COLUMNA_CROMATOGRAFICA", "FASE_ESTACIONARIA", "FABRICANTE", "LONGITUD_MM", "DIAMETRO_MM", "TAMANO_PARTICULA_UM", "DESCRIPCION"]),
    "adquisicion": ("05_Plataforma_analitica/04_Modos_adquisicion.csv", ["ID_MODO_ADQUISICION", "MODO_ADQUISICION", "DESCRIPCION"]),
    "analizadores": ("05_Plataforma_analitica/05_Analizadores.csv", ["ID_ANALIZADOR", "ANALIZADOR", "DESCRIPCION"]),
    "instrumentos": ("05_Plataforma_analitica/06_Instrumentos.csv", ["ID_INSTRUMENTO", "INSTRUMENTO", "SISTEMA_CROMATOGRAFICO", "FABRICANTE", "ID_ANALIZADOR", "DESCRIPCION"]),
    "tipos_intensidad": ("05_Plataforma_analitica/07_Tipos_intensidad.csv", ["ID_TIPO_INTENSIDAD", "TIPO_INTENSIDAD", "DESCRIPCION"]),
    "niveles": ("06_Quimica_Analitica/01_Niveles_identificacion.csv", ["ID_NIVEL_IDENTIFICACION", "NIVEL_IDENTIFICACION", "DESCRIPCION"]),
    "superclases": ("06_Quimica_Analitica/02_Superclases_quimicas.csv", ["ID_SUPERCLASE_QUIMICA", "SUPERCLASE_QUIMICA", "DESCRIPCION"]),
    "clases_quim": ("06_Quimica_Analitica/03_Clases_quimicas.csv", ["ID_CLASE_QUIMICA", "ID_SUPERCLASE_QUIMICA", "CLASE_QUIMICA", "DESCRIPCION"]),
    "aductos": ("06_Quimica_Analitica/04_Aductos.csv", ["ID_ADUCTO", "ADUCTO", "ID_MODO_IONIZACION", "CARGA", "MULTIPLICADOR_M", "DELTA_MASA", "DESCRIPCION"]),
    "metabolitos": ("07_Metabolitos/01_Metabolitos.csv", ["ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR", "MASA_MONOISOTOPICA", "ID_CLASE_QUIMICA", "ID_SUPERCLASE_QUIMICA", "INCHIKEY", "N_BATCHES", "N_SENALES", "DESCRIPCION"]),
    "sinonimos": ("07_Metabolitos/02_Sinonimos_metabolitos.csv", ["ID_SINONIMO", "ID_METABOLITO", "SINONIMO", "TIPO_SINONIMO", "ID_BATCH"]),
    "identificadores": ("07_Metabolitos/03_Identificadores_externos.csv", ["ID_IDENTIFICADOR", "ID_METABOLITO", "BASE_DATOS", "IDENTIFICADOR", "ID_BATCH"]),
    "categorias": ("08_Actividad_biologica/01_Categorias_actividad.csv", ["ID_CATEGORIA_ACTIVIDAD", "CATEGORIA_ACTIVIDAD", "DESCRIPCION"]),
    "actividades": ("08_Actividad_biologica/02_Actividades_biologicas.csv", ["ID_ACTIVIDAD_BIOLOGICA", "ID_CATEGORIA_ACTIVIDAD", "ACTIVIDAD_BIOLOGICA", "DESCRIPCION"]),
    "muestras": ("09_Hechos/01_Muestras.csv", ["ID_MUESTRA", "ID_BATCH", "CODIGO_MUESTRA", "ID_ESPECIE", "ID_PARTE_ESTUDIADA", "ID_TIPO_MUESTRA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION", "ID_UBICACION", "GRUPO_EXPERIMENTAL", "TRATAMIENTO", "REPLICA", "DESCRIPCION"]),
    "senales": ("09_Hechos/02_Senales.csv", ["ID_SENAL", "ID_BATCH", "CODIGO_SENAL", "HOJA_ORIGEN", "ID_METABOLITO", "ID_NIVEL_IDENTIFICACION", "ID_MODO_IONIZACION", "ID_ADUCTO", "ID_SUPERCLASE_QUIMICA", "ID_CLASE_QUIMICA", "ID_TECNICA_SEPARACION", "ID_COLUMNA_CROMATOGRAFICA", "ID_INSTRUMENTO", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS", "MASA_MONOISOTOPICA", "ION_PRODUCTO_Q3", "INDICE_RETENCION", "PUNTAJE_ANOTACION", "ERROR_MASA_PPM", "FORMULA_MOLECULAR", "NOMBRE_ORIGINAL", "CLASE_ORIGINAL"]),
    "intensidades": ("09_Hechos/03_Intensidades.csv", ["ID_SENAL", "ID_MUESTRA", "ID_TIPO_INTENSIDAD", "VALOR"]),
    "registro_actividades": ("09_Hechos/04_Registro_actividades.csv", ["ID_REGISTRO", "ID_ARTICULO", "ID_BATCH", "ID_ESPECIE", "ID_MUESTRA", "ID_METABOLITO", "ID_ACTIVIDAD_BIOLOGICA", "TIPO_EVIDENCIA", "ENSAYO", "VALOR_ACTIVIDAD", "UNIDAD_ACTIVIDAD", "GRUPO_EXPERIMENTAL", "FUENTE"]),
}
DATASET = "10_Dataset_final/Dataset.csv"
COLUMNAS_DATASET = [
    # 29 columnas historicas (02_Script/src/data/dataset.py)
    "ID_ARTICULO", "ID_BATCH", "ID_MUESTRA", "ID_REINO", "ID_FILO", "ID_CLASE_TAXONOMICA", "ID_ORDEN", "ID_FAMILIA", "ID_GENERO",
    "ID_ESPECIE", "ID_TIPO_MUESTRA", "ID_PARTE_ESTUDIADA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION", "ID_COLUMNA_CROMATOGRAFICA",
    "ID_MODO_IONIZACION", "ID_NIVEL_IDENTIFICACION", "ID_SUPERCLASE_QUIMICA", "ID_CLASE_QUIMICA", "ID_ADUCTO", "ID_METABOLITO",
    "ID_ACTIVIDAD_BIOLOGICA", "FORMULA_MOLECULAR", "MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS",
    "ALTURA_PICO", "VALOR_ACTIVIDAD", "UNIDAD_ACTIVIDAD",
    # columnas nuevas de la estructura normalizada
    "ID_SENAL", "ID_UBICACION", "ID_SOLVENTE", "ID_TECNICA_SEPARACION", "ID_INSTRUMENTO", "ID_ANALIZADOR", "ID_MODO_ADQUISICION",
    "ID_TIPO_INTENSIDAD", "ID_CATEGORIA_ACTIVIDAD", "ES_ORQUIDEA",
]


# ------------------------------------------------------------------------------------------------ registros con ID
class Registro:
    """Catalogo que asigna ID incrementales a claves naturales."""

    def __init__(self, columnas: list[str], fila_cero: dict[str, Any], inicio: int = 1):
        self.columnas = columnas
        self.filas: dict[Any, dict[str, Any]] = {}
        self.ids: dict[Any, int] = {}
        self.pk = columnas[0]
        self.siguiente = inicio
        self.filas["__0__"] = {self.pk: 0, **fila_cero}
        self.ids["__0__"] = 0

    def id(self, clave: Any, fijo: int | None = None, **attrs: Any) -> int:
        if clave in (None, "", "__0__"):
            return 0
        if clave in self.ids:
            return self.ids[clave]
        nuevo = fijo if fijo is not None else self.siguiente
        if fijo is None:
            self.siguiente += 1
        self.ids[clave] = nuevo
        self.filas[clave] = {self.pk: nuevo, **attrs}
        return nuevo

    def df(self) -> pd.DataFrame:
        filas = sorted(self.filas.values(), key=lambda r: r[self.pk])
        return pd.DataFrame(filas).reindex(columns=self.columnas)


def _ne(cols: list[str], **extra: Any) -> dict[str, Any]:
    """Fila 0 'No especificado' con ceros en las FK y 'No disponible' en el texto."""
    fila: dict[str, Any] = {}
    for c in cols[1:]:
        fila[c] = 0 if c.startswith("ID_") or c.startswith("N_") or c == "ES_ORQUIDEA" else ""
    nombre = cols[2] if len(cols) > 2 and cols[1].startswith("ID_") else cols[1]
    fila[nombre] = NE
    if "DESCRIPCION" in fila:
        fila["DESCRIPCION"] = ND
    fila.update(extra)
    return fila


@dataclass
class Contexto:
    base_lotes: Path
    salida: Path
    lotes: list[int]
    log: Callable[[str], None] = print
    avisos: list[str] = field(default_factory=list)


# ------------------------------------------------------------------------------------------------ construccion
class Constructor:
    def __init__(self, ctx: Contexto):
        self.ctx = ctx
        C = {k: v[1] for k, v in ARCHIVOS.items()}
        self.C = C
        self.r = {k: Registro(C[k], _ne(C[k])) for k in C if k not in ("muestras", "senales", "intensidades", "registro_actividades",
                                                                       "sinonimos", "identificadores")}
        self.r["metabolitos"].id("__desconocido__", fijo=1, NOMBRE_METABOLITO="Senal no identificada", FORMULA_MOLECULAR="",
                                 MASA_MONOISOTOPICA=None, ID_CLASE_QUIMICA=0, ID_SUPERCLASE_QUIMICA=0, INCHIKEY="",
                                 DESCRIPCION="Caracteristica espectral sin anotacion (nivel MSI IV)")
        self.r["metabolitos"].siguiente = 2
        self.muestras: list[dict[str, Any]] = []
        self.senales: list[pd.DataFrame] = []
        self.intensidades: list[pd.DataFrame] = []
        self.registro: list[dict[str, Any]] = []
        self.sinonimos: dict[tuple[int, str], dict[str, Any]] = {}
        self.identificadores: dict[tuple[int, str, str], dict[str, Any]] = {}
        self.met_formulas: dict[int, Counter] = defaultdict(Counter)
        self.met_clases: dict[int, Counter] = defaultdict(Counter)
        self.met_inchikey: dict[str, int] = {}
        self.met_principal: dict[int, str] = {1: "__desconocido__"}
        self.met_batches: dict[int, set] = defaultdict(set)
        self.met_senales: Counter = Counter()
        self.lote_resumen: dict[int, dict[str, Any]] = {}
        self._estaticos()

    # ---------------------------------------------------------------------------- catalogos estaticos
    def _estaticos(self) -> None:
        r = self.r
        for k, (n, d) in {"positivo": ("Positivo", "ESI positivo: iones con carga positiva, tipicamente [M+H]+"),
                          "negativo": ("Negativo", "ESI negativo: iones con carga negativa, tipicamente [M-H]-"),
                          "ei": ("EI", "Impacto electronico (GC-MS)")}.items():
            r["modos"].id(k, MODO_IONIZACION=n, DESCRIPCION=d)
        for i, (n, d) in enumerate([("I", "Identificado con estandar de referencia (MS/MS y tiempo de retencion)"),
                                    ("II", "Anotacion putativa por similitud espectral con bibliotecas"),
                                    ("III", "Clase o compuesto caracterizado de forma tentativa (masa exacta, formula o prediccion)"),
                                    ("IV", "Senal desconocida sin anotacion")], start=1):
            r["niveles"].id(n, fijo=i, NIVEL_IDENTIFICACION=n, DESCRIPCION=d)
        for i, n, d in q.SUPERCLASES:
            r["superclases"].id(n, fijo=i, SUPERCLASE_QUIMICA=n, DESCRIPCION=d)
        r["superclases"].siguiente = len(q.SUPERCLASES) + 1
        for k, (i, n, d) in ref.TIPOS_MUESTRA.items():
            r["tipos_muestra"].id(k, fijo=i, TIPO_MUESTRA=n, DESCRIPCION=d)
        r["reinos"].id("Plantae", REINO="Plantae", DESCRIPCION="Reino vegetal")
        for f, (reino, d) in ref.FILOS.items():
            r["filos"].id(f, ID_REINO=r["reinos"].id(reino), FILO=f, DESCRIPCION=d)
        for c, (f, d) in ref.CLASES_TAX.items():
            r["clases_tax"].id(c, ID_FILO=r["filos"].id(f), CLASE_TAXONOMICA=c, DESCRIPCION=d)
        for o, c in ref.ORDENES.items():
            r["ordenes"].id(o, ID_CLASE_TAXONOMICA=r["clases_tax"].id(c), ORDEN=o, DESCRIPCION="")
        for fa, o in ref.FAMILIAS.items():
            r["familias"].id(fa, ID_ORDEN=r["ordenes"].id(o), FAMILIA=fa, DESCRIPCION="")
        for k, (nom, aut, gen, fam, comun, desc) in ref.ESPECIES.items():
            idg = r["generos"].id(gen, ID_FAMILIA=r["familias"].id(fam), GENERO=gen, DESCRIPCION="")
            r["especies"].id(k, ID_GENERO=idg, NOMBRE_CIENTIFICO=nom, AUTORIDAD=aut, NOMBRE_COMUN=comun,
                             ES_ORQUIDEA=int(fam == "Orchidaceae"), DESCRIPCION=desc)
        for k, (pais, reg, loc, lat, lon, alt, d) in ref.UBICACIONES.items():
            r["ubicaciones"].id(k, PAIS=pais, REGION=reg, LOCALIDAD=loc, LATITUD=lat, LONGITUD=lon, ALTITUD_M=alt, DESCRIPCION=d)
        for k, (n, d) in ref.PARTES.items():
            r["partes"].id(k, PARTE_PLANTA_ESTUDIADA=n, DESCRIPCION=d)
        for k, (n, d) in ref.TIPOS_CULTIVO.items():
            r["cultivos"].id(k, TIPO_CULTIVO=n, DESCRIPCION=d)
        for k, (n, f, pol, d) in ref.SOLVENTES.items():
            r["solventes"].id(k, SOLVENTE=n, FORMULA=f, INDICE_POLARIDAD=pol, DESCRIPCION=d)
        for k, (n, sol, comp, tec, d) in ref.METODOS.items():
            r["metodos"].id(k, METODO_EXTRACCION=n, ID_SOLVENTE=r["solventes"].id(sol), COMPOSICION_SOLVENTE=comp,
                            TECNICA_EXTRACCION=tec, DESCRIPCION=d)
        for k, (n, d) in ref.TECNICAS.items():
            r["tecnicas"].id(k, TECNICA_SEPARACION=n, DESCRIPCION=d)
        for k, (n, fase, fab, lon, dia, par) in ref.COLUMNAS.items():
            r["columnas"].id(k, COLUMNA_CROMATOGRAFICA=n, FASE_ESTACIONARIA=fase, FABRICANTE=fab, LONGITUD_MM=lon,
                             DIAMETRO_MM=dia, TAMANO_PARTICULA_UM=par, DESCRIPCION="")
        for k, (n, d) in ref.ADQUISICION.items():
            r["adquisicion"].id(k, MODO_ADQUISICION=n, DESCRIPCION=d)
        for k, (n, d) in ref.ANALIZADORES.items():
            r["analizadores"].id(k, ANALIZADOR=n, DESCRIPCION=d)
        for k, (n, sis, fab, an) in ref.INSTRUMENTOS.items():
            r["instrumentos"].id(k, INSTRUMENTO=n, SISTEMA_CROMATOGRAFICO=sis, FABRICANTE=fab,
                                 ID_ANALIZADOR=r["analizadores"].id(an), DESCRIPCION="")
        for k, (n, d) in ref.TIPOS_INTENSIDAD.items():
            r["tipos_intensidad"].id(k, TIPO_INTENSIDAD=n, DESCRIPCION=d)
        for k, (n, d) in ref.CATEGORIAS.items():
            r["categorias"].id(k, CATEGORIA_ACTIVIDAD=n, DESCRIPCION=d)
        for k, (n, cat, d) in ref.ACTIVIDADES.items():
            r["actividades"].id(k, ID_CATEGORIA_ACTIVIDAD=r["categorias"].id(cat), ACTIVIDAD_BIOLOGICA=n, DESCRIPCION=d)
        for i, a in ARTICULOS.items():
            r["articulos"].id(i, fijo=i, **a, DESCRIPCION="")
        r["articulos"].siguiente = max(ARTICULOS) + 1

    # ---------------------------------------------------------------------------- utilidades
    def aviso(self, texto: str) -> None:
        self.ctx.avisos.append(texto)

    def id_modo(self, m: int) -> int:
        return {1: self.r["modos"].id("positivo"), 2: self.r["modos"].id("negativo"), 3: self.r["modos"].id("ei")}.get(m, 0)

    def id_aducto(self, a: str) -> int:
        if not a:
            return 0
        carga = q.carga_aducto(a)
        modo = 1 if carga > 0 else 2 if carga < 0 else 0
        delta = q.delta_masa_aducto(a)
        return self.r["aductos"].id(a, ADUCTO=a, ID_MODO_IONIZACION=self.id_modo(modo), CARGA=carga,
                                    MULTIPLICADOR_M=q.multiplicador_aducto(a), DELTA_MASA=delta, DESCRIPCION="")

    def id_clase(self, sc: int, etiqueta: str) -> int:
        if not etiqueta:
            return 0
        return self.r["clases_quim"].id((sc, etiqueta.lower()), ID_SUPERCLASE_QUIMICA=sc, CLASE_QUIMICA=etiqueta, DESCRIPCION="")

    def id_metabolito(self, nombre: str, formula: str, inchikey: str, lote: int) -> int:
        if q.es_nombre_desconocido(nombre):
            return 1
        clave = q.clave_nombre(nombre)
        if not clave:
            return 1
        reg = self.r["metabolitos"]
        if clave in reg.ids:
            mid = reg.ids[clave]
        elif inchikey and inchikey in self.met_inchikey:
            mid = self.met_inchikey[inchikey]
            reg.ids[clave] = mid
            self._sinonimo(mid, nombre, "Nombre alternativo (misma InChIKey)", lote)
            return mid
        else:
            mid = reg.id(clave, NOMBRE_METABOLITO=nombre, FORMULA_MOLECULAR="", MASA_MONOISOTOPICA=None, ID_CLASE_QUIMICA=0,
                         ID_SUPERCLASE_QUIMICA=0, INCHIKEY="", DESCRIPCION="")
            self.met_principal[mid] = clave
        fila = reg.filas[self.met_principal.get(mid, clave)]
        if inchikey and inchikey not in self.met_inchikey:
            self.met_inchikey[inchikey] = mid
            if not fila["INCHIKEY"]:
                fila["INCHIKEY"] = inchikey
        if fila["NOMBRE_METABOLITO"] != nombre and q.clave_nombre(fila["NOMBRE_METABOLITO"]) != clave:
            self._sinonimo(mid, nombre, "Nombre alternativo", lote)
        return mid

    def _sinonimo(self, mid: int, texto: str, tipo: str, lote: int) -> None:
        t = q.limpiar_nombre(texto)
        if mid <= 1 or not t or len(t) > 400:
            return
        clave = (mid, q.clave_nombre(t))
        if clave not in self.sinonimos:
            self.sinonimos[clave] = dict(ID_METABOLITO=mid, SINONIMO=t, TIPO_SINONIMO=tipo, ID_BATCH=lote)

    def _identificador(self, mid: int, base: str, valor: str, lote: int) -> None:
        v = str(valor).strip().strip('"').strip("'").strip()
        if mid <= 1 or not v or v.lower() in ("nan", "-", "--", "/", "\\", "none", "null", "na", "n/a") or v.startswith("HASH("):
            return
        for parte in re.split(r"\s*[;|,]\s*|\s+", v) if base in ("CAS", "KEGG", "HMDB", "PubChem CID", "ChEBI") else [v]:
            p = parte.strip().strip('"').lstrip("#")
            if not p:
                continue
            if base == "CAS" and not re.fullmatch(r"\d{2,7}-\d{2}-\d", p):
                continue
            if base == "KEGG" and not re.fullmatch(r"C\d{5}", p):
                continue
            if base == "HMDB" and not re.fullmatch(r"HMDB\d{5,7}", p):
                continue
            if base in ("PubChem CID", "METLIN") and not re.fullmatch(r"\d+", p.replace(".0", "")):
                continue
            if base == "InChIKey" and not re.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z]", p):
                continue
            p = p.replace(".0", "") if base in ("PubChem CID", "METLIN") else p
            clave = (mid, base, p)
            if clave not in self.identificadores:
                self.identificadores[clave] = dict(ID_METABOLITO=mid, BASE_DATOS=base, IDENTIFICADOR=p, ID_BATCH=lote)

    # ---------------------------------------------------------------------------- muestras
    def _defaults(self, lote: Lote, tipo: str) -> dict[str, str]:
        if tipo in ("blanco",):
            return dict(especie="", parte="", cultivo="", ubicacion="", extraccion=lote.extraccion)
        return dict(especie=lote.especie, parte=lote.parte, cultivo=lote.cultivo, ubicacion=lote.ubicacion, extraccion=lote.extraccion)

    def registrar_muestras(self, lote: Lote, tabla: TablaLote, existentes: dict[str, int]) -> dict[str, int]:
        r = self.r
        mapa = {}
        for codigo in tabla.valores.columns:
            if codigo in existentes:
                mapa[codigo] = existentes[codigo]
                continue
            at = interpretar_muestra(lote, tabla.contexto_muestra.get(codigo, codigo))
            if at is None:
                self.aviso(f"BAT{lote.id:04d}: la muestra '{codigo}' no coincide con ninguna regla; se registra como biologica")
                at = dict(tipo="biologica", grupo=codigo)
            tipo = at.get("tipo", "biologica")
            d = self._defaults(lote, tipo)
            for k in ("especie", "parte", "cultivo", "ubicacion", "extraccion"):
                if k in at:
                    d[k] = at[k]
            if tipo in ("qc", "subqc") and not lote.especie and "especie" not in at:
                d["especie"] = ""
            if tipo in ("qc", "subqc") and not lote.parte and "parte" not in at:
                d["parte"] = ""
            idm = len(self.muestras) + 1
            self.muestras.append(dict(
                ID_MUESTRA=idm, ID_BATCH=lote.id, CODIGO_MUESTRA=codigo,
                ID_ESPECIE=r["especies"].ids.get(d["especie"], 0) if d["especie"] else 0,
                ID_PARTE_ESTUDIADA=r["partes"].ids.get(d["parte"], 0) if d["parte"] else 0,
                ID_TIPO_MUESTRA=r["tipos_muestra"].ids[tipo],
                ID_TIPO_CULTIVO=r["cultivos"].ids.get(d["cultivo"], 0) if d["cultivo"] else 0,
                ID_METODO_EXTRACCION=r["metodos"].ids.get(d["extraccion"], 0) if d["extraccion"] else 0,
                ID_UBICACION=r["ubicaciones"].ids.get(d["ubicacion"], 0) if d["ubicacion"] else 0,
                GRUPO_EXPERIMENTAL=str(at.get("grupo", "") or ""), TRATAMIENTO=str(at.get("tratamiento", "") or ""),
                REPLICA=str(at.get("replica", "") or ""), DESCRIPCION=f"Columna '{codigo}' del archivo {lote.archivo}"))
            for k in ("especie", "parte", "cultivo", "extraccion", "ubicacion"):
                if d[k] and d[k] not in {"especie": r["especies"], "parte": r["partes"], "cultivo": r["cultivos"],
                                         "extraccion": r["metodos"], "ubicacion": r["ubicaciones"]}[k].ids:
                    self.aviso(f"BAT{lote.id:04d}: clave de {k} desconocida '{d[k]}' en la muestra {codigo}")
            mapa[codigo] = idm
        return mapa

    # ---------------------------------------------------------------------------- senales
    def registrar_senales(self, lote: Lote, tabla: TablaLote, id_senal_inicial: int) -> tuple[pd.DataFrame, list[int]]:
        r = self.r
        h = tabla.hoja
        s = tabla.senales
        modo_lote = q.modo_desde_texto(lote.modos) if "/" not in lote.modos else 0
        modo_hoja = q.modo_desde_texto(h.modo)
        filas = []
        ids = []
        tecnica_def = h.tecnica or lote.tecnica
        for k, row in enumerate(s.itertuples(index=False)):
            nombre_raw = q.limpiar_nombre(row.nombre) or q.limpiar_nombre(getattr(row, "nombre_ms1", ""))
            sinonimos_extra = []
            if ";" in nombre_raw:
                partes = [p.strip() for p in nombre_raw.split(";") if p.strip()]
                nombre_raw, sinonimos_extra = partes[0], partes[1:]
            formula = q.limpiar_formula(row.formula)
            aducto = q.normalizar_aducto(row.aducto)
            # modo de ionizacion
            m = 0
            if row.modo:
                m = q.modo_desde_texto(h.modo_por_valor.get(row.modo, row.modo))
            if not m:
                m = q.modo_desde_aducto(aducto)
            if not m:
                mm = re.search(r"(?i)(^|_)(pos|neg)(_|$|\d)", str(row.id))
                m = q.modo_desde_texto(mm.group(2)) if mm else 0
            if not m:
                m = modo_hoja or modo_lote
            tecnica, instr, col = tecnica_def, h.instrumento or lote.instrumento, h.columna_crom or lote.columna
            if m == q.MODO_EI and tecnica != "gc":
                tecnica, instr, col = "gc", "gcms_ne", "gc_ne"
            # clases
            superclase_txt = row.superclase
            clase_txt, subclase_txt = row.clase, row.subclase
            if lote.id == 54 and superclase_txt:  # 'Secondary Metabolites_Phenolics_Tannins_PMDBxxxx_Nombre'
                partes = [p.strip() for p in re.split(r"_", re.sub(r"\s+", " ", superclase_txt))]
                superclase_txt, clase_txt = (partes[1] if len(partes) > 1 else ""), (partes[2] if len(partes) > 2 else "")
            sc = q.superclase_unificada(subclase_txt, clase_txt, superclase_txt, row.clase2)
            etiqueta = q.etiqueta_clase(clase_txt, subclase_txt, superclase_txt, row.clase2)
            idc = self.id_clase(sc, etiqueta) if sc else 0
            # metabolito
            inchikey = row.inchikey if re.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z]", row.inchikey or "") else ""
            mid = self.id_metabolito(nombre_raw, formula, inchikey, lote.id)
            anotado = mid > 1
            nivel_raw = row.nivel if row.nivel else h.nivel_defecto
            if row.nivel and h.mapa_nivel:
                nivel_raw = h.mapa_nivel.get(str(row.nivel).replace(".0", "").strip(), row.nivel)
            nivel = q.nivel_msi(nivel_raw, anotado)
            if anotado and not row.nivel and h.nivel_defecto is None:
                nivel = 3
            if anotado:
                self.met_batches[mid].add(lote.id)
                self.met_senales[mid] += 1
                if formula:
                    self.met_formulas[mid][formula] += 1
                if sc:
                    self.met_clases[mid][(sc, idc)] += 1
                for sn in sinonimos_extra:
                    self._sinonimo(mid, sn, "Nombre alternativo", lote.id)
                if row.sinonimo:
                    tipo_s = "IUPAC" if lote.id == 44 else "Nombre en chino"
                    self._sinonimo(mid, row.sinonimo, tipo_s, lote.id)
                nm1 = q.limpiar_nombre(getattr(row, "nombre_ms1", ""))
                if nm1 and q.clave_nombre(nm1) != q.clave_nombre(nombre_raw) and not q.es_nombre_desconocido(nm1):
                    self._sinonimo(mid, nm1, "Nombre MS1", lote.id)
                for base, attr in (("CAS", "cas"), ("KEGG", "kegg"), ("HMDB", "hmdb"), ("PubChem CID", "pubchem"), ("ChEBI", "chebi"),
                                   ("METLIN", "metlin"), ("LIPID MAPS", "lipidmaps"), ("InChIKey", "inchikey"), ("InChI", "inchi"),
                                   ("SMILES", "smiles"), ("ChemSpider", "chemspider"), ("MetWare", "mwdb"), ("PMDB", "pmdb"),
                                   ("NIST", "nist")):
                    val = getattr(row, attr, "")
                    if base == "HMDB" and val and not str(val).startswith("HMDB"):
                        if str(val).startswith("LM"):
                            self._identificador(mid, "LIPID MAPS", val, lote.id)
                        continue
                    if base == "LIPID MAPS" and val:
                        for p in re.split(r"[;|]", str(val)):
                            if p.strip().startswith("LM"):
                                self._identificador(mid, "LIPID MAPS", p.strip(), lote.id)
                            elif p.strip().startswith("HMDB"):
                                self._identificador(mid, "HMDB", p.strip(), lote.id)
                        continue
                    if val:
                        self._identificador(mid, base, val, lote.id)
                if lote.adquisicion.startswith("mrm") and row.id and attr_es_mw(row.id):
                    self._identificador(mid, "MetWare", row.id, lote.id)
            # masas
            rt = row.rt
            if rt == rt and h.rt_segundos:
                rt = rt / 60.0
            if rt == rt and (rt <= 0 or rt > 120):
                rt = np.nan
            masa = q.masa_monoisotopica(formula) if formula else None
            if masa is None and row.masa == row.masa:
                masa = float(row.masa)
            mz = row.mz
            if mz != mz and masa is not None and aducto:
                d = q.delta_masa_aducto(aducto)
                z = abs(q.carga_aducto(aducto))
                if d is not None and z:
                    mz = (q.multiplicador_aducto(aducto) * masa + d) / z
            ids.append(id_senal_inicial + k)
            filas.append(dict(
                ID_SENAL=id_senal_inicial + k, ID_BATCH=lote.id, CODIGO_SENAL=str(row.id) if row.id else f"fila_{k + 1}",
                HOJA_ORIGEN=row._hoja if hasattr(row, "_hoja") else str(h.hoja), ID_METABOLITO=mid, ID_NIVEL_IDENTIFICACION=nivel,
                ID_MODO_IONIZACION=self.id_modo(m), ID_ADUCTO=self.id_aducto(aducto), ID_SUPERCLASE_QUIMICA=sc, ID_CLASE_QUIMICA=idc,
                ID_TECNICA_SEPARACION=r["tecnicas"].ids.get(tecnica, 0), ID_COLUMNA_CROMATOGRAFICA=r["columnas"].ids.get(col, 0),
                ID_INSTRUMENTO=r["instrumentos"].ids.get(instr, 0), RELACION_MASA_CARGA=_r(mz, 6), TIEMPO_RETENCION_MINUTOS=_r(rt, 4),
                MASA_MONOISOTOPICA=_r(masa, 6), ION_PRODUCTO_Q3=_r(row.q3, 4), INDICE_RETENCION=_r(row.ri, 2),
                PUNTAJE_ANOTACION=_r(row.puntaje, 4), ERROR_MASA_PPM=_r(row.error_ppm, 4), FORMULA_MOLECULAR=formula,
                NOMBRE_ORIGINAL=q.limpiar_nombre(row.nombre)[:300], CLASE_ORIGINAL=" | ".join(x for x in (superclase_txt, clase_txt, subclase_txt) if x)[:300]))
        return pd.DataFrame(filas), ids

    # ---------------------------------------------------------------------------- lotes
    def procesar_lote(self, lote: Lote, id_senal: int) -> int:
        t0 = time.time()
        tablas = leer_lote(self.ctx.base_lotes, lote)
        muestras: dict[str, int] = {}
        n_sen = n_int = n_anot = 0
        hojas = []
        tipo_int = self.r["tipos_intensidad"].ids[lote.intensidad]
        for t in tablas:
            for a in t.avisos:
                self.aviso(a)
            hojas.append(str(t.hoja.hoja) + (" + " + ", ".join(map(str, t.hoja.combinar)) if t.hoja.combinar else ""))
            mapa = self.registrar_muestras(lote, t, muestras)
            muestras.update(mapa)
            sen, ids = self.registrar_senales(lote, t, id_senal)
            tipo_hoja = self.r["tipos_intensidad"].ids[t.hoja.intensidad] if t.hoja.intensidad else tipo_int
            v = t.valores.copy()
            if lote.cero_si_igual is not None:
                v = v.mask(v == lote.cero_si_igual, 0.0)
            if lote.umbral_cero is not None:
                v = v.mask(v.abs() < lote.umbral_cero, 0.0)
            v.index = ids
            v.columns = [mapa[c] for c in v.columns]
            larga = v.stack().dropna()
            larga = larga[np.isfinite(larga) & (larga > 0)] if lote.intensidad != "log10" else larga[np.isfinite(larga)]
            larga = larga.rename("VALOR").reset_index()
            larga.columns = ["ID_SENAL", "ID_MUESTRA", "VALOR"]
            larga["ID_TIPO_INTENSIDAD"] = tipo_hoja
            larga["VALOR"] = larga["VALOR"].map(lambda x: float(f"{x:.6g}"))
            self.senales.append(sen)
            self.intensidades.append(larga[["ID_SENAL", "ID_MUESTRA", "ID_TIPO_INTENSIDAD", "VALOR"]])
            n_sen += len(sen)
            n_anot += int((sen["ID_METABOLITO"] > 1).sum())
            n_int += len(larga)
            id_senal += len(sen)
        self.lote_resumen[lote.id] = dict(hojas="; ".join(hojas), n_muestras=len(set(muestras.values())), n_senales=n_sen,
                                          n_anotadas=n_anot, n_intensidades=n_int)
        self.ctx.log(f"  BAT{lote.id:04d}: {n_sen:>6} senales ({n_anot} anotadas), {len(set(muestras.values())):>3} muestras, "
                     f"{n_int:>8} intensidades  [{time.time() - t0:.1f} s]")
        return id_senal

    # ---------------------------------------------------------------------------- actividades
    def registrar_actividades(self) -> None:
        r = self.r
        mu = pd.DataFrame(self.muestras)
        especies_art: dict[int, set] = defaultdict(set)
        for lid in self.ctx.lotes:
            lote = LOTES[lid]
            for e in mu.loc[(mu.ID_BATCH == lid) & (mu.ID_ESPECIE > 0), "ID_ESPECIE"].unique():
                especies_art[lote.articulo].add(int(e))
        for a, ks in ESPECIES_ARTICULO.items():
            especies_art[a] |= {r["especies"].ids[k] for k in ks}

        def fila(**kw: Any) -> None:
            base = dict(ID_ARTICULO=0, ID_BATCH=0, ID_ESPECIE=0, ID_MUESTRA=0, ID_METABOLITO=0, ID_ACTIVIDAD_BIOLOGICA=0,
                        TIPO_EVIDENCIA="", ENSAYO="", VALOR_ACTIVIDAD=None, UNIDAD_ACTIVIDAD="", GRUPO_EXPERIMENTAL="", FUENTE="")
            base.update(kw)
            base["ID_REGISTRO"] = len(self.registro) + 1
            self.registro.append(base)

        lotes_por_art = defaultdict(list)
        for lid in self.ctx.lotes:
            lotes_por_art[LOTES[lid].articulo].append(lid)
        for art, lista in ACT_ESPECIE.items():
            if art not in ESPECIES_ARTICULO and art not in lotes_por_art:
                continue
            for esp, acts in lista:
                for act in acts:
                    if act not in r["actividades"].ids:
                        self.aviso(f"Actividad desconocida '{act}' (articulo {art})")
                        continue
                    fila(ID_ARTICULO=art, ID_ESPECIE=r["especies"].ids[esp], ID_ACTIVIDAD_BIOLOGICA=r["actividades"].ids[act],
                         TIPO_EVIDENCIA="Literatura citada en el articulo", FUENTE="Introduccion o discusion del articulo")
        for art, lista in ACT_METABOLITO.items():
            if art not in lotes_por_art:
                continue
            esp = list(especies_art.get(art, []))
            for nombre, acts in lista:
                mid = self.id_metabolito(nombre, "", "", 0)
                for act in acts:
                    fila(ID_ARTICULO=art, ID_ESPECIE=esp[0] if len(esp) == 1 else 0, ID_METABOLITO=mid,
                         ID_ACTIVIDAD_BIOLOGICA=r["actividades"].ids[act], TIPO_EVIDENCIA="Literatura citada en el articulo",
                         FUENTE=f"Actividad atribuida a {nombre} en el articulo")
        for lid, grupo, act, ensayo, valor, unidad, fuente in MEDICIONES:
            if lid not in self.ctx.lotes:
                continue
            sel = mu[(mu.ID_BATCH == lid) & (mu.GRUPO_EXPERIMENTAL == grupo) & mu.ID_TIPO_MUESTRA.isin([1, 2])]
            if sel.empty:
                self.aviso(f"BAT{lid:04d}: medicion '{ensayo}' del grupo '{grupo}' sin muestras; se registra a nivel de lote")
                sel = pd.DataFrame([dict(ID_MUESTRA=0, ID_ESPECIE=0)])
            for m in sel.itertuples():
                fila(ID_ARTICULO=LOTES[lid].articulo, ID_BATCH=lid, ID_ESPECIE=int(m.ID_ESPECIE), ID_MUESTRA=int(m.ID_MUESTRA),
                     ID_ACTIVIDAD_BIOLOGICA=r["actividades"].ids[act], TIPO_EVIDENCIA="Ensayo experimental del articulo", ENSAYO=ensayo,
                     VALOR_ACTIVIDAD=valor, UNIDAD_ACTIVIDAD=unidad, GRUPO_EXPERIMENTAL=grupo, FUENTE=fuente)

    # ---------------------------------------------------------------------------- cierre de catalogos
    def cerrar_metabolitos(self) -> None:
        reg = self.r["metabolitos"]
        for clave, fila in reg.filas.items():
            mid = fila["ID_METABOLITO"]
            if mid <= 1:
                continue
            if self.met_formulas[mid]:
                f = self.met_formulas[mid].most_common(1)[0][0]
                fila["FORMULA_MOLECULAR"] = f
                fila["MASA_MONOISOTOPICA"] = q.masa_monoisotopica(f)
            if self.met_clases[mid]:
                (sc, idc), _ = self.met_clases[mid].most_common(1)[0]
                fila["ID_SUPERCLASE_QUIMICA"], fila["ID_CLASE_QUIMICA"] = sc, idc
            fila["N_BATCHES"] = len(self.met_batches[mid])
            fila["N_SENALES"] = self.met_senales[mid]
            if not self.met_senales[mid]:
                fila["DESCRIPCION"] = "Citado en un articulo; sin senal anotada con este nombre en los lotes"

    def construir(self) -> dict[str, pd.DataFrame]:
        ctx = self.ctx
        ctx.log(f"Leyendo {len(ctx.lotes)} lotes de {ctx.base_lotes} ...")
        id_senal = 1
        for lid in ctx.lotes:
            id_senal = self.procesar_lote(LOTES[lid], id_senal)
        self.registrar_actividades()
        self.cerrar_metabolitos()
        r = self.r
        tablas = {k: reg.df() for k, reg in r.items()}
        # lotes
        bt = []
        for lid in ctx.lotes:
            lt, rs = LOTES[lid], self.lote_resumen[lid]
            bt.append(dict(ID_BATCH=lid, ID_ARTICULO=lt.articulo, CODIGO_BATCH=f"BAT{lid:04d}", ARCHIVO_BATCH=lt.archivo,
                           HOJAS_UTILIZADAS=rs["hojas"], MODOS_IONIZACION=lt.modos, ID_TECNICA_SEPARACION=r["tecnicas"].ids[lt.tecnica],
                           ID_COLUMNA_CROMATOGRAFICA=r["columnas"].ids.get(lt.columna, 0), ID_INSTRUMENTO=r["instrumentos"].ids.get(lt.instrumento, 0),
                           ID_MODO_ADQUISICION=r["adquisicion"].ids[lt.adquisicion], ID_TIPO_INTENSIDAD=r["tipos_intensidad"].ids[lt.intensidad],
                           FASE_MOVIL=lt.fase_movil, FLUJO=lt.flujo, VOLTAJE_CAPILAR=lt.voltaje, TEMPERATURA_FUENTE=lt.temp_fuente,
                           N_MUESTRAS=rs["n_muestras"], N_SENALES=rs["n_senales"], N_SENALES_ANOTADAS=rs["n_anotadas"],
                           N_INTENSIDADES=rs["n_intensidades"], DESCRIPCION=lt.notas))
        tablas["batches"] = pd.concat([pd.DataFrame([dict(ID_BATCH=0, ID_ARTICULO=0, CODIGO_BATCH=NE, ARCHIVO_BATCH=ND,
                                                          DESCRIPCION=ND)]), pd.DataFrame(bt)], ignore_index=True).reindex(columns=self.C["batches"])
        art = tablas["articulos"]
        mu = pd.DataFrame(self.muestras)
        nb = pd.Series({lid: LOTES[lid].articulo for lid in ctx.lotes}).value_counts()
        art["N_BATCHES"] = art["ID_ARTICULO"].map(nb).fillna(0).astype(int)
        esp_por_art = mu[mu.ID_ESPECIE > 0].assign(A=mu.ID_BATCH.map(lambda b: LOTES[b].articulo)).groupby("A")["ID_ESPECIE"].nunique()
        art["N_ESPECIES"] = art["ID_ARTICULO"].map(esp_por_art).fillna(0).astype(int)
        art.loc[art.ID_ARTICULO == 4, "N_ESPECIES"] = 1
        tablas["articulos"] = art
        tablas["muestras"] = pd.concat([pd.DataFrame([dict(ID_MUESTRA=0, ID_BATCH=0, CODIGO_MUESTRA=NE, ID_ESPECIE=0, ID_PARTE_ESTUDIADA=0,
                                                           ID_TIPO_MUESTRA=0, ID_TIPO_CULTIVO=0, ID_METODO_EXTRACCION=0, ID_UBICACION=0,
                                                           GRUPO_EXPERIMENTAL="", TRATAMIENTO="", REPLICA="", DESCRIPCION=ND)]), mu],
                                       ignore_index=True)
        tablas["senales"] = pd.concat(self.senales, ignore_index=True)
        tablas["intensidades"] = pd.concat(self.intensidades, ignore_index=True)
        tablas["registro_actividades"] = pd.DataFrame(self.registro).reindex(columns=self.C["registro_actividades"])
        sin = pd.DataFrame(list(self.sinonimos.values()))
        sin.insert(0, "ID_SINONIMO", range(1, len(sin) + 1))
        tablas["sinonimos"] = sin.reindex(columns=self.C["sinonimos"])
        ide = pd.DataFrame(list(self.identificadores.values())).sort_values(["ID_METABOLITO", "BASE_DATOS"], kind="stable")
        ide.insert(0, "ID_IDENTIFICADOR", range(1, len(ide) + 1))
        tablas["identificadores"] = ide.reindex(columns=self.C["identificadores"])
        return tablas


def attr_es_mw(codigo: str) -> bool:
    """Indices de la biblioteca Metware (pme3504, Lmhp009034, MWSmce694, Zbqn002049 ...)."""
    return bool(re.fullmatch(r"(?i)(pm[a-z]\d+|mw[a-z]*\d+|[a-z]{3,4}[pn]\d{5,6}|mws\d+|mw\d+|[a-z]{4}\d{6})", str(codigo)))


def _r(x: Any, nd: int) -> float | None:
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, nd)


# ------------------------------------------------------------------------------------------------ escritura
def _cabecera_existente(p: Path) -> list[str] | None:
    if not p.exists() or p.stat().st_size == 0:
        return None
    with open(p, encoding="utf-8-sig", errors="replace") as fh:
        linea = fh.readline().strip()
    if not linea or linea.startswith("version https://git-lfs"):
        return None
    sep = ";" if linea.count(";") >= linea.count(",") else ","
    return [c.strip().strip('"') for c in linea.split(sep) if c.strip().strip('"')]


def _columnas_finales(propias: list[str], existentes: list[str] | None, respetar: bool, nombre: str,
                      informe: list[str]) -> list[str]:
    if not existentes or not respetar or existentes == propias:
        return propias
    faltan = [c for c in propias if c not in existentes]
    extra = [c for c in existentes if c not in propias]
    if extra:
        informe.append(f"- `{nombre}`: columnas de su plantilla sin dato en la construccion (quedan vacias): {', '.join(extra)}")
    if faltan:
        informe.append(f"- `{nombre}`: columnas agregadas al final de su plantilla: {', '.join(faltan)}")
    return existentes + faltan


def escribir_csv(df: pd.DataFrame, p: Path, bom: bool = True) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    for c in df.columns:
        if c.startswith("ID_") or c in ("ES_ORQUIDEA",) or c.startswith("N_"):
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64")
        elif df[c].dtype == object:
            df[c] = df[c].map(lambda x: "" if x is None or (isinstance(x, float) and math.isnan(x)) else re.sub(r"[\r\n\t]+", " ", str(x)).strip())
    df.to_csv(p, sep=";", index=False, encoding="utf-8-sig" if bom else "utf-8", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")


def construir_dataset_final(tablas: dict[str, pd.DataFrame], p: Path, columnas: list[str], log: Callable[[str], None]) -> int:
    """Une Intensidades con Senales, Muestras, Batches, taxonomia y actividades medidas (una fila por senal x muestra;
    si la muestra tiene k mediciones experimentales de actividad, cada senal se repite k veces de forma consecutiva)."""
    t = tablas
    esp = t["especies"].merge(t["generos"][["ID_GENERO", "ID_FAMILIA"]], on="ID_GENERO", how="left") \
        .merge(t["familias"][["ID_FAMILIA", "ID_ORDEN"]], on="ID_FAMILIA", how="left") \
        .merge(t["ordenes"][["ID_ORDEN", "ID_CLASE_TAXONOMICA"]], on="ID_ORDEN", how="left") \
        .merge(t["clases_tax"][["ID_CLASE_TAXONOMICA", "ID_FILO"]], on="ID_CLASE_TAXONOMICA", how="left") \
        .merge(t["filos"][["ID_FILO", "ID_REINO"]], on="ID_FILO", how="left")
    esp = esp[["ID_ESPECIE", "ID_GENERO", "ID_FAMILIA", "ID_ORDEN", "ID_CLASE_TAXONOMICA", "ID_FILO", "ID_REINO", "ES_ORQUIDEA"]].fillna(0)
    mu = t["muestras"].merge(esp, on="ID_ESPECIE", how="left")
    mu = mu.merge(t["metodos"][["ID_METODO_EXTRACCION", "ID_SOLVENTE"]], on="ID_METODO_EXTRACCION", how="left")
    mu = mu.merge(t["batches"][["ID_BATCH", "ID_ARTICULO", "ID_MODO_ADQUISICION"]], on="ID_BATCH", how="left")
    mu = mu[["ID_MUESTRA", "ID_BATCH", "ID_ARTICULO", "ID_ESPECIE", "ID_GENERO", "ID_FAMILIA", "ID_ORDEN", "ID_CLASE_TAXONOMICA", "ID_FILO",
             "ID_REINO", "ES_ORQUIDEA", "ID_TIPO_MUESTRA", "ID_PARTE_ESTUDIADA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION", "ID_SOLVENTE",
             "ID_UBICACION", "ID_MODO_ADQUISICION"]].fillna(0)
    se = t["senales"].merge(t["instrumentos"][["ID_INSTRUMENTO", "ID_ANALIZADOR"]], on="ID_INSTRUMENTO", how="left")
    met = t["metabolitos"][["ID_METABOLITO", "FORMULA_MOLECULAR", "ID_SUPERCLASE_QUIMICA", "ID_CLASE_QUIMICA"]].rename(
        columns={"FORMULA_MOLECULAR": "F_MET", "ID_SUPERCLASE_QUIMICA": "SC_MET", "ID_CLASE_QUIMICA": "C_MET"})
    se = se.merge(met, on="ID_METABOLITO", how="left")
    # la clase de la senal manda; si no tiene, se usa la del metabolito; la formula del metabolito si la senal no la trae
    sc0 = se["ID_SUPERCLASE_QUIMICA"].eq(0)
    se.loc[sc0, "ID_SUPERCLASE_QUIMICA"] = se.loc[sc0, "SC_MET"].fillna(0)
    se.loc[sc0, "ID_CLASE_QUIMICA"] = se.loc[sc0, "C_MET"].fillna(0)
    sinf = se["FORMULA_MOLECULAR"].fillna("").eq("") & se["ID_METABOLITO"].gt(1)
    se.loc[sinf, "FORMULA_MOLECULAR"] = se.loc[sinf, "F_MET"].fillna("")
    se = se[["ID_SENAL", "ID_METABOLITO", "ID_NIVEL_IDENTIFICACION", "ID_MODO_IONIZACION", "ID_ADUCTO", "ID_SUPERCLASE_QUIMICA",
             "ID_CLASE_QUIMICA", "ID_TECNICA_SEPARACION", "ID_COLUMNA_CROMATOGRAFICA", "ID_INSTRUMENTO", "ID_ANALIZADOR",
             "FORMULA_MOLECULAR", "MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS"]]
    reg = t["registro_actividades"]
    med = reg[reg["ID_MUESTRA"] > 0][["ID_MUESTRA", "ID_ACTIVIDAD_BIOLOGICA", "VALOR_ACTIVIDAD", "UNIDAD_ACTIVIDAD"]]
    cat = t["actividades"][["ID_ACTIVIDAD_BIOLOGICA", "ID_CATEGORIA_ACTIVIDAD"]]
    med = med.merge(cat, on="ID_ACTIVIDAD_BIOLOGICA", how="left")
    p.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    it = t["intensidades"]
    primero = True
    with open(p, "w", encoding="utf-8", newline="") as fh:
        for lid, bloque in it.groupby(it["ID_SENAL"].map(dict(zip(t["senales"]["ID_SENAL"], t["senales"]["ID_BATCH"])))):
            d = bloque.merge(se, on="ID_SENAL", how="left").merge(mu, on="ID_MUESTRA", how="left")
            d = d.rename(columns={"VALOR": "ALTURA_PICO"})
            d = d.merge(med, on="ID_MUESTRA", how="left")
            for c in ("ID_ACTIVIDAD_BIOLOGICA", "ID_CATEGORIA_ACTIVIDAD"):
                d[c] = d[c].fillna(0)
            d = d.sort_values(["ID_MUESTRA", "ID_SENAL"], kind="stable")
            d = d.reindex(columns=columnas)
            for c in columnas:
                if c.startswith("ID_") or c == "ES_ORQUIDEA":
                    d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype("int64")
            d["UNIDAD_ACTIVIDAD"] = d["UNIDAD_ACTIVIDAD"].fillna("")
            d["FORMULA_MOLECULAR"] = d["FORMULA_MOLECULAR"].fillna("")
            d.to_csv(fh, sep=";", index=False, header=primero, lineterminator="\n")
            primero = False
            total += len(d)
            log(f"  Dataset: BAT{int(lid):04d} -> {len(d):>8} filas (acumulado {total})")
    return total


def ejecutar(base_lotes: Path, salida: Path, lotes: list[int] | None = None, respetar_cabeceras: bool = True,
             con_dataset: bool = True, log: Callable[[str], None] = print) -> dict[str, Any]:
    """Construye y escribe las 40 tablas. Devuelve un resumen con conteos y avisos."""
    t0 = time.time()
    ctx = Contexto(base_lotes=base_lotes, salida=salida, lotes=sorted(lotes or LOTES), log=log)
    cons = Constructor(ctx)
    tablas = cons.construir()
    informe_cab: list[str] = []
    conteos = {}
    for nombre, (rel, cols) in ARCHIVOS.items():
        p = salida / rel
        finales = _columnas_finales(cols, _cabecera_existente(p), respetar_cabeceras, rel, informe_cab)
        df = tablas[nombre].reindex(columns=finales)
        escribir_csv(df, p, bom=True)
        conteos[rel] = len(df)
        log(f"  {rel}: {len(df)} filas")
    n_ds = 0
    if con_dataset:
        p = salida / DATASET
        finales = _columnas_finales(COLUMNAS_DATASET, _cabecera_existente(p), respetar_cabeceras, DATASET, informe_cab)
        n_ds = construir_dataset_final(tablas, p, finales, log)
        conteos[DATASET] = n_ds
    resumen = dict(conteos=conteos, avisos=ctx.avisos, cabeceras=informe_cab, segundos=round(time.time() - t0, 1), tablas=tablas)
    escribir_informe(salida / "INFORME_CONSTRUCCION.md", resumen, cons)
    return resumen


def escribir_informe(p: Path, resumen: dict[str, Any], cons: Constructor) -> None:
    t = resumen["tablas"]
    mu, se, it = t["muestras"], t["senales"], t["intensidades"]
    lin = ["# Informe de construccion del Dataset", "",
           f"Generado por `python main.py construir-dataset` en {resumen['segundos']} s a partir de 01_Datos/Data "
           f"({len(ARTICULOS)} fuentes: 52 articulos + 1 articulo sin PDF + 2 conjuntos de datos sin articulo; "
           f"{len(cons.ctx.lotes)} lotes).", "",
           "## Tablas generadas", "", "| Archivo | Filas |", "|---|---|"]
    lin += [f"| `{k}` | {v:,} |" for k, v in resumen["conteos"].items()]
    lin += ["", "## Resumen por lote", "", "| Lote | Articulo | Hojas | Muestras | Senales | Anotadas | Intensidades |", "|---|---|---|---|---|---|---|"]
    for lid in cons.ctx.lotes:
        rs = cons.lote_resumen[lid]
        lin.append(f"| BAT{lid:04d} | ART{LOTES[lid].articulo:04d} | {rs['hojas']} | {rs['n_muestras']} | {rs['n_senales']:,} | "
                   f"{rs['n_anotadas']:,} | {rs['n_intensidades']:,} |")
    niv = se["ID_NIVEL_IDENTIFICACION"].value_counts().sort_index()
    lin += ["", "## Cifras clave", "",
            f"- Especies con datos: {int(mu.loc[mu.ID_ESPECIE > 0, 'ID_ESPECIE'].nunique())} "
            f"(orquideas: {int(t['especies'].loc[t['especies'].ES_ORQUIDEA == 1, 'ID_ESPECIE'].count())})",
            f"- Muestras: {len(mu) - 1:,} (QC: {int((mu.ID_TIPO_MUESTRA == 9).sum())}, blancos: {int((mu.ID_TIPO_MUESTRA == 10).sum())}, "
            f"medias de grupo: {int((mu.ID_TIPO_MUESTRA == 2).sum())}, sub-QC: {int((mu.ID_TIPO_MUESTRA == 3).sum())})",
            f"- Senales: {len(se):,}; anotadas con metabolito: {int((se.ID_METABOLITO > 1).sum()):,}; "
            f"niveles MSI: " + ", ".join(f"{k}={v:,}" for k, v in niv.items()),
            f"- Metabolitos distintos: {len(t['metabolitos']) - 2:,}; sinonimos: {len(t['sinonimos']):,}; "
            f"identificadores externos: {len(t['identificadores']):,}",
            f"- Intensidades (valores > 0): {len(it):,}",
            f"- Registros de actividad biologica: {len(t['registro_actividades']):,} "
            f"(experimentales: {int((t['registro_actividades'].TIPO_EVIDENCIA == 'Ensayo experimental del articulo').sum())})", ""]
    if resumen["cabeceras"]:
        lin += ["## Diferencias con las plantillas existentes", ""] + resumen["cabeceras"] + [""]
    lin += ["## Decisiones de curacion", "",
            "- ART0043 (`ART0043_lonicera_japonica.pdf`) trata del loto (*Nelumbo nucifera*); BAT0047 (`lonicera_japonica`) contiene sus seis tejidos.",
            "- BAT0048 (`lonicera_japonica`) contiene cuatro *Rhododendron* de Linzhi; su articulo (doi 10.3390/metabo16040226) no esta en 01_Datos/Data/Articulos y se registra como ART0053 con los datos de BASE DE DATOS GLOBAL.",
            "- BAT0003 (*Banisteriopsis caapi*) y BAT0004 (*Piper peltatum*) no tienen articulo: se registran como ART0054 y ART0055 (repositorios IKIAM) para no mezclarlos en un mismo grupo.",
            "- ART0004 (*Sophora flavescens*) no tiene lote; se conserva en 01_Articulos y en el registro de actividades.",
            "- BAT0002 usa la hoja `Hoja1` (tabla anotada); las demas hojas son reprocesamientos de las mismas inyecciones.",
            "- BAT0020: las senales de las tablas S4 (positivo) y S5 (negativo) se anotan con los nombres de las tablas S6-S8 por ID y modo.",
            "- BAT0024 solo trae metabolitos diferenciales por pares de especies: se unen las seis hojas y se deduplica por ID.",
            "- BAT0029, BAT0042 y BAT0049 solo reportan medias por grupo: se guardan como muestras de tipo 'Media de grupo'.",
            "- BAT0016: la asignacion de las variedades A-D a TW, XY, MX y ZC sigue el orden del articulo (no esta explicita en la tabla).",
            "- Metware usa el valor 9 como marcador de no detectado en tablas MRM; se trata como 0 (no se guarda).",
            "- Las tablas en log10 (BAT0018, BAT0052, BAT0055) se conservan en esa escala (ver ID_TIPO_INTENSIDAD).",
            "- Las clases quimicas de cada laboratorio (Metware, ClassyFire, HMDB) se unifican en 21 superclases; la clase original se guarda en 02_Senales.CLASE_ORIGINAL.",
            ""]
    if resumen["avisos"]:
        lin += ["## Avisos", ""] + [f"- {a}" for a in resumen["avisos"]] + [""]
    p.write_text("\n".join(lin), encoding="utf-8")
