"""Archivos y columnas que usa cada experimento para entrenar (parametrizables en config/modelos/*.yaml).

Bloque `datos_entrenamiento` de cada YAML (opcional; sin el se usan los archivos de config/rutas.yaml):

    datos_entrenamiento:
      archivos:              # archivo logico -> ruta (relativa a datos.catalogos de rutas.yaml, o absoluta)
        dataset: Dataset.csv
        metabolitos: 03_Catalogo_Metabolito/05_Metabolitos.csv
      variables:             # seleccion de las variables de entrada (X) ya construidas
        incluir: []          # vacio = todas; admite comodines (* ?)
        excluir: []

Los patrones de `variables` se comparan con el nombre de la variable (p. ej. `ID_FAMILIA_6`, `clase_240`, `dbe`) y con
la columna del archivo de la que procede (p. ej. `ID_SUPERCLASE_QUIMICA` o `FORMULA_MOLECULAR`): excluir una columna
de origen elimina todas las variables derivadas de ella.

Cada ejecucion informa (consola, ejecucion.log, datos_entrenamiento.md/.json e informe.md) que archivos se leyeron,
que columnas de cada archivo se usaron (X, objetivo, grupos, filtros, control instrumental) y la lista final de
variables con las que se entreno.
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
from .perfiles import ATRIBUTOS_MUESTRA, NIVEL_QUIMICO
from .quimica import descriptores

ROLES = {"X": "variables de entrada", "y": "objetivo", "grupos": "grupos de validacion",
         "instrumental": "control instrumental", "factores": "factores de contraste", "filtros": "filtros y agregacion"}
DESCRIPTORES_FORMULA = list(descriptores("CH4"))
INSTRUMENTALES_ORIGEN = ["ID_COLUMNA_CROMATOGRAFICA", "ID_MODO_IONIZACION", "ID_METABOLITO", "ID_NIVEL_IDENTIFICACION"]
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


def archivos_configurados(cfg: dict[str, Any]) -> dict[str, str]:
    return dict((cfg.get("datos_entrenamiento") or {}).get("archivos") or {})


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
    for nombre, roles in columnas_origen(cfg).items():
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
    for c in sorted(set(ATRIBUTOS_MUESTRA) | set(CATALOGO_DE), key=len, reverse=True):
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


def describir(cfg: dict[str, Any], conj: Any = None, descartadas: list[str] | None = None,
              estricto: bool = False) -> dict[str, Any]:
    """Resumen de archivos y columnas de entrenamiento (y, si hay conjunto, de las variables finales)."""
    archivos = describir_archivos(cfg, estricto)
    d: dict[str, Any] = {"id": cfg.get("id"), "archivos": archivos,
                         "seleccion_variables": (cfg.get("datos_entrenamiento") or {}).get("variables") or {}}
    if conj is not None:
        roles = {a["nombre"]: a["roles"] for a in archivos}
        d["variables"] = [{"variable": c, "nombre": nombre_variable(c), "columna_origen": columna_de_variable(c),
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
    L = [f"Archivos y columnas de entrenamiento - {d['id']}"]
    for a in d["archivos"]:
        estado = "" if a["existe"] and not a["aviso"] else "  [NO DISPONIBLE]"
        L.append(f"  Archivo {a['nombre']}: {a['ruta']}{estado}")
        for rol, cols in a["roles"].items():
            L.append(f"    - {ROLES.get(rol, rol)}: {', '.join(cols)}")
        if a["columnas_faltantes"]:
            L.append(f"    ! columnas que faltan en el archivo: {', '.join(a['columnas_faltantes'])}")
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
