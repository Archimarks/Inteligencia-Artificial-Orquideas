"""Especificacion y carga de catalogos (claves primarias, claves foraneas y columna de nombre)."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..utils.rutas import config_global, ruta


@dataclass(frozen=True)
class Catalogo:
    nombre: str
    archivo: str
    pk: str
    etiqueta: str | None = None                       # columna legible
    fks: dict[str, str] = field(default_factory=dict)  # columna -> catalogo referenciado


CATALOGOS: dict[str, Catalogo] = {c.nombre: c for c in [
    Catalogo("articulos", "01_Catalogo_Nucleo/01_Articulos.csv", "ID_ARTICULO", "TITULO"),
    Catalogo("batches", "01_Catalogo_Nucleo/02_Batches.csv", "ID_BATCH", "ARCHIVO_BATCH", {"ID_ARTICULO": "articulos"}),
    Catalogo("modos", "01_Catalogo_Nucleo/03_Modo_ionizacion.csv", "ID_MODO_IONIZACION", "MODO_IONIZACION"),
    Catalogo("actividades", "01_Catalogo_Nucleo/04_Actividades_biologicas.csv", "ID_ACTIVIDAD_BIOLOGICA", "ACTIVIDAD_BIOLOGICA"),
    Catalogo("reinos", "02_Catalogo_Especie/01_Reinos.csv", "ID_REINO", "REINO"),
    Catalogo("filos", "02_Catalogo_Especie/02_Filos.csv", "ID_FILO", "FILO", {"ID_REINO": "reinos"}),
    Catalogo("clases_tax", "02_Catalogo_Especie/03_Clases_taxonomicas.csv", "ID_CLASE_TAXONOMICA", "CLASE_TAXONOMICA", {"ID_FILO": "filos"}),
    Catalogo("ordenes", "02_Catalogo_Especie/04_Ordenes.csv", "ID_ORDEN", "ORDEN", {"ID_CLASE_TAXONOMICA": "clases_tax"}),
    Catalogo("familias", "02_Catalogo_Especie/05_Familias.csv", "ID_FAMILIA", "FAMILIA", {"ID_ORDEN": "ordenes"}),
    Catalogo("generos", "02_Catalogo_Especie/06_Generos.csv", "ID_GENERO", "GENERO", {"ID_FAMILIA": "familias"}),
    Catalogo("especies", "02_Catalogo_Especie/07_Especies.csv", "ID_ESPECIE", "NOMBRE_CIENTIFICO", {"ID_GENERO": "generos"}),
    Catalogo("niveles", "03_Catalogo_Metabolito/01_Niveles_identificacion.csv", "ID_NIVEL_IDENTIFICACION", "NIVEL_IDENTIFICACION"),
    Catalogo("superclases", "03_Catalogo_Metabolito/02_Superclases_quimicas.csv", "ID_SUPERCLASE_QUIMICA", "SUPERCLASE_QUIMICA"),
    Catalogo("clases_quim", "03_Catalogo_Metabolito/03_Clases_quimicas.csv", "ID_CLASE_QUIMICA", "CLASE_QUIMICA", {"ID_SUPERCLASE_QUIMICA": "superclases"}),
    Catalogo("aductos", "03_Catalogo_Metabolito/04_Aductos.csv", "ID_ADUCTO", "ADUCTO"),
    Catalogo("metabolitos", "03_Catalogo_Metabolito/05_Metabolitos.csv", "ID_METABOLITO", "NOMBRE_METABOLITO", {"ID_CLASE_QUIMICA": "clases_quim"}),
    Catalogo("columnas", "04_Catalogo_Muestra/01_Columnas_cromatograficas.csv", "ID_COLUMNA_CROMATOGRAFICA", "COLUMNA_CROMATOGRAFICA"),
    Catalogo("tipos_muestra", "04_Catalogo_Muestra/02_Tipos_muestra.csv", "ID_TIPO_MUESTRA", "TIPO_MUESTRA"),
    Catalogo("partes", "04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv", "ID_PARTE_ESTUDIADA", "PARTE_PLANTA_ESTUDIADA"),
    Catalogo("cultivos", "04_Catalogo_Muestra/04_Tipos_cultivo.csv", "ID_TIPO_CULTIVO", "TIPO_CULTIVO"),
    Catalogo("metodos", "04_Catalogo_Muestra/05_Metodos_extraccion.csv", "ID_METODO_EXTRACCION", "METODO_EXTRACCION"),
    Catalogo("muestras", "04_Catalogo_Muestra/06_Muestras_Batch.csv", "ID_MUESTRA", "CODIGO_MUESTRA",
             {"ID_BATCH": "batches", "ID_ESPECIE": "especies", "ID_PARTE_ESTUDIADA": "partes", "ID_TIPO_MUESTRA": "tipos_muestra",
              "ID_TIPO_CULTIVO": "cultivos", "ID_METODO_EXTRACCION": "metodos"}),
    Catalogo("registro_actividades", "05_Pivotes/Registo_Actividades_biologicas.csv", "ID_REGISTRO", None,
             {"ID_ARTICULO": "articulos", "ID_ESPECIE": "especies", "ID_MUESTRA": "muestras", "ID_METABOLITO": "metabolitos",
              "ID_ACTIVIDAD_BIOLOGICA": "actividades"}),
]}

# Columna del Dataset -> catalogo referenciado
FK_DATASET: dict[str, str] = {
    "ID_ARTICULO": "articulos", "ID_BATCH": "batches", "ID_MUESTRA": "muestras", "ID_REINO": "reinos", "ID_FILO": "filos",
    "ID_CLASE_TAXONOMICA": "clases_tax", "ID_ORDEN": "ordenes", "ID_FAMILIA": "familias", "ID_GENERO": "generos",
    "ID_ESPECIE": "especies", "ID_TIPO_MUESTRA": "tipos_muestra", "ID_PARTE_ESTUDIADA": "partes", "ID_TIPO_CULTIVO": "cultivos",
    "ID_METODO_EXTRACCION": "metodos", "ID_COLUMNA_CROMATOGRAFICA": "columnas", "ID_MODO_IONIZACION": "modos",
    "ID_NIVEL_IDENTIFICACION": "niveles", "ID_SUPERCLASE_QUIMICA": "superclases", "ID_CLASE_QUIMICA": "clases_quim",
    "ID_ADUCTO": "aductos", "ID_METABOLITO": "metabolitos", "ID_ACTIVIDAD_BIOLOGICA": "actividades",
}


class ErrorDatos(RuntimeError):
    """Error de lectura o integridad de los datos."""


def verificar_archivo_datos(p: Path) -> None:
    """Falla con un mensaje claro si el CSV no existe o es un puntero de Git LFS (texto de ~130 bytes que
    sustituye al archivo real cuando se clona el repositorio sin descargar los datos)."""
    if not p.exists():
        raise ErrorDatos(f"No existe el archivo de datos: {p}")
    with open(p, "rb") as fh:
        inicio = fh.read(64)
    if inicio.startswith(b"version https://git-lfs"):
        raise ErrorDatos(f"{p} es un puntero de Git LFS, no los datos reales. Copie en 01_Datos/Base los CSV "
                         "procesados (ZIP de datos entregado) o ejecute `git lfs pull`.")


# Archivos fijados por `datos_entrenamiento.archivos` del experimento en curso (nombre logico -> ruta absoluta)
ARCHIVOS_FIJADOS: dict[str, Path] = {}
NOMBRES_ARCHIVO = ["dataset"] + list(CATALOGOS)


def ruta_archivo(nombre: str) -> Path:
    """Ruta del archivo logico `nombre` ('dataset' o un catalogo), respetando la del experimento si la fijo."""
    if nombre in ARCHIVOS_FIJADOS:
        return ARCHIVOS_FIJADOS[nombre]
    if nombre == "dataset":
        return ruta("datos", "dataset")
    if nombre not in CATALOGOS:
        raise ErrorDatos(f"Archivo desconocido: {nombre!r}. Opciones: {NOMBRES_ARCHIVO}")
    return ruta("datos", "catalogos") / CATALOGOS[nombre].archivo


def ruta_catalogo(nombre: str) -> Path:
    return ruta_archivo(nombre)


@lru_cache(maxsize=None)
def cargar_catalogo(nombre: str) -> pd.DataFrame:
    """Lee un catalogo; los ID se convierten a enteros y se valida que la PK sea unica."""
    if nombre not in CATALOGOS:
        raise ErrorDatos(f"Catalogo desconocido: {nombre!r}. Opciones: {sorted(CATALOGOS)}")
    cat = CATALOGOS[nombre]
    p = ruta_catalogo(nombre)
    verificar_archivo_datos(p)
    cfg = config_global()["datos"]
    df = pd.read_csv(p, sep=cfg["separador"], encoding=cfg["codificacion_catalogos"], dtype=str, keep_default_na=False)
    for c in df.columns:
        if c.startswith("ID_"):
            df[c] = pd.to_numeric(df[c], errors="raise").astype("int64")
    if cat.pk in df and df[cat.pk].duplicated().any():
        raise ErrorDatos(f"Clave primaria duplicada en {nombre}: {df.loc[df[cat.pk].duplicated(), cat.pk].tolist()[:5]}")
    if nombre == "registro_actividades":
        df["VALOR_ACTIVIDAD"] = pd.to_numeric(df["VALOR_ACTIVIDAD"].replace("", None), errors="coerce")
    return df


def mapa_etiquetas(nombre: str) -> dict[int, str]:
    cat = CATALOGOS[nombre]
    df = cargar_catalogo(nombre)
    return dict(zip(df[cat.pk], df[cat.etiqueta]))
