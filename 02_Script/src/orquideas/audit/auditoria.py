"""Auditoria exhaustiva de los CSV de 01_Datos/Base.

Genera en 03_Resultados/Global/auditoria_datos/<run_id>/:
  tablas/   perfiles por archivo, claves foraneas, cardinalidades, distribuciones, calidad
  graficas/ visualizaciones de cobertura, distribuciones y desbalance
  informe_auditoria.md  informe de diagnostico con respuestas a las preguntas del proyecto
  resumen.json          cifras clave (usadas por la documentacion y los experimentos)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import relaciones
from ..data.catalogos import CATALOGOS, cargar_catalogo, mapa_etiquetas, ruta_catalogo
from ..data.dataset import cargar_dataset, identificados, muestras_biologicas, vista_quimica
from ..utils.es import guardar_json, guardar_tabla
from ..utils.huella import huellas_datos
from ..utils.registro import cerrar_archivos, obtener_logger
from ..utils.rutas import asegurar_dir, ruta, ruta_global
from ..visualization import graficas as G


def _perfil_columnas(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    filas = []
    for c in df.columns:
        s = df[c]
        vacio = s.isna() | (s.astype(str).str.strip() == "")
        fila = {"archivo": nombre, "columna": c, "tipo": str(s.dtype), "n": len(s), "vacios": int(vacio.sum()),
                "pct_vacios": round(100 * vacio.mean(), 2), "distintos": int(s.nunique(dropna=True))}
        if c.startswith("ID_"):
            fila["pct_cero"] = round(100 * float((s == 0).mean()), 2)
        if pd.api.types.is_numeric_dtype(s) and not c.startswith("ID_"):
            d = s.dropna()
            if len(d):
                q1, q3 = d.quantile([0.25, 0.75])
                iqr = q3 - q1
                fila.update({"min": d.min(), "p25": q1, "mediana": d.median(), "p75": q3, "max": d.max(),
                             "atipicos_iqr": int(((d < q1 - 3 * iqr) | (d > q3 + 3 * iqr)).sum())})
        else:
            top = s[~vacio].astype(str).value_counts().head(3)
            fila["valores_frecuentes"] = " | ".join(f"{k[:40]} ({v})" for k, v in top.items())
        filas.append(fila)
    return pd.DataFrame(filas)


def _calidad_catalogos() -> pd.DataFrame:
    """Duplicados exactos, nombres duplicados (sin distinguir mayusculas) y problemas de formato."""
    filas = []
    for cat in CATALOGOS.values():
        df = cargar_catalogo(cat.nombre)
        dup_exacto = int(df.drop(columns=[cat.pk]).duplicated().sum()) if cat.pk in df else 0
        dup_nombre = 0
        if cat.etiqueta and cat.etiqueta in df:
            n = df[cat.etiqueta].str.strip().str.casefold()
            dup_nombre = int(n[n != ""].duplicated().sum())
        esp = sum(int(df[c].astype(str).str.contains(r"^\s|\s$", regex=True).sum()) for c in df.columns if df[c].dtype == object)
        filas.append({"catalogo": cat.nombre, "archivo": cat.archivo, "filas": len(df), "columnas": df.shape[1],
                      "pk": cat.pk, "duplicados_exactos_sin_pk": dup_exacto, "nombres_duplicados_casefold": dup_nombre,
                      "celdas_con_espacios_extremos": esp, "tiene_registro_0_no_especificado": bool((df[cat.pk] == 0).any())})
    return pd.DataFrame(filas)


def ejecutar_auditoria(run_id: str | None = None) -> Path:
    run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    out = asegurar_dir(ruta_global("auditoria_datos") / run_id)
    tab, fig = asegurar_dir(out / "tablas"), asegurar_dir(out / "graficas")
    log = obtener_logger("auditoria", out / "auditoria.log")
    log.info("Auditoria %s -> %s", run_id, out)
    R: dict = {"run_id": run_id, "fecha": datetime.now().isoformat(timespec="seconds"), "huellas": huellas_datos()}

    # ---------------------------------------------------------------- estructura
    estructura, perfiles = [], []
    for cat in CATALOGOS.values():
        df = cargar_catalogo(cat.nombre)
        estructura.append({"archivo": cat.archivo, "filas": len(df), "columnas": df.shape[1], "pk": cat.pk,
                           "fks": ", ".join(f"{k}->{v}" for k, v in cat.fks.items()), "bytes": ruta_catalogo(cat.nombre).stat().st_size})
        perfiles.append(_perfil_columnas(df, cat.archivo))
    ds = cargar_dataset()
    estructura.append({"archivo": "Dataset.csv", "filas": len(ds), "columnas": ds.shape[1], "pk": "(sin clave unica; ver informe)",
                       "fks": f"{sum(c.startswith('ID_') for c in ds.columns)} columnas ID_*", "bytes": ruta("datos", "dataset").stat().st_size})
    perfiles.append(_perfil_columnas(ds, "Dataset.csv"))
    guardar_tabla(pd.DataFrame(estructura), tab / "01_estructura_archivos.csv")
    perf = pd.concat(perfiles, ignore_index=True)
    guardar_tabla(perf, tab / "02_perfil_columnas.csv")
    guardar_tabla(_calidad_catalogos(), tab / "03_calidad_catalogos.csv")
    log.info("Estructura y perfiles listos")

    # ---------------------------------------------------------------- relaciones
    fk_cat = relaciones.verificar_fks_catalogos()
    fk_ds = relaciones.verificar_fks_dataset()
    jer = relaciones.verificar_consistencia_jerarquica()
    guardar_tabla(fk_cat, tab / "04_fk_catalogos.csv")
    guardar_tabla(fk_ds, tab / "05_fk_dataset.csv")
    guardar_tabla(jer, tab / "06_consistencia_jerarquica.csv")
    R["fk_huerfanos_total"] = int(fk_cat["huerfanos"].sum() + fk_ds["huerfanos"].sum())

    # ---------------------------------------------------------------- unidades y cardinalidades
    vq = vista_quimica()
    bio = muestras_biologicas(vq)
    ident = identificados(bio)
    mu = cargar_catalogo("muestras")
    mu_bio = mu[(mu["ID_MUESTRA"] > 0) & ~mu["ID_TIPO_MUESTRA"].isin([9, 10])]
    reg = cargar_catalogo("registro_actividades")
    R["filas_dataset"] = len(ds)
    R["filas_replicadas_por_actividad"] = len(ds) - len(vq)
    R["observaciones_quimicas"] = len(vq)
    R["observaciones_muestras_biologicas"] = len(bio)
    R["observaciones_identificadas"] = len(ident)
    R["pct_identificadas"] = round(100 * len(ident) / max(len(bio), 1), 2)
    R["articulos_con_datos"] = int(ds.loc[ds["ID_ARTICULO"] > 0, "ID_ARTICULO"].nunique())
    R["articulos_catalogo"] = int((cargar_catalogo("articulos")["ID_ARTICULO"] > 0).sum())
    R["lotes"] = int(ds["ID_BATCH"].nunique())
    R["muestras_total"] = int((mu["ID_MUESTRA"] > 0).sum())
    R["muestras_biologicas"] = len(mu_bio)
    R["muestras_qc_blanco"] = int(mu["ID_TIPO_MUESTRA"].isin([9, 10]).sum())
    R["especies_con_datos"] = int(ds.loc[ds["ID_ESPECIE"] > 0, "ID_ESPECIE"].nunique())
    R["metabolitos_identificados_distintos"] = int(ident["ID_METABOLITO"].nunique())
    R["registros_actividad"] = len(reg)
    card = {
        "lotes_por_articulo": ds.groupby("ID_ARTICULO")["ID_BATCH"].nunique().describe().to_dict(),
        "muestras_por_lote": mu[mu["ID_MUESTRA"] > 0].groupby("ID_BATCH").size().describe().to_dict(),
        "especies_por_articulo": ds[ds["ID_ESPECIE"] > 0].groupby("ID_ARTICULO")["ID_ESPECIE"].nunique().describe().to_dict(),
        "articulos_por_especie": ds[ds["ID_ESPECIE"] > 0].groupby("ID_ESPECIE")["ID_ARTICULO"].nunique().describe().to_dict(),
        "metabolitos_identificados_por_lote": ident.groupby("ID_BATCH")["ID_METABOLITO"].nunique().describe().to_dict(),
        "lotes_por_metabolito": ident.groupby("ID_METABOLITO")["ID_BATCH"].nunique().describe().to_dict(),
    }
    guardar_tabla(pd.DataFrame(card).T.round(2), tab / "07_cardinalidades.csv", index=True)
    R["cardinalidades"] = card

    por_lote = vq.groupby("ID_BATCH").agg(filas=("ID_MUESTRA", "size"), muestras=("ID_MUESTRA", "nunique"),
                                         identificadas=("ID_METABOLITO", lambda s: int((s > 1).sum())),
                                         metabolitos=("ID_METABOLITO", lambda s: int(s[s > 1].nunique())),
                                         articulo=("ID_ARTICULO", "first"), especie=("ID_ESPECIE", "first"),
                                         columna=("ID_COLUMNA_CROMATOGRAFICA", "first"))
    por_lote["pct_identificadas"] = (100 * por_lote["identificadas"] / por_lote["filas"]).round(2)
    por_lote["especie"] = por_lote["especie"].map(mapa_etiquetas("especies"))
    por_lote["columna"] = por_lote["columna"].map(mapa_etiquetas("columnas"))
    guardar_tabla(por_lote.reset_index(), tab / "08_resumen_por_lote.csv")

    # ---------------------------------------------------------------- distribuciones categoricas
    cats = {"familia": ("ID_FAMILIA", "familias"), "orden": ("ID_ORDEN", "ordenes"), "clase_taxonomica": ("ID_CLASE_TAXONOMICA", "clases_tax"),
            "filo": ("ID_FILO", "filos"), "genero": ("ID_GENERO", "generos"), "especie": ("ID_ESPECIE", "especies"),
            "parte": ("ID_PARTE_ESTUDIADA", "partes"), "tipo_muestra": ("ID_TIPO_MUESTRA", "tipos_muestra"),
            "cultivo": ("ID_TIPO_CULTIVO", "cultivos"), "metodo": ("ID_METODO_EXTRACCION", "metodos"),
            "columna": ("ID_COLUMNA_CROMATOGRAFICA", "columnas"), "modo": ("ID_MODO_IONIZACION", "modos"),
            "nivel": ("ID_NIVEL_IDENTIFICACION", "niveles"), "superclase": ("ID_SUPERCLASE_QUIMICA", "superclases"),
            "aducto": ("ID_ADUCTO", "aductos")}
    resumen_cat = []
    # cobertura por articulo (unidad independiente): cuantos articulos y muestras biologicas tiene cada categoria
    mu_ds = bio[["ID_MUESTRA", "ID_ARTICULO"] + [c for c, _ in cats.values() if c in mu.columns or c in bio.columns]].drop_duplicates("ID_MUESTRA")
    for nombre, (col, cat) in cats.items():
        et = mapa_etiquetas(cat)
        if col in ("ID_MODO_IONIZACION", "ID_NIVEL_IDENTIFICACION", "ID_SUPERCLASE_QUIMICA", "ID_ADUCTO"):
            base = bio if col != "ID_SUPERCLASE_QUIMICA" else ident
            cnt = base.groupby(col).agg(observaciones=("ID_MUESTRA", "size"), articulos=("ID_ARTICULO", "nunique"))
        else:
            cnt = mu_ds.groupby(col).agg(muestras=("ID_MUESTRA", "size"), articulos=("ID_ARTICULO", "nunique"))
        cnt.index = [f"{i} - {et.get(i, '?')}" for i in cnt.index]
        guardar_tabla(cnt.reset_index().rename(columns={"index": nombre}), tab / f"09_distribucion_{nombre}.csv")
        k_art = (cnt["articulos"] >= 2).sum() if "articulos" in cnt else np.nan
        cnt_no0 = cnt[~cnt.index.str.startswith("0 -")]
        prim = cnt_no0.iloc[:, 0]
        resumen_cat.append({"variable": nombre, "categorias_no_vacias": len(cnt_no0), "categorias_con_>=2_articulos": int((cnt_no0["articulos"] >= 2).sum()),
                            "categorias_con_>=3_articulos": int((cnt_no0["articulos"] >= 3).sum()),
                            "razon_desbalance_max_min": round(float(prim.max() / max(prim.min(), 1)), 1) if len(prim) else None,
                            "pct_registros_categoria_0": round(100 * float(cnt.iloc[:, 0][cnt.index.str.startswith('0 -')].sum() / cnt.iloc[:, 0].sum()), 2)})
        if nombre in ("familia", "orden", "parte", "tipo_muestra", "cultivo", "columna", "metodo", "genero", "especie"):
            G.barras(cnt_no0["articulos"].astype(float), fig / f"dist_{nombre}_articulos.png",
                     f"Articulos independientes por {nombre}", nombre, "Numero de articulos",
                     nota=f"Cada barra cuenta articulos distintos (unidad independiente). Solo las categorias con >=2 articulos "
                          f"pueden evaluarse con validacion por grupos ({int((cnt_no0['articulos'] >= 2).sum())} de {len(cnt_no0)}).")
    rc = pd.DataFrame(resumen_cat)
    guardar_tabla(rc, tab / "10_resumen_variables_categoricas.csv")
    R["variables_categoricas"] = rc.to_dict(orient="records")

    # ---------------------------------------------------------------- numericas
    num = ["MASA_MONOISOTOPICA", "RELACION_MASA_CARGA", "TIEMPO_RETENCION_MINUTOS", "ALTURA_PICO"]
    desc = bio[num].describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).T
    desc["pct_faltante"] = (100 * bio[num].isna().mean()).round(2)
    guardar_tabla(desc.reset_index().rename(columns={"index": "variable"}), tab / "11_variables_numericas.csv")
    cov = bio.groupby("ID_BATCH")[num].apply(lambda d: d.notna().mean() * 100).round(1)
    guardar_tabla(cov.reset_index(), tab / "12_cobertura_numericas_por_lote.csv")
    G.mapa_calor(cov.T, fig / "cobertura_numericas_por_lote.png", "Cobertura (%) de variables analiticas por lote",
                 "Lote (ID_BATCH)", "Variable", cmap="mako", cbar_label="% de filas con valor",
                 nota="El tiempo de retencion y la masa no estan disponibles en todos los lotes (p. ej. tablas MRM de Metware sin RT); "
                      "esto limita el uso de RT/masa como predictores comunes.")
    s = bio[["ID_BATCH", "ALTURA_PICO"]].dropna()
    s = s[s["ALTURA_PICO"] > 0].assign(log10_altura=lambda d: np.log10(d["ALTURA_PICO"]))
    med = s.groupby("ID_BATCH")["log10_altura"].median().sort_values()
    fig_, ax = G.plt.subplots(figsize=(14, 5))
    G.sns.boxplot(data=s.sample(min(len(s), 400_000), random_state=0), x="ID_BATCH", y="log10_altura", order=list(med.index),
                  ax=ax, fliersize=0.5, color="#8ecae6")
    ax.set_title("Distribucion de la intensidad (log10 ALTURA_PICO) por lote"); ax.set_xlabel("Lote (ID_BATCH, ordenado por mediana)")
    ax.set_ylabel("log10(intensidad, unidades del lote)"); ax.tick_params(axis="x", rotation=90, labelsize=7)
    G.guardar(fig_, fig / "intensidad_por_lote.png",
              "Las escalas de intensidad difieren varios ordenes de magnitud entre lotes (areas, alturas, contenidos relativos, "
              "datos normalizados). Las intensidades absolutas NO son comparables entre lotes: los perfiles se construyen con "
              "composiciones relativas o presencia/ausencia dentro de cada muestra.")
    R["rango_medianas_log10_intensidad_lotes"] = [round(float(med.min()), 2), round(float(med.max()), 2)]

    # ---------------------------------------------------------------- figuras de cobertura quimica
    G.barras(por_lote["pct_identificadas"], fig / "pct_identificadas_por_lote.png", "Porcentaje de senales con metabolito identificado por lote",
             "Lote", "% de filas identificadas (nivel I-III)", top=None,
             nota="Los lotes de metabolomica no dirigida (p. ej. BAT0005/0006/0018) no tienen anotaciones; los MRM de Metware estan 100% anotados. "
                  "La disponibilidad de identidades quimicas esta fuertemente ligada a la plataforma analitica.")
    sc = ident.groupby("ID_SUPERCLASE_QUIMICA")["ID_METABOLITO"].nunique()
    sc.index = sc.index.map(mapa_etiquetas("superclases"))
    G.barras(sc, fig / "metabolitos_por_superclase.png", "Metabolitos identificados distintos por superclase quimica",
             "Superclase", "Numero de metabolitos distintos",
             nota="'No especificado' agrupa metabolitos sin clase en su fuente; las superclases ClassyFire son la clasificacion armonizada.")
    act = reg.groupby("ID_ACTIVIDAD_BIOLOGICA").agg(registros=("ID_REGISTRO", "size"), especies=("ID_ESPECIE", "nunique"))
    act.index = act.index.map(mapa_etiquetas("actividades"))
    G.barras(act["especies"].astype(float), fig / "actividades_por_especies.png", "Especies con cada actividad biologica registrada",
             "Actividad", "Numero de especies", top=None,
             nota="Mayoritariamente actividades citadas en la literatura del articulo; la ausencia de una actividad no implica que no exista.")
    tev = reg["TIPO_EVIDENCIA"].value_counts()
    guardar_tabla(tev.reset_index(), tab / "13_tipo_evidencia_actividades.csv")
    guardar_tabla(act.reset_index(), tab / "14_actividades_frecuencia.csv")
    R["tipo_evidencia"] = tev.to_dict()

    nivel = bio["ID_NIVEL_IDENTIFICACION"].value_counts().rename(index=mapa_etiquetas("niveles"))
    G.barras(nivel.astype(float), fig / "niveles_identificacion.png", "Observaciones por nivel de identificacion (MSI)",
             "Nivel", "Observaciones", horizontal=False, log=True,
             nota="El nivel IV (senal no identificada) domina el conjunto: la mayor parte de la informacion espectral no tiene identidad quimica.")

    # duplicados potenciales en Dataset (misma muestra, metabolito, aducto y modo con mas de una fila)
    k = ident.groupby(["ID_MUESTRA", "ID_METABOLITO", "ID_MODO_IONIZACION"]).size()
    R["detecciones_repetidas_mismo_metabolito_muestra_modo"] = int((k > 1).sum())
    R["filas_en_detecciones_repetidas"] = int(k[k > 1].sum())

    # ---------------------------------------------------------------- informe
    guardar_json(R, out / "resumen.json")
    _escribir_informe(out, R, rc, por_lote, fk_cat, fk_ds, jer)
    log.info("Auditoria terminada")
    cerrar_archivos(log)
    return out


def _md_tabla(df: pd.DataFrame, max_filas: int = 60) -> str:
    d = df.head(max_filas).copy()
    d.columns = [str(c) for c in d.columns]
    lineas = ["| " + " | ".join(d.columns) + " |", "|" + "---|" * len(d.columns)]
    for _, r in d.iterrows():
        lineas.append("| " + " | ".join(str(v)[:70] for v in r.values) + " |")
    return "\n".join(lineas)


def _escribir_informe(out: Path, R: dict, rc: pd.DataFrame, por_lote: pd.DataFrame, fk_cat, fk_ds, jer) -> None:
    viables = rc[rc["categorias_con_>=2_articulos"] >= 2]["variable"].tolist()
    no_viables = rc[rc["categorias_con_>=2_articulos"] < 2]["variable"].tolist()
    txt = f"""# Informe de auditoria de datos

