#
# Archivo: no_supervisado.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Flujo comun de las tareas de 02_No_supervisado (clustering, reduccion de
# dimensionalidad, deteccion de anomalias, reglas de asociacion).
#
# No hay variable objetivo: se carga la matriz de features, se ajusta el modelo,
# se calculan metricas propias de la tarea y se guarda
# modelo.joblib + resumen.json + graficos/ + fila en el leaderboard, igual que
# en supervisado. Exige un perfil de hardware activo.
#
from __future__ import annotations

import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, Normalizer, StandardScaler

from .. import submodulo

dataset_en_memoria = submodulo("03_datasets.dataset_en_memoria")
datos = submodulo("01_catalogos.datos")
perfiles = submodulo("00_fundamentos.perfiles")
registro = submodulo("00_fundamentos.registro")
resultados = submodulo("00_fundamentos.resultados")
rutas = submodulo("00_fundamentos.rutas")
config = submodulo("00_fundamentos.config")

_VALIDACION_NO_SUPERVISADA = (
    "No aplica: aprendizaje no supervisado; no requiere columna Y.")


# Arma el dataset en memoria (solo features; no tiene Y).
def cargar(paradigma: str, tarea: str, objetivo: str) -> datos.Dataset:
    return dataset_en_memoria.cargar(paradigma, tarea, objetivo, requiere_objetivo=False)


# Devuelve la matriz y el transformador ajustado. Guardar el transformador
# permite aplicar exactamente la misma escala al usar el modelo entrenado.
def matriz_con_preprocesador(ds: datos.Dataset, escalar: bool = True):
    X = ds.X.to_numpy(dtype=float)
    if not len(X):
        raise datos.DatasetError(f"{ds.nombre}: no hay filas para entrenar.")
    if not np.isfinite(X).all():
        raise datos.DatasetError(f"{ds.nombre}: hay valores NaN o infinitos en las features.")
    if not escalar:
        return X, None
    if ds.nombre.startswith("Perfil químico vegetal por especie"):
        if np.any(X < 0):
            raise datos.DatasetError(
                f"{ds.nombre}: Hellinger requiere abundancias no negativas.")
        preprocesador = make_pipeline(
            FunctionTransformer(np.sqrt, validate=False),
            Normalizer(norm="l2"),
        )
        return preprocesador.fit_transform(X), preprocesador
    preprocesador = StandardScaler()
    return preprocesador.fit_transform(X), preprocesador


# Matriz de features como ndarray float, estandarizada salvo que `escalar=False`
# (Reglas de asociacion ya viene 0/1).
def matriz(ds: datos.Dataset, escalar: bool = True) -> np.ndarray:
    return matriz_con_preprocesador(ds, escalar)[0]


_MODELOS_COSTOSOS_POR_TAREA = {
    "Clustering": {"agglomerative", "dbscan"},
    "Reduccion de dimensionalidad": {"kernel_pca", "isomap", "tsne"},
    "Deteccion de anomalias": {"local_outlier_factor", "one_class_svm"},
}


def _limitar_muestra_costosa(tarea: str, modelo: str, ds: datos.Dataset,
                             X: np.ndarray) -> tuple[datos.Dataset, np.ndarray, int]:
    total = ds.n_filas
    limite = config.MAX_FILAS_MODELOS_NO_SUPERVISADOS
    costosos = _MODELOS_COSTOSOS_POR_TAREA.get(
        rutas.tarea_interna("No supervisado", tarea), set())
    if modelo not in costosos or total <= limite:
        return ds, X, total

    indices = np.sort(np.random.default_rng(config.SEMILLA).choice(
        total, limite, replace=False))
    ds = datos.Dataset(
        nombre=ds.nombre,
        X=ds.X.iloc[indices].copy(),
        y=None,
        referencias=ds.referencias.iloc[indices].copy(),
        archivo_fuente=ds.archivo_fuente,
    )
    registro.obtener().warning(
        "'%s' escala cuadráticamente: se ajustará con una submuestra determinista "
        "de %d de %d filas (%s).",
        modelo, len(indices), total, ds.archivo_fuente or "fuente no registrada")
    return ds, X[indices], total


def _tabla_diagnostico(ds: datos.Dataset, columnas: dict[str, object]) -> pd.DataFrame:
    tabla = ds.referencias.copy()
    nombre_id = ds.X.index.name or "ID"
    tabla.insert(0, nombre_id, ds.X.index.astype(str))
    for nombre, valores in columnas.items():
        tabla[nombre] = valores
    return tabla.reset_index(drop=True)


def _diagnostico_categoria(referencias: pd.DataFrame, etiquetas: np.ndarray,
                           columna: str, prefijo: str):
    if columna not in referencias or len(referencias) != len(etiquetas):
        return {}, None
    etiquetas = np.asarray(etiquetas)
    categorias = (referencias[columna].fillna("").astype(str).str.strip()
                  .replace("", "Sin dato").to_numpy())
    validas = etiquetas != -1
    categorias_validas = categorias[validas]
    grupos = etiquetas[validas]
    clave_unidades = (
        "especies_evaluadas"
        if prefijo == "especie" and referencias[columna].nunique() == len(referencias)
        else f"{prefijo}_muestras_evaluadas"
    )
    metricas = {
        clave_unidades: int(len(grupos)),
        f"{prefijo}_n_categorias": int(len(np.unique(categorias_validas))),
    }
    if (len(np.unique(categorias_validas)) > 1
            and len(np.unique(categorias_validas)) < len(categorias_validas)
            and len(np.unique(grupos)) > 1):
        metricas[f"{prefijo}_nmi"] = float(
            normalized_mutual_info_score(categorias_validas, grupos))
        metricas[f"{prefijo}_ari"] = float(
            adjusted_rand_score(categorias_validas, grupos))
    tabla = pd.crosstab(
        pd.Series(categorias, name=prefijo.upper()),
        pd.Series(etiquetas.astype(str), name="GRUPO"),
        dropna=False,
    ).reset_index()
    return metricas, tabla


