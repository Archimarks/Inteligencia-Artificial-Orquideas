#
# Archivo: reporte_global.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Reúne los resúmenes de entrenamiento y genera un índice global más un informe
# separado por tarea, con métricas aplicables y sus límites de interpretación.
#
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime

import pandas as pd

from .. import submodulo

rutas = submodulo("00_fundamentos.rutas")
registro = submodulo("00_fundamentos.registro")
config = submodulo("00_fundamentos.config")

_VALIDACION_SIN_Y = (
    "No aplica: aprendizaje no supervisado; no requiere columna Y.")
_CLAVES_FIJAS = (
    "estado", "paradigma", "tarea", "objetivo", "modelo", "dataset", "archivo_fuente",
    "dispositivo", "validacion", "n_filas", "n_filas_dataset", "n_features",
    "marca_tiempo", "directorio_resultados", "tipo_error", "error", "recomendacion",
    "alertas_interpretacion",
)
_METRICAS_TAREA = {
    "Clasificación": (
        "accuracy", "balanced_accuracy", "precision_macro", "recall_macro",
        "f1_macro", "f1_weighted",
    ),
    "Regresión": ("rmse", "mae", "r2"),
    "Clustering": (
        "n_clusters", "silhouette", "davies_bouldin", "ruido_pct",
        "tamano_cluster_min", "tamano_cluster_max", "estabilidad_ari_media",
        "k_mejor_silhouette", "k_candidatos_evaluados",
        "cluster_minimo_requerido", "cluster_minimo_observado",
        "k_seleccion_criterio",
        "estabilidad_ari_desviacion", "estabilidad_ari_repeticiones",
        "batch_nmi", "batch_ari",
        "especie_nmi", "especie_ari", "batch_holdout_batches",
        "batch_holdout_fuera_soporte_pct", "batch_holdout_distancia_mediana",
        "batch_n_especies_mediana", "batch_una_especie_pct",
        "especie_un_batch_pct",
        "cobertura_clasificacion_media_pct",
        "cobertura_clasificacion_mediana_pct",
        "especies_cobertura_menor_10_pct",
        "especies_cobertura_menor_30_pct",
        "especies_cobertura_menor_50_pct",
        "muestras_cobertura_menor_10_pct",
        "muestras_cobertura_menor_30_pct",
        "muestras_cobertura_menor_50_pct",
    ),
    "Reducción de dimensionalidad": ("trustworthiness", "varianza_explicada_acumulada"),
    "Detección de anomalías": (
        "anomalias_n", "anomalias_pct", "separacion_puntaje", "silhouette_anomalias",
        "diagnostico_covarianza",
    ),
    "Reglas de asociación": (
        "n_reglas", "n_reglas_diagnostico", "min_soporte", "min_confianza",
        "prevalencia_minima_muestras", "muestras_clasificadas_media",
        "muestras_clasificadas_mediana", "muestras_clasificadas_minima",
        "lift_medio",
    ),
    "Cadenas de Markov": (
        "n_secuencias", "n_muestras_unicas", "n_modos_ionizacion", "n_batches",
        "n_transiciones_evaluadas", "n_estados", "precision_siguiente_estado",
        "n_transiciones_en_vocabulario", "cobertura_vocabulario_pct",
        "precision_baseline_orden_cero", "mejora_precision_vs_orden_cero_pp",
        "log_verosimilitud_media", "log_verosimilitud_baseline_orden_cero",
    ),
}
_DESCRIPCIONES = {
    "accuracy": "Exactitud; puede ocultar clases poco frecuentes (más alto es mejor).",
    "balanced_accuracy": "Exactitud media por clase; reduce el efecto del desbalance.",
    "precision_macro": "Precisión media dando igual peso a cada clase.",
    "recall_macro": "Cobertura media dando igual peso a cada clase.",
    "f1_macro": "Media armónica macro de precisión/recall; útil con clases desbalanceadas.",
    "f1_weighted": "F1 ponderado por soporte; las clases frecuentes pesan más.",
    "rmse": "Error cuadrático medio en unidades del objetivo (más bajo es mejor).",
    "mae": "Error absoluto medio en unidades del objetivo (más bajo es mejor).",
    "r2": "Varianza explicada respecto a predecir la media; puede ser negativa.",
    "n_clusters": "Número de grupos encontrados; no mide calidad por sí solo.",
    "silhouette": "Separación/compactación interna; comparable solo con la misma X y tratamiento de ruido.",
    "davies_bouldin": "Dispersión relativa entre grupos (más bajo suele ser mejor).",
    "ruido_pct": "Porcentaje sin grupo asignado por el algoritmo.",
    "tamano_cluster_min": "Tamaño del grupo más pequeño, sin contar ruido.",
    "tamano_cluster_max": "Tamaño del grupo más grande, sin contar ruido.",
    "k_mejor_silhouette": "k con silhouette máximo entre las soluciones que respetan el tamaño mínimo de grupo.",
    "k_candidatos_evaluados": "Cantidad de valores k elegibles tras aplicar el tamaño mínimo de grupo.",
    "cluster_minimo_requerido": "Mínimo de plantas exigido en cada grupo candidato.",
    "cluster_minimo_observado": "Tamaño del grupo más pequeño de la solución seleccionada.",
    "k_seleccion_criterio": "Regla aplicada para elegir k entre las particiones evaluables.",
    "estabilidad_ari_media": "ARI medio frente a submuestras del 80%; descriptivo, no holdout.",
    "estabilidad_ari_desviacion": "Desviación del ARI entre submuestras; más bajo implica menos variación.",
    "estabilidad_ari_repeticiones": "Cantidad de submuestras usadas para estimar estabilidad.",
    "batch_nmi": "Asociación entre cluster y batch; alto alerta posible efecto de lote, no causalidad.",
    "batch_ari": "Concordancia ajustada entre cluster y batch; alto alerta posible efecto de lote.",
    "especie_nmi": "Asociación entre cluster y especie; no demuestra relación causal.",
    "especie_ari": "Concordancia ajustada entre cluster y especie.",
    "batch_holdout_batches": "Batches evaluados como grupos no vistos durante el ajuste.",
    "batch_holdout_fuera_soporte_pct": "Muestras de batch externo más allá del soporte de los grupos entrenados.",
    "batch_holdout_distancia_mediana": "Distancia mediana al centroide asignado en batches no usados durante el ajuste.",
    "batch_n_especies_mediana": "Mediana de especies representadas por batch.",
    "batch_una_especie_pct": "Porcentaje de batches que contienen una sola especie; alto indica confusión batch-especie posible.",
    "especie_un_batch_pct": "Porcentaje de especies observadas en un solo batch; alto limita la separación de ambos efectos.",
    "cobertura_clasificacion_media_pct": "Media de registros clasificados por unidad de análisis; considerar junto a la mediana.",
    "cobertura_clasificacion_mediana_pct": "Mediana de cobertura de clasificación química.",
    "especies_cobertura_menor_10_pct": "Especies con menos de 10% de registros clasificados.",
    "especies_cobertura_menor_30_pct": "Especies con menos de 30% de registros clasificados.",
    "especies_cobertura_menor_50_pct": "Especies con menos de 50% de registros clasificados.",
    "muestras_cobertura_menor_10_pct": "Muestras con menos de 10% de registros clasificados.",
    "muestras_cobertura_menor_30_pct": "Muestras con menos de 30% de registros clasificados.",
    "muestras_cobertura_menor_50_pct": "Muestras con menos de 50% de registros clasificados.",
    "trustworthiness": "Conservación de vecindarios locales (cercano a 1 es mejor; no mide calidad de clusters).",
    "varianza_explicada_acumulada": "Fracción de varianza retenida por las componentes guardadas.",
    "anomalias_n": "Número de muestras marcadas como anomalías; requiere revisión.",
    "anomalias_pct": "Porcentaje marcado como anomalía; depende del modelo y sus parámetros.",
    "diagnostico_covarianza": "Aviso de posible matriz de covarianza singular para EllipticEnvelope; sus resultados no deben interpretarse sin cautela.",
    "separacion_puntaje": "Separación interna de puntajes; no confirma anomalías reales.",
    "silhouette_anomalias": "Separación geométrica de normal/anomalía; cerca de cero indica solapamiento.",
    "n_reglas": "Total de reglas que cumplen los umbrales configurados.",
    "n_reglas_diagnostico": "Reglas incluidas en el CSV legible (máximo 200).",
    "min_soporte": "Fracción mínima de perfiles de especie donde aparece el conjunto de la regla.",
    "min_confianza": "Umbral mínimo de confianza condicional de la regla.",
    "prevalencia_minima_muestras": "Fracción mínima de muestras biológicas clasificadas en que debe aparecer una clase para contarla presente en una especie.",
    "muestras_clasificadas_media": "Media de muestras biológicas clasificadas que sustentan cada perfil vegetal para Apriori.",
    "muestras_clasificadas_mediana": "Mediana de muestras biológicas clasificadas que sustentan cada perfil vegetal para Apriori.",
    "muestras_clasificadas_minima": "Menor número de muestras biológicas clasificadas usado en un perfil vegetal para Apriori.",
    "lift_medio": "Lift medio; >1 indica asociación sobre independencia, no causalidad.",
    "n_secuencias": "Número de corridas instrumentales independientes modeladas.",
    "n_muestras_unicas": "Número de muestras biológicas representadas en las corridas.",
    "n_modos_ionizacion": "Cantidad de modos instrumentales; cada modo permanece en una secuencia separada.",
    "n_batches": "Cantidad de lotes disponibles para validación agrupada.",
    "n_transiciones_evaluadas": "Todas las transiciones del conjunto de prueba; los estados desconocidos cuentan como fallos top-1.",
    "n_transiciones_en_vocabulario": "Transiciones de prueba con estados conocidos por el entrenamiento.",
    "n_estados": "Cantidad de clases químicas distintas en el vocabulario de Markov.",
    "cobertura_vocabulario_pct": "Porcentaje de transiciones de prueba cubiertas por el vocabulario entrenado; cobertura baja limita la transferencia.",
    "precision_siguiente_estado": "Exactitud top-1 para predecir la clase siguiente.",
    "precision_baseline_orden_cero": "Exactitud de predecir siempre el estado siguiente más frecuente en entrenamiento.",
    "mejora_precision_vs_orden_cero_pp": "Diferencia de exactitud frente al baseline, en puntos porcentuales.",
    "log_verosimilitud_media": "Log-probabilidad media del siguiente estado; más cerca de cero es mejor.",
    "log_verosimilitud_baseline_orden_cero": "Log-probabilidad media del baseline de frecuencia.",
}


