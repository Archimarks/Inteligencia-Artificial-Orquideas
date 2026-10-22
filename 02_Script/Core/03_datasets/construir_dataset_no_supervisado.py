#
# Archivo: construir_dataset_no_supervisado.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# ETL de 02_No_supervisado. En los perfiles químicos, cada fila representa
# una especie vegetal. Cada corrida se normaliza a composición relativa antes
# de promediarla, para que las especies con más registros no dominen el
# agrupamiento por tamaño de muestra o intensidad total.
#
# La taxonomia/tipo de muestra/metodo de extraccion NO entran como features
# (X): quedan como REF_* de contexto. Si entraran, clustering terminaria
# re-descubriendo esas mismas etiquetas categoricas en vez de agrupar por
# similitud quimica real, que es la pregunta que interesa.
#
# construir_perfil_continuo() y construir_perfil_binario() comparten el
# agregado cacheado y exponen composición o presencia por especie.
#
# En perfiles solo entran eventos con clase quimica conocida; los eventos sin
# clasificacion se excluyen, no se convierten en una clase ni cuentan como
# evidencia de ausencia. El continuo además requiere señal positiva. Por ello,
# los ceros del perfil significan no detectado/no clasificado en los datos,
# nunca ausencia quimica confirmada.
#
from __future__ import annotations

import csv
import functools
import io
import math
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

from .. import submodulo

datos = submodulo("01_catalogos.datos")
config = submodulo("00_fundamentos.config")
_cd = None
BASE = submodulo("00_fundamentos.rutas").DATOS / "Dataset"
ARCHIVO_FUENTE = "03_Dataset_Metabolito_Identificados.csv"
ARCHIVO_PATRONES = "04_Dataset_Patrones_Quimicos.csv"
ARCHIVO_PATRONES_UNIFICADO = "04_Dataset_Patrones_Quimicos_Unificado.csv"
NOMBRE_BATCH: dict[str, str] = {}
NOMBRE_ESPECIE: dict[str, str] = {}
NOMBRE_CLASE: dict[str, str] = {}
NOMBRE_TIPO_MUESTRA: dict[str, str] = {}
NOMBRE_PARTE: dict[str, str] = {}
NOMBRE_METODO: dict[str, str] = {}
_leer_csv = None
_mapa_nombre = None

_COLUMNAS_QUIMICAS_DERIVADAS = [
    "ID_CLASE_QUIMICA",
    "NOMBRE_METABOLITO",
    "FORMULA_MOLECULAR",
    "CLASE_QUIMICA",
    "ID_SUPERCLASE_QUIMICA",
    "SUPERCLASE_QUIMICA",
    "ESTADO_CLASIFICACION_QUIMICA",
]
ARCHIVO_CALIDAD_MUESTRA = "04_Informe_Calidad_Por_Muestra.csv"
ARCHIVO_CALIDAD_BATCH = "04_Informe_Calidad_Por_Batch.csv"
ARCHIVO_METABOLITOS_PENDIENTES = "04_Metabolitos_Sin_Clase_Quimica.csv"
_ARCHIVOS_04 = {
    "PATRONES_QUIMICOS": ARCHIVO_PATRONES,
    "CALIDAD_BATCH": ARCHIVO_CALIDAD_BATCH,
    "CALIDAD_MUESTRA": ARCHIVO_CALIDAD_MUESTRA,
    "METABOLITOS_SIN_CLASE": ARCHIVO_METABOLITOS_PENDIENTES,
}

def _slug(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")[:40]


def _escribir_csv_atomico(ruta: Path, encabezado: list[str], filas) -> None:
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8-sig", newline="", delete=False,
                dir=ruta.parent, prefix=f".{ruta.name}.", suffix=".tmp") as archivo:
            temporal = archivo.name
            escritor = csv.writer(archivo, delimiter=";", lineterminator="\n")
            escritor.writerow(encabezado)
            escritor.writerows(filas)
        os.replace(temporal, ruta)
        temporal = None
    finally:
        if temporal is not None and os.path.exists(temporal):
            os.unlink(temporal)


def _texto_csv(encabezado: list[str], filas) -> str:
    buffer = io.StringIO(newline="")
    escritor = csv.writer(buffer, delimiter=";", lineterminator="\n")
    escritor.writerow(encabezado)
    escritor.writerows(filas)
    return buffer.getvalue()


def _fila_metabolito_pendiente(
        metabolito: str, resumen: dict,
        clases_por_nombre_formula: dict[tuple[str, str], dict[str, set[str]]],
        clases: dict[str, tuple[str, str]]) -> list[str]:
    clave = (resumen["nombre"].strip().casefold(), resumen["formula"].strip().upper())
    coincidencias = clases_por_nombre_formula.get(clave)
    ids_clase = sorted(
        coincidencias["clases"],
        key=lambda valor: (not valor.isdigit(), valor),
    ) if coincidencias else []
    nombres_clase = sorted({clases[id_clase][1] for id_clase in ids_clase})
    ids_metabolito = sorted(
        coincidencias["metabolitos"],
        key=lambda valor: (not valor.isdigit(), valor),
    ) if coincidencias else []
    estado = (
        "Coincidencia exacta por nombre y fórmula; requiere revisión"
        if len(ids_clase) == 1 else
        "Coincidencia ambigua; requiere revisión"
        if ids_clase else
        "Sin coincidencia exacta en el catálogo"
    )
    return [
        metabolito, resumen["nombre"], resumen["formula"], resumen["registros"],
        ",".join(sorted(
            resumen["batches"], key=lambda valor: (not valor.isdigit(), valor))),
        ",".join(ids_clase), ",".join(nombres_clase),
        ",".join(ids_metabolito), estado,
    ]