def _validacion_por_lotes(ds: datos.Dataset, modelo: str,
                          X: np.ndarray) -> pd.DataFrame:
    """Evalúa transferencia a grupos de batches no usados al ajustar cada fold."""
    ev_ns = submodulo("02_etl.evaluacion_no_supervisada")
    catalogo = submodulo("01_catalogos.modelos_no_supervisados")
    referencias = ds.referencias.reset_index(drop=True)
    if "REF_BATCH" not in referencias or len(referencias) != len(X):
        return pd.DataFrame()
    batches = referencias["REF_BATCH"].fillna("").astype(str).to_numpy()
    batches_unicos = sorted(set(batches) - {""})
    if len(batches_unicos) < 2:
        return pd.DataFrame()

    cantidad_folds = min(5, len(batches_unicos))
    folds = [batches_unicos[i::cantidad_folds] for i in range(cantidad_folds)]
    filas: list[dict] = []
    for numero_fold, batches_prueba in enumerate(folds, 1):
        prueba = np.isin(batches, batches_prueba)
        entrenamiento = ~prueba
        X_train, X_test = X[entrenamiento], X[prueba]
        if len(X_train) < 3 or not len(X_test):
            continue

        if modelo == "dbscan":
            ajuste, etiquetas_train, eps = ev_ns._ajustar_dbscan(X_train, registro.obtener())
        elif modelo in catalogo.CLUSTERING_CON_K:
            k, _ = ev_ns._elegir_k(modelo, X_train)
            ajuste = catalogo.CLUSTERING[modelo](k)
            etiquetas_train = ajuste.fit_predict(X_train)
            eps = None
        else:
            ajuste = catalogo.CLUSTERING[modelo]()
            etiquetas_train = ajuste.fit_predict(X_train)
            eps = None

        grupos = sorted(set(etiquetas_train) - {-1})
        if not grupos:
            for batch in batches_prueba:
                filas.append({
                    "FOLD": numero_fold, "BATCH": batch,
                    "MUESTRAS_PRUEBA": int(np.sum(batches == batch)),
                    "ESTADO": "Sin grupos en entrenamiento",
                })
            continue

        indices_grupo = {
            grupo: np.flatnonzero(etiquetas_train == grupo) for grupo in grupos
        }
        centroides = {
            grupo: X_train[indices].mean(axis=0)
            for grupo, indices in indices_grupo.items()
        }
        radios = {
            grupo: float(np.percentile(
                np.linalg.norm(X_train[indices] - centroides[grupo], axis=1), 95))
            for grupo, indices in indices_grupo.items()
        }
        distancias = np.column_stack([
            np.linalg.norm(X_test - centroides[grupo], axis=1) for grupo in grupos
        ])
        posiciones = distancias.argmin(axis=1)
        predichas = np.asarray(grupos, dtype=int)[posiciones]
        metodo_asignacion = "centroide más cercano"
        if modelo in {"kmeans", "gaussian_mixture"}:
            predichas = ajuste.predict(X_test)
            posiciones = np.asarray([grupos.index(int(g)) for g in predichas])
            metodo_asignacion = "predict nativo"
        distancias_asignadas = distancias[np.arange(len(X_test)), posiciones]
        radios_asignados = np.asarray([radios[grupo] for grupo in grupos])[posiciones]
        limites = np.maximum(radios_asignados, float(eps or 0.0))
        fuera_soporte = distancias_asignadas > limites
        if modelo == "dbscan":
            predichas[fuera_soporte] = -1
            metodo_asignacion = "centroide DBSCAN (diagnóstico, no predict nativo)"

        mascara_local = referencias.loc[prueba].reset_index(drop=True)
        for batch in batches_prueba:
            seleccion = mascara_local["REF_BATCH"].fillna("").astype(str).to_numpy() == batch
            pred_batch = predichas[seleccion]
            especies = (mascara_local.loc[seleccion, "REF_ESPECIE"]
                        .fillna("Sin dato").astype(str).to_numpy()
                        if "REF_ESPECIE" in mascara_local else np.array([]))
            metricas_especie = {}
            if (len(especies) and len(np.unique(especies)) > 1
                    and len(np.unique(pred_batch)) > 1):
                metricas_especie = {
                    "ESPECIE_NMI": float(normalized_mutual_info_score(especies, pred_batch)),
                    "ESPECIE_ARI": float(adjusted_rand_score(especies, pred_batch)),
                }
            filas.append({
                "FOLD": numero_fold,
                "BATCH": batch,
                "MUESTRAS_PRUEBA": int(seleccion.sum()),
                "GRUPOS_ENTRENAMIENTO": len(grupos),
                "GRUPOS_ASIGNADOS": len(set(pred_batch) - {-1}),
                "FUERA_SOPORTE_PCT": round(
                    100 * float(fuera_soporte[seleccion].mean()), 2),
                "DISTANCIA_CENTROIDE_MEDIANA": float(
                    np.median(distancias_asignadas[seleccion])),
                "METODO_ASIGNACION": metodo_asignacion,
                "ESTADO": "Evaluado",
                **metricas_especie,
            })
    return pd.DataFrame(filas)


