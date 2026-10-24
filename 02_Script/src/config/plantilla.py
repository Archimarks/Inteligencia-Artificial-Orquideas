"""Escritura de config/modelos/<ID>.yaml en un formato comun y comentado (`python main.py datos --escribir-yaml`).

Conserva todos los valores del YAML (y explicita los de config_global.yaml que aplican: split y evaluation), anade el
bloque `no_supervisado` en los experimentos supervisados si falta y regenera `datos_entrenamiento` a partir del
codigo. Cada seccion y cada clave llevan un comentario que explica para que sirve.
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import yaml

from ..utils.es import leer_yaml

ANCHO = 112
COL = 34   # columna de los comentarios en linea

COMENTARIO_PARAMETRO = {
    "nivel": "superclase | clase: nivel quimico del perfil",
    "transformacion": "clr | fraccion | conteo",
    "min_metabolitos": "excluye unidades con menos metabolitos clasificados",
    "min_articulos_categoria": "solo categorias quimicas presentes en >= N articulos",
    "max_categorias": "maximo de categorias quimicas (el resto se suma en 'otras')",
    "agregar_por": "agrega muestras por estas columnas (null = una unidad por muestra)",
    "ponderar_por_grupo": "pesos 1/n por articulo: cada estudio pesa lo mismo",
    "incluir_superclase": "anade la superclase quimica como variable de entrada",
    "max_clases": "solo las N clases mas frecuentes",
    "min_positivos": "solo etiquetas con >= N unidades positivas",
    "min_articulos": "solo metabolitos presentes en >= N articulos",
    "max_metabolitos": "maximo de metabolitos (etiquetas)",
    "predictores": "atributos de la unidad usados como variables de entrada",
    "min_identificados": "excluye grupos con menos metabolitos identificados",
}
COMENTARIO_MODELO = {
    "baseline_mayoritaria": "referencia: siempre predice la clase mas frecuente",
    "baseline_prior": "referencia: predice la prevalencia de cada etiqueta",
    "baseline_estratificada": "referencia: azar con las proporciones de clase",
    "logistica": "regresion logistica (lineal, interpretable)",
    "random_forest": "bosque aleatorio",
    "extra_trees": "arboles extremadamente aleatorios",
    "hist_gradient_boosting": "gradient boosting de scikit-learn",
    "lightgbm": "gradient boosting (CPU)",
    "xgboost": "gradient boosting (GPU si hay)",
    "catboost": "gradient boosting (GPU si hay)",
    "knn": "k vecinos mas cercanos",
}
COMENTARIO_SPLIT = {
    "strategy": "group_kfold | leave_one_group_out (un grupo nunca se reparte)",
    "n_splits": "numero de particiones de la validacion cruzada",
    "min_groups_per_class": "una clase se evalua solo si aparece en >= N grupos",
    "min_samples_per_class": "... y en >= N unidades",
}
COMENTARIO_EVALUACION = {
    "permutation_test": "prueba de permutacion de la etiqueta (p-valor)",
    "n_permutations": "mas permutaciones = p mas preciso y entrenamiento mas largo",
    "confounding_control": "modelo con solo variables de plataforma: el quimico debe superarlo",
    "evaluacion_optimista": "repite sin agrupar para medir cuanto inflaria una validacion ingenua",
}
COMENTARIO_NS = {
    "activo": "false = solo el entrenamiento supervisado",
    "matriz": "entrada = variables X | objetivo = matriz multietiqueta (presencias, actividades)",
    "referencias": "con que se comparan los grupos: objetivo, grupos o columnas de la unidad",
    "componentes": "componentes principales (PCA) tras estandarizar",
    "metodos": "kmeans | jerarquico (Ward; se omite con > 12000 unidades)",
    "k_min": "numero de grupos a probar; se elige el de mayor silueta",
    "k_max": "",
    "n_bootstrap": "remuestreos para medir la estabilidad de los grupos",
    "contaminacion": "fraccion esperada de unidades atipicas (Isolation Forest)",
    "max_unidades": "submuestra estratificada si hay mas unidades",
}
COMENTARIO_PATRONES = {
    "alfa": "nivel de significancia tras la correccion BH",
    "min_metabolitos": "excluye unidades con menos metabolitos identificados",
    "min_articulos_categoria": "superclases presentes en >= N articulos",
    "min_articulos_clase": "clases presentes en >= N articulos",
    "max_clases": "maximo de clases quimicas",
    "max_aristas": "aristas en la red de coocurrencia",
    "n_permutaciones": "permutaciones de PERMANOVA",
    "factores_enriquecimiento": "factores con los que se contrastan los perfiles",
    "n_nulos": "aleatorizaciones curveball para la coocurrencia",
    "reglas": "reglas de asociacion (FP-growth)",
    "agrupamiento": "K-means sobre el perfil (k elegido por silueta)",
    "min_soporte": "", "min_confianza": "", "min_confianza_taxon": "", "min_lift": "", "max_longitud": "",
    "max_soporte_item": "", "max_reglas_guardadas": "", "items_taxonomicos": "taxones usados como items",
    "k_max": "", "n_bootstrap": "remuestreos para la estabilidad",
}
ORDEN = ["id", "nombre", "tarea", "prioridad", "pregunta_cientifica", "descripcion", "interpretacion", "conjunto",
         "split", "max_clases", "modelos", "seleccion_variables", "usar_pesos", "evaluation", "patrones",
         "no_supervisado", "datos_entrenamiento"]


def _seccion(titulo: str, ayuda: list[str] | None = None) -> list[str]:
    L = ["", f"# --- {titulo} " + "-" * max(3, ANCHO - len(titulo) - 7)]
    return L + [f"# {a}" for a in ayuda or []]


def _valor(v: Any) -> str:
    if isinstance(v, (dict, list)):
        return yaml.safe_dump(v, default_flow_style=True, allow_unicode=True, width=10_000).strip()
    if isinstance(v, str):
        return yaml.safe_dump(v, allow_unicode=True, width=10_000).strip().removesuffix("\n...").removesuffix("...").strip()
    return yaml.safe_dump(v).strip().removesuffix("...").strip()


def _linea(sangria: int, clave: str, valor: Any, comentario: str = "") -> str:
    base = " " * sangria + f"{clave}: {_valor(valor)}"
    if comentario:
        base = base.ljust(COL) + f"  # {comentario}" if len(base) < COL else base + f"  # {comentario}"
    return base


def _texto(clave: str, v: str) -> list[str]:
    t = " ".join(str(v).split())
    return [f"{clave}: >-"] + ["  " + x for x in textwrap.wrap(t, ANCHO - 2)]


def _por_defecto_ns(cfg: dict[str, Any]) -> dict[str, Any]:
    """Bloque no_supervisado sugerido segun el conjunto del experimento."""
    from ..tasks.no_supervisado import POR_DEFECTO
    ns = dict(POR_DEFECTO)
    nombre = cfg["conjunto"].get("nombre")
    objetivo = (cfg["conjunto"].get("parametros") or {}).get("objetivo")
    if nombre == "presencia_metabolitos":
        ns.update(matriz="objetivo", referencias=["ID_ORDEN", "ID_FAMILIA", "ID_PARTE_ESTUDIADA", "grupos"])
    elif nombre == "actividad_especie":
        ns["referencias"] = ["objetivo", "grupos", "ID_ORDEN", "ID_FAMILIA"]
    elif nombre == "actividad_metabolito":
        ns.update(referencias=["objetivo"], k_max=6)
    elif nombre == "metabolito_quimica":
        ns["referencias"] = ["objetivo"] + (["ID_SUPERCLASE_QUIMICA"] if objetivo == "ID_CLASE_QUIMICA" else [])
    elif nombre == "metabolito_aducto":
        ns["referencias"] = ["objetivo", "grupos", "ID_MODO_IONIZACION"]
    elif nombre == "perfil_muestra" and objetivo != "ID_COLUMNA_CROMATOGRAFICA":
        ns["referencias"] = ["objetivo", "grupos", "ID_COLUMNA_CROMATOGRAFICA"]
    return ns


def texto_config(p: Path, completo: bool = False) -> str:
    """YAML completo, ordenado y comentado del experimento `p`."""
    from ..config.esquema import cargar_config
    from ..features import fuentes
    from ..tasks.no_supervisado import POR_DEFECTO as NS_DEFECTO
    crudo = leer_yaml(p) or {}
    cfg = cargar_config(p)
    sup = cfg["tarea"] == "supervisado"
    if sup and crudo.get("no_supervisado") is None:
        crudo["no_supervisado"] = _por_defecto_ns(cfg)
        cfg["no_supervisado"] = crudo["no_supervisado"]
    corto = cfg["id"].split("_")[0]
    tipos = fuentes.tipos_aprendizaje(cfg)
    multi = cfg.get("conjunto", {}).get("nombre") in ("presencia_metabolitos", "actividad_especie", "actividad_metabolito")
    entren = (("supervisado (" + ("multietiqueta" if multi else "clasificacion") + ")") if sup else "no supervisado (patrones)")
    if "no_supervisado" in tipos and sup:
        entren += " + no supervisado (agrupamiento)"
    L = ["# " + "=" * (ANCHO - 2), f"# {cfg['id']} - {cfg['nombre']}", f"# Entrenamientos: {entren}",
         f"# Ejecutar: python main.py ejecutar {corto} | Ver datos y variables sin entrenar: python main.py datos {corto} --variables",
         "# " + "=" * (ANCHO - 2)]
    L += [_linea(0, "id", cfg["id"]), _linea(0, "nombre", cfg["nombre"]),
          _linea(0, "tarea", cfg["tarea"], "entrenamiento principal: supervisado | patrones (no supervisado)"),
          _linea(0, "prioridad", crudo.get("prioridad", "normal"), "normal | alta | central (orden en la interfaz)")]
    for k in ("pregunta_cientifica", "descripcion", "interpretacion"):
        if crudo.get(k):
            L += _texto(k, crudo[k])

    if sup:
        conj = crudo.get("conjunto") or {}
        L += _seccion("Conjunto: unidad de analisis y construccion de las variables",
                      ["El objetivo se indica en datos_entrenamiento.objetivo (abajo)."])
        L += ["conjunto:", _linea(2, "nombre", conj.get("nombre"), "constructor en src/features/conjuntos.py")]
        par = {k: v for k, v in (conj.get("parametros") or {}).items() if k != "objetivo"}
        if par:
            L.append("  parametros:")
            L += [_linea(4, k, v, COMENTARIO_PARAMETRO.get(k, "")) for k, v in par.items()]
        else:
            L.append("  parametros: {}")
        L += _seccion("Validacion cruzada agrupada (entrenamiento supervisado)")
        L.append("split:")
        L += [_linea(2, k, cfg["split"][k], COMENTARIO_SPLIT.get(k, "")) for k in COMENTARIO_SPLIT if k in cfg["split"]]
        if crudo.get("max_clases") is not None:
            L.append(_linea(0, "max_clases", crudo["max_clases"], "solo las N clases mas frecuentes"))
        L += _seccion("Entrenamiento supervisado: algoritmos",
                      ["Los baselines no aprenden de la quimica: un algoritmo util debe superarlos."])
        L.append("modelos:")
        for m in crudo.get("modelos") or []:
            L.append(_linea(0, "- nombre", m["nombre"], COMENTARIO_MODELO.get(m["nombre"], "")))
            if m.get("hiperparametros"):
                L.append(_linea(2, "hiperparametros", m["hiperparametros"]))
        sel = crudo.get("seleccion_variables") or {"metodo": "ninguna"}
        L.append("seleccion_variables:")
        L += [_linea(2, k, v, "ninguna | anova | informacion_mutua (con k = numero de variables)" if k == "metodo" else "")
              for k, v in sel.items()]
        if "usar_pesos" in crudo:
            L.append(_linea(0, "usar_pesos", crudo["usar_pesos"], "pesos por grupo en el entrenamiento"))
        L += _seccion("Evaluacion del entrenamiento supervisado")
        L.append("evaluation:")
        L += [_linea(2, k, cfg["evaluation"][k], COMENTARIO_EVALUACION[k]) for k in COMENTARIO_EVALUACION
              if k in cfg["evaluation"]]
        ns = {**NS_DEFECTO, **crudo["no_supervisado"]}
        L += _seccion("Entrenamiento no supervisado: mismas unidades, sin usar el objetivo",
                      ["Agrupa las unidades (PCA + K-means/jerarquico), mide la estabilidad de los grupos y busca atipicos;",
                       "despues compara los grupos con las referencias. Si siguen al articulo y no al objetivo, domina el",
                       "efecto de estudio/plataforma. Resultados en metricas/<run_id>/no_supervisado/."])
        L.append("no_supervisado:")
        L += [_linea(2, k, ns[k], COMENTARIO_NS.get(k, "")) for k in NS_DEFECTO]
    else:
        L += _seccion("Analisis no supervisado de patrones (sin variable objetivo)")
        L.append("conjunto: {}")
        L.append("patrones:")
        for k, v in (crudo.get("patrones") or {}).items():
            if isinstance(v, dict):
                L.append(f"  {k}:" + (f"  # {COMENTARIO_PATRONES[k]}" if COMENTARIO_PATRONES.get(k) else ""))
                L += [_linea(4, k2, v2, COMENTARIO_PATRONES.get(k2, "")) for k2, v2 in v.items()]
            else:
                L.append(_linea(2, k, v, COMENTARIO_PATRONES.get(k, "")))
    otros = {k: v for k, v in crudo.items() if k not in ORDEN}
    if otros:
        L += _seccion("Otras opciones")
        L += [_linea(0, k, v) for k, v in otros.items()]
    L += [""] + fuentes.bloque_yaml(cfg, completo).rstrip("\n").splitlines()
    return "\n".join(L) + "\n"


def escribir(p: Path, completo: bool = False) -> bool:
    nuevo = texto_config(p, completo)
    if p.read_text(encoding="utf-8") == nuevo:
        return False
    p.write_text(nuevo, encoding="utf-8")
    return True