def _estado_cobertura(registros: int, clasificados: int) -> str:
    if registros == 0:
        return "Sin registros identificados"
    if clasificados == 0:
        return "Sin clasificación química"
    if clasificados == registros:
        return "Completa"
    return "Parcial"


def _cargar_dependencias_legadas() -> None:
    global _cd, _leer_csv, _mapa_nombre
    global NOMBRE_BATCH, NOMBRE_ESPECIE, NOMBRE_CLASE
    global NOMBRE_TIPO_MUESTRA, NOMBRE_PARTE, NOMBRE_METODO
    if _cd is not None:
        return
    _cd = submodulo("02_etl.construir_dataset")
    _leer_csv = _cd._leer_csv
    _mapa_nombre = _cd._mapa_nombre
    NOMBRE_BATCH = _cd.NOMBRE_BATCH
    NOMBRE_ESPECIE = _cd.NOMBRE_ESPECIE
    NOMBRE_CLASE = _mapa_nombre(
        "03_Catalogo_Metabolito/03_Clases_quimicas.csv", col_nombre=2)
    NOMBRE_TIPO_MUESTRA = _mapa_nombre("04_Catalogo_Muestra/02_Tipos_muestra.csv")
    NOMBRE_PARTE = _mapa_nombre("04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv")
    NOMBRE_METODO = _mapa_nombre("04_Catalogo_Muestra/05_Metodos_extraccion.csv")