Ejecucion: `{R['run_id']}` ({R['fecha']}). Huellas SHA-256 de los archivos de entrada en `resumen.json`.

## 1. Inventario
{_md_tabla(pd.read_csv(out / 'tablas/01_estructura_archivos.csv', sep=';'))}

**Unidad de observacion de `Dataset.csv`.** Cada fila es una senal espectral (caracteristica LC/GC-MS o metabolito anotado)
medida en una muestra de un lote, con su intensidad `ALTURA_PICO`. No existe una clave unica: la combinacion natural
(muestra, senal) no tiene identificador de senal. Cuando una muestra tiene k medidas experimentales de actividad, cada
senal se repite k veces (columnas `ID_ACTIVIDAD_BIOLOGICA`, `VALOR_ACTIVIDAD`, `UNIDAD_ACTIVIDAD`): {R['filas_replicadas_por_actividad']:,}
filas replicadas. La vista quimica sin replicacion tiene {R['observaciones_quimicas']:,} observaciones
({R['observaciones_muestras_biologicas']:,} de muestras biologicas, sin QC ni blancos).

| Entidad | Cantidad |
|---|---|
| Articulos con datos / en catalogo | {R['articulos_con_datos']} / {R['articulos_catalogo']} |
| Lotes (batches) | {R['lotes']} |
| Muestras (biologicas / QC+blanco) | {R['muestras_total']} ({R['muestras_biologicas']} / {R['muestras_qc_blanco']}) |
| Especies con datos | {R['especies_con_datos']} |
| Metabolitos identificados distintos (nivel I-III) | {R['metabolitos_identificados_distintos']:,} |
| Observaciones con metabolito identificado | {R['observaciones_identificadas']:,} ({R['pct_identificadas']} %) |
| Registros de actividad biologica | {R['registros_actividad']} |