def recolectar() -> pd.DataFrame:
    log = registro.obtener()
    por_modelo: dict[Path, tuple[int, dict]] = {}
    for nombre, es_fallo in (("resumen.json", False), ("error.json", True)):
        for ruta in rutas.MODELS.rglob(nombre):
            try:
                datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                log.warning("%s ilegible, se omite del reporte: %s (%s)",
                            nombre, ruta, exc)
                continue
            fila = {clave: datos.get(clave) for clave in _CLAVES_FIJAS}
            fila["estado"] = datos.get("estado") or ("FALLIDO" if es_fallo else "COMPLETADO")
            fila["directorio_resultados"] = datos.get(
                "directorio_resultados", str(ruta.parent.relative_to(rutas.RAIZ)))
            if es_fallo:
                fila["recomendacion"] = datos.get("recomendacion")
            else:
                fila["archivo_fuente"] = (
                    fila["archivo_fuente"] or "No registrado (entrenamiento anterior)")
                metricas = datos.get("metricas", {})
                if fila["paradigma"] == "No supervisado":
                    detalle_validacion = fila["validacion"] or ""
                    detalle_validacion = detalle_validacion.replace(
                        "sin validacion (no hay Y)", "").replace("no hay Y", "").strip(" ;.")
                    fila["validacion"] = (
                        f"{_VALIDACION_SIN_Y} {detalle_validacion}".strip())
                alertas = (
                    datos.get("alertas_interpretacion")
                    or _alertas_heredadas(str(fila["tarea"]), metricas)
                )
                fila["alertas_interpretacion"] = "; ".join(alertas)
                if alertas and fila["estado"] == "COMPLETADO":
                    fila["estado"] = "COMPLETADO_CON_ALERTAS"
                if ("vegetal por especie" in str(fila["dataset"]).casefold()):
                    metricas = {
                        clave: valor for clave, valor in metricas.items()
                        if clave not in {"especie_nmi", "especie_ari"}
                    }
                fila.update(metricas)
            anterior = por_modelo.get(ruta.parent)
            if anterior is None or ruta.stat().st_mtime_ns > anterior[0]:
                por_modelo[ruta.parent] = (ruta.stat().st_mtime_ns, fila)
    return pd.DataFrame(fila for _, fila in por_modelo.values())