def asegurar_dataset_patrones_quimicos() -> None:
    """Crea o actualiza el dataset 04 con etiquetas químicas legibles."""
    _cargar_dependencias_legadas()
    fuente = BASE / ARCHIVO_FUENTE
    catalogo_metabolitos = BASE / "03_Catalogo_Metabolito/05_Metabolitos.csv"
    catalogo_clases = BASE / "03_Catalogo_Metabolito/03_Clases_quimicas.csv"
    catalogo_superclases = BASE / "03_Catalogo_Metabolito/02_Superclases_quimicas.csv"
    destino = BASE / ARCHIVO_PATRONES
    with open(fuente, encoding="utf-8-sig", newline="") as archivo_fuente:
        encabezado_fuente = next(csv.reader(archivo_fuente, delimiter=";"), [])
    if not encabezado_fuente or "ID_METABOLITO" not in encabezado_fuente:
        raise ValueError(f"El encabezado de {ARCHIVO_FUENTE} no contiene ID_METABOLITO.")
    indice_metabolito = encabezado_fuente.index("ID_METABOLITO")
    encabezado_esperado = encabezado_fuente + _COLUMNAS_QUIMICAS_DERIVADAS
    i_fuente_muestra = encabezado_fuente.index("ID_MUESTRA")
    i_fuente_batch = encabezado_fuente.index("ID_BATCH")
    indices_contexto_muestra = [
        encabezado_fuente.index(columna)
        for columna in (
            "ID_BATCH", "ID_ESPECIE", "ID_TIPO_MUESTRA",
            "ID_PARTE_ESTUDIADA", "ID_METODO_EXTRACCION",
        )
    ]
    i_fuente_altura = encabezado_fuente.index("ALTURA_PICO")
    encabezados_informes = {
        BASE / ARCHIVO_CALIDAD_MUESTRA: [
            "ID_MUESTRA", "ID_BATCH", "NOMBRE_BATCH", "REGISTROS_IDENTIFICADOS",
            "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
            "ESTADO_COBERTURA", "CLASES_QUIMICAS_DISTINTAS",
            "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ],
        BASE / ARCHIVO_CALIDAD_BATCH: [
            "ID_BATCH", "NOMBRE_BATCH", "MUESTRAS", "REGISTROS_IDENTIFICADOS",
            "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
            "ESTADO_COBERTURA", "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ],
        BASE / ARCHIVO_METABOLITOS_PENDIENTES: [
            "ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR",
            "REGISTROS_SIN_CLASE", "BATCHES", "ID_CLASE_CANDIDATA",
            "CLASE_CANDIDATA", "ID_METABOLITO_COINCIDENTE", "ESTADO_SUGERENCIA",
        ],
    }
    fuente_batch = _cd.rutas.DATOS / "Data" / "Batch"
    dependencias = [
        fuente, catalogo_metabolitos, catalogo_clases, catalogo_superclases,
        Path(__file__), Path(_cd.__file__), fuente_batch,
    ]

    actualizar = not destino.is_file()
    if not actualizar:
        actualizar = destino.stat().st_mtime_ns < max(
            dependencia.stat().st_mtime_ns for dependencia in dependencias)
    if not actualizar:
        for archivo, encabezado_esperado_informe in encabezados_informes.items():
            if not archivo.is_file() or archivo.stat().st_mtime_ns < destino.stat().st_mtime_ns:
                actualizar = True
                break
            with open(archivo, encoding="utf-8-sig", newline="") as informe:
                encabezado_actual = next(csv.reader(informe, delimiter=";"), [])
            if encabezado_actual != encabezado_esperado_informe:
                actualizar = True
                break
    if not actualizar:
        with open(destino, encoding="utf-8-sig", newline="") as archivo:
            encabezado_actual = next(csv.reader(archivo, delimiter=";"), [])
        actualizar = encabezado_actual != encabezado_esperado
    if not actualizar:
        return

    catalogo_met = _leer_csv("03_Catalogo_Metabolito/05_Metabolitos.csv")
    cabecera_met = catalogo_met[0]
    i_metabolito = cabecera_met.index("ID_METABOLITO")
    i_nombre_metabolito = cabecera_met.index("NOMBRE_METABOLITO")
    i_formula = cabecera_met.index("FORMULA_MOLECULAR")
    i_clase_metabolito = cabecera_met.index("ID_CLASE_QUIMICA")
    metabolitos_sin_clase: dict[str, dict] = {}
    metabolitos = {
        fila[i_metabolito]: (
            fila[i_nombre_metabolito], fila[i_formula], fila[i_clase_metabolito])
        for fila in catalogo_met[1:]
        if len(fila) > max(i_metabolito, i_nombre_metabolito, i_formula, i_clase_metabolito)
    }

    catalogo_clase = _leer_csv("03_Catalogo_Metabolito/03_Clases_quimicas.csv")
    cabecera_clase = catalogo_clase[0]
    i_clase = cabecera_clase.index("ID_CLASE_QUIMICA")
    i_superclase = cabecera_clase.index("ID_SUPERCLASE_QUIMICA")
    i_nombre_clase = cabecera_clase.index("CLASE_QUIMICA")
    clases = {
        fila[i_clase]: (fila[i_superclase], fila[i_nombre_clase])
        for fila in catalogo_clase[1:]
        if len(fila) > max(i_clase, i_superclase, i_nombre_clase)
    }
    clases_por_nombre_formula: dict[tuple[str, str], dict[str, set[str]]] = {}
    for id_metabolito, (nombre, formula, id_clase) in metabolitos.items():
        if id_clase and id_clase not in clases:
            raise ValueError(
                f"ID_CLASE_QUIMICA {id_clase!r} del metabolito "
                f"{id_metabolito!r} no existe en el catálogo de clases.")
        clave = (nombre.strip().casefold(), formula.strip().upper())
        if id_clase and all(clave):
            coincidencia = clases_por_nombre_formula.setdefault(
                clave, {"clases": set(), "metabolitos": set()})
            coincidencia["clases"].add(id_clase)
            coincidencia["metabolitos"].add(id_metabolito)

    catalogo_super = _leer_csv("03_Catalogo_Metabolito/02_Superclases_quimicas.csv")
    cabecera_super = catalogo_super[0]
    i_id_super = cabecera_super.index("ID_SUPERCLASE_QUIMICA")
    i_nombre_super = cabecera_super.index("SUPERCLASE_QUIMICA")
    superclases = {
        fila[i_id_super]: fila[i_nombre_super]
        for fila in catalogo_super[1:]
        if len(fila) > max(i_id_super, i_nombre_super)
    }

    temporal = None
    filas_escritas = 0
    por_muestra: dict[str, dict] = {}
    contexto_por_muestra: dict[str, tuple[str, ...]] = {}
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8-sig", newline="", delete=False,
                dir=BASE, prefix=f".{ARCHIVO_PATRONES}.", suffix=".tmp") as archivo_salida:
            temporal = archivo_salida.name
            escritor = csv.writer(archivo_salida, delimiter=";", lineterminator="\n")
            escritor.writerow(encabezado_esperado)
            with open(fuente, encoding="utf-8-sig", newline="") as archivo_fuente:
                lector = csv.reader(archivo_fuente, delimiter=";")
                next(lector, None)
                for fila in lector:
                    if len(fila) != len(encabezado_fuente):
                        raise ValueError(
                            f"Fila invalida en {ARCHIVO_FUENTE}: se esperaban "
                            f"{len(encabezado_fuente)} columnas y hay {len(fila)}.")
                    if fila[indice_metabolito] not in metabolitos:
                        raise ValueError(
                            f"ID_METABOLITO {fila[indice_metabolito]!r} no existe "
                            "en el catálogo de metabolitos.")
                    nombre_metabolito, formula, id_clase = metabolitos[fila[indice_metabolito]]
                    muestra = fila[i_fuente_muestra]
                    batch = fila[i_fuente_batch]
                    if not muestra.strip() or not batch.strip():
                        raise ValueError(
                            f"Fila {lector.line_num} de {ARCHIVO_FUENTE} no tiene "
                            "ID_MUESTRA o ID_BATCH.")
                    if batch not in NOMBRE_BATCH:
                        raise ValueError(
                            f"ID_BATCH {batch!r} en {ARCHIVO_FUENTE} no corresponde "
                            "a ningún archivo BAT####_nombre de Data/Batch.")
                    contexto = tuple(fila[indice] for indice in indices_contexto_muestra)
                    contexto_previo = contexto_por_muestra.setdefault(muestra, contexto)
                    if contexto_previo != contexto:
                        raise ValueError(
                            f"ID_MUESTRA {muestra!r} tiene metadatos de especie, "
                            "batch o preparación inconsistentes.")
                    resumen_muestra = por_muestra.setdefault(muestra, {
                        "batch": batch, "registros": 0, "clasificados": 0,
                        "altura_faltante": 0, "altura_invalida": 0, "clases": set(),
                    })
                    resumen_muestra["registros"] += 1
                    if id_clase:
                        resumen_muestra["clasificados"] += 1
                        resumen_muestra["clases"].add(id_clase)
                    else:
                        pendiente = metabolitos_sin_clase.setdefault(
                            fila[indice_metabolito], {
                                "nombre": nombre_metabolito,
                                "formula": formula,
                                "registros": 0,
                                "batches": set(),
                            })
                        pendiente["registros"] += 1
                        pendiente["batches"].add(batch)
                    altura = fila[i_fuente_altura].strip()
                    if not altura:
                        resumen_muestra["altura_faltante"] += 1
                    else:
                        try:
                            altura_valor = float(altura)
                        except ValueError:
                            resumen_muestra["altura_invalida"] += 1
                        else:
                            if not math.isfinite(altura_valor) or altura_valor < 0:
                                resumen_muestra["altura_invalida"] += 1
                    id_superclase, nombre_clase = clases.get(id_clase, ("", ""))
                    if id_clase and not nombre_clase:
                        raise ValueError(
                            f"ID_CLASE_QUIMICA {id_clase!r} del metabolito "
                            f"{fila[indice_metabolito]!r} no existe en el catálogo de clases.")
                    if id_superclase and id_superclase not in superclases:
                        raise ValueError(
                            f"ID_SUPERCLASE_QUIMICA {id_superclase!r} de la clase "
                            f"{id_clase!r} no existe en el catálogo de superclases.")
                    nombre_superclase = superclases.get(id_superclase, "")
                    estado_clasificacion = (
                        "Clasificado" if id_clase else "Sin clase química asignada")
                    escritor.writerow(fila + [
                        id_clase, nombre_metabolito, formula, nombre_clase,
                        id_superclase, nombre_superclase, estado_clasificacion,
                    ])
                    filas_escritas += 1
            if not filas_escritas:
                raise datos.DatasetError(
                    f"No se encontraron metabolitos identificados para crear {ARCHIVO_PATRONES}.")
        os.replace(temporal, destino)
        temporal = None
        muestras_ordenadas = sorted(por_muestra.items())
        _escribir_csv_atomico(
            BASE / ARCHIVO_CALIDAD_MUESTRA,
            ["ID_MUESTRA", "ID_BATCH", "NOMBRE_BATCH", "REGISTROS_IDENTIFICADOS",
             "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
             "ESTADO_COBERTURA", "CLASES_QUIMICAS_DISTINTAS", "ALTURA_FALTANTE",
             "ALTURA_INVALIDA"],
            ([
                muestra, resumen["batch"],
                NOMBRE_BATCH.get(resumen["batch"], ""),
                resumen["registros"],
                resumen["clasificados"],
                f"{100 * resumen['clasificados'] / resumen['registros']:.4f}",
                _estado_cobertura(resumen["registros"], resumen["clasificados"]),
                len(resumen["clases"]), resumen["altura_faltante"],
                resumen["altura_invalida"],
            ] for muestra, resumen in muestras_ordenadas),
        )

        por_batch: dict[str, dict] = {
            batch: {
                "muestras": 0, "registros": 0, "clasificados": 0,
                "altura_faltante": 0, "altura_invalida": 0,
            }
            for batch in NOMBRE_BATCH
        }
        for resumen in por_muestra.values():
            grupo = por_batch.setdefault(resumen["batch"], {
                "muestras": 0, "registros": 0, "clasificados": 0,
                "altura_faltante": 0, "altura_invalida": 0,
            })
            grupo["muestras"] += 1
            grupo["registros"] += resumen["registros"]
            grupo["clasificados"] += resumen["clasificados"]
            grupo["altura_faltante"] += resumen["altura_faltante"]
            grupo["altura_invalida"] += resumen["altura_invalida"]
        _escribir_csv_atomico(
            BASE / ARCHIVO_CALIDAD_BATCH,
            ["ID_BATCH", "NOMBRE_BATCH", "MUESTRAS", "REGISTROS_IDENTIFICADOS",
             "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
             "ESTADO_COBERTURA", "ALTURA_FALTANTE", "ALTURA_INVALIDA"],
            ([
                batch, NOMBRE_BATCH.get(batch, ""),
                resumen["muestras"], resumen["registros"],
                resumen["clasificados"],
                (f"{100 * resumen['clasificados'] / resumen['registros']:.4f}"
                 if resumen["registros"] else "0.0000"),
                _estado_cobertura(resumen["registros"], resumen["clasificados"]),
                resumen["altura_faltante"], resumen["altura_invalida"],
            ] for batch, resumen in sorted(
                por_batch.items(),
                key=lambda elemento: (not elemento[0].isdigit(),
                                     int(elemento[0]) if elemento[0].isdigit()
                                     else elemento[0]))),
        )

        _escribir_csv_atomico(
            BASE / ARCHIVO_METABOLITOS_PENDIENTES,
            ["ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR",
             "REGISTROS_SIN_CLASE", "BATCHES", "ID_CLASE_CANDIDATA",
             "CLASE_CANDIDATA", "ID_METABOLITO_COINCIDENTE",
             "ESTADO_SUGERENCIA"],
            (_fila_metabolito_pendiente(metabolito, resumen,
                                        clases_por_nombre_formula, clases)
             for metabolito, resumen in sorted(
                metabolitos_sin_clase.items(),
                key=lambda elemento: (-elemento[1]["registros"], elemento[0]))),
        )
    finally:
        if temporal is not None and os.path.exists(temporal):
            os.unlink(temporal)


# Las clases "--" y vacías representan falta de clasificación, no categorías.
_CLASES_SIN_CLASIFICAR = {
    "", "--", "unclassified", "sin clasificar", "null", "none", "na", "n/a", "nan",
}


def _ruta_patrones_quimicos() -> Path:
    unificado = BASE / ARCHIVO_PATRONES_UNIFICADO
    if unificado.is_file():
        return unificado
    _cargar_dependencias_legadas()
    asegurar_dataset_patrones_quimicos()
    return BASE / ARCHIVO_PATRONES


# Construye perfiles de especie a partir de corridas independientes. La clave
# de corrida incluye artículo, muestra, lote, modo de ionización y archivo para
# evitar colisiones de ID_MUESTRA entre estudios o polaridades.
@functools.lru_cache(maxsize=1)
def _perfiles_por_planta() -> tuple[dict, list[str], str]:
    ruta = _ruta_patrones_quimicos()
    corridas: dict[tuple[str, ...], dict] = {}
    clases_por_muestra: dict[tuple[str, ...], set[str]] = {}
    with open(ruta, encoding="utf-8-sig", newline="") as fin:
        lector = csv.DictReader(fin, delimiter=";")
        requeridas = {"ID_MUESTRA", "REF_ESPECIE", "CLASE_QUIMICA", "ALTURA_PICO"}
        if lector.fieldnames is None or not requeridas.issubset(lector.fieldnames):
            faltantes = sorted(requeridas - set(lector.fieldnames or []))
            raise datos.DatasetError(
                f"{ruta.name}: faltan columnas requeridas: {', '.join(faltantes)}.")
        for numero_fila, fila in enumerate(lector, 2):
            especie = (fila.get("REF_ESPECIE") or "").strip()
            if not especie:
                continue
            muestra = (fila.get("ID_MUESTRA") or "").strip()
            if not muestra:
                raise datos.DatasetError(
                    f"{ruta.name}: ID_MUESTRA vacío en la fila {numero_fila}.")
            clave_corrida = tuple(
                (fila.get(columna) or "").strip()
                for columna in (
                    "ID_ARTICULO", "ID_MUESTRA", "ID_BATCH", "REF_ESPECIE",
                    "MODO_IONIZACION", "ARCHIVO_ORIGEN",
                )
            )
            corrida = corridas.setdefault(clave_corrida, {
                "especie": especie, "muestra": muestra,
                "batch": (fila.get("ID_BATCH") or "").strip(),
                "registros": 0, "clasificados": 0, "positivos": 0,
                "clases": Counter(), "presentes": set(),
            })
            corrida["registros"] += 1
            clase = (fila.get("CLASE_QUIMICA") or "").strip()
            if clase.casefold() in _CLASES_SIN_CLASIFICAR:
                continue
            corrida["clasificados"] += 1
            corrida["presentes"].add(clase)
            clave_muestra = tuple(
                (fila.get(columna) or "").strip()
                for columna in (
                    "ID_ARTICULO", "ID_MUESTRA", "ID_BATCH", "REF_ESPECIE",
                )
            )
            clases_por_muestra.setdefault(clave_muestra, set()).add(clase)
            try:
                altura = float(fila.get("ALTURA_PICO", ""))
            except (TypeError, ValueError):
                continue
            if math.isfinite(altura) and altura > 0:
                corrida["positivos"] += 1
                corrida["clases"][clase] += altura

    perfiles: dict[str, dict] = {}
    clases_usadas: set[str] = set()
    for corrida in corridas.values():
        especie = corrida["especie"]
        perfil = perfiles.setdefault(especie, {
            "clases": Counter(), "presentes": set(), "muestras": set(),
            "lotes": set(), "registros_identificados": 0,
            "registros_clasificados": 0, "registros_clasificados_altura_positiva": 0,
            "corridas_utiles": 0, "muestras_clasificadas": 0,
            "prevalencia_muestras": Counter(),
        })
        perfil["muestras"].add(corrida["muestra"])
        if corrida["batch"]:
            perfil["lotes"].add(corrida["batch"])
        perfil["registros_identificados"] += corrida["registros"]
        perfil["registros_clasificados"] += corrida["clasificados"]
        perfil["registros_clasificados_altura_positiva"] += corrida["positivos"]
        perfil["presentes"].update(corrida["presentes"])
        clases_usadas.update(corrida["presentes"])
        total = sum(corrida["clases"].values())
        if total > 0:
            perfil["corridas_utiles"] += 1
            for clase, abundancia in corrida["clases"].items():
                perfil["clases"][clase] += abundancia / total

    for perfil in perfiles.values():
        if perfil["corridas_utiles"]:
            for clase in perfil["clases"]:
                perfil["clases"][clase] /= perfil["corridas_utiles"]
    for clave_muestra, clases in clases_por_muestra.items():
        especie = clave_muestra[3]
        perfil = perfiles[especie]
        perfil["muestras_clasificadas"] += 1
        perfil["prevalencia_muestras"].update(clases)
    return perfiles, sorted(clases_usadas), ruta.name


def _columnas_clase(clases: list[str]) -> list[str]:
    return [f"CQ_{i:04d}_{_slug(clase)}" for i, clase in enumerate(clases)]


def _leer_tabla_04(nombre: str) -> tuple[list[str], list[list[str]]]:
    asegurar_dataset_patrones_quimicos()
    ruta = BASE / nombre
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo, delimiter=";")
        encabezado = next(lector, None)
        if not encabezado:
            raise datos.DatasetError(f"{nombre}: el archivo está vacío o no tiene encabezado.")
        filas = [fila for fila in lector if fila]
    return encabezado, filas


