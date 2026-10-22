#
# Archivo: construir_dataset.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# ETL: convierte las tablas de hechos normalizadas de 01_Datos/Dataset/
# (catalogos + 01_Dataset_Actividad_biologica.csv + 02_Dataset_Metabolito.csv,
# con IDs de catalogo en vez de texto) en el Core.datos.Dataset que necesita
# cada objetivo de 01_Supervisado, EN MEMORIA -- no se escribe ningun archivo
# intermedio a disco. Cada llamada arma el texto CSV con las columnas de
# salida y lo empaqueta con Core.datos.desde_texto(); Core.dataset_en_memoria
# cachea el resultado por proceso para no rehacer el trabajo si se pide dos
# veces el mismo objetivo dentro de la misma corrida.
#
# Convencion de columnas de salida (ver Core/datos.py):
#     primera columna -> ID_MUESTRA (pasa a indice, no es feature)
#     REF_*           -> metadatos de trazabilidad (se excluyen de X)
#     Y               -> objetivo (texto en clasificacion; asi Core.datos lo
#                        detecta como no-numerico y activa es_clasificacion)
#     resto           -> features, todas numericas
#
# Codificacion de las dimensiones de catalogo:
#     - baja cardinalidad (<=16 categorias: taxonomia alta, tipo de muestra,
#       tipo de cultivo, modo de ionizacion, nivel de identificacion, parte de
#       planta estudiada) -> one-hot (columnas OH_<dimension>_<id>).
#     - cardinalidad media/alta (orden, familia, genero, especie, metodo de
#       extraccion, columna cromatografica, aducto, y metabolito cuando es
#       feature en vez de objetivo) -> se deja el ID entero tal cual. Es una
#       simplificacion deliberada: un one-hot de ID_METABOLITO (32 mil clases)
#       en un dataset de millones de filas no es viable en disco ni en memoria.
#       Los modelos de arbol del catalogo (xgboost/lightgbm/catboost/random_
#       forest/extra_trees/gradient_boosting) toleran bien IDs enteros como
#       categoricos; los modelos lineales/distancia (ridge, svm, knn) pierden
#       precision con esta codificacion -- limitacion conocida, no un descuido.
#
from __future__ import annotations

import csv
import io
import math
import re

from .. import submodulo

datos = submodulo("01_catalogos.datos")
rutas = submodulo("00_fundamentos.rutas")

BASE = rutas.DATOS / "Dataset"

# 03_Dataset_Metabolito_Identificados.csv es 02_Dataset_Metabolito.csv filtrado
# a las filas con metabolito identificado (mismas columnas, mismo orden) --
# todo lo de aca abajo que usa la tabla de metabolitos filtra a identificados
# de entrada, asi que leer el archivo chico (965K filas, 74MB) en vez del
# grande (12.6M filas, 854MB) da EXACTAMENTE el mismo resultado y mucho mas
# rapido (import solo, sin cachear a disco: ver la conversacion sobre por que
# ya no hay una carpeta "Por Entrenamiento").
ARCHIVO_METABOLITO = "03_Dataset_Metabolito_Identificados.csv"

# --- columnas de origen (indice 0-based) en cada fact table -----------------
# 02_Dataset_Metabolito.csv
M_MUESTRA, M_BATCH = 0, 1
M_REINO, M_FILO, M_CLASE, M_ORDEN, M_FAMILIA, M_GENERO, M_ESPECIE = 2, 3, 4, 5, 6, 7, 8
M_TIPO_MUESTRA, M_PARTE, M_TIPO_CULTIVO, M_METODO, M_COLUMNA, M_MODO = 9, 10, 11, 12, 13, 14
M_ADUCTO, M_MASA, M_MZ, M_RT, M_ALTURA, M_NIVEL, M_METABOLITO = 15, 16, 17, 18, 19, 20, 21

# 01_Dataset_Actividad_biologica.csv
A_MUESTRA, A_BATCH = 0, 1
A_REINO, A_FILO, A_CLASE, A_ORDEN, A_FAMILIA, A_GENERO, A_ESPECIE = 2, 3, 4, 5, 6, 7, 8
A_TIPO_MUESTRA, A_PARTE, A_TIPO_CULTIVO, A_METODO, A_COLUMNA, A_MODO = 9, 10, 11, 12, 13, 14
A_METABOLITO, A_NIVEL, A_ADUCTO = 15, 16, 17
A_MASA, A_MZ, A_RT, A_ALTURA = 18, 19, 20, 21
A_ACTIVIDAD, A_VALOR, A_UNIDAD = 22, 23, 24