def _sensibilidad_cobertura(ds: datos.Dataset, X: np.ndarray,
                            estimador_completo) -> pd.DataFrame:
    referencias = ds.referencias.reset_index(drop=True)
    if "REF_COBERTURA_CLASIFICACION_PCT" not in referencias:
        return pd.DataFrame()
    cobertura = pd.to_numeric(
        referencias["REF_COBERTURA_CLASIFICACION_PCT"], errors="coerce").to_numpy()
    unidad = "ESPECIES" if "vegetal por especie" in ds.nombre else "MUESTRAS"
    filas = []
    ev_ns = submodulo("02_etl.evaluacion_no_supervisada")
    for umbral in config.UMBRALES_COBERTURA_CLUSTERING:
        mascara = np.isfinite(cobertura) & (cobertura >= umbral)
        X_umbral = X[mascara]
        if len(X_umbral) < 3:
            filas.append({
                "COBERTURA_MINIMA_PCT": umbral,
                unidad: len(X_umbral),
                "ESTADO": "Insuficientes unidades de análisis",
            })
            continue
        ajuste = clone(estimador_completo)
        etiquetas = ajuste.fit_predict(X_umbral)
        validas = etiquetas != -1
        grupos = set(etiquetas[validas])
        silhouette = None
        if len(grupos) > 1 and int(validas.sum()) > len(grupos):
            silhouette = ev_ns._silhouette(X_umbral[validas], etiquetas[validas])
        filas.append({
            "COBERTURA_MINIMA_PCT": umbral,
            unidad: len(X_umbral),
            f"{unidad}_EXCLUIDAS": int(len(X) - len(X_umbral)),
            "N_CLUSTERS": len(grupos),
            "RUIDO_PCT": round(100 * float((etiquetas == -1).mean()), 2),
            "SILHOUETTE": silhouette,
            "ESTADO": "Evaluado con parámetros fijos; descriptivo, no holdout",
        })
    return pd.DataFrame(filas)


def _tablas_perfiles_cluster(ds: datos.Dataset, X: np.ndarray,
                             etiquetas: np.ndarray) -> dict[str, pd.DataFrame]:
    referencias = ds.referencias.reset_index(drop=True)
    filas_resumen: list[dict] = []
    filas_firmas: list[dict] = []
    cobertura = pd.to_numeric(
        referencias.get("REF_COBERTURA_CLASIFICACION_PCT",
                        pd.Series(np.nan, index=referencias.index)),
        errors="coerce").to_numpy()
    cobertura_util = pd.to_numeric(
        referencias.get("REF_COBERTURA_QUIMICA_UTIL_PCT",
                        pd.Series(np.nan, index=referencias.index)),
        errors="coerce").to_numpy()
    medias_globales = X.mean(axis=0)
    unidad = "ESPECIES" if "vegetal por especie" in ds.nombre else "MUESTRAS"
    for grupo in sorted(set(etiquetas)):
        mascara = etiquetas == grupo
        sub = referencias.loc[mascara]
        def categoria_principal(columna: str) -> tuple[str, float]:
            if columna not in sub or sub.empty:
                return "Sin dato", 0.0
            valores = sub[columna].fillna("Sin dato").astype(str).replace("", "Sin dato")
            conteo = valores.value_counts()
            return str(conteo.index[0]), float(conteo.iloc[0] / len(valores))

        batch, pct_batch = categoria_principal("REF_BATCH_NOMBRE")
        especie, pct_especie = categoria_principal("REF_ESPECIE")
        fila_resumen = {
            "GRUPO": int(grupo),
            unidad: int(mascara.sum()),
            f"{unidad}_PCT": round(100 * float(mascara.mean()), 2),
            "BATCH_PREDOMINANTE": batch,
            "BATCH_PREDOMINANTE_PCT": round(100 * pct_batch, 2),
            "ESPECIE_PREDOMINANTE": especie,
            "ESPECIE_PREDOMINANTE_PCT": round(100 * pct_especie, 2),
            "COBERTURA_CLASIFICACION_MEDIA_PCT": float(np.nanmean(cobertura[mascara]))
            if np.isfinite(cobertura[mascara]).any() else None,
            "COBERTURA_CLASIFICACION_MEDIANA_PCT": float(np.nanmedian(cobertura[mascara]))
            if np.isfinite(cobertura[mascara]).any() else None,
            "COBERTURA_QUIMICA_UTIL_MEDIA_PCT": float(np.nanmean(cobertura_util[mascara]))
            if np.isfinite(cobertura_util[mascara]).any() else None,
            "NOTA": "Grupo -1 = ruido DBSCAN" if grupo == -1 else "",
        }
        filas_resumen.append(fila_resumen)
        medias_grupo = X[mascara].mean(axis=0)
        diferencias = medias_grupo - medias_globales
        for rango, indice in enumerate(np.argsort(diferencias)[::-1][:10], 1):
            filas_firmas.append({
                "GRUPO": int(grupo),
                "RANK": rango,
                "CLASE_QUIMICA": str(ds.X.columns[indice]),
                "MEDIA_GRUPO_HELLINGER": float(medias_grupo[indice]),
                "MEDIA_GLOBAL_HELLINGER": float(medias_globales[indice]),
                "DIFERENCIA_VS_GLOBAL": float(diferencias[indice]),
            })
    return {
        "perfil_grupos.csv": pd.DataFrame(filas_resumen),
        "firmas_quimicas_grupos.csv": pd.DataFrame(filas_firmas),
    }