Jerarquia: articulo (1) -> lote (1..3) -> muestra (n) -> observacion (senal x muestra). Especie, parte, tipo de muestra,
cultivo y metodo de extraccion son atributos de la muestra; columna cromatografica es atributo del lote; modo, aducto,
nivel y metabolito son atributos de la observacion; las actividades biologicas se registran por articulo/especie,
por metabolito (literatura) o por muestra (ensayo experimental) en `05_Pivotes/Registo_Actividades_biologicas.csv`.

## 2. Integridad referencial
Claves foraneas huerfanas (catalogos + Dataset): **{R['fk_huerfanos_total']}**.

{_md_tabla(fk_ds[['columna', 'referencia', 'valores_distintos', 'huerfanos', 'pct_cero']])}

Consistencia jerarquica:

{_md_tabla(jer)}

## 3. Variables categoricas, cobertura y desbalance
La unidad independiente para evaluar generalizacion es el **articulo** (cada articulo usa su propia plataforma, laboratorio
y especie). `categorias_con_>=2_articulos` indica cuantas categorias pueden evaluarse con validacion por grupos.

{_md_tabla(rc)}

## 4. Cobertura por lote
{_md_tabla(por_lote.reset_index()[['ID_BATCH', 'articulo', 'especie', 'columna', 'muestras', 'filas', 'metabolitos', 'pct_identificadas']], 60)}