def _columnas_metricas(grupo: pd.DataFrame) -> list[str]:
    candidatas = _METRICAS_TAREA.get(str(grupo["tarea"].iloc[0]), ())
    return [columna for columna in candidatas
            if columna in grupo and grupo[columna].notna().any()]


def _slug(texto: str) -> str:
    ascii_texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_texto.casefold()).strip("_")


def _alertas_heredadas(tarea: str, metricas: dict) -> list[str]:
    alertas = []
    if tarea == "Clustering":
        silhouette = metricas.get("silhouette")
        if silhouette is not None and silhouette < 0.25:
            alertas.append("Silhouette < 0.25: separación interna débil.")
        estabilidad = metricas.get("estabilidad_ari_media")
        if estabilidad is not None and estabilidad < 0.6:
            alertas.append("ARI de estabilidad < 0.60: agrupamiento sensible al submuestreo.")
        if metricas.get("especies_cobertura_menor_10_pct", 0) > 0:
            alertas.append("Hay especies con cobertura química menor al 10%.")
    elif tarea == "Cadenas de Markov":
        cobertura = metricas.get("cobertura_vocabulario_pct")
        if (cobertura is not None
                and cobertura < config.MARKOV_COBERTURA_MINIMA_ALERTA_PCT):
            alertas.append(
                "Cobertura baja del vocabulario en datos de prueba; la cadena no "
                "representa bien los estados de batches no vistos.")
        mejora = metricas.get("mejora_precision_vs_orden_cero_pp")
        if mejora is not None and mejora <= 0:
            alertas.append(
                "La cadena no supera el baseline de frecuencia global en precision.")
    return alertas