def _composicion_batch_especie(referencias: pd.DataFrame) -> tuple[dict, pd.DataFrame | None]:
    columnas = {"REF_BATCH_NOMBRE", "REF_BATCH", "REF_ESPECIE"}
    if not columnas.issubset(referencias.columns):
        return {}, None
    tabla = referencias[["REF_BATCH", "REF_BATCH_NOMBRE", "REF_ESPECIE"]].copy()
    tabla = tabla.replace("", np.nan).dropna(subset=["REF_BATCH", "REF_ESPECIE"])
    if tabla.empty:
        return {}, None
    tabla["BATCH"] = tabla["REF_BATCH_NOMBRE"].fillna(tabla["REF_BATCH"]).astype(str)
    cruce = pd.crosstab(tabla["BATCH"], tabla["REF_ESPECIE"].astype(str))
    especies_por_batch = (cruce > 0).sum(axis=1)
    batches_por_especie = (cruce > 0).sum(axis=0)
    return {
        "batch_n_especies_mediana": float(especies_por_batch.median()),
        "batch_una_especie_pct": float(100 * (especies_por_batch == 1).mean()),
        "especie_un_batch_pct": float(100 * (batches_por_especie == 1).mean()),
    }, cruce.reset_index()


def _resumen_fuentes(archivo_fuente: str | None = None) -> list[dict]:
    carpeta_dataset = rutas.DATOS / "Dataset"
    if archivo_fuente:
        relativa = Path(archivo_fuente)
        candidatos = (
            relativa if relativa.is_absolute() else rutas.RAIZ / relativa,
            carpeta_dataset / relativa.name,
        )
        fuente = next((ruta for ruta in candidatos if ruta.is_file()), None)
        if fuente is None:
            raise FileNotFoundError(
                f"No se encontró el archivo fuente del entrenamiento: {archivo_fuente}")
        fuentes = [fuente]
    else:
        carpeta_batches = rutas.DATOS / "Data" / "Batch"
        if not carpeta_batches.is_dir():
            raise FileNotFoundError(f"No se encontró la carpeta de lotes crudos: {carpeta_batches}")
        fuentes = [
            carpeta_dataset / "04_Dataset_Patrones_Quimicos.csv",
            carpeta_dataset / "03_Dataset_Metabolito_Identificados.csv",
            carpeta_dataset / "03_Catalogo_Metabolito" / "05_Metabolitos.csv",
            carpeta_dataset / "03_Catalogo_Metabolito" / "03_Clases_quimicas.csv",
            carpeta_dataset / "03_Catalogo_Metabolito" / "02_Superclases_quimicas.csv",
        ]
        archivos_batch = sorted(
            fuente for fuente in carpeta_batches.iterdir() if fuente.is_file())
        if not archivos_batch:
            raise FileNotFoundError(f"No hay archivos de lotes crudos en {carpeta_batches}")
        fuentes.extend(archivos_batch)
    resumen = []
    for fuente in fuentes:
        if not fuente.is_file():
            raise FileNotFoundError(f"No se encontró un archivo fuente del entrenamiento: {fuente}")
        info = fuente.stat()
        resumen.append({
            "archivo": str(fuente.relative_to(rutas.RAIZ)),
            "bytes": info.st_size,
            "modificado_utc": datetime.fromtimestamp(
                info.st_mtime, tz=timezone.utc).isoformat(),
        })
    return resumen


def _alertas_resultado(tarea: str, metricas: dict) -> list[str]:
    alertas = []
    if tarea == "Clustering":
        silhouette = metricas.get("silhouette")
        if silhouette is not None and silhouette < 0.25:
            alertas.append(
                "Separación interna débil (silhouette < 0.25); los grupos pueden solaparse.")
        estabilidad = metricas.get("estabilidad_ari_media")
        if estabilidad is not None and estabilidad < 0.6:
            alertas.append(
                "Agrupamiento sensible al submuestreo (ARI medio < 0.60).")
        if metricas.get("especies_cobertura_menor_10_pct", 0) > 0:
            alertas.append(
                "Hay especies con menos de 10% de cobertura química; revisar "
                "sensibilidad_cobertura.csv antes de interpretar sus grupos.")
    elif tarea == "Detección de anomalías":
        alertas.append(
            "Las anomalías son candidatas a revisión, no errores confirmados; "
            "la proporción depende del algoritmo.")
        if metricas.get("diagnostico_covarianza"):
            alertas.append(str(metricas["diagnostico_covarianza"]))
    elif tarea == "Reglas de asociación":
        alertas.append(
            "Las reglas son asociaciones descriptivas; no demuestran causalidad.")
    elif tarea == "Reducción de dimensionalidad":
        alertas.append(
            "La proyección conserva vecindarios, pero no valida grupos ni significado biológico.")
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
                "La cadena no supera el baseline de frecuencia global en precision; "
                "el orden de transiciones no aporta mejora demostrada.")
        if not metricas.get("n_transiciones_evaluadas"):
            alertas.append(
                "No hubo transiciones de prueba evaluables; las métricas no permiten "
                "valorar el modelo.")
    return alertas