def _leer_csv(relpath: str) -> list[list[str]]:
    ruta = BASE / relpath
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return [fila for fila in csv.reader(f, delimiter=";") if fila and fila[0]]


# {id (str) -> nombre} a partir de un catalogo con columnas nombradas.
def _mapa_nombre(
        relpath: str, col_nombre: int = 1, *,
        id_col: str | None = None,
        nombre_col: str | None = None) -> dict[str, str]:
    filas = _leer_csv(relpath)
    encabezado = filas[0]
    indice_id = encabezado.index(id_col) if id_col else 0
    indice_nombre = encabezado.index(nombre_col) if nombre_col else col_nombre
    return {fila[indice_id]: fila[indice_nombre] for fila in filas[1:]}


def _mapa_batch_desde_archivos_crudos() -> dict[str, str]:
    # BAT#### en el nombre del archivo conserva el ID incluso si el catálogo
    # tabular de lotes no está disponible o no se puede leer.
    carpeta = rutas.DATOS / "Data" / "Batch"
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de lotes crudos: {carpeta}")
    archivos = sorted(ruta for ruta in carpeta.iterdir() if ruta.is_file())
    if not archivos:
        raise FileNotFoundError(f"No hay archivos de lotes crudos en {carpeta}")

    nombres: dict[str, str] = {}
    for archivo in archivos:
        coincidencia = re.fullmatch(r"BAT(\d{4})_(.+)", archivo.stem, flags=re.IGNORECASE)
        if coincidencia is None:
            raise ValueError(
                f"Nombre de lote no reconocible en {carpeta}: {archivo.name}. "
                "Se esperaba BAT####_nombre.ext.")
        id_batch = str(int(coincidencia.group(1)))
        if id_batch in nombres:
            raise ValueError(f"El lote {id_batch} aparece en más de un archivo crudo.")
        nombres[id_batch] = archivo.stem
    return nombres


# Lista ordenada de IDs (str) de un catalogo -- define el orden de las columnas one-hot.
def _ids_catalogo(relpath: str, id_col: str) -> list[str]:
    filas = _leer_csv(relpath)
    indice_id = filas[0].index(id_col)
    return [fila[indice_id] for fila in filas[1:]]


# --- catalogos: nombres (para Y / REF_) --------------------------------------
NOMBRE_ACTIVIDAD = _mapa_nombre(
    "01_Catalogo_Nucleo/04_Actividades_biologicas.csv",
    id_col="ID_ACTIVIDAD_BIOLOGICA",
    nombre_col="ACTIVIDAD_BIOLOGICA")
NOMBRE_METABOLITO = _mapa_nombre(
    "03_Catalogo_Metabolito/05_Metabolitos.csv",
    id_col="ID_METABOLITO",
    nombre_col="NOMBRE_METABOLITO")
NOMBRE_ESPECIE = _mapa_nombre(
    "02_Catalogo_Especie/07_Especies.csv",
    id_col="ID_ESPECIE",
    nombre_col="NOMBRE_CIENTIFICO")
NOMBRE_BATCH = _mapa_batch_desde_archivos_crudos()

# --- catalogos: universo de categorias para one-hot --------------------------
# (nombre de la dimension, ruta del catalogo, columna ID)
_DIMENSIONES_ONEHOT = [
    ("REINO", "02_Catalogo_Especie/01_Reinos.csv", "ID_REINO"),
    ("FILO", "02_Catalogo_Especie/02_Filos.csv", "ID_FILO"),
    ("CLASE_TAXONOMICA", "02_Catalogo_Especie/03_Clases_taxonomicas.csv",
     "ID_CLASE_TAXONOMICA"),
    ("TIPO_MUESTRA", "04_Catalogo_Muestra/02_Tipos_muestra.csv",
     "ID_TIPO_MUESTRA"),
    ("TIPO_CULTIVO", "04_Catalogo_Muestra/04_Tipos_cultivo.csv",
     "ID_TIPO_CULTIVO"),
    ("MODO_IONIZACION", "01_Catalogo_Nucleo/03_Modo_ionizacion.csv",
     "ID_MODO_IONIZACION"),
    ("NIVEL", "03_Catalogo_Metabolito/01_Niveles_identificacion.csv",
     "ID_NIVEL_IDENTIFICACION"),
    ("PARTE_ESTUDIADA", "04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv",
     "ID_PARTE_ESTUDIADA"),
]
_CATEGORIAS = {
    nombre: _ids_catalogo(ruta, id_col)
    for nombre, ruta, id_col in _DIMENSIONES_ONEHOT
}