def _conclusion_tarea(tarea: str) -> list[str]:
    if tarea == "Clustering":
        return [
            "Interpretación: silhouette y estabilidad son diagnósticos internos, no validación biológica.",
            "k se elige entre soluciones con tamaño mínimo por grupo mediante un error estándar aproximado;",
            "el número de grupos sigue siendo exploratorio y debe contrastarse con conocimiento botánico.",
            "DBSCAN puede fallar sin que los datos estén dañados: indica que no encontró densidad",
            "con soporte suficiente en las configuraciones examinadas; revise error.json para",
            "el detalle del intento y la recomendación.",
            "Una asociación alta con batch puede reflejar condiciones experimentales; revise",
            "validacion_lote_externo.csv, cruce_lote_grupo.csv, composicion_batch_especie.csv",
            "y sensibilidad_cobertura.csv.",
            "La transferencia externa usa predict nativo donde existe; Agglomerative y DBSCAN",
            "usan asignación por centroides solo como diagnóstico, no como inferencia nativa.",
            "Los ceros del perfil significan no detectado/no clasificado, no ausencia química confirmada.",
        ]
    if tarea == "Reducción de dimensionalidad":
        return [
            "Interpretación: trustworthiness evalúa vecindarios, no separabilidad ni calidad predictiva.",
            "n_filas indica cuántas muestras ajustó el modelo; n_filas_dataset es el total disponible.",
            "Los algoritmos cuadráticos usan una submuestra determinista cuando el dataset supera el tope.",
        ]
    if tarea == "Detección de anomalías":
        return ["Interpretación: anomalías son candidatos a revisar, no observaciones erróneas confirmadas.",
                "Consulte diagnostico.csv para muestra, puntaje y características atípicas."]
    if tarea == "Reglas de asociación":
        return ["Interpretación: las reglas son asociaciones descriptivas, no relaciones causales.",
                "La presencia requiere prevalencia mínima entre muestras biológicas clasificadas; "
                "varios modos de una misma muestra no se cuentan como réplicas.",
                "diagnostico.csv muestra el top 200; reglas_completas.csv permite revisar todas "
                "las reglas que superaron los umbrales."]
    if tarea == "Cadenas de Markov":
        return [
            "Interpretación: cada modo de ionización se modela como secuencia independiente; "
            "el holdout separa batches completos cuando hay suficientes lotes.",
            "Cobertura de vocabulario baja significa que muchas clases de las pruebas no aparecieron al entrenar.",
            "Compare la exactitud y log-probabilidad con el baseline de orden cero; el azar uniforme no basta.",
        ]
    return []