# Carpeta del modelo, vaciada (se sobreescribe en cada entrenamiento).
def _preparar_carpeta(paradigma: str, tarea: str, objetivo: str, modelo: str) -> Path:
    return resultados.preparar_carpeta(rutas.carpeta_resultados(paradigma, tarea, objetivo, modelo))


# Guarda modelo + resumen + graficos + leaderboard. `graficos_fn(carpeta_graficos)`
# devuelve la lista de PNG generados (o None).
def finalizar(paradigma: str, tarea: str, objetivo: str, modelo: str, estimador,
              ds: datos.Dataset, metricas: dict, validacion: str,
              graficos_fn: Callable[[Path], list] | None = None,
              preprocesador=None,
              diagnostico: pd.DataFrame | None = None,
              diagnostico_lote: pd.DataFrame | None = None,
              tablas_diagnostico: dict[str, pd.DataFrame] | None = None,
              n_filas_dataset: int | None = None) -> dict:
    log = registro.obtener()
    perfil = perfiles.requerido()
    carpeta = _preparar_carpeta(paradigma, tarea, objetivo, modelo)
    handler = registro.agregar_archivo(carpeta / "entrenamiento.log")
    try:
        log.info("=== %s | %s | %s ===", paradigma, tarea, modelo)
        total = n_filas_dataset if n_filas_dataset is not None else ds.n_filas
        log.info("Dataset %s (%s): %d filas ajustadas de %d disponibles x %d features",
                 ds.nombre, ds.archivo_fuente or "fuente no registrada",
                 ds.n_filas, total, ds.n_features)
        log.info("Validacion: %s", validacion)
        for clave, valor in metricas.items():
            log.info("  %-22s %s", clave,
                     f"{valor:.4f}" if isinstance(valor, (int, float, np.floating)) else valor)
        if "batch_nmi" in metricas or "especie_nmi" in metricas:
            log.info(
                "NMI/ARI comparan grupo con lote/especie. Valores altos indican asociación, "
                "no causalidad; lote y especie pueden estar confundidos.")

        dispositivo = perfiles.dispositivo_de(estimador)
        resultados.guardar_modelo(estimador, carpeta)
        if preprocesador is not None:
            resultados.guardar_modelo(preprocesador, carpeta, nombre="preprocesador.joblib")
        if diagnostico is not None:
            diagnostico.to_csv(carpeta / "diagnostico.csv", sep=";", index=False,
                               encoding="utf-8-sig")
        if diagnostico_lote is not None:
            diagnostico_lote.to_csv(carpeta / "cruce_lote_grupo.csv", sep=";",
                                    index=False, encoding="utf-8-sig")
        diagnosticos_adicionales = []
        for nombre, tabla in (tablas_diagnostico or {}).items():
            tabla.to_csv(carpeta / nombre, sep=";", index=False, encoding="utf-8-sig")
            diagnosticos_adicionales.append(nombre)

        graficos: list = []
        error_graficos = None
        if graficos_fn is not None:
            try:
                graficos = graficos_fn(carpeta / "graficos") or []
            except Exception as exc:
                error_graficos = {
                    "tipo_error": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                resultados.guardar_json(
                    error_graficos, carpeta / "error_graficos.json")
                log.exception("No se pudieron generar los graficos del modelo %s", modelo)

        metricas_json = {
            k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
            for k, v in metricas.items()
        }
        alertas = _alertas_resultado(tarea, metricas)
        if error_graficos:
            alertas.append(
                "El entrenamiento terminó, pero falló la generación de gráficos; "
                "revise error_graficos.json.")
        artefactos = [
            "resumen.json", "entrenamiento.log", "modelo.joblib",
            *(["error_graficos.json"] if error_graficos else []),
            *(["preprocesador.joblib"] if preprocesador is not None else []),
            *(["diagnostico.csv"] if diagnostico is not None else []),
            *(["cruce_lote_grupo.csv"] if diagnostico_lote is not None else []),
            *sorted(diagnosticos_adicionales),
            *[f"graficos/{nombre}" for nombre in sorted(p.name for p in graficos)],
        ]
        resumen = {
            "paradigma": paradigma, "tarea": tarea, "objetivo": objetivo, "modelo": modelo,
            "estado": "COMPLETADO_CON_ALERTAS" if alertas else "COMPLETADO",
            "dataset": ds.nombre, "archivo_fuente": ds.archivo_fuente,
            "features": list(ds.X.columns),
            "perfil": perfil.nombre, "dispositivo": dispositivo,
            "n_filas": ds.n_filas, "n_filas_dataset": total,
            "n_features": ds.n_features,
            "marca_tiempo": resultados.marca_tiempo(),
            "validacion": validacion, "metricas": metricas_json,
            "preprocesador": "preprocesador.joblib" if preprocesador is not None else None,
            "diagnostico": "diagnostico.csv" if diagnostico is not None else None,
            "diagnostico_lote": (
                "cruce_lote_grupo.csv" if diagnostico_lote is not None else None),
            "diagnosticos_adicionales": sorted(diagnosticos_adicionales),
            "directorio_resultados": str(carpeta.relative_to(rutas.RAIZ)),
            "artefactos": artefactos,
            "alertas_interpretacion": alertas,
            "error_graficos": error_graficos,
            "interpretacion_diagnostico_lote": (
                "NMI y ARI cuantifican asociación entre grupo y lote/especie; no prueban "
                "causalidad y el lote puede estar confundido con la especie."
                if "batch_nmi" in metricas_json or "especie_nmi" in metricas_json
                else None),
            "interpretacion_perfil_quimico": (
                "Cada cero significa que esa clase no se detectó o no quedó clasificada "
                "en los registros disponibles de la especie; no demuestra ausencia química. "
                "Cada corrida con señal positiva se normaliza antes de promediar las corridas "
                "de la especie. Las clases desconocidas no se convierten en etiquetas ficticias; "
                "considere la cobertura y el número de corridas al interpretar los grupos."
                if "Perfil químico vegetal por especie" in ds.nombre else
                "Cada cero significa que esa clase no se detectó o no quedó clasificada "
                "en los registros de la muestra; no demuestra ausencia química. La cobertura "
                "debe considerarse al interpretar perfiles y grupos."
                if "Perfil químico" in ds.nombre else None),
            "interpretacion_anomalias": (
                "Las plantas marcadas son candidatas a revisión, no errores confirmados. "
                "diagnostico.csv lista cobertura, puntaje y las cinco features más alejadas "
                "de la mediana global."
                if tarea == "Detección de anomalías" else None),
            "interpretacion_validacion": (
                "La columna Y solo es necesaria para aprendizaje supervisado. Su ausencia "
                "es esperada en esta tarea; la evaluación usa métricas internas/descriptivas."
                if paradigma == "No supervisado" else None),
            "graficos": sorted(p.name for p in graficos),
            "semilla": config.SEMILLA,
            "parametros_modelo": (
                estimador.get_params(deep=True)
                if hasattr(estimador, "get_params") else None),
            "fuentes": _resumen_fuentes(ds.archivo_fuente),
            "entorno": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
            },
        }
        resultados.guardar_json(resumen, carpeta / "resumen.json")
        resultados.actualizar_leaderboard(
            rutas.carpeta_objetivo_resultados(paradigma, tarea, objetivo),
            resultados.fila_leaderboard(resumen))
        log.info("Guardado en %s", carpeta)
        return resumen
    finally:
        registro.quitar_archivo(handler)


