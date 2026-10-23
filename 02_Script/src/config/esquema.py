"""Carga, fusion con valores por defecto y validacion de las configuraciones de experimento (YAML)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from ..data.catalogos import NOMBRES_ARCHIVO
from ..features.conjuntos import CONSTRUCTORES
from ..models.registro_modelos import MODELOS
from ..utils.es import leer_yaml
from ..utils.rutas import config_global, ruta

TAREAS = {"supervisado", "patrones"}
ESTRATEGIAS = {"group_kfold", "leave_one_group_out", "stratified_kfold"}
SELECCION = {None, "ninguna", "anova", "informacion_mutua"}
# Variables que nunca deben entrar como predictoras (codifican plataforma, aducto o la propia intensidad del lote)
PROHIBIDAS_SIEMPRE = ["RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS", "ALTURA_PICO", "ID_BATCH", "ID_ARTICULO",
                      "ID_MUESTRA"]


class ErrorConfiguracion(ValueError):
    """Configuracion invalida; el mensaje indica el archivo y la clave."""


def _fusionar(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = _fusionar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def listar_configs() -> list[Path]:
    return sorted(ruta("configuracion", "modelos").glob("*.yaml"))


def buscar_config(identificador: str) -> Path:
    for p in listar_configs():
        if p.stem == identificador or p.stem.split("_")[0] == identificador:
            return p
    raise ErrorConfiguracion(f"No existe configuracion para '{identificador}'. Use `python main.py listar`.")


def cargar_config(p: Path) -> dict[str, Any]:
    """Lee el YAML, aplica los defaults de config_global.yaml y valida."""
    crudo = leer_yaml(p) or {}
    g = config_global()
    cfg = _fusionar(g["defaults"], crudo)
    cfg.setdefault("semilla", g["semilla"])
    cfg.setdefault("n_jobs", g.get("n_jobs", -1))
    cfg["_archivo"] = str(p)
    validar(cfg, p)
    cfg["_huella"] = huella_config(cfg)
    return cfg


def huella_config(cfg: dict[str, Any]) -> str:
    limpio = {k: v for k, v in cfg.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(limpio, sort_keys=True, default=str).encode()).hexdigest()


def validar(cfg: dict[str, Any], p: Path | str = "<config>") -> None:
    errores: list[str] = []

    def req(clave: str, tipo: type | tuple) -> Any:
        v = cfg.get(clave)
        if v is None:
            errores.append(f"falta la clave obligatoria '{clave}'")
        elif not isinstance(v, tipo):
            errores.append(f"'{clave}' debe ser {tipo}, se recibio {type(v).__name__}")
        return v

    ident = req("id", str)
    if ident and Path(str(p)).stem != ident and Path(str(p)).name != "<config>":
        errores.append(f"'id' ({ident}) debe coincidir con el nombre del archivo ({Path(str(p)).stem})")
    req("nombre", str)
    req("pregunta_cientifica", str)
    tarea = req("tarea", str)
    if tarea and tarea not in TAREAS:
        errores.append(f"'tarea' debe ser una de {sorted(TAREAS)}")
    conj = req("conjunto", dict)
    if tarea == "supervisado":
        if isinstance(conj, dict):
            if conj.get("nombre") not in CONSTRUCTORES:
                errores.append(f"conjunto.nombre='{conj.get('nombre')}' no existe; opciones: {sorted(CONSTRUCTORES)}")
            if not isinstance(conj.get("parametros", {}), dict):
                errores.append("conjunto.parametros debe ser un diccionario")
        modelos = req("modelos", list)
        if isinstance(modelos, list):
            nombres = []
            for i, m in enumerate(modelos):
                if not isinstance(m, dict) or "nombre" not in m:
                    errores.append(f"modelos[{i}] debe tener 'nombre'")
                    continue
                if m["nombre"] not in MODELOS:
                    errores.append(f"modelos[{i}].nombre='{m['nombre']}' no existe; opciones: {MODELOS}")
                nombres.append(m["nombre"])
            if not any(n.startswith("baseline") for n in nombres):
                errores.append("se requiere al menos un modelo baseline (baseline_mayoritaria/prior/estratificada)")
            if not any(not n.startswith("baseline") for n in nombres):
                errores.append("se requiere al menos un modelo no baseline")
        sp = cfg.get("split", {})
        if sp.get("strategy") not in ESTRATEGIAS:
            errores.append(f"split.strategy debe ser una de {sorted(ESTRATEGIAS)}")
        if sp.get("strategy") == "stratified_kfold":
            errores.append("split.strategy=stratified_kfold ignora los grupos y produce fuga entre articulos; solo se "
                           "permite como evaluacion secundaria (evaluation.evaluacion_optimista)")
        if int(sp.get("n_splits", 0)) < 2:
            errores.append("split.n_splits debe ser >= 2")
        if int(sp.get("min_groups_per_class", 0)) < 2:
            errores.append("split.min_groups_per_class debe ser >= 2 (una clase de un solo grupo no es evaluable)")
        sel = (cfg.get("seleccion_variables") or {}).get("metodo")
        if sel not in SELECCION:
            errores.append(f"seleccion_variables.metodo debe ser uno de {sorted(x for x in SELECCION if x)}")
        objetivo = (conj or {}).get("parametros", {}).get("objetivo") if isinstance(conj, dict) else None
        if objetivo and objetivo in (cfg.get("variables_permitidas") or []):
            errores.append(f"el objetivo {objetivo} no puede figurar en variables_permitidas")
    errores += _validar_datos_entrenamiento(cfg.get("datos_entrenamiento"))
    if errores:
        raise ErrorConfiguracion(f"Configuracion invalida en {p}:\n  - " + "\n  - ".join(errores))


def _validar_datos_entrenamiento(de: Any) -> list[str]:
    """Bloque opcional `datos_entrenamiento` (archivos y variables usados para entrenar)."""
    if de is None:
        return []
    if not isinstance(de, dict):
        return ["datos_entrenamiento debe ser un diccionario con 'archivos' y/o 'variables'"]
    errores = [f"datos_entrenamiento.{k} no es una clave valida (use 'archivos' o 'variables')"
               for k in de if k not in ("archivos", "variables")]
    arch = de.get("archivos") or {}
    if not isinstance(arch, dict):
        errores.append("datos_entrenamiento.archivos debe ser un diccionario archivo -> ruta")
    else:
        for k, v in arch.items():
            if k not in NOMBRES_ARCHIVO:
                errores.append(f"datos_entrenamiento.archivos.{k} no existe; opciones: {NOMBRES_ARCHIVO}")
            if not isinstance(v, str) or not v.strip():
                errores.append(f"datos_entrenamiento.archivos.{k} debe ser una ruta (texto)")
    var = de.get("variables") or {}
    if not isinstance(var, dict):
        errores.append("datos_entrenamiento.variables debe ser un diccionario con 'incluir' y/o 'excluir'")
    else:
        for k, v in var.items():
            if k not in ("incluir", "excluir"):
                errores.append(f"datos_entrenamiento.variables.{k} no es valida (use 'incluir' o 'excluir')")
            elif v is not None and (not isinstance(v, list) or not all(isinstance(x, str) for x in v)):
                errores.append(f"datos_entrenamiento.variables.{k} debe ser una lista de nombres o patrones")
    return errores


def verificar_fuga(cfg: dict[str, Any], columnas: list[str], instrumentales: list[str] | None = None) -> None:
    """Comprueba en tiempo de ejecucion que ninguna variable predictora codifique el objetivo o la plataforma."""
    objetivo = cfg.get("conjunto", {}).get("parametros", {}).get("objetivo")
    prohibidas = list(PROHIBIDAS_SIEMPRE) + list(cfg.get("variables_prohibidas") or [])
    if objetivo:
        prohibidas.append(objetivo)
    malas = [c for c in columnas if any(c == p or c.startswith(p + "_") for p in prohibidas)]
    if objetivo and instrumentales:
        malas += [c for c in instrumentales if c == objetivo or c.startswith(objetivo + "_")]
    if malas:
        raise ErrorConfiguracion(f"Fuga de informacion en {cfg.get('id')}: variables prohibidas entre las predictoras: "
                                 f"{malas[:10]}")