## 5. Respuestas a las preguntas del diagnostico
1. **Informacion disponible.** Intensidades por senal y muestra, identidades quimicas (para {R['pct_identificadas']} % de las
   observaciones biologicas), clase/superclase quimica, aducto, modo, masa, m/z y RT (cobertura parcial por lote), atributos
   de muestra (especie, parte, tipo, cultivo, extraccion), columna cromatografica y actividades biologicas por especie,
   metabolito o muestra.
2. **Variables utiles para ML.** Composicion quimica relativa por muestra (fraccion de metabolitos por superclase/clase), presencia
   de metabolitos, composicion elemental derivada de la formula (C, H, N, O, P, S, insaturaciones, cocientes H/C y O/C), masa
   monoisotopica. Las intensidades absolutas y el RT no son comparables entre lotes.
3. **Objetivos de prediccion posibles.** Superclase/clase quimica de un metabolito a partir de su formula; modo de ionizacion y
   tipo de aducto a partir de la quimica del compuesto; categorias de muestra (clase taxonomica, familia, orden, parte, tipo de
   muestra, metodo, columna) a partir del perfil quimico; actividades biologicas por especie (multietiqueta).
4. **Requieren supervision.** Los anteriores, con validacion agrupada por articulo para no mezclar datos del mismo estudio.
5. **Se benefician de tecnicas no supervisadas.** Similitud y agrupamiento de especies por perfil quimico, coocurrencia de
   metabolitos y clases, reglas de asociacion, deteccion de perfiles atipicos y redes metabolito-especie-actividad.