# --- entrenar por tarea ------------------------------------------------
# Clustering: selecciona parámetros por silhouette, mide estabilidad y añade
# diagnósticos por batch, cobertura y perfiles. El puntaje de ajuste no es holdout.
def entrenar_clustering(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    from .. import submodulo
    ev_ns = submodulo("02_etl.evaluacion_no_supervisada")
    visualizacion = submodulo("02_etl.visualizacion_no_supervisado")

    log = registro.obtener()
    tarea_interna = rutas.tarea_interna(paradigma, tarea)
    ds = cargar(paradigma, tarea, objetivo)
    X, preprocesador = matriz_con_preprocesador(ds)
    ds, X, n_filas_dataset = _limitar_muestra_costosa(tarea, modelo, ds, X)
    resultado = ev_ns.evaluar_clustering(modelo, X, log)
    metricas_lote, cruce_lote = _diagnostico_categoria(
        ds.referencias, resultado.etiquetas, "REF_BATCH", "batch")
    metricas_especie, cruce_especie = _diagnostico_categoria(
        ds.referencias, resultado.etiquetas, "REF_ESPECIE", "especie")
    metricas_confusion_batch, cruce_batch_especie = _composicion_batch_especie(
        ds.referencias)
    cobertura = pd.to_numeric(
        ds.referencias.get("REF_COBERTURA_CLASIFICACION_PCT", pd.Series(dtype=float)),
        errors="coerce",
    ).dropna()
    if not cobertura.empty:
        unidad_cobertura = (
            "especies" if "vegetal por especie" in ds.nombre else "muestras")
        metricas_cobertura = {
            "cobertura_clasificacion_media_pct": float(cobertura.mean()),
            "cobertura_clasificacion_mediana_pct": float(cobertura.median()),
            "cobertura_clasificacion_minima_pct": float(cobertura.min()),
            f"{unidad_cobertura}_cobertura_reportada": int(cobertura.size),
            f"{unidad_cobertura}_cobertura_cero": int((cobertura == 0).sum()),
            "registros_sin_clasificar_pct_media": float(100 - cobertura.mean()),
        }
        metricas_cobertura.update({
            f"{unidad_cobertura}_cobertura_menor_{int(umbral)}_pct":
            int((cobertura < umbral).sum())
            for umbral in config.UMBRALES_COBERTURA_CLUSTERING
        })
    else:
        metricas_cobertura = {}
    cobertura_util = pd.to_numeric(
        ds.referencias.get("REF_COBERTURA_QUIMICA_UTIL_PCT", pd.Series(dtype=float)),
        errors="coerce",
    ).dropna()
    if not cobertura_util.empty:
        metricas_cobertura.update({
            "cobertura_quimica_util_media_pct": float(cobertura_util.mean()),
            "cobertura_quimica_util_mediana_pct": float(cobertura_util.median()),
            "cobertura_quimica_util_minima_pct": float(cobertura_util.min()),
        })
    resultado.metricas.update(metricas_lote)
    resultado.metricas.update(metricas_especie)
    resultado.metricas.update(metricas_cobertura)
    resultado.metricas.update(metricas_confusion_batch)
    tablas = _tablas_perfiles_cluster(ds, X, resultado.etiquetas)
    if cruce_especie is not None:
        tablas["cruce_especie_grupo.csv"] = cruce_especie
    if cruce_batch_especie is not None:
        tablas["composicion_batch_especie.csv"] = cruce_batch_especie
    sensibilidad = _sensibilidad_cobertura(ds, X, resultado.estimador)
    if not sensibilidad.empty:
        tablas["sensibilidad_cobertura.csv"] = sensibilidad
    holdout_lotes = _validacion_por_lotes(ds, modelo, X)
    if not holdout_lotes.empty:
        tablas["validacion_lote_externo.csv"] = holdout_lotes
        evaluadas = holdout_lotes[holdout_lotes.get("ESTADO") == "Evaluado"]
        resultado.metricas["batch_holdout_batches"] = int(len(evaluadas))
        if not evaluadas.empty:
            pesos = evaluadas["MUESTRAS_PRUEBA"].to_numpy(dtype=float)
            resultado.metricas["batch_holdout_fuera_soporte_pct"] = float(
                np.average(evaluadas["FUERA_SOPORTE_PCT"], weights=pesos))
            resultado.metricas["batch_holdout_distancia_mediana"] = float(
                np.median(evaluadas["DISTANCIA_CENTROIDE_MEDIANA"]))

    def graficos_fn(destino):
        ctx = visualizacion.ContextoNS(
            modelo=modelo, paradigma=paradigma, tarea=tarea, metricas=resultado.metricas,
            nombres_features=list(ds.X.columns), n_filas=ds.n_filas,
            X=X, etiquetas=resultado.etiquetas)
        return visualizacion.generar_no_supervisado(tarea_interna, destino, ctx, log)

    if resultado.k_elegido:
        validacion = (
            f"Evaluación interna no supervisada; no requiere Y. "
            f"k={resultado.k_elegido} se seleccionó por silhouette en los datos de ajuste "
            "(no es holdout).")
    elif modelo == "dbscan":
        validacion = (
            "Evaluación interna no supervisada; no requiere Y. "
            f"DBSCAN eps={resultado.metricas['dbscan_eps']:.5g}, "
            f"min_samples={resultado.metricas['dbscan_min_samples']}.")
    else:
        validacion = "Evaluación interna no supervisada; no requiere Y; modelo por densidad."
    if ds.n_filas < n_filas_dataset:
        validacion += (
            f"; ajuste sobre submuestra determinista de {ds.n_filas} "
            f"de {n_filas_dataset} filas")
    return finalizar(paradigma, tarea, objetivo, modelo, resultado.estimador, ds,
                     resultado.metricas, validacion, graficos_fn, preprocesador,
                     _tabla_diagnostico(ds, {"GRUPO": resultado.etiquetas}),
                     cruce_lote, tablas, n_filas_dataset=n_filas_dataset)


# Reduccion de dimensionalidad: ajusta, mide trustworthiness sobre todos los datos.
def entrenar_reduccion(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    from .. import submodulo
    ev_ns = submodulo("02_etl.evaluacion_no_supervisada")
    visualizacion = submodulo("02_etl.visualizacion_no_supervisado")

    log = registro.obtener()
    tarea_interna = rutas.tarea_interna(paradigma, tarea)
    ds = cargar(paradigma, tarea, objetivo)
    X, preprocesador = matriz_con_preprocesador(ds)
    ds, X, n_filas_dataset = _limitar_muestra_costosa(tarea, modelo, ds, X)
    resultado = ev_ns.evaluar_reduccion(modelo, X, log)

    def graficos_fn(destino):
        ctx = visualizacion.ContextoNS(
            modelo=modelo, paradigma=paradigma, tarea=tarea, metricas=resultado.metricas,
            nombres_features=list(ds.X.columns), n_filas=ds.n_filas,
            X=X, X_reducido=resultado.X_reducido, estimador=resultado.estimador)
        return visualizacion.generar_no_supervisado(tarea_interna, destino, ctx, log)

    componentes = {
        f"COMPONENTE_{i + 1}": resultado.X_reducido[:, i]
        for i in range(resultado.X_reducido.shape[1])
    }
    validacion = _VALIDACION_NO_SUPERVISADA
    if ds.n_filas < n_filas_dataset:
        validacion = (
            f"{_VALIDACION_NO_SUPERVISADA} Ajuste sobre submuestra determinista "
            f"de {ds.n_filas} de {n_filas_dataset} filas.")
    return finalizar(paradigma, tarea, objetivo, modelo, resultado.estimador, ds,
                     resultado.metricas, validacion, graficos_fn,
                     preprocesador, _tabla_diagnostico(ds, componentes),
                     n_filas_dataset=n_filas_dataset)


# Deteccion de anomalias: ajusta, separa normal/anomalia, mide separacion de puntaje.
def entrenar_anomalias(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    from .. import submodulo
    ev_ns = submodulo("02_etl.evaluacion_no_supervisada")
    visualizacion = submodulo("02_etl.visualizacion_no_supervisado")

    log = registro.obtener()
    tarea_interna = rutas.tarea_interna(paradigma, tarea)
    ds = cargar(paradigma, tarea, objetivo)
    X, preprocesador = matriz_con_preprocesador(ds)
    ds, X, n_filas_dataset = _limitar_muestra_costosa(tarea, modelo, ds, X)
    resultado = ev_ns.evaluar_anomalias(modelo, X, log)
    anomalias = resultado.etiquetas == -1
    resultado.metricas["anomalias_n"] = int(anomalias.sum())

    def graficos_fn(destino):
        ctx = visualizacion.ContextoNS(
            modelo=modelo, paradigma=paradigma, tarea=tarea, metricas=resultado.metricas,
            nombres_features=list(ds.X.columns), n_filas=ds.n_filas,
            X=X, etiquetas=resultado.etiquetas, es_anomalia=True, puntajes=resultado.puntajes)
        return visualizacion.generar_no_supervisado(tarea_interna, destino, ctx, log)

    diagnostico = _tabla_diagnostico(ds, {
        "ESTADO": np.where(anomalias, "Anomalia", "Normal"),
        "PUNTAJE_NORMALIDAD": resultado.puntajes,
    })
    medianas = np.median(X, axis=0)
    desviaciones = np.abs(X - medianas)
    top = np.argsort(desviaciones, axis=1)[:, -5:][:, ::-1]
    diagnostico["FEATURES_ATIPICAS"] = [
        " | ".join(str(ds.X.columns[i]) for i in indices) for indices in top
    ]
    diagnostico["VALORES_HELLINGER_ATIPICOS"] = [
        " | ".join(f"{X[fila, i]:.4g}" for i in indices)
        for fila, indices in enumerate(top)
    ]
    diagnostico["DESVIACIONES_ABS_ATIPICAS"] = [
        " | ".join(f"{desviaciones[fila, i]:.4g}" for i in indices)
        for fila, indices in enumerate(top)
    ]
    diagnostico = diagnostico.sort_values(
        ["ESTADO", "PUNTAJE_NORMALIDAD"], ascending=[True, True])
    validacion = _VALIDACION_NO_SUPERVISADA
    if ds.n_filas < n_filas_dataset:
        validacion = (
            f"{_VALIDACION_NO_SUPERVISADA} Ajuste sobre submuestra determinista "
            f"de {ds.n_filas} de {n_filas_dataset} filas.")
    return finalizar(paradigma, tarea, objetivo, modelo, resultado.estimador, ds,
                     resultado.metricas, validacion, graficos_fn,
                     preprocesador, diagnostico, n_filas_dataset=n_filas_dataset)


# Reglas de asociacion: unico "modelo" (apriori) -- no es un estimador
# fit/predict, el "estimador" guardado es la lista de reglas encontradas.
def entrenar_reglas(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    from .. import submodulo
    reglas_asociacion = submodulo("01_catalogos.reglas_asociacion")
    visualizacion = submodulo("02_etl.visualizacion_no_supervisado")

    log = registro.obtener()
    tarea_interna = rutas.tarea_interna(paradigma, tarea)
    ds = cargar(paradigma, tarea, objetivo)
    X = matriz(ds, escalar=False)  # ya es 0/1, no estandarizar
    reglas = reglas_asociacion.entrenar(X, list(ds.X.columns))

    lift_medio = float(np.mean([r.lift for r in reglas])) if reglas else 0.0
    metricas = {
        "n_reglas": len(reglas),
        "lift_medio": lift_medio,
        "min_soporte": config.REGLAS_MIN_SOPORTE,
        "min_confianza": config.REGLAS_MIN_CONFIANZA,
        "prevalencia_minima_muestras": config.REGLAS_MIN_PREVALENCIA_MUESTRAS,
        "tamano_max_itemset": config.REGLAS_TAMANO_MAX_ITEMSET,
        "n_reglas_diagnostico": min(len(reglas), config.REGLAS_MAX_DIAGNOSTICO),
    }
    muestras_clasificadas = pd.to_numeric(
        ds.referencias.get(
            "REF_CANTIDAD_MUESTRAS_CLASIFICADAS", pd.Series(dtype=float)),
        errors="coerce",
    ).dropna()
    if not muestras_clasificadas.empty:
        metricas.update({
            "muestras_clasificadas_media": float(muestras_clasificadas.mean()),
            "muestras_clasificadas_mediana": float(muestras_clasificadas.median()),
            "muestras_clasificadas_minima": int(muestras_clasificadas.min()),
        })
    columnas_reglas = [
        "ANTECEDENTE", "CONSECUENTE", "SOPORTE", "CONFIANZA", "LIFT",
    ]
    tabla_reglas_completas = pd.DataFrame([{
        "ANTECEDENTE": " + ".join(regla.antecedente),
        "CONSECUENTE": regla.consecuente,
        "SOPORTE": regla.soporte,
        "CONFIANZA": regla.confianza,
        "LIFT": regla.lift,
    } for regla in reglas], columns=columnas_reglas)
    if not tabla_reglas_completas.empty:
        tabla_reglas_completas = tabla_reglas_completas.sort_values(
            ["LIFT", "CONFIANZA", "SOPORTE"],
            ascending=[False, False, False])
    tabla_reglas = tabla_reglas_completas.head(
        config.REGLAS_MAX_DIAGNOSTICO).copy()

    def graficos_fn(destino):
        ctx = visualizacion.ContextoNS(
            modelo=modelo, paradigma=paradigma, tarea=tarea, metricas=metricas,
            nombres_features=list(ds.X.columns), n_filas=ds.n_filas, reglas=reglas)
        return visualizacion.generar_no_supervisado(tarea_interna, destino, ctx, log)

    return finalizar(paradigma, tarea, objetivo, modelo, reglas, ds,
                     metricas, _VALIDACION_NO_SUPERVISADA, graficos_fn,
                     diagnostico=tabla_reglas,
                     tablas_diagnostico={
                         "reglas_completas.csv": tabla_reglas_completas,
                     })