def _indice_encabezado(encabezado: list[str], nombre: str, archivo: str) -> int:
    try:
        return encabezado.index(nombre)
    except ValueError as exc:
        raise datos.DatasetError(
            f"{archivo}: falta la columna requerida {nombre!r}.") from exc


def _numero(fila: list[str], indice: int, archivo: str, columna: str) -> float:
    try:
        valor = float(fila[indice])
    except (ValueError, IndexError) as exc:
        raise datos.DatasetError(
            f"{archivo}: valor numérico inválido en {columna!r}: "
            f"{fila[indice] if indice < len(fila) else '<faltante>'!r}.") from exc
    if not math.isfinite(valor):
        raise datos.DatasetError(f"{archivo}: valor no finito en {columna!r}.")
    return valor


def construir_dataset_04(objetivo: str) -> datos.Dataset:
    """Construye features numéricas pertinentes a partir de un CSV 04 concreto."""
    if objetivo not in _ARCHIVOS_04:
        raise ValueError(f"Dataset 04 desconocido: {objetivo!r}.")
    archivo = _ARCHIVOS_04[objetivo]
    encabezado, origen = _leer_tabla_04(archivo)
    filas: list[list[object]] = []

    if objetivo == "PATRONES_QUIMICOS":
        raise ValueError(
            "04_Dataset_Patrones_Quimicos.csv se entrena mediante perfiles químicos "
            "por muestra, reglas de asociación o secuencias de Markov.")

    if objetivo == "CALIDAD_BATCH":
        columnas = [
            "ID_BATCH", "NOMBRE_BATCH", "MUESTRAS", "REGISTROS_IDENTIFICADOS",
            "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
            "ESTADO_COBERTURA", "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ]
        indices = {nombre: _indice_encabezado(encabezado, nombre, archivo)
                   for nombre in columnas}
        for fila in origen:
            batch = fila[indices["ID_BATCH"]]
            identificados = _numero(
                fila, indices["REGISTROS_IDENTIFICADOS"], archivo,
                "REGISTROS_IDENTIFICADOS")
            clasificados = _numero(
                fila, indices["REGISTROS_CLASIFICADOS"], archivo,
                "REGISTROS_CLASIFICADOS")
            filas.append([
                batch,
                fila[indices["NOMBRE_BATCH"]],
                fila[indices["ESTADO_COBERTURA"]],
                _numero(fila, indices["MUESTRAS"], archivo, "MUESTRAS"),
                identificados,
                clasificados,
                max(identificados - clasificados, 0.0),
                _numero(fila, indices["COBERTURA_CLASIFICACION_PCT"],
                        archivo, "COBERTURA_CLASIFICACION_PCT"),
                _numero(fila, indices["ALTURA_FALTANTE"], archivo, "ALTURA_FALTANTE"),
                _numero(fila, indices["ALTURA_INVALIDA"], archivo, "ALTURA_INVALIDA"),
            ])
        encabezado_dataset = [
            "ID", "REF_BATCH", "REF_BATCH_NOMBRE", "REF_ESTADO_COBERTURA",
            "MUESTRAS", "REGISTROS_IDENTIFICADOS", "REGISTROS_CLASIFICADOS",
            "REGISTROS_SIN_CLASIFICAR", "COBERTURA_CLASIFICACION_PCT",
            "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ]
        nombre_dataset = "Calidad de perfiles por batch"

    elif objetivo == "CALIDAD_MUESTRA":
        columnas = [
            "ID_MUESTRA", "ID_BATCH", "NOMBRE_BATCH", "REGISTROS_IDENTIFICADOS",
            "REGISTROS_CLASIFICADOS", "COBERTURA_CLASIFICACION_PCT",
            "ESTADO_COBERTURA", "CLASES_QUIMICAS_DISTINTAS",
            "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ]
        indices = {nombre: _indice_encabezado(encabezado, nombre, archivo)
                   for nombre in columnas}
        for fila in origen:
            batch = fila[indices["ID_BATCH"]]
            cobertura = _numero(
                fila, indices["COBERTURA_CLASIFICACION_PCT"],
                archivo, "COBERTURA_CLASIFICACION_PCT")
            filas.append([
                fila[indices["ID_MUESTRA"]],
                batch,
                fila[indices["NOMBRE_BATCH"]],
                fila[indices["ESTADO_COBERTURA"]],
                cobertura,
                _numero(fila, indices["REGISTROS_IDENTIFICADOS"],
                        archivo, "REGISTROS_IDENTIFICADOS"),
                _numero(fila, indices["REGISTROS_CLASIFICADOS"],
                        archivo, "REGISTROS_CLASIFICADOS"),
                _numero(fila, indices["CLASES_QUIMICAS_DISTINTAS"],
                        archivo, "CLASES_QUIMICAS_DISTINTAS"),
                _numero(fila, indices["ALTURA_FALTANTE"], archivo, "ALTURA_FALTANTE"),
                _numero(fila, indices["ALTURA_INVALIDA"], archivo, "ALTURA_INVALIDA"),
            ])
        encabezado_dataset = [
            "ID", "REF_BATCH", "REF_BATCH_NOMBRE", "REF_ESTADO_COBERTURA",
            "REF_COBERTURA_CLASIFICACION_PCT", "REGISTROS_IDENTIFICADOS",
            "REGISTROS_CLASIFICADOS", "CLASES_QUIMICAS_DISTINTAS",
            "ALTURA_FALTANTE", "ALTURA_INVALIDA",
        ]
        nombre_dataset = "Calidad química por muestra"

    else:
        columnas = [
            "ID_METABOLITO", "NOMBRE_METABOLITO", "FORMULA_MOLECULAR",
            "REGISTROS_SIN_CLASE", "BATCHES", "ID_CLASE_CANDIDATA",
            "CLASE_CANDIDATA", "ESTADO_SUGERENCIA",
        ]
        indices = {nombre: _indice_encabezado(encabezado, nombre, archivo)
                   for nombre in columnas}
        elementos: set[str] = set()
        datos_formula: list[tuple[str, Counter[str], bool]] = []
        for fila in origen:
            formula = fila[indices["FORMULA_MOLECULAR"]].strip()
            tokens = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
            valida = bool(formula) and "".join(
                elemento + cantidad for elemento, cantidad in tokens) == formula
            conteo: Counter[str] = Counter()
            if valida:
                for elemento, cantidad in tokens:
                    conteo[elemento] += int(cantidad) if cantidad else 1
            elementos.update(conteo)
            datos_formula.append((fila[indices["ID_METABOLITO"]], conteo, valida))

        elementos_ordenados = sorted(elementos)
        for fila, (_, conteo, valida) in zip(origen, datos_formula):
            formula = fila[indices["FORMULA_MOLECULAR"]].strip()
            batches = {
                batch.strip() for batch in fila[indices["BATCHES"]].split(",")
                if batch.strip()
            }
            filas.append([
                fila[indices["ID_METABOLITO"]],
                fila[indices["ESTADO_SUGERENCIA"]],
                fila[indices["CLASE_CANDIDATA"]],
                _numero(fila, indices["REGISTROS_SIN_CLASE"], archivo, "REGISTROS_SIN_CLASE"),
                len(batches),
                len(formula),
                int(valida),
                *[conteo.get(elemento, 0) for elemento in elementos_ordenados],
            ])
        encabezado_dataset = [
            "ID", "REF_ESTADO_SUGERENCIA", "REF_CLASE_CANDIDATA",
            "REGISTROS_SIN_CLASE", "BATCHES_DISTINTOS",
            "LONGITUD_FORMULA", "FORMULA_VALIDA",
            *[f"ATOMOS_{elemento}" for elemento in elementos_ordenados],
        ]
        nombre_dataset = "Metabolitos sin clase química (descriptores moleculares)"

    texto = _texto_csv(encabezado_dataset, filas)
    return datos.desde_texto(
        nombre_dataset, texto, requiere_objetivo=False, archivo_fuente=archivo)


# Cada planta aporta el promedio de la composición relativa de sus corridas
# con señal química válida; las features son clases químicas.
def construir_perfil_continuo() -> datos.Dataset:
    perfiles, clases, archivo_fuente = _perfiles_por_planta()
    orden_clases = [clase for clase in clases if any(
        perfil["clases"].get(clase, 0.0) > 0 for perfil in perfiles.values())]
    if not orden_clases:
        raise datos.DatasetError(
            "No hay abundancias positivas válidas para construir perfiles químicos continuos.")
    columnas = _columnas_clase(orden_clases)
    header = [
        "ID_PLANTA", "REF_ESPECIE", "REF_CANTIDAD_MUESTRAS",
        "REF_CANTIDAD_LOTES", "REF_CORRIDAS_UTILIZADAS",
        "REF_REGISTROS_IDENTIFICADOS", "REF_REGISTROS_CLASIFICADOS",
        "REF_COBERTURA_CLASIFICACION_PCT",
        "REF_REGISTROS_CLASIFICADOS_ALTURA_POSITIVA",
        "REF_COBERTURA_QUIMICA_UTIL_PCT",
    ] + columnas

    def filas():
        for especie, perfil in sorted(perfiles.items()):
            if not perfil["corridas_utiles"]:
                continue
            total = perfil["registros_identificados"]
            clasificados = perfil["registros_clasificados"]
            positivos = perfil["registros_clasificados_altura_positiva"]
            ref = [
                especie, especie, str(len(perfil["muestras"])),
                str(len(perfil["lotes"])), str(perfil["corridas_utiles"]),
                str(total), str(clasificados),
                f"{100 * clasificados / total:.4f}" if total else "0.0000",
                str(positivos),
                f"{100 * positivos / total:.4f}" if total else "0.0000",
            ]
            valores = [
                f"{perfil['clases'].get(clase, 0.0):.8f}" for clase in orden_clases
            ]
            yield ref + valores

    return datos.desde_texto("Perfil químico vegetal por especie (composición relativa)",
                             _texto_csv(header, filas()),
                             requiere_objetivo=False,
                             archivo_fuente=archivo_fuente)


# Reglas de asociación: presencia recurrente en muestras biologicas
# clasificadas; polaridades/archivos de una misma muestra no cuentan varias
# veces como replicas.
def construir_perfil_binario() -> datos.Dataset:
    perfiles, orden_clases, archivo_fuente = _perfiles_por_planta()
    columnas = _columnas_clase(orden_clases)
    header = [
        "ID_PLANTA", "REF_ESPECIE", "REF_CANTIDAD_MUESTRAS_CLASIFICADAS",
    ] + columnas
    prevalencia_minima = config.REGLAS_MIN_PREVALENCIA_MUESTRAS

    filas = (
        [
            especie, especie, str(perfil["muestras_clasificadas"]),
        ] + [
            "1" if (
                perfil["muestras_clasificadas"] > 0
                and perfil["prevalencia_muestras"].get(clase, 0)
                    / perfil["muestras_clasificadas"] >= prevalencia_minima
            ) else "0"
            for clase in orden_clases
        ]
        for especie, perfil in sorted(perfiles.items())
        if perfil["muestras_clasificadas"] > 0
    )
    return datos.desde_texto(
        "Perfil químico vegetal por especie (presencia recurrente por muestra)",
        _texto_csv(header, filas),
                             requiere_objetivo=False,
        archivo_fuente=archivo_fuente)


# --- Cadenas de Markov -------------------------------------------------
# Secuencia = clases quimicas de una corrida, ordenadas por tiempo de retencion.
# Cada combinacion de estudio, muestra, lote, especie, modo y archivo conserva
# una secuencia independiente.
@functools.lru_cache(maxsize=1)
def construir_secuencias() -> datos.Dataset:
    ruta = _ruta_patrones_quimicos()
    filas_por_secuencia: dict[tuple[str, ...], list[tuple[float, str]]] = {}
    with open(ruta, encoding="utf-8-sig", newline="") as fin:
        lector = csv.DictReader(fin, delimiter=";")
        requeridas = {"ID_MUESTRA", "CLASE_QUIMICA", "TIEMPO_RETENCION_MIN"}
        if lector.fieldnames is None or not requeridas.issubset(lector.fieldnames):
            faltantes = sorted(requeridas - set(lector.fieldnames or []))
            raise datos.DatasetError(
                f"{ruta.name}: faltan columnas requeridas: {', '.join(faltantes)}.")
        for fila in lector:
            nombre_clase = (fila.get("CLASE_QUIMICA") or "").strip()
            if nombre_clase.casefold() in _CLASES_SIN_CLASIFICAR:
                continue
            estado = nombre_clase or (fila.get("ID_CLASE_QUIMICA") or "").strip()
            try:
                rt = float(fila.get("TIEMPO_RETENCION_MIN", ""))
            except (TypeError, ValueError):
                continue
            if math.isfinite(rt):
                muestra = (fila.get("ID_MUESTRA") or "").strip()
                if not muestra or not estado:
                    continue
                clave = tuple((fila.get(columna) or "").strip() for columna in (
                    "ID_ARTICULO", "ID_MUESTRA", "ID_BATCH", "REF_ESPECIE",
                    "MODO_IONIZACION", "ARCHIVO_ORIGEN",
                ))
                filas_por_secuencia.setdefault(clave, []).append((rt, estado))

    header = [
        "ID", "REF_SECUENCIA", "REF_ARTICULO", "REF_MUESTRA",
        "REF_BATCH", "REF_BATCH_NOMBRE", "REF_ESPECIE",
        "REF_MODO_IONIZACION", "REF_ARCHIVO_ORIGEN", "REF_POSICION",
        "REF_ESTADO", "CODIGO_ESTADO",
    ]
    estados = sorted({estado for eventos in filas_por_secuencia.values()
                      for _, estado in eventos})
    codigo_estado = {estado: indice for indice, estado in enumerate(estados)}

    def filas():
        for numero, (clave, eventos) in enumerate(sorted(filas_por_secuencia.items()), 1):
            articulo, muestra, batch, especie, modo, archivo = clave
            id_secuencia = f"SEQ_{numero:08d}"
            eventos.sort(key=lambda e: (e[0], e[1]))  # RT y clase para desempatar
            for posicion, (_, estado) in enumerate(eventos):
                yield [
                    f"{id_secuencia}-{posicion}", id_secuencia, articulo, muestra,
                    batch, NOMBRE_BATCH.get(batch, ""), especie, modo, archivo,
                    str(posicion), estado, str(codigo_estado[estado]),
                ]

    return datos.desde_texto("Cadenas de Markov", _texto_csv(header, filas()),
                             requiere_objetivo=False,
                             archivo_fuente=ruta.name)