6. **No modelables de forma fiable hoy.** Variables con <2 categorias evaluables entre articulos: {', '.join(no_viables) or 'ninguna'}.
   Prediccion de especie entre articulos (casi cada especie aparece en un solo articulo) y de filo/reino (1-2 lotes fuera de
   Magnoliophyta). Regresion de valores de actividad (muy pocos grupos con valor medido y escalas/ensayos distintos).
   Identificacion de un metabolito desconocido: no hay espectros MS/MS en el conjunto.
7. **Limitaciones para generalizar.** Confusion total entre especie, articulo, plataforma analitica y laboratorio; cobertura
   desigual de familias (la mayoria representada por uno o dos articulos); bibliotecas de anotacion distintas entre plataformas
   (los MRM de Metware comparten biblioteca y eso induce coocurrencias artificiales); intensidades no comparables; actividades
   mayoritariamente bibliograficas (etiquetas positivas sin negativos verificados).
8. **Informacion adicional necesaria.** Espectros MS/MS y RT estandarizados (indices de retencion), mas especies por familia,
   varias especies analizadas con un mismo protocolo, muestras compartidas entre laboratorios (puente de lotes), ensayos de
   actividad con controles negativos y valores cuantitativos homogeneos, y el mapeo pozo-especie de BAT0005/0006.

Variables con >=2 categorias evaluables entre articulos: {', '.join(viables)}.

## 6. Graficas
""" + "\n".join(f"- `graficas/{p.name}`" for p in sorted((out / 'graficas').glob('*.png'))) + "\n"
    (out / "informe_auditoria.md").write_text(txt, encoding="utf-8")
