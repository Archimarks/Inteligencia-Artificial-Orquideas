"""Informe por ejecucion y resumen ejecutivo. Las conclusiones se derivan solo de las metricas obtenidas."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..utils.es import guardar_tabla
from ..utils.rutas import asegurar_dir, ruta

UMBRAL_GANANCIA = 0.05      # mejora minima sobre el baseline para hablar de senal
UMBRAL_CONTROL = 0.03       # si el control instrumental queda a menos de esto del modelo, se considera confundido
UMBRAL_FUGA = 0.10          # diferencia optimista - agrupada considerada inflacion importante
MIN_GRUPOS_CLASE = 3        # mediana minima de grupos independientes por clase para extraer conclusiones
MIN_GRUPOS_TOTAL = 10       # grupos (articulos) minimos en total


def completar(r: dict[str, Any], dir_ejecucion: Path) -> dict[str, Any]:
    """Anade campos derivados que ejecuciones antiguas no guardaron (p. ej. grupos minimos por clase)."""
    t = dir_ejecucion / "tablas" / "distribucion_clases.csv"
    if "mediana_grupos_por_clase" not in r and t.exists():
        d = pd.read_csv(t, sep=";")
        if "grupos" in d:
            r["min_grupos_por_clase"] = int(d["grupos"].min())
            r["mediana_grupos_por_clase"] = float(d["grupos"].median())
    return r


def veredicto(r: dict[str, Any]) -> tuple[str, str]:
    """(etiqueta, explicacion) a partir de baseline, permutacion, control instrumental y evaluacion optimista."""
    if r.get("estado") == "no_viable":
        return "no viable", r.get("motivo", "")
    if r.get("estado") == "error":
        return "error", r.get("motivo", "")
    if r.get("tarea") == "patrones":
        return "descriptivo", "Analisis no supervisado / de asociacion; ver hallazgos."
    v, b = r.get("valor_mejor"), r.get("valor_baseline")
    if v is None or b is None:
        return "sin evaluar", ""
    gan = v - b
    perm = r.get("permutacion") or {}
    p = perm.get("p_valor")
    p_min = 1 / (1 + perm["n"]) if perm.get("n") else None
    ctrl = r.get("valor_control_instrumental")
    opt = r.get("valor_optimista_sin_agrupar")
    partes = [f"{r['metrica_principal']} = {v:.3f} frente a {b:.3f} del baseline (ganancia {gan:+.3f})"]
    if p is not None:
        partes.append(f"p de permutacion = {p:.3f}" + (f" (minimo alcanzable con {perm['n']} permutaciones; ninguna "
                                                       "permutacion igualo al valor observado)" if p <= p_min + 1e-12 else ""))
    if ctrl is not None:
        partes.append(f"control solo-plataforma = {ctrl:.3f}")
    if opt is not None:
        partes.append(f"evaluacion sin agrupar = {opt:.3f}")
    texto = "; ".join(partes) + "."
    # con n permutaciones el menor p posible es 1/(n+1): si ninguna permutacion alcanza el valor observado se
    # considera significativo aunque n sea pequeno (se informa el p minimo alcanzable)
    mg = r.get("mediana_grupos_por_clase")
    if (mg is not None and mg < MIN_GRUPOS_CLASE) or (r.get("grupos") or 99) < MIN_GRUPOS_TOTAL:
        return "evidencia insuficiente", texto + (f" Solo {r.get('grupos')} grupos independientes (mediana {mg} por clase): "
                                                  "el resultado depende de muy pocos estudios y no permite conclusiones.")
    significativo = p is None or p < 0.05 or (p_min is not None and p <= p_min + 1e-12)
    if gan < UMBRAL_GANANCIA or not significativo:
        etiqueta = "sin senal"
    elif ctrl is not None and ctrl >= v - UMBRAL_CONTROL:
        etiqueta = "confundido con plataforma"
        texto += " El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica."
    elif gan < 0.15:
        etiqueta = "senal debil"
    else:
        etiqueta = "senal robusta"
    if opt is not None and opt - v > UMBRAL_FUGA:
        texto += (f" Sin agrupar por {r.get('columna_grupo', 'grupo')} la metrica sube {opt - v:+.3f}: "
                  "la evaluacion ingenua sobrestimaria el rendimiento.")
    return etiqueta, texto


def _tabla_md(df: pd.DataFrame, max_filas: int = 30) -> str:
    if df.empty:
        return "_(sin filas)_"
    d = df.head(max_filas).copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else f"{x:.3f}")
    cab = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return cab + "\n".join("| " + " | ".join(str(v) for v in fila) + " |" for fila in d.itertuples(index=False))


def escribir_informe(cfg: dict[str, Any], r: dict[str, Any], man: dict[str, Any], salida: dict[str, Path]) -> Path:
    r.setdefault("tarea", cfg["tarea"])
    etiqueta, texto = veredicto(r)
    r["veredicto"], r["explicacion"] = etiqueta, texto
    L = [f"# {cfg['id']} - {cfg['nombre']}", "",
         f"- Ejecucion: `{man['run_id']}` ({man['inicio']}, {man.get('segundos', '?')} s)",
         f"- Configuracion: `{Path(cfg['_archivo']).name}` (huella `{cfg['_huella'][:12]}`), semilla {cfg['semilla']}",
         f"- Estado: **{r.get('estado')}** - Veredicto: **{etiqueta}**", "",
         "## Pregunta cientifica", cfg["pregunta_cientifica"].strip(), ""]
    if cfg.get("descripcion"):
        L += ["## Diseno", cfg["descripcion"].strip(), ""]
    if r.get("notas"):
        L += ["## Unidad de analisis y precauciones"] + [f"- {n}" for n in r["notas"]] + [""]
    if cfg["tarea"] == "supervisado" and r.get("estado") in ("completado", "no_viable"):
        L += ["## Datos evaluados",
              f"- Unidades: {r.get('unidades')} de {r.get('unidades_iniciales')} (grupos: {r.get('grupos')} de "
              f"{r.get('grupos_iniciales')}; columna de grupo `{r.get('columna_grupo')}`)",
              f"- Clases/etiquetas evaluables: {r.get('clases_evaluables')} (descartadas: {r.get('clases_descartadas')}; "
              "ver `tablas/clases_descartadas.csv`)",
              f"- Variables predictoras: {r.get('variables')}", ""]
    if r.get("estado") == "completado" and cfg["tarea"] == "supervisado":
        tabla = pd.read_csv(salida["metricas"] / "metricas_modelos.csv", sep=";")
        cols = [c for c in tabla.columns if not c.endswith("_particiones") and c not in ("es_baseline",)]
        L += ["## Resultados (validacion agrupada, predicciones fuera de particion)", _tabla_md(tabla[cols]), "",
              f"Mejor modelo: **{r['mejor_modelo']}**. {texto}", ""]
        if r.get("variables_principales"):
            L += ["Variables mas influyentes del modelo final: " +
                  ", ".join(f"`{k}` ({v:.3f})" for k, v in list(r["variables_principales"].items())[:8]) + ".", ""]
    if r.get("estado") == "no_viable":
        L += ["## Resultado", f"No viable: {r.get('motivo')}", ""]
    if r.get("estado") == "error":
        L += ["## Error", f"`{r.get('motivo')}` (ver `ejecucion.log`).", ""]
    if r.get("hallazgos"):
        L += ["## Hallazgos"] + [f"- {h}" for h in r["hallazgos"]] + [""]
    if cfg.get("interpretacion"):
        L += ["## Como interpretar", cfg["interpretacion"].strip(), ""]
    graf = sorted(salida["graficas"].glob("*.png"))
    if graf:
        L += ["## Graficas"] + [f"- `{g.relative_to(salida['graficas'].parent.parent)}`" for g in graf] + [""]
    L += ["## Reproducibilidad",
          f"Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `{salida['ejecucion'].name}/manifiesto.json`. "
          f"Reejecutar: `python main.py ejecutar {cfg['id']}`.", ""]
    p = salida["ejecucion"] / "informe.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


def resumen_ejecutivo(df: pd.DataFrame) -> Path:
    """Tabla resumen (ultima ejecucion de cada experimento) en Markdown y CSV."""
    filas = []
    for _, r in df.iterrows():
        rr = r.to_dict()
        rr.setdefault("tarea", "patrones" if str(rr.get("id_experimento", "")).startswith("M18") else "supervisado")
        et, tx = veredicto(rr)
        perm = rr.get("permutacion") if isinstance(rr.get("permutacion"), dict) else {}
        filas.append({
            "experimento": rr.get("id_experimento"), "estado": rr.get("estado"), "unidades": rr.get("unidades"),
            "grupos": rr.get("grupos"), "clases": rr.get("clases_evaluables"), "mejor_modelo": rr.get("mejor_modelo"),
            "metrica": rr.get("metrica_principal"), "valor": rr.get("valor_mejor"), "baseline": rr.get("valor_baseline"),
            "control_plataforma": rr.get("valor_control_instrumental"), "sin_agrupar": rr.get("valor_optimista_sin_agrupar"),
            "p_permutacion": perm.get("p_valor"), "veredicto": et, "run_id": rr.get("run_id"),
        })
    t = pd.DataFrame(filas)
    d = asegurar_dir(ruta("salidas", "resumen"))
    guardar_tabla(t, d / "resumen_ejecutivo.csv")
    md = ["# Resumen ejecutivo de experimentos", "",
          "Ultima ejecucion de cada experimento. Metricas sobre validacion agrupada por articulo (o formula para los "
          "modelos de compuesto). `control_plataforma` = mismo modelo con solo variables instrumentales; `sin_agrupar` = "
          "validacion ingenua (optimista).", "",
          "Veredictos: **senal robusta** (ganancia >= 0.15 sobre baseline, p < 0.05, supera al control); **senal debil** "
          "(ganancia 0.05-0.15); **confundido con plataforma** (el control instrumental rinde igual); **sin senal**; "
          "**evidencia insuficiente** (< 10 grupos independientes o mediana < 3 grupos por clase); **no viable** (clases/grupos "
          "insuficientes para evaluar).", "", _tabla_md(t.drop(columns=["run_id"]), 100), ""]
    p = d / "resumen_ejecutivo.md"
    p.write_text("\n".join(md), encoding="utf-8")
    return p


def guia_modelos(df: pd.DataFrame) -> Path:
    """Manual por modelo (05_Documentacion/guia_modelos.md) a partir de los YAML y la ultima ejecucion de cada uno."""
    from ..config.esquema import cargar_config, listar_configs
    ult = {r["id_experimento"]: r for r in df.to_dict("records")} if not df.empty else {}
    L = ["# Guia de modelos", "",
         "Generada por `python main.py resumen` a partir de `02_Script/config/modelos/*.yaml` y de la ultima ejecucion de "
         "cada experimento. Para cambiar un experimento edite su YAML (ver `02_Script/README.md`, seccion Configuracion) y "
         "reejecutelo con `python main.py ejecutar <ID>`.", ""]
    for p in listar_configs():
        c = cargar_config(p)
        r = ult.get(c["id"], {})
        L += [f"## {c['id']} - {c['nombre']}", "", f"**Pregunta.** {c['pregunta_cientifica'].strip()}", ""]
        if c.get("descripcion"):
            L += [f"**Diseno.** {c['descripcion'].strip()}", ""]
        if c["tarea"] == "supervisado":
            L += [f"- Conjunto: `{c['conjunto']['nombre']}` con parametros `{c['conjunto'].get('parametros', {})}`",
                  f"- Modelos: {', '.join(m['nombre'] for m in c['modelos'])}",
                  f"- Validacion: {c['split']['strategy']} ({c['split']['n_splits']} particiones), clases con >= "
                  f"{c['split']['min_groups_per_class']} grupos y >= {c['split']['min_samples_per_class']} unidades; "
                  f"{c['evaluation'].get('n_permutations', 0)} permutaciones"]
        if r:
            rr = dict(r)
            rr.setdefault("tarea", c["tarea"])
            et, tx = veredicto(rr)
            L += [f"- Ultima ejecucion: `{r.get('run_id')}` - estado **{r.get('estado')}**, veredicto **{et}**"]
            if tx:
                L += [f"- Resultado: {tx}"]
            if isinstance(r.get("hallazgos"), list):
                L += ["- Hallazgos:"] + [f"  - {h}" for h in r["hallazgos"]]
        else:
            L += ["- Sin ejecuciones registradas."]
        if c.get("interpretacion"):
            L += ["", f"**Como interpretarlo.** {c['interpretacion'].strip()}"]
        L += [""]
    p = ruta("salidas", "documentacion") / "guia_modelos.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(L), encoding="utf-8")
    return p