def _reporte_tarea(tarea: str, grupo: pd.DataFrame) -> str:
    grupo = grupo.sort_values(["estado", "modelo", "objetivo"], na_position="first")
    metricas = _columnas_metricas(grupo)
    buenos = grupo[grupo["estado"] != "FALLIDO"]
    fallidos = grupo[grupo["estado"] == "FALLIDO"]
    con_alertas = int(buenos["estado"].eq("COMPLETADO_CON_ALERTAS").sum())
    columnas_buenos = [
        c for c in (
            "estado", "modelo", "objetivo", "archivo_fuente", "n_filas", "n_features",
            "validacion", *metricas, "alertas_interpretacion", "directorio_resultados",
        ) if c in buenos and buenos[c].notna().any()
    ]
    columnas_fallos = [
        c for c in (
            "estado", "modelo", "tipo_error", "error", "recomendacion",
            "directorio_resultados",
        ) if c in fallidos and fallidos[c].notna().any()
    ]
    lineas = [
        "=" * 76,
        f"RESULTADOS: {tarea}",
        "=" * 76,
        f"Modelos registrados: {len(grupo)} | completados: {len(buenos)} "
        f"({con_alertas} con alertas) | fallidos: {len(fallidos)}",
        "",
        "La ausencia de Y en aprendizaje no supervisado es esperada; no constituye un error.",
    ]
    if not buenos.empty:
        lineas.extend([
            "",
            "## Modelos completados",
            buenos[columnas_buenos].to_string(
                index=False, max_colwidth=60,
                float_format=lambda valor: f"{valor:.4f}"),
        ])
    if not fallidos.empty:
        lineas.extend([
            "",
            "## Modelos fallidos: diagnóstico y siguiente paso",
            fallidos[columnas_fallos].to_string(index=False, max_colwidth=90),
            "Abra error.json para el resumen estructurado y error.log para el traceback.",
        ])
    lineas.extend(["", "## Cómo leer las métricas"])
    lineas.extend(
        f"- {metrica}: {_DESCRIPCIONES.get(metrica, 'Consultar la definición del modelo.')}"
        for metrica in metricas
    )
    lineas.extend(["", "## Límites de interpretación", *_conclusion_tarea(tarea), ""])
    return "\n".join(lineas)


def generar() -> tuple[str, Path | None]:
    df = recolectar()
    if df.empty:
        return "No hay entrenamientos en 03_Resultados/Models todavía.", None

    destino = rutas.RESULTADOS / "Global"
    destino.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino / "resultados.csv", index=False, encoding="utf-8-sig")

    tareas = sorted(df["tarea"].dropna().astype(str).unique())
    secciones = []
    archivos_tarea = []
    for tarea in tareas:
        grupo = df[df["tarea"] == tarea]
        contenido = _reporte_tarea(tarea, grupo)
        nombre = f"comparacion_{_slug(tarea)}.txt"
        (destino / nombre).write_text(contenido, encoding="utf-8")
        archivos_tarea.append(nombre)
        secciones.extend([contenido, ""])

    cabecera = [
        "=" * 76,
        "REPORTE GLOBAL DE RESULTADOS",
        "=" * 76,
        f"Generado: {datetime.now():%Y-%m-%d %H:%M}",
        f"Modelos registrados: {len(df)}",
        f"Completados: {int(df['estado'].ne('FALLIDO').sum())} "
        f"({int(df['estado'].eq('COMPLETADO_CON_ALERTAS').sum())} con alertas) | "
        f"Fallidos: {int(df['estado'].eq('FALLIDO').sum())}",
        f"Paradigmas: {', '.join(sorted(df['paradigma'].dropna().astype(str).unique()))}",
        "",
        "Los resultados se separan por tarea: métricas de tareas distintas no son comparables.",
        "Las métricas son descriptivas y no sustituyen una evaluación independiente.",
        "La ausencia de Y en tareas no supervisadas es esperada; no significa que falte un dato.",
        "Los modelos fallidos se incluyen con explicación y recomendación; revise error.json",
        "y error.log en su carpeta específica.",
        "Cada resultado registra el CSV fuente; los entrenamientos antiguos que no guardaban",
        "esa información aparecen como 'No registrado'.",
        "resultados.csv conserva las métricas crudas; cada archivo comparacion_<tarea>.txt",
        "contiene solo las columnas aplicables, una guía de lectura y limitaciones.",
        "",
        "Informes por tarea:",
        *[f"- {nombre}" for nombre in archivos_tarea],
        "",
    ]
    texto = "\n".join(cabecera + secciones)
    ruta_txt = destino / "comparacion.txt"
    ruta_txt.write_text(texto, encoding="utf-8")
    return texto, ruta_txt