# Encabezados OH_<dimension>_<id> de todas las dimensiones one-hot, en orden.
def _encabezados_onehot() -> list[str]:
    cabeceras: list[str] = []
    for nombre, _, _ in _DIMENSIONES_ONEHOT:
        ids = _CATEGORIAS[nombre]
        cabeceras += [f"OH_{nombre}_{i}" for i in ids]
    return cabeceras


# Bits "0"/"1" de todas las dimensiones one-hot para los valores de una fila
# (valores en el mismo orden que _DIMENSIONES_ONEHOT). Valor "" (desconocido) -> todo ceros.
def _bits_onehot(valores: list[str]) -> list[str]:
    bits: list[str] = []
    for (nombre, _, _), valor in zip(_DIMENSIONES_ONEHOT, valores):
        for cat in _CATEGORIAS[nombre]:
            bits.append("1" if valor == cat else "0")
    return bits


# Deja pasar el valor solo si es un numero valido; cualquier otra cosa (celda
# vacia, o texto colado en un campo numerico -- "Nd"/"nan" de la fuente, o una
# etiqueta de grupo que se filtro en una fila puntual del batch 26 -- se trata
# como dato ausente, igual que una celda vacia.
def _num(valor: str) -> str:
    if not valor:
        return ""
    try:
        float(valor)
    except ValueError:
        return ""
    return valor


ENCABEZADOS_ONEHOT = _encabezados_onehot()
FEATURES_ORDINALES_COMUNES = ["ID_ORDEN", "ID_FAMILIA", "ID_GENERO", "ID_ESPECIE",
                               "ID_METODO_EXTRACCION", "ID_COLUMNA", "ID_ADUCTO"]
FEATURES_NUMERICAS = ["MASA_MONOISOTOPICA", "RELACION_MASA_CARGA",
                       "TIEMPO_RETENCION_MINUTOS", "ALTURA_PICO"]


# --- Clasificacion / METABOLITO ----------------------------------------------
# Y = nombre del metabolito (texto). Se excluyen tanto el ID 0 reservado para
# datos no especificados como el ID 1 reservado para señales no identificadas.
def construir_metabolito() -> datos.Dataset:
    header = ["ID_MUESTRA", "REF_BATCH", "REF_ESPECIE", "Y"] + \
        ENCABEZADOS_ONEHOT + FEATURES_ORDINALES_COMUNES + FEATURES_NUMERICAS
    buffer = io.StringIO()
    buffer.write(";".join(header) + "\n")
    with open(BASE / ARCHIVO_METABOLITO, encoding="utf-8") as fin:
        next(fin)  # encabezado de origen
        for linea in fin:
            p = linea.rstrip("\n").split(";")
            if p[M_METABOLITO] in {"0", "1"} or not p[M_METABOLITO]:
                continue  # sin identificar: no es una clase valida
            nombre_metabolito = NOMBRE_METABOLITO.get(p[M_METABOLITO], "")
            if not nombre_metabolito:
                continue
            ref_batch = NOMBRE_BATCH.get(p[M_BATCH], "")
            ref_especie = NOMBRE_ESPECIE.get(p[M_ESPECIE], "")
            onehot = _bits_onehot([p[M_REINO], p[M_FILO], p[M_CLASE], p[M_TIPO_MUESTRA],
                                    p[M_TIPO_CULTIVO], p[M_MODO], p[M_NIVEL], p[M_PARTE]])
            ordinales = [_num(p[i]) for i in (M_ORDEN, M_FAMILIA, M_GENERO, M_ESPECIE,
                                               M_METODO, M_COLUMNA, M_ADUCTO)]
            numericas = [_num(p[i]) for i in (M_MASA, M_MZ, M_RT, M_ALTURA)]
            fila = [p[M_MUESTRA], ref_batch, ref_especie, nombre_metabolito] + \
                onehot + ordinales + numericas
            buffer.write(";".join(fila) + "\n")
    return datos.desde_texto("Clasificacion/METABOLITO", buffer.getvalue())


