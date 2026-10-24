"""Archivos y columnas que usa cada experimento para entrenar (bloque `datos_entrenamiento` de config/modelos/*.yaml).

Supervisado (tarea: supervisado; hay variable objetivo):

    datos_entrenamiento:
      tipo_aprendizaje: supervisado
      objetivo: ID_FAMILIA                # columna que el modelo aprende a predecir
      grupos_validacion: ID_ARTICULO      # un grupo nunca se reparte entre entrenamiento y prueba
      archivos:
        dataset:
          ruta: 10_Dataset_final/Dataset.csv
          entrada: [ID_CLASE_QUIMICA, ID_METABOLITO]     # origen de las variables X
          objetivo: [ID_FAMILIA]
          grupos_validacion: [ID_ARTICULO]
          control_instrumental: [ID_COLUMNA_CROMATOGRAFICA, ID_MODO_IONIZACION]
          filtros_agregacion: [ID_MUESTRA, ID_TIPO_MUESTRA]
      variables: {incluir: [], excluir: []}

No supervisado (tarea: patrones; sin objetivo ni grupos de validacion):

    datos_entrenamiento:
      tipo_aprendizaje: no_supervisado
      archivos:
        dataset:
          ruta: 10_Dataset_final/Dataset.csv
          entrada: [ID_SUPERCLASE_QUIMICA, ID_CLASE_QUIMICA, ID_METABOLITO]
          factores_contraste: [ID_FAMILIA, ID_PARTE_ESTUDIADA]
          filtros_agregacion: [ID_MUESTRA, ID_TIPO_MUESTRA]

Efecto de cada clave:
- `objetivo` (supervisado): es la variable objetivo del experimento. En los conjuntos con objetivo configurable
  (perfil_muestra, metabolito_quimica) se toma de aqui; en los demas debe coincidir con el objetivo fijo del conjunto.
- `entrada` y `control_instrumental`: quitar una columna elimina las variables derivadas de ella (p. ej. quitar
  ID_SUPERCLASE_QUIMICA quita todas las variables de superclase). No se pueden anadir columnas que el conjunto no sabe
  usar ni quitar las que necesita para construir la unidad de analisis.
- `objetivo`, `grupos_validacion` (por archivo): deben coincidir con lo que usa el conjunto.
- `filtros_agregacion` y `factores_contraste`: informativos; si no coinciden con lo que usa el codigo se avisa.
- `variables.incluir/excluir`: seleccion fina sobre las variables ya construidas (comodines * ?), por nombre de la
  variable (p. ej. `ID_FAMILIA_6`, `clase_240`, `dbe`) o por su columna de origen (`FORMULA_MOLECULAR`).
- `ruta`: relativa a datos.catalogos de config/rutas.yaml, o absoluta. Tambien se acepta la forma corta
  `dataset: 10_Dataset_final/Dataset.csv` (solo la ruta).

`python main.py datos M05` muestra el bloque efectivo sin entrenar y `--escribir-yaml` lo regenera en el YAML a partir
del codigo (conserva rutas, columnas quitadas y la seleccion de variables). Cada ejecucion registra en consola,
ejecucion.log, datos_entrenamiento.md/.json e informe.md los archivos, columnas por rol y variables finales.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import pandas as pd

from ..data.catalogos import (ARCHIVOS_FIJADOS, NOMBRES_ARCHIVO, ErrorDatos, cargar_catalogo, ruta_archivo,
                              verificar_archivo_datos)
from ..utils.rutas import config_global, raiz_proyecto, ruta
from .conjuntos import CATALOGO_DE, nombre_variable
from .perfiles import ATRIBUTOS_MUESTRA, ATRIBUTOS_PLATAFORMA, NIVEL_QUIMICO
from .quimica import descriptores

ROLES = {"X": "variables de entrada", "y": "objetivo", "grupos": "grupos de validacion",
         "instrumental": "control instrumental", "factores": "factores de contraste", "filtros": "filtros y agregacion"}
# clave del YAML -> rol interno
CLAVES_ROL = {"entrada": "X", "objetivo": "y", "grupos_validacion": "grupos", "control_instrumental": "instrumental",
              "factores_contraste": "factores", "filtros_agregacion": "filtros"}
CLAVE_DE_ROL = {v: k for k, v in CLAVES_ROL.items()}
TIPO_DE_TAREA = {"supervisado": "supervisado", "patrones": "no_supervisado"}
ROLES_POR_TIPO = {"supervisado": ["X", "y", "grupos", "instrumental", "filtros"],
                  "no_supervisado": ["X", "factores", "filtros"]}
ROLES_INFORMATIVOS = {"filtros", "factores"}   # en no supervisado tambien "X" (los perfiles los fija `patrones`)
# conjuntos cuyo objetivo se configura (el resto tiene un objetivo fijo)
OBJETIVO_CONFIGURABLE = {"perfil_muestra": None, "metabolito_quimica": "ID_SUPERCLASE_QUIMICA"}
DESCRIPTORES_FORMULA = list(descriptores("CH4"))
INSTRUMENTALES_ORIGEN = ["ID_COLUMNA_CROMATOGRAFICA", "ID_MODO_IONIZACION"] + ATRIBUTOS_PLATAFORMA + [
    "ID_METABOLITO", "ID_NIVEL_IDENTIFICACION"]
# vista_quimica() quita la replicacion por medidas de actividad con el registro de actividades
_VISTA_QUIMICA = {"dataset": {"filtros": ["ID_MUESTRA", "ID_ACTIVIDAD_BIOLOGICA", "ID_METABOLITO",
                                          "ID_NIVEL_IDENTIFICACION"]},
                  "registro_actividades": {"filtros": ["ID_MUESTRA"]}}


# ---------------------------------------------------------------------------------------------------------------------
# Columnas de origen de cada conjunto
# ---------------------------------------------------------------------------------------------------------------------
def _unir(*partes: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = {}
    for p in partes:
        for archivo, roles in p.items():
            for rol, cols in roles.items():
                lista = out.setdefault(archivo, {}).setdefault(rol, [])
                lista[:] = list(dict.fromkeys(lista + [c for c in cols if c]))
    return {a: {r: roles[r] for r in ROLES if r in roles} for a, roles in out.items()}


def _perfil(nivel: str, extra_filtros: list[str] | None = None) -> dict[str, dict[str, list[str]]]:
    return {"dataset": {"X": [NIVEL_QUIMICO[nivel], "ID_METABOLITO"],
                        "filtros": ["ID_MUESTRA", "ID_TIPO_MUESTRA"] + (extra_filtros or [])}}


def columnas_origen(cfg: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Archivo logico -> rol -> columnas que se leen de el para construir el conjunto del experimento."""
    if cfg.get("tarea") == "patrones":
        pc = cfg.get("patrones", {})
        factores = list(pc.get("factores_enriquecimiento", [])) + list(pc.get("reglas", {}).get("items_taxonomicos", []))
        return _unir(_VISTA_QUIMICA, {
            "dataset": {"X": ["ID_SUPERCLASE_QUIMICA", "ID_CLASE_QUIMICA", "ID_METABOLITO"],
                        "factores": factores + ["ID_ARTICULO", "ID_COLUMNA_CROMATOGRAFICA", "ID_METODO_EXTRACCION",
                                         "ID_TIPO_CULTIVO", "ID_ESPECIE"],
                        "filtros": ["ID_MUESTRA", "ID_TIPO_MUESTRA", "ID_PARTE_ESTUDIADA"]},
            "registro_actividades": {"X": ["ID_METABOLITO"], "factores": ["ID_ACTIVIDAD_BIOLOGICA"]},
            "metabolitos": {"X": ["ID_METABOLITO", "ID_CLASE_QUIMICA"]},
            "clases_quim": {"X": ["ID_CLASE_QUIMICA", "ID_SUPERCLASE_QUIMICA"]},
            "familias": {"filtros": ["ID_FAMILIA", "FAMILIA"]}})
    conj = cfg.get("conjunto", {})
    nombre, par = conj.get("nombre"), conj.get("parametros", {}) or {}
    sup = ["ID_SUPERCLASE_QUIMICA"] if par.get("incluir_superclase", True) else []
    instr = {"dataset": {"instrumental": INSTRUMENTALES_ORIGEN}}
    if nombre == "metabolito_quimica":
        objetivo = par.get("objetivo", "ID_SUPERCLASE_QUIMICA")
        return _unir(_VISTA_QUIMICA, {
            "metabolitos": {"X": ["FORMULA_MOLECULAR"], "grupos": ["FORMULA_MOLECULAR"],
                            "filtros": ["ID_METABOLITO", "ID_CLASE_QUIMICA"]},
            "clases_quim": {"y": [objetivo], "filtros": ["ID_CLASE_QUIMICA"]}})
    if nombre == "metabolito_modo":
        return _unir(_VISTA_QUIMICA, {"dataset": {"X": ["FORMULA_MOLECULAR"] + sup, "y": ["ID_MODO_IONIZACION"],
                                                  "grupos": ["ID_ARTICULO"]}})
    if nombre == "metabolito_aducto":
        return _unir(_VISTA_QUIMICA, {"dataset": {"X": ["FORMULA_MOLECULAR", "ID_MODO_IONIZACION"] + sup,
                                                  "y": ["ID_ADUCTO"], "grupos": ["ID_ARTICULO"],
                                                  "instrumental": ["ID_MODO_IONIZACION"]}})
    if nombre == "actividad_metabolito":
        return _unir({
            "registro_actividades": {"y": ["ID_ACTIVIDAD_BIOLOGICA"], "filtros": ["ID_METABOLITO"]},
            "metabolitos": {"X": ["FORMULA_MOLECULAR"] + (["ID_CLASE_QUIMICA"] if sup else []),
                            "grupos": ["FORMULA_MOLECULAR"], "filtros": ["ID_METABOLITO"]},
            "clases_quim": {"X": ["ID_CLASE_QUIMICA"] + sup} if sup else {}})
    if nombre == "perfil_muestra":
        instr = {"dataset": {"instrumental": [c for c in INSTRUMENTALES_ORIGEN if c != par.get("objetivo")]}}
        return _unir(_VISTA_QUIMICA, _perfil(par.get("nivel", "superclase"), par.get("agregar_por")), instr,
                     {"dataset": {"y": [par.get("objetivo")], "grupos": ["ID_ARTICULO"]}})
    if nombre == "presencia_metabolitos":
        por = par.get("agregar_por") or ["ID_BATCH", "ID_ESPECIE", "ID_PARTE_ESTUDIADA", "ID_TIPO_MUESTRA",
                                         "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION"]
        pred = par.get("predictores") or ["ID_CLASE_TAXONOMICA", "ID_ORDEN", "ID_FAMILIA", "ID_PARTE_ESTUDIADA",
                                          "ID_TIPO_MUESTRA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION"]
        return _unir(_VISTA_QUIMICA, instr, {"dataset": {"X": pred, "y": ["ID_METABOLITO"], "grupos": ["ID_ARTICULO"],
                                                         "filtros": ["ID_MUESTRA", "ID_TIPO_MUESTRA"] + por}})
    if nombre == "actividad_especie":
        return _unir(_VISTA_QUIMICA, _perfil(par.get("nivel", "superclase"), ["ID_ESPECIE"]), instr,
                     {"dataset": {"grupos": ["ID_ARTICULO"]},
                      "registro_actividades": {"y": ["ID_ACTIVIDAD_BIOLOGICA"],
                                               "filtros": ["ID_ARTICULO", "ID_ESPECIE"]}})
    return {}


