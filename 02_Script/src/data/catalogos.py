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
    # 01_Trazabilidad
    Catalogo("articulos", "01_Trazabilidad/01_Articulos.csv", "ID_ARTICULO", "TITULO"),
    Catalogo("batches", "01_Trazabilidad/02_Batches.csv", "ID_BATCH", "ARCHIVO_BATCH",
             {"ID_ARTICULO": "articulos", "ID_TECNICA_SEPARACION": "tecnicas", "ID_COLUMNA_CROMATOGRAFICA": "columnas",
              "ID_INSTRUMENTO": "instrumentos", "ID_MODO_ADQUISICION": "adquisicion", "ID_TIPO_INTENSIDAD": "tipos_intensidad"}),
    # 02_Taxonomia
    Catalogo("reinos", "02_Taxonomia/01_Reinos.csv", "ID_REINO", "REINO"),
    Catalogo("filos", "02_Taxonomia/02_Filos.csv", "ID_FILO", "FILO", {"ID_REINO": "reinos"}),
    Catalogo("clases_tax", "02_Taxonomia/03_Clases_taxonomicas.csv", "ID_CLASE_TAXONOMICA", "CLASE_TAXONOMICA", {"ID_FILO": "filos"}),
    Catalogo("ordenes", "02_Taxonomia/04_Ordenes.csv", "ID_ORDEN", "ORDEN", {"ID_CLASE_TAXONOMICA": "clases_tax"}),
    Catalogo("familias", "02_Taxonomia/05_Familias.csv", "ID_FAMILIA", "FAMILIA", {"ID_ORDEN": "ordenes"}),
    Catalogo("generos", "02_Taxonomia/06_Generos.csv", "ID_GENERO", "GENERO", {"ID_FAMILIA": "familias"}),
    Catalogo("especies", "02_Taxonomia/07_Especies.csv", "ID_ESPECIE", "NOMBRE_CIENTIFICO", {"ID_GENERO": "generos"}),
    # 03_Geografia
    Catalogo("ubicaciones", "03_Geografia/01_Ubicaciones.csv", "ID_UBICACION", "LOCALIDAD"),
    # 04_Muestra
    Catalogo("tipos_muestra", "04_Muestra/01_Tipos_muestra.csv", "ID_TIPO_MUESTRA", "TIPO_MUESTRA"),
    Catalogo("partes", "04_Muestra/02_Partes_planta_estudiadas.csv", "ID_PARTE_ESTUDIADA", "PARTE_PLANTA_ESTUDIADA"),
    Catalogo("cultivos", "04_Muestra/03_Tipos_cultivo.csv", "ID_TIPO_CULTIVO", "TIPO_CULTIVO"),
    Catalogo("metodos", "04_Muestra/04_Metodos_extraccion.csv", "ID_METODO_EXTRACCION", "METODO_EXTRACCION", {"ID_SOLVENTE": "solventes"}),
    Catalogo("solventes", "04_Muestra/05_Solventes.csv", "ID_SOLVENTE", "SOLVENTE"),
    # 05_Plataforma_analitica
    Catalogo("modos", "05_Plataforma_analitica/01_Modos_ionizacion.csv", "ID_MODO_IONIZACION", "MODO_IONIZACION"),
    Catalogo("tecnicas", "05_Plataforma_analitica/02_Tecnicas_separacion.csv", "ID_TECNICA_SEPARACION", "TECNICA_SEPARACION"),
    Catalogo("columnas", "05_Plataforma_analitica/03_Columnas_cromatograficas.csv", "ID_COLUMNA_CROMATOGRAFICA", "COLUMNA_CROMATOGRAFICA"),
    Catalogo("adquisicion", "05_Plataforma_analitica/04_Modos_adquisicion.csv", "ID_MODO_ADQUISICION", "MODO_ADQUISICION"),
    Catalogo("analizadores", "05_Plataforma_analitica/05_Analizadores.csv", "ID_ANALIZADOR", "ANALIZADOR"),
    Catalogo("instrumentos", "05_Plataforma_analitica/06_Instrumentos.csv", "ID_INSTRUMENTO", "INSTRUMENTO", {"ID_ANALIZADOR": "analizadores"}),
    Catalogo("tipos_intensidad", "05_Plataforma_analitica/07_Tipos_intensidad.csv", "ID_TIPO_INTENSIDAD", "TIPO_INTENSIDAD"),
    # 06_Quimica_Analitica
    Catalogo("niveles", "06_Quimica_Analitica/01_Niveles_identificacion.csv", "ID_NIVEL_IDENTIFICACION", "NIVEL_IDENTIFICACION"),
    Catalogo("superclases", "06_Quimica_Analitica/02_Superclases_quimicas.csv", "ID_SUPERCLASE_QUIMICA", "SUPERCLASE_QUIMICA"),
    Catalogo("clases_quim", "06_Quimica_Analitica/03_Clases_quimicas.csv", "ID_CLASE_QUIMICA", "CLASE_QUIMICA", {"ID_SUPERCLASE_QUIMICA": "superclases"}),
    Catalogo("aductos", "06_Quimica_Analitica/04_Aductos.csv", "ID_ADUCTO", "ADUCTO", {"ID_MODO_IONIZACION": "modos"}),
    # 07_Metabolitos
    Catalogo("metabolitos", "07_Metabolitos/01_Metabolitos.csv", "ID_METABOLITO", "NOMBRE_METABOLITO",
             {"ID_CLASE_QUIMICA": "clases_quim", "ID_SUPERCLASE_QUIMICA": "superclases"}),
    Catalogo("sinonimos", "07_Metabolitos/02_Sinonimos_metabolitos.csv", "ID_SINONIMO", "SINONIMO",
             {"ID_METABOLITO": "metabolitos", "ID_BATCH": "batches"}),
    Catalogo("identificadores", "07_Metabolitos/03_Identificadores_externos.csv", "ID_IDENTIFICADOR", "IDENTIFICADOR",
             {"ID_METABOLITO": "metabolitos", "ID_BATCH": "batches"}),
    # 08_Actividad_biologica
    Catalogo("categorias", "08_Actividad_biologica/01_Categorias_actividad.csv", "ID_CATEGORIA_ACTIVIDAD", "CATEGORIA_ACTIVIDAD"),
    Catalogo("actividades", "08_Actividad_biologica/02_Actividades_biologicas.csv", "ID_ACTIVIDAD_BIOLOGICA", "ACTIVIDAD_BIOLOGICA",
             {"ID_CATEGORIA_ACTIVIDAD": "categorias"}),
    # 09_Hechos (03_Intensidades.csv no se registra aqui: se consume a traves de 10_Dataset_final/Dataset.csv)
    Catalogo("muestras", "09_Hechos/01_Muestras.csv", "ID_MUESTRA", "CODIGO_MUESTRA",
             {"ID_BATCH": "batches", "ID_ESPECIE": "especies", "ID_PARTE_ESTUDIADA": "partes", "ID_TIPO_MUESTRA": "tipos_muestra",
              "ID_TIPO_CULTIVO": "cultivos", "ID_METODO_EXTRACCION": "metodos", "ID_UBICACION": "ubicaciones"}),
    Catalogo("senales", "09_Hechos/02_Senales.csv", "ID_SENAL", "CODIGO_SENAL",
             {"ID_BATCH": "batches", "ID_METABOLITO": "metabolitos", "ID_NIVEL_IDENTIFICACION": "niveles", "ID_MODO_IONIZACION": "modos",
              "ID_ADUCTO": "aductos", "ID_SUPERCLASE_QUIMICA": "superclases", "ID_CLASE_QUIMICA": "clases_quim",
              "ID_TECNICA_SEPARACION": "tecnicas", "ID_COLUMNA_CROMATOGRAFICA": "columnas", "ID_INSTRUMENTO": "instrumentos"}),
    Catalogo("registro_actividades", "09_Hechos/04_Registro_actividades.csv", "ID_REGISTRO", None,
             {"ID_ARTICULO": "articulos", "ID_BATCH": "batches", "ID_ESPECIE": "especies", "ID_MUESTRA": "muestras",
              "ID_METABOLITO": "metabolitos", "ID_ACTIVIDAD_BIOLOGICA": "actividades"}),
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
# Columnas nuevas de la estructura normalizada (solo se verifican si estan en el Dataset)
FK_DATASET_OPCIONALES: dict[str, str] = {
    "ID_SENAL": "senales", "ID_UBICACION": "ubicaciones", "ID_SOLVENTE": "solventes", "ID_TECNICA_SEPARACION": "tecnicas",
    "ID_INSTRUMENTO": "instrumentos", "ID_ANALIZADOR": "analizadores", "ID_MODO_ADQUISICION": "adquisicion",
    "ID_TIPO_INTENSIDAD": "tipos_intensidad", "ID_CATEGORIA_ACTIVIDAD": "categorias",
}


class ErrorDatos(RuntimeError):
    """Error de lectura o integridad de los datos."""


def verificar_archivo_datos(p: Path) -> None:
    """Falla con un mensaje claro si el CSV no existe o es un puntero de Git LFS (texto de ~130 bytes que
    sustituye al archivo real cuando se clona el repositorio sin descargar los datos)."""
    if not p.exists():
        raise ErrorDatos(f"No existe el archivo de datos: {p}. Genere 01_Datos/Dataset con `python main.py construir-dataset`.")
    with open(p, "rb") as fh:
        inicio = fh.read(64)
    if inicio.startswith(b"version https://git-lfs"):
        raise ErrorDatos(f"{p} es un puntero de Git LFS, no los datos reales. Genere 01_Datos/Dataset con "
                         "`python main.py construir-dataset` o ejecute `git lfs pull`.")


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