# --- Clasificacion / ACTIVIDAD_BIOLOGICA -------------------------------------
# Y = nombre de la actividad biologica (texto). Incluye ID_METABOLITO como
# feature ordinal adicional (que compuesto, si se conoce, acompanaba la
# actividad observada).
def construir_actividad_clasificacion() -> datos.Dataset:
    header = ["ID_MUESTRA", "REF_BATCH", "REF_ESPECIE", "REF_METABOLITO", "Y"] + \
        ENCABEZADOS_ONEHOT + ["ID_METABOLITO"] + FEATURES_ORDINALES_COMUNES + FEATURES_NUMERICAS
    buffer = io.StringIO()
    buffer.write(";".join(header) + "\n")
    with open(BASE / "01_Dataset_Actividad_biologica.csv", encoding="utf-8") as fin:
        next(fin)
        for linea in fin:
            p = linea.rstrip("\n").split(";")
            nombre_actividad = NOMBRE_ACTIVIDAD.get(p[A_ACTIVIDAD], "")
            if not nombre_actividad:
                continue
            ref_batch = NOMBRE_BATCH.get(p[A_BATCH], "")
            ref_especie = NOMBRE_ESPECIE.get(p[A_ESPECIE], "")
            ref_metabolito = NOMBRE_METABOLITO.get(p[A_METABOLITO], "")
            onehot = _bits_onehot([p[A_REINO], p[A_FILO], p[A_CLASE], p[A_TIPO_MUESTRA],
                                    p[A_TIPO_CULTIVO], p[A_MODO], p[A_NIVEL], p[A_PARTE]])
            ordinales = [_num(p[A_METABOLITO])] + \
                [_num(p[i]) for i in (A_ORDEN, A_FAMILIA, A_GENERO, A_ESPECIE,
                                       A_METODO, A_COLUMNA, A_ADUCTO)]
            numericas = [_num(p[i]) for i in (A_MASA, A_MZ, A_RT, A_ALTURA)]
            fila = [p[A_MUESTRA], ref_batch, ref_especie, ref_metabolito, nombre_actividad] + \
                onehot + ordinales + numericas
            buffer.write(";".join(fila) + "\n")
    return datos.desde_texto("Clasificacion/ACTIVIDAD_BIOLOGICA", buffer.getvalue())


# --- Regresion / METABOLITO ---------------------------------------------------
# Y = log1p(ALTURA_PICO): la abundancia del pico cromatografico -- la cantidad
# continua con sentido real que se puede sacar de esta tabla ("cuanto de este
# compuesto aparece segun especie/tejido/metodo"). MASA_MONOISOTOPICA y
# RELACION_MASA_CARGA NO sirven como objetivo: estan casi determinadas por el
# aducto (m/z = (masa + aducto) / carga), asi que "predecirlas" seria solo
# redescubrir esa formula, no una relacion real; quedan como features.
#
# En log1p y no en la escala original: ALTURA_PICO va de 0 a ~1.1e11 (la
# mediana es ~6e4 pero el percentil 99 ya esta en ~2.8e8) -- tipico de una
# intensidad cromatografica, practicamente log-normal. En la escala cruda un
# regresor lineal da R2 ~ 0 (unos pocos valores enormes dominan el error);
# log1p es la transformacion estandar para este tipo de dato y hace que el
# problema sea aprendible para todo el catalogo, no solo para arboles/boosting.
# Para volver a la unidad original: altura = expm1(prediccion).
#
# Mismo filtro de fila que Clasificacion/METABOLITO (solo metabolitos
# identificados) por dos motivos: sin eso, el 92% de las 12.6 millones de filas
# de la tabla no tiene compuesto conocido y el feature ID_METABOLITO (que aca SI
# es un feature valido, no el objetivo) pierde sentido; y de paso el dataset
# queda del mismo tamano que Clasificacion/METABOLITO (~965 mil filas).
def construir_metabolito_regresion() -> datos.Dataset:
    header = ["ID_MUESTRA", "REF_BATCH", "REF_ESPECIE", "REF_METABOLITO", "Y"] + \
        ENCABEZADOS_ONEHOT + ["ID_METABOLITO"] + FEATURES_ORDINALES_COMUNES + \
        ["MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS"]
    buffer = io.StringIO()
    buffer.write(";".join(header) + "\n")
    with open(BASE / ARCHIVO_METABOLITO, encoding="utf-8") as fin:
        next(fin)  # encabezado de origen
        for linea in fin:
            p = linea.rstrip("\n").split(";")
            if p[M_METABOLITO] in {"0", "1"} or not p[M_METABOLITO]:
                continue  # sin identificar: mismo criterio que Clasificacion/METABOLITO
            nombre_metabolito = NOMBRE_METABOLITO.get(p[M_METABOLITO], "")
            if not nombre_metabolito:
                continue
            altura = _num(p[M_ALTURA])
            if not altura:
                continue  # sin altura de pico valida: no hay Y
            valor = repr(math.log1p(float(altura)))
            ref_batch = NOMBRE_BATCH.get(p[M_BATCH], "")
            ref_especie = NOMBRE_ESPECIE.get(p[M_ESPECIE], "")
            onehot = _bits_onehot([p[M_REINO], p[M_FILO], p[M_CLASE], p[M_TIPO_MUESTRA],
                                    p[M_TIPO_CULTIVO], p[M_MODO], p[M_NIVEL], p[M_PARTE]])
            ordinales = [_num(p[M_METABOLITO])] + \
                [_num(p[i]) for i in (M_ORDEN, M_FAMILIA, M_GENERO, M_ESPECIE,
                                       M_METODO, M_COLUMNA, M_ADUCTO)]
            numericas = [_num(p[i]) for i in (M_MASA, M_MZ, M_RT)]
            fila = [p[M_MUESTRA], ref_batch, ref_especie, nombre_metabolito, valor] + \
                onehot + ordinales + numericas
            buffer.write(";".join(fila) + "\n")
    return datos.desde_texto("Regresion/METABOLITO", buffer.getvalue())