# ---------------------------------------------------------------------------------------------------------------------
# Archivos (rutas parametrizables)
# ---------------------------------------------------------------------------------------------------------------------
def _resolver(valor: str | Path) -> Path:
    p = Path(valor)
    return p if p.is_absolute() else ruta("datos", "catalogos") / p


def _bloque(cfg: dict[str, Any]) -> dict[str, Any]:
    de = cfg.get("datos_entrenamiento")
    return de if isinstance(de, dict) else {}


def tipo_aprendizaje(cfg: dict[str, Any]) -> str:
    return TIPO_DE_TAREA.get(str(cfg.get("tarea")), "supervisado")


def archivos_configurados(cfg: dict[str, Any]) -> dict[str, str]:
    """Archivo logico -> ruta (acepta `dataset: ruta` o `dataset: {ruta: ...}`)."""
    out = {}
    for k, v in (_bloque(cfg).get("archivos") or {}).items():
        r = v.get("ruta") if isinstance(v, dict) else v
        if isinstance(r, str) and r.strip():
            out[k] = r
    return out


def roles_declarados(cfg: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Archivo -> rol interno -> columnas declaradas en el YAML (solo archivos escritos con la forma completa)."""
    out: dict[str, dict[str, list[str]]] = {}
    for k, v in (_bloque(cfg).get("archivos") or {}).items():
        if isinstance(v, dict):
            out[k] = {CLAVES_ROL[c]: [str(x) for x in (cols or [])] for c, cols in v.items()
                      if c in CLAVES_ROL and isinstance(cols, list)}
    return out


def _declarado(cfg: dict[str, Any], rol: str) -> list[str] | None:
    """Union de las columnas declaradas para `rol` (None si ningun archivo usa la forma completa)."""
    decl = roles_declarados(cfg)
    if not decl:
        return None
    return list(dict.fromkeys(c for roles in decl.values() for c in roles.get(rol, [])))


def _computado(cfg: dict[str, Any], rol: str) -> list[str]:
    return list(dict.fromkeys(c for roles in columnas_origen(cfg).values() for c in roles.get(rol, [])))


def sincronizar(cfg: dict[str, Any]) -> list[str]:
    """Lleva `datos_entrenamiento.objetivo` y `grupos_validacion` a la configuracion del conjunto y del split
    (modifica cfg; es idempotente). Devuelve los errores de coherencia."""
    de = _bloque(cfg)
    errores: list[str] = []
    if cfg.get("tarea") != "supervisado" or not isinstance(cfg.get("conjunto"), dict):
        return errores
    conj = cfg["conjunto"]
    objetivo = de.get("objetivo")
    if conj.get("nombre") in OBJETIVO_CONFIGURABLE and isinstance(objetivo, str) and objetivo:
        par = conj.get("parametros")
        if par is None:
            par = conj["parametros"] = {}
        if isinstance(par, dict):
            previo = par.get("objetivo")
            if previo and previo != objetivo:
                errores.append(f"conjunto.parametros.objetivo ({previo}) contradice datos_entrenamiento.objetivo "
                               f"({objetivo}); deje solo datos_entrenamiento.objetivo")
            par["objetivo"] = objetivo
    if conj.get("nombre") == "perfil_muestra" and not (conj.get("parametros") or {}).get("objetivo"):
        errores.append("falta la variable objetivo: indique datos_entrenamiento.objetivo (p. ej. ID_FAMILIA)")
    grupos = de.get("grupos_validacion")
    if isinstance(grupos, str) and grupos and isinstance(cfg.get("split"), dict):
        cfg["split"]["group_column"] = grupos
    return errores


def validar_declaracion(cfg: dict[str, Any]) -> list[str]:
    """Coherencia del bloque `datos_entrenamiento` con la tarea y con lo que usa el conjunto (sin leer datos)."""
    de = _bloque(cfg)
    if not de:
        return []
    errores: list[str] = []
    tipo = tipo_aprendizaje(cfg)
    completo = bool(roles_declarados(cfg)) or "tipo_aprendizaje" in de
    if "tipo_aprendizaje" in de and de["tipo_aprendizaje"] != tipo:
        errores.append(f"datos_entrenamiento.tipo_aprendizaje='{de['tipo_aprendizaje']}' no corresponde a "
                       f"tarea: {cfg.get('tarea')} (debe ser '{tipo}')")
    elif completo and "tipo_aprendizaje" not in de:
        errores.append(f"falta datos_entrenamiento.tipo_aprendizaje (debe ser '{tipo}')")
    if tipo == "no_supervisado":
        for k in ("objetivo", "grupos_validacion"):
            if k in de:
                errores.append(f"datos_entrenamiento.{k}: un experimento no supervisado (tarea: patrones) no tiene "
                               f"{'variable objetivo' if k == 'objetivo' else 'grupos de validacion'}")
    elif completo:
        for k in ("objetivo", "grupos_validacion"):
            v = de.get(k)
            if not isinstance(v, str) or not v:
                errores.append(f"falta datos_entrenamiento.{k} (columna, texto)")
                continue
            usado = _computado(cfg, CLAVES_ROL[k])
            if usado and usado != [v]:
                errores.append(f"datos_entrenamiento.{k}={v}, pero el conjunto '{cfg['conjunto'].get('nombre')}' usa "
                               f"{', '.join(usado)}")
    permitidos = set(ROLES_POR_TIPO[tipo])
    calculado = columnas_origen(cfg) if not errores else {}
    for archivo, v in (de.get("archivos") or {}).items():
        if not isinstance(v, dict):
            continue
        for c, cols in v.items():
            if c == "ruta":
                continue
            if c not in CLAVES_ROL:
                errores.append(f"datos_entrenamiento.archivos.{archivo}.{c} no es valida; use ruta o "
                               + ", ".join(CLAVE_DE_ROL[r] for r in ROLES_POR_TIPO[tipo]))
            elif CLAVES_ROL[c] not in permitidos:
                errores.append(f"datos_entrenamiento.archivos.{archivo}.{c} no aplica a un experimento {tipo}")
            elif not isinstance(cols, list) or not all(isinstance(x, str) for x in cols):
                errores.append(f"datos_entrenamiento.archivos.{archivo}.{c} debe ser una lista de columnas")
        if not isinstance(v.get("ruta"), str) or not v.get("ruta", "").strip():
            errores.append(f"datos_entrenamiento.archivos.{archivo}.ruta debe ser una ruta (texto)")
    if errores:
        return errores
    for archivo, roles in roles_declarados(cfg).items():
        usa = calculado.get(archivo, {})
        for rol in ("y", "grupos"):
            if rol in roles and sorted(roles[rol]) != sorted(usa.get(rol, [])):
                errores.append(f"datos_entrenamiento.archivos.{archivo}.{CLAVE_DE_ROL[rol]}={roles[rol]}, pero el "
                               f"conjunto usa {usa.get(rol, [])} de ese archivo")
        for rol in (("X", "instrumental") if tipo == "supervisado" else ()):
            extra = [c for c in roles.get(rol, []) if c not in usa.get(rol, [])]
            if extra:
                errores.append(f"datos_entrenamiento.archivos.{archivo}.{CLAVE_DE_ROL[rol]}: el conjunto no sabe usar "
                               f"{extra} de este archivo (disponibles: {usa.get(rol, []) or 'ninguna'})")
    return errores


def avisos_declaracion(cfg: dict[str, Any]) -> list[str]:
    """Diferencias en los roles informativos (filtros, factores) entre el YAML y el codigo."""
    out = []
    usa = columnas_origen(cfg)
    informativos = ROLES_INFORMATIVOS | ({"X"} if tipo_aprendizaje(cfg) == "no_supervisado" else set())
    for archivo, roles in roles_declarados(cfg).items():
        for rol in sorted(informativos):
            d, u = set(roles.get(rol, [])), set(usa.get(archivo, {}).get(rol, []))
            if d != u and (d or u):
                out.append(f"{archivo}.{CLAVE_DE_ROL[rol]} del YAML ({sorted(d)}) no coincide con lo que usa el codigo "
                           f"({sorted(u)}); regenere con `python main.py datos {cfg.get('id')} --escribir-yaml`")
    return out


def roles_efectivos(cfg: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Columnas por rol que se usaran: las del conjunto, sin las de entrada o control quitadas en el YAML."""
    calc = columnas_origen(cfg)
    decl = roles_declarados(cfg) if tipo_aprendizaje(cfg) == "supervisado" else {}
    out = {}
    for archivo, roles in calc.items():
        r = {k: list(v) for k, v in roles.items()}
        for rol in ("X", "instrumental"):
            if archivo in decl and rol in r:
                r[rol] = [c for c in r[rol] if c in decl[archivo].get(rol, [])]
                if not r[rol]:
                    del r[rol]
        out[archivo] = r
    return out


def origenes_instrumental(col: str) -> list[str]:
    """Columnas de origen de una covariable del control instrumental."""
    if col.startswith(("MODOS_", "ID_MODO_IONIZACION_")) or col == "MODOS":
        return ["ID_MODO_IONIZACION"]
    if col == "log_n_identificados":
        return ["ID_METABOLITO", "ID_NIVEL_IDENTIFICACION"]
    if col == "log_n_senales":
        return ["ID_METABOLITO"]
    return [columna_de_variable(col)]


def aplicar_declaracion(conj: Any, cfg: dict[str, Any]) -> list[str]:
    """Quita de conj.X y conj.X_instrumental las variables cuyas columnas de origen se quitaron de `entrada` o de
    `control_instrumental` en el YAML. Devuelve las variables de entrada descartadas."""
    from ..config.esquema import ErrorConfiguracion
    descartadas: list[str] = []
    if tipo_aprendizaje(cfg) != "supervisado":
        return descartadas
    decl_x = _declarado(cfg, "X")
    if decl_x is not None:
        quitadas = [c for c in _computado(cfg, "X") if c not in decl_x]
        for origen in quitadas:
            vs = [c for c in conj.X.columns if columna_de_variable(c) == origen]
            if not vs:
                raise ErrorConfiguracion(
                    f"{cfg.get('id')}: {origen} no se puede quitar de datos_entrenamiento...entrada: el conjunto la "
                    "necesita para construir la unidad de analisis (no genera variables propias). Para reducir las "
                    "variables use datos_entrenamiento.variables.excluir")
            descartadas += vs
        if descartadas:
            conj.X = conj.X.drop(columns=descartadas)
            conj.notas.append(f"datos_entrenamiento: sin las columnas de entrada {quitadas} "
                              f"({len(descartadas)} variables menos).")
        if conj.X.shape[1] == 0:
            raise ErrorConfiguracion(f"{cfg.get('id')}: datos_entrenamiento...entrada no deja ninguna variable de entrada")
    decl_i = _declarado(cfg, "instrumental")
    if decl_i is not None and conj.X_instrumental is not None:
        quitadas = [c for c in _computado(cfg, "instrumental") if c not in decl_i]
        fuera = [c for c in conj.X_instrumental.columns if any(o in quitadas for o in origenes_instrumental(c))]
        if fuera:
            conj.X_instrumental = conj.X_instrumental.drop(columns=fuera)
            conj.notas.append(f"datos_entrenamiento: control instrumental sin {quitadas}.")
        if conj.X_instrumental.shape[1] == 0:
            conj.X_instrumental = None
            conj.notas.append("datos_entrenamiento: sin columnas de control instrumental; el control se omite.")
    return descartadas


def fijar_archivos(cfg: dict[str, Any]) -> dict[str, Path]:
    """Aplica las rutas de `datos_entrenamiento.archivos` (y vacia las caches si cambian). Devuelve las fijadas."""
    nuevas = {k: _resolver(v) for k, v in archivos_configurados(cfg).items()}
    nuevas = {k: v for k, v in nuevas.items() if v != _ruta_por_defecto(k)}
    if nuevas != ARCHIVOS_FIJADOS:
        ARCHIVOS_FIJADOS.clear()
        ARCHIVOS_FIJADOS.update(nuevas)
        _vaciar_caches()
    return dict(ARCHIVOS_FIJADOS)


def _ruta_por_defecto(nombre: str) -> Path:
    guardadas = dict(ARCHIVOS_FIJADOS)
    ARCHIVOS_FIJADOS.clear()
    try:
        return ruta_archivo(nombre)
    finally:
        ARCHIVOS_FIJADOS.update(guardadas)


def _vaciar_caches() -> None:
    from ..data import dataset
    from . import perfiles
    for f in (cargar_catalogo, dataset.cargar_dataset, dataset.vista_quimica, perfiles.tabla_muestras,
              perfiles.presencias):
        f.cache_clear()


def _cabecera(p: Path) -> list[str]:
    verificar_archivo_datos(p)
    g = config_global()["datos"]
    return pd.read_csv(p, sep=g["separador"], encoding=g["codificacion_catalogos"], nrows=0).columns.tolist()


def _ruta_legible(p: Path) -> str:
    try:
        return str(p.relative_to(raiz_proyecto())).replace("\\", "/")
    except ValueError:
        return str(p)


def describir_archivos(cfg: dict[str, Any], estricto: bool = False) -> list[dict[str, Any]]:
    """Archivos que lee el experimento con sus columnas por rol; comprueba que existan y tengan esas columnas.

    Con `estricto=True` lanza ErrorDatos si falta un archivo o una columna (se usa antes de entrenar)."""
    out = []
    for nombre, roles in roles_efectivos(cfg).items():
        p = ruta_archivo(nombre)
        usadas = list(dict.fromkeys(c for cols in roles.values() for c in cols))
        d: dict[str, Any] = {"nombre": nombre, "ruta": _ruta_legible(p), "roles": roles, "columnas": usadas,
                             "existe": p.exists(), "columnas_faltantes": [], "aviso": None}
        try:
            cab = _cabecera(p)
            d["columnas_faltantes"] = [c for c in usadas if c not in cab]
            d["columnas_no_usadas"] = [c for c in cab if c not in usadas]
        except ErrorDatos as e:
            d["aviso"] = str(e)
        if estricto and d["aviso"]:
            raise ErrorDatos(f"{cfg.get('id')}: {d['aviso']}")
        if estricto and d["columnas_faltantes"]:
            raise ErrorDatos(f"{cfg.get('id')}: el archivo {d['ruta']} no tiene las columnas {d['columnas_faltantes']} "
                             "que necesita el modelo (revise datos_entrenamiento.archivos)")
        out.append(d)
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Variables de entrada (X)
# ---------------------------------------------------------------------------------------------------------------------
def columna_de_variable(col: str) -> str:
    """Columna del archivo de la que procede una variable: 'ID_FAMILIA_6' -> 'ID_FAMILIA', 'dbe' -> 'FORMULA_MOLECULAR'."""
    if col in DESCRIPTORES_FORMULA:
        return "FORMULA_MOLECULAR"
    nivel = col.rsplit("_", 1)[0]
    if nivel in NIVEL_QUIMICO:
        return NIVEL_QUIMICO[nivel]
    if col.startswith("MODOS_") or col == "MODOS":
        return "ID_MODO_IONIZACION"
    if col in ("log_n_identificados", "log_n_senales"):
        return "ID_METABOLITO" if col == "log_n_identificados" else "ID_MUESTRA"
    for c in sorted(set(ATRIBUTOS_MUESTRA) | set(ATRIBUTOS_PLATAFORMA) | set(CATALOGO_DE), key=len, reverse=True):
        if col.startswith(c + "_"):
            return c
    return col


def _coincide(col: str, patrones: list[str]) -> bool:
    origen = columna_de_variable(col)
    return any(fnmatch.fnmatchcase(col, p) or fnmatch.fnmatchcase(origen, p) for p in patrones)


def seleccionar_variables(conj: Any, cfg: dict[str, Any]) -> list[str]:
    """Aplica `datos_entrenamiento.variables` (incluir/excluir) a conj.X. Devuelve las variables descartadas."""
    v = (cfg.get("datos_entrenamiento") or {}).get("variables") or {}
    incluir, excluir = list(v.get("incluir") or []), list(v.get("excluir") or [])
    if not incluir and not excluir:
        return []
    cols = list(conj.X.columns)
    sin_uso = [p for p in incluir + excluir if not any(_coincide(c, [p]) for c in cols)]
    if sin_uso:
        conj.notas.append(f"Patrones de datos_entrenamiento.variables sin coincidencias: {sin_uso}")
    quedan = [c for c in cols if (not incluir or _coincide(c, incluir)) and not _coincide(c, excluir)]
    if not quedan:
        from ..config.esquema import ErrorConfiguracion
        raise ErrorConfiguracion(f"{cfg.get('id')}: datos_entrenamiento.variables no deja ninguna variable de entrada "
                                 f"(incluir={incluir}, excluir={excluir}; disponibles: {cols[:15]}...)")
    descartadas = [c for c in cols if c not in quedan]
    conj.X = conj.X[quedan]
    conj.notas.append(f"datos_entrenamiento.variables: se usan {len(quedan)} de {len(cols)} variables de entrada "
                      f"(incluir={incluir or 'todas'}, excluir={excluir or 'ninguna'}).")
    return descartadas


def _archivo_de(columna: str, roles_por_archivo: dict[str, dict[str, list[str]]]) -> str:
    for archivo, roles in roles_por_archivo.items():
        if columna in roles.get("X", []):
            return archivo
    return "dataset"


def _nombre_legible(col: str) -> str:
    try:
        return nombre_variable(col)
    except ErrorDatos:   # sin catalogos (p. ej. punteros de Git LFS) se usa el nombre tecnico
        return col


def describir(cfg: dict[str, Any], conj: Any = None, descartadas: list[str] | None = None,
              estricto: bool = False) -> dict[str, Any]:
    """Resumen de archivos y columnas de entrenamiento (y, si hay conjunto, de las variables finales)."""
    archivos = describir_archivos(cfg, estricto)
    de = _bloque(cfg)
    d: dict[str, Any] = {"id": cfg.get("id"), "tipo_aprendizaje": tipo_aprendizaje(cfg), "archivos": archivos,
                         "objetivo_configurado": next(iter(_computado(cfg, "y")), None),
                         "grupos_configurados": next(iter(_computado(cfg, "grupos")), None),
                         "seleccion_variables": de.get("variables") or {}, "avisos": avisos_declaracion(cfg)}
    if conj is not None:
        roles = {a["nombre"]: a["roles"] for a in archivos}
        d["variables"] = [{"variable": c, "nombre": _nombre_legible(c), "columna_origen": columna_de_variable(c),
                           "archivo": ruta_archivo(_archivo_de(columna_de_variable(c), roles)).name}
                          for c in conj.X.columns]
        d["variables_descartadas"] = list(descartadas or [])
        d["objetivo"] = list(map(str, conj.y.columns)) if isinstance(conj.y, pd.DataFrame) else str(conj.y.name)
        d["columna_grupo"] = str(conj.grupos.name)
        d["variables_instrumentales"] = [] if conj.X_instrumental is None else list(conj.X_instrumental.columns)
        d["unidades"] = int(len(conj.X))
    return d


def texto(d: dict[str, Any]) -> str:
    """Texto legible (consola / log) del resumen de `describir`."""
    L = [f"Archivos y columnas de entrenamiento - {d['id']} ({d.get('tipo_aprendizaje', 'supervisado').replace('_', ' ')})"]
    if d.get("objetivo_configurado"):
        L.append(f"  Variable objetivo: {d['objetivo_configurado']} | grupos de validacion: {d.get('grupos_configurados')}")
    elif d.get("tipo_aprendizaje") == "no_supervisado":
        L.append("  Sin variable objetivo (aprendizaje no supervisado: patrones, agrupamiento, contrastes)")
    for a in d["archivos"]:
        estado = "" if a["existe"] and not a["aviso"] else "  [NO DISPONIBLE]"
        L.append(f"  Archivo {a['nombre']}: {a['ruta']}{estado}")
        for rol, cols in a["roles"].items():
            L.append(f"    - {ROLES.get(rol, rol)}: {', '.join(cols)}")
        if a["columnas_faltantes"]:
            L.append(f"    ! columnas que faltan en el archivo: {', '.join(a['columnas_faltantes'])}")
    for a in d.get("avisos") or []:
        L.append(f"  ! {a}")
    sel = d.get("seleccion_variables") or {}
    if sel.get("incluir") or sel.get("excluir"):
        L.append(f"  Seleccion de variables: incluir={sel.get('incluir') or 'todas'} excluir={sel.get('excluir') or 'ninguna'}")
    if "variables" in d:
        L.append(f"  Unidades: {d['unidades']} | objetivo: {d['objetivo'] if isinstance(d['objetivo'], str) else str(len(d['objetivo'])) + ' etiquetas'}"
                 f" | grupos: {d['columna_grupo']}")
        L.append(f"  Variables de entrada usadas para entrenar ({len(d['variables'])}):")
        por_origen: dict[str, list[str]] = {}
        for v in d["variables"]:
            por_origen.setdefault(f"{v['archivo']} / {v['columna_origen']}", []).append(v["variable"])
        for origen, vs in por_origen.items():
            L.append(f"    - {origen} -> {len(vs)}: {', '.join(vs[:12])}{' ...' if len(vs) > 12 else ''}")
        if d["variables_descartadas"]:
            L.append(f"  Variables descartadas por la configuracion ({len(d['variables_descartadas'])}): "
                     f"{', '.join(d['variables_descartadas'][:20])}")
    return "\n".join(L)


def markdown(d: dict[str, Any]) -> str:
    L = [f"# Archivos y columnas de entrenamiento - {d['id']}", "",
         "Parametrizable en `config/modelos/<id>.yaml`, bloque `datos_entrenamiento` (archivos y variables).", "",
         f"Tipo de aprendizaje: **{d.get('tipo_aprendizaje', 'supervisado').replace('_', ' ')}**"
         + (f" - variable objetivo: `{d['objetivo_configurado']}` - grupos de validacion: `{d.get('grupos_configurados')}`"
            if d.get("objetivo_configurado") else " (sin variable objetivo)"), "",
         "## Archivos leidos", "", "| archivo | ruta | " + " | ".join(ROLES.values()) + " |",
         "|---|---|" + "---|" * len(ROLES)]
    for a in d["archivos"]:
        L.append(f"| {a['nombre']} | `{a['ruta']}` | " + " | ".join(", ".join(a["roles"].get(r, [])) or "-" for r in ROLES) + " |")
    if "variables" in d:
        L += ["", f"## Variables de entrada ({len(d['variables'])})", "",
              f"Objetivo: `{d['objetivo']}` - grupos: `{d['columna_grupo']}` - unidades: {d['unidades']}", "",
              "| variable | nombre | columna de origen | archivo |", "|---|---|---|---|"]
        L += [f"| `{v['variable']}` | {v['nombre']} | {v['columna_origen']} | {v['archivo']} |" for v in d["variables"]]
        if d["variables_descartadas"]:
            L += ["", "Descartadas por `datos_entrenamiento.variables`: "
                  + ", ".join(f"`{c}`" for c in d["variables_descartadas"])]
        if d["variables_instrumentales"]:
            L += ["", "Variables del control instrumental: " + ", ".join(f"`{c}`" for c in d["variables_instrumentales"])]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------------------------------
# Escritura del bloque en el YAML
# ---------------------------------------------------------------------------------------------------------------------
MARCA_BLOQUE = "# --- Datos de entrenamiento"
_ANCHO = 112

_AYUDA = {
    "supervisado": [
        "tipo_aprendizaje: supervisado -> el modelo aprende a predecir una variable objetivo",
        "objetivo: columna a predecir | grupos_validacion: columna cuyos valores nunca se reparten entre",
        "  entrenamiento y prueba en la validacion cruzada",
        "archivos.<archivo>: ruta (relativa a datos.catalogos de config/rutas.yaml, o absoluta) y columnas por rol:",
        "  entrada: origen de las variables X (quitar una columna elimina sus variables)",
        "  objetivo / grupos_validacion: de que archivo salen (deben coincidir con lo de arriba)",
        "  control_instrumental: variables de plataforma del modelo de control (quitar = no usarlas)",
        "  filtros_agregacion: columnas para filtrar muestras y agregar (informativo)",
        "variables.incluir / excluir: seleccion fina de las variables X ya construidas (comodines * ?)",
    ],
    "no_supervisado": [
        "tipo_aprendizaje: no_supervisado -> no hay variable objetivo: se buscan patrones, grupos y contrastes",
        "archivos.<archivo>: ruta (relativa a datos.catalogos de config/rutas.yaml, o absoluta) y columnas por rol:",
        "  entrada: columnas que forman los perfiles quimicos analizados (informativo; los perfiles se ajustan",
        "    en el bloque patrones)",
        "  factores_contraste: factores con los que se contrastan los perfiles (taxon, organo, articulo...)",
        "  filtros_agregacion: columnas para filtrar muestras y agregar (informativo)",
    ],
}


def _lista_yaml(clave: str, valores: list[str], sangria: int) -> list[str]:
    """`clave: [a, b, ...]` partida en varias lineas si no cabe (lista YAML en estilo flujo)."""
    pre = " " * sangria + f"{clave}: ["
    lineas, actual = [], pre
    for i, v in enumerate(valores):
        trozo = v + (", " if i < len(valores) - 1 else "]")
        if len(actual) + len(trozo.rstrip()) > _ANCHO and actual.strip() not in (f"{clave}: [",):
            lineas.append(actual.rstrip())
            actual = " " * (sangria + 2) + trozo
        else:
            actual += trozo
    if not valores:
        actual += "]"
    lineas.append(actual.rstrip())
    return lineas


def bloque_yaml(cfg: dict[str, Any], completo: bool = False) -> str:
    """Texto del bloque `datos_entrenamiento` para el YAML, a partir de lo que usa el codigo. Conserva rutas, seleccion
    de variables y columnas quitadas de entrada/control (con `completo=True` vuelve a poner todas las que admite)."""
    tipo = tipo_aprendizaje(cfg)
    rutas = archivos_configurados(cfg)
    roles = columnas_origen(cfg) if completo else roles_efectivos(cfg)
    sel = _bloque(cfg).get("variables") or {}
    L = [MARCA_BLOQUE + f" ({tipo.replace('_', ' ')}) " + "-" * (_ANCHO - len(MARCA_BLOQUE) - len(tipo) - 4)]
    L += [f"# {t}" for t in _AYUDA[tipo]]
    corto = str(cfg.get("id", "")).split("_")[0]
    L += [f"# Ver sin entrenar: python main.py datos {corto} [--variables] | Regenerar: python main.py datos {corto} "
          "--escribir-yaml", "datos_entrenamiento:",
          f"  tipo_aprendizaje: {tipo}"]
    if tipo == "supervisado":
        L.append(f"  objetivo: {next(iter(_computado(cfg, 'y')), '')}")
        L.append(f"  grupos_validacion: {next(iter(_computado(cfg, 'grupos')), '')}")
    L.append("  archivos:")
    for archivo, rr in roles.items():
        ruta_txt = rutas.get(archivo) or _ruta_relativa(archivo)
        L += [f"    {archivo}:", f"      ruta: {ruta_txt}"]
        for rol in ROLES_POR_TIPO[tipo]:
            if rr.get(rol):
                L += _lista_yaml(CLAVE_DE_ROL[rol], rr[rol], 6)
    if tipo == "supervisado":
        L.append("  variables:")
        L += _lista_yaml("incluir", list(sel.get("incluir") or []), 4)
        L += _lista_yaml("excluir", list(sel.get("excluir") or []), 4)
    return "\n".join(L) + "\n"


def _ruta_relativa(archivo: str) -> str:
    p = ruta_archivo(archivo)
    try:
        return str(p.relative_to(ruta("datos", "catalogos"))).replace("\\", "/")
    except ValueError:
        return str(p)


def escribir_yaml(p: Path, cfg: dict[str, Any], completo: bool = False) -> bool:
    """Sustituye el bloque `datos_entrenamiento` (y su comentario) al final del YAML. Devuelve True si cambio."""
    texto_original = p.read_text(encoding="utf-8")
    lineas = texto_original.splitlines()
    corte = len(lineas)
    for i, ln in enumerate(lineas):
        if ln.startswith("datos_entrenamiento:"):
            corte = i
            break
    # sube por los comentarios y lineas vacias que preceden al bloque
    while corte > 0 and (lineas[corte - 1].startswith("#") or not lineas[corte - 1].strip()):
        corte -= 1
    # el bloque debe ser lo ultimo del archivo: si hay otras claves despues, se conservan
    fin = len(lineas)
    for j in range(corte, len(lineas)):
        if j > corte and lineas[j] and not lineas[j][0].isspace() and not lineas[j].startswith(("#", "datos_entrenamiento:")):
            fin = j
            break
    nuevo = "\n".join(lineas[:corte]).rstrip() + "\n\n" + bloque_yaml(cfg, completo)
    if fin < len(lineas):
        nuevo += "\n" + "\n".join(lineas[fin:]).rstrip() + "\n"
    if nuevo == texto_original:
        return False
    p.write_text(nuevo, encoding="utf-8")
    return True