# --- Regresion / ACTIVIDAD_BIOLOGICA -----------------------------------------
# Y = VALOR_ACTIVIDAD (numero). Solo existen valores reales para 3 de los 44
# batches (ver conversacion): ~139 mil filas de las 2.47 millones. Se agrupa
# por UNIDAD_ACTIVIDAD (mismo ensayo/misma escala) via REF_UNIDAD_ACTIVIDAD en
# vez de mezclar escalas (mg/mL de IC50 con % de inhibicion, etc. no son
# comparables como un unico target numerico).
def construir_actividad_regresion() -> datos.Dataset:
    header = ["ID_MUESTRA", "REF_BATCH", "REF_ESPECIE", "REF_METABOLITO",
              "REF_UNIDAD_ACTIVIDAD", "Y"] + \
        ENCABEZADOS_ONEHOT + ["ID_METABOLITO", "ID_ACTIVIDAD"] + \
        FEATURES_ORDINALES_COMUNES + FEATURES_NUMERICAS
    buffer = io.StringIO()
    buffer.write(";".join(header) + "\n")
    with open(BASE / "01_Dataset_Actividad_biologica.csv", encoding="utf-8") as fin:
        next(fin)
        for linea in fin:
            p = linea.rstrip("\n").split(";")
            if not p[A_VALOR]:
                continue  # sin valor cuantitativo real
            ref_batch = NOMBRE_BATCH.get(p[A_BATCH], "")
            ref_especie = NOMBRE_ESPECIE.get(p[A_ESPECIE], "")
            ref_metabolito = NOMBRE_METABOLITO.get(p[A_METABOLITO], "")
            onehot = _bits_onehot([p[A_REINO], p[A_FILO], p[A_CLASE], p[A_TIPO_MUESTRA],
                                    p[A_TIPO_CULTIVO], p[A_MODO], p[A_NIVEL], p[A_PARTE]])
            ordinales = [_num(p[A_METABOLITO]), _num(p[A_ACTIVIDAD])] + \
                [_num(p[i]) for i in (A_ORDEN, A_FAMILIA, A_GENERO, A_ESPECIE,
                                       A_METODO, A_COLUMNA, A_ADUCTO)]
            numericas = [_num(p[i]) for i in (A_MASA, A_MZ, A_RT, A_ALTURA)]
            fila = [p[A_MUESTRA], ref_batch, ref_especie, ref_metabolito, p[A_UNIDAD],
                    p[A_VALOR]] + onehot + ordinales + numericas
            buffer.write(";".join(fila) + "\n")
    if buffer.tell() == len(";".join(header)) + 1:
        raise datos.DatasetError("Regresion/ACTIVIDAD_BIOLOGICA: 0 filas con VALOR_ACTIVIDAD.")
    return datos.desde_texto("Regresion/ACTIVIDAD_BIOLOGICA", buffer.getvalue())
