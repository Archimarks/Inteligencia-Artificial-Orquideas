#
# Archivo: evaluacion_no_supervisada.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Metricas de las 3 tareas de 02_No_supervisado que son un estimador
# fit/predict (Clustering, Reduccion de dimensionalidad, Deteccion de
# anomalias). No hay Y: cada tarea tiene su propia nocion de "que tan bien
# salio", sin holdout ni validacion cruzada -- se mide sobre todos los datos.
#
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.base import clone
from sklearn.manifold import trustworthiness
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
    silhouette_samples,
)
from sklearn.neighbors import NearestNeighbors

from .. import submodulo

config = submodulo("00_fundamentos.config")
catalogo = submodulo("01_catalogos.modelos_no_supervisados")


@dataclass
class ResultadoClustering:
    estimador: Any
    etiquetas: np.ndarray
    metricas: dict
    k_elegido: int | None


# Calcula silhouette de forma reproducible, limitando el coste para datasets
# grandes y evitando resultados indefinidos si la muestra no contiene grupos.
def _silhouette(X: np.ndarray, etiquetas: np.ndarray) -> float | None:
    if len(X) < 3:
        return None
    n_grupos = len(np.unique(etiquetas))
    if n_grupos < 2 or n_grupos >= len(X):
        return None
    tamano = min(len(X), config.MAX_FILAS_SILHOUETTE)
    try:
        return float(silhouette_score(
            X, etiquetas, sample_size=tamano if tamano < len(X) else None,
            random_state=config.SEMILLA))
    except ValueError:
        return None


def _elegir_k(nombre: str, X: np.ndarray, k_max: int = 15) -> tuple[int, float, dict]:
    minimo_cluster = min(
        max(
            config.TAMANO_MINIMO_CLUSTER,
            int(np.ceil(config.FRACCION_MINIMA_CLUSTER * len(X))),
        ),
        max(1, len(X) // 2),
    )
    candidatos = []
    tamano_muestra = min(len(X), config.MAX_FILAS_SILHOUETTE)
    indices_muestra = (
        np.arange(len(X)) if tamano_muestra == len(X)
        else np.sort(np.random.default_rng(config.SEMILLA).choice(
            len(X), size=tamano_muestra, replace=False))
    )
    tope = min(k_max, len(X) - 1)
    for k in range(2, tope + 1):
        etiquetas = catalogo.CLUSTERING[nombre](k).fit_predict(X)
        tamanos = np.unique(etiquetas, return_counts=True)[1]
        if len(tamanos) < 2 or int(tamanos.min()) < minimo_cluster:
            continue
        X_muestra = X[indices_muestra]
        etiquetas_muestra = etiquetas[indices_muestra]
        if len(np.unique(etiquetas_muestra)) < 2:
            continue
        try:
            valores = silhouette_samples(X_muestra, etiquetas_muestra)
        except ValueError:
            continue
        puntaje = float(np.mean(valores))
        error_estandar = float(
            np.std(valores, ddof=1) / np.sqrt(len(valores)))
        if puntaje is not None:
            candidatos.append((k, puntaje, error_estandar, int(tamanos.min())))
    if not candidatos:
        raise ValueError(
            f"{nombre}: no se encontró una partición evaluable con al menos "
            f"{minimo_cluster} plantas por grupo. Revise la variación de los perfiles "
            "o elija otro algoritmo.")
    mejor = max(candidatos, key=lambda candidato: candidato[1])
    limite_un_error = mejor[1] - mejor[2]
    seleccionado = min(
        (candidato for candidato in candidatos if candidato[1] >= limite_un_error),
        key=lambda candidato: candidato[0],
    )
    k, puntaje, _, tamanio_minimo = seleccionado
    diagnostico = {
        "k_seleccion_criterio": (
            "menor k dentro de un error estandar aproximado del mejor silhouette"),
        "k_mejor_silhouette": mejor[0],
        "k_candidatos_evaluados": len(candidatos),
        "cluster_minimo_requerido": minimo_cluster,
        "cluster_minimo_observado": tamanio_minimo,
    }
    return k, puntaje, diagnostico


def _estabilidad_clustering(
        estimador, X: np.ndarray, etiquetas: np.ndarray,
        repeticiones: int = config.REPETICIONES_ESTABILIDAD_CLUSTERING,
        fraccion: float = 0.8) -> dict:
    if len(X) < 10:
        return {"estabilidad_ari_repeticiones": 0}
    rng = np.random.default_rng(config.SEMILLA)
    tamano = max(3, int(len(X) * fraccion))
    puntuaciones = []
    for _ in range(repeticiones):
        indices = np.sort(rng.choice(len(X), size=tamano, replace=False))
        repetido = clone(estimador)
        etiquetas_repetidas = repetido.fit_predict(X[indices])
        puntuaciones.append(float(adjusted_rand_score(
            etiquetas[indices], etiquetas_repetidas)))
    return {
        "estabilidad_ari_media": float(np.mean(puntuaciones)),
        "estabilidad_ari_desviacion": float(np.std(puntuaciones)),
        "estabilidad_ari_minima": float(np.min(puntuaciones)),
        "estabilidad_ari_repeticiones": len(puntuaciones),
        "estabilidad_porcentaje_muestras": round(100 * fraccion, 1),
    }


def _ajustar_dbscan(X: np.ndarray, log):
    mejor = None
    mejor_puntaje = -np.inf
    configuraciones_probadas = 0
    candidatos_con_dos_grupos = 0
    mejor_candidato = None
    for min_samples in (5, 10, 15):
        if len(X) <= min_samples:
            continue
        distancias = NearestNeighbors(n_neighbors=min_samples).fit(X).kneighbors()[0]
        epsilons = np.unique(np.quantile(distancias[:, -1], (0.65, 0.75, 0.85, 0.95)))
        for eps in epsilons:
            if eps <= 0:
                continue
            configuraciones_probadas += 1
            estimador = catalogo.CLUSTERING["dbscan"]()
            estimador.set_params(eps=float(eps), min_samples=min_samples)
            etiquetas = estimador.fit_predict(X)
            valida = etiquetas != -1
            grupos = np.unique(etiquetas[valida])
            if len(grupos) < 2 or valida.sum() <= len(grupos):
                continue
            candidatos_con_dos_grupos += 1
            puntaje_s = _silhouette(X[valida], etiquetas[valida])
            if mejor_candidato is None or len(grupos) > mejor_candidato["grupos"]:
                mejor_candidato = {
                    "grupos": len(grupos),
                    "cobertura_pct": 100 * float(valida.mean()),
                    "epsilon": float(eps),
                    "min_samples": min_samples,
                    "silhouette": puntaje_s,
                }
            if puntaje_s is None:
                continue
            cobertura = float(valida.mean())
            puntaje = puntaje_s * cobertura
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor = estimador, etiquetas, float(eps), min_samples, puntaje_s, cobertura

    if mejor is None:
        detalle = (
            f"Se probaron {configuraciones_probadas} configuraciones "
            f"(min_samples=5, 10, 15; epsilon entre los percentiles 65 y 95). "
        )
        if candidatos_con_dos_grupos:
            detalle += (
                f"{candidatos_con_dos_grupos} formaron al menos dos grupos, pero no "
                "permitieron calcular silhouette con soporte suficiente."
            )
        else:
            detalle += (
                "Ninguna formó dos grupos con soporte suficiente; con estos perfiles "
                "no se detectó una estructura de densidad adecuada para DBSCAN."
            )
        if mejor_candidato is not None:
            silhouette = mejor_candidato["silhouette"]
            valor_silhouette = (
                f"{silhouette:.4f}" if silhouette is not None
                else "no calculable")
            detalle += (
                f" El candidato con más grupos obtuvo {mejor_candidato['grupos']} grupos, "
                f"{mejor_candidato['cobertura_pct']:.1f}% de cobertura, "
                f"epsilon={mejor_candidato['epsilon']:.5g}, "
                f"min_samples={mejor_candidato['min_samples']} y "
                f"silhouette={valor_silhouette}."
            )
        raise ValueError(
            "DBSCAN no produjo un agrupamiento evaluable. "
            f"{detalle} Use KMeans o Agglomerative como comparación; si DBSCAN es "
            "necesario, revise la cobertura química, la dimensionalidad y una métrica "
            "de distancia/escala apropiada antes de cambiar epsilon.")
    estimador, etiquetas, eps, min_samples, puntaje_s, cobertura = mejor
    log.info(
        "DBSCAN ajustado: eps=%.5g, min_samples=%d, silhouette=%.4f, cobertura=%.1f%%",
        eps, min_samples, puntaje_s, 100 * cobertura)
    return estimador, etiquetas, eps


def evaluar_clustering(nombre: str, X: np.ndarray, log) -> ResultadoClustering:
    if X.ndim != 2 or len(X) < 3 or X.shape[1] == 0:
        raise ValueError("Clustering requiere al menos 3 muestras y una feature.")
    k_elegido = None
    parametros = {}
    if nombre == "dbscan":
        estimador, etiquetas, eps = _ajustar_dbscan(X, log)
        parametros = {"dbscan_eps": eps, "dbscan_min_samples": estimador.min_samples}
    elif nombre in catalogo.CLUSTERING_CON_K:
        k_elegido, puntaje_k, diagnostico_k = _elegir_k(nombre, X)
        log.info("k elegido por silhouette muestreado: %d (%.4f)", k_elegido, puntaje_k)
        estimador = catalogo.CLUSTERING[nombre](k_elegido)
        etiquetas = estimador.fit_predict(X)
        parametros.update(diagnostico_k)
        parametros["k_silhouette_seleccionado"] = puntaje_k
    else:
        estimador = catalogo.CLUSTERING[nombre]()
        etiquetas = estimador.fit_predict(X)
    grupos = set(etiquetas) - {-1}  # -1 = ruido (DBSCAN)
    metricas: dict = {
        "n_clusters": len(grupos),
        "estabilidad_semilla": config.SEMILLA,
        **parametros,
    }
    ruido = int((etiquetas == -1).sum())
    metricas["ruido_pct"] = round(100 * ruido / len(etiquetas), 2)

    valida = etiquetas != -1
    if len(grupos) >= 2 and valida.sum() > len(grupos):
        puntaje = _silhouette(X[valida], etiquetas[valida])
        if puntaje is not None:
            metricas["silhouette"] = puntaje
        metricas["davies_bouldin"] = float(davies_bouldin_score(
            X[valida], etiquetas[valida]))
        metricas["calinski_harabasz"] = float(calinski_harabasz_score(
            X[valida], etiquetas[valida]))
        tamanos = np.unique(etiquetas[valida], return_counts=True)[1]
        metricas["tamano_cluster_min"] = int(tamanos.min())
        metricas["tamano_cluster_max"] = int(tamanos.max())
    else:
        log.warning("Un solo grupo (o ninguno): silhouette/davies_bouldin no aplican.")

    estabilidad = _estabilidad_clustering(estimador, X, etiquetas)
    metricas.update(estabilidad)
    if "estabilidad_ari_media" in estabilidad:
        log.info(
            "Estabilidad ARI en subconjuntos: media=%.4f, minima=%.4f (%d repeticiones)",
            estabilidad["estabilidad_ari_media"],
            estabilidad["estabilidad_ari_minima"],
            estabilidad["estabilidad_ari_repeticiones"],
        )

    return ResultadoClustering(estimador=estimador, etiquetas=etiquetas,
                               metricas=metricas, k_elegido=k_elegido)


@dataclass
class ResultadoReduccion:
    estimador: Any
    X_reducido: np.ndarray
    metricas: dict


# trustworthiness: de los vecinos mas cercanos en el espacio reducido, que
# fraccion tambien lo eran en el espacio original -- 1.0 = la reduccion no
# inventa vecindades falsas. Se acota la cantidad de filas: es O(n^2).
def evaluar_reduccion(nombre: str, X: np.ndarray, log) -> ResultadoReduccion:
    if X.ndim != 2 or len(X) < 3 or X.shape[1] == 0:
        raise ValueError("La reducción requiere al menos 3 muestras y una feature.")
    estimador = catalogo.REDUCCION[nombre]()
    if nombre == "tsne":
        estimador.set_params(n_components=2)
        estimador.set_params(perplexity=min(30.0, max(1.0, (len(X) - 1) / 3)))
    else:
        componentes = min(catalogo.N_COMPONENTES, X.shape[1], len(X) - 1)
        if hasattr(estimador, "n_components"):
            estimador.set_params(n_components=componentes)
    if nombre == "isomap":
        estimador.set_params(n_neighbors=min(5, len(X) - 1))
    X_red = estimador.fit_transform(X)

    Xt, Xr = X, X_red
    if len(X) > config.MAX_FILAS_TRUSTWORTHINESS:
        rng = np.random.default_rng(config.SEMILLA)
        indices = rng.choice(len(X), config.MAX_FILAS_TRUSTWORTHINESS, replace=False)
        Xt, Xr = X[indices], X_red[indices]
    n_vecinos = min(5, max(1, (len(Xt) - 1) // 2))
    metricas = {"trustworthiness": float(
        trustworthiness(Xt, Xr, n_neighbors=n_vecinos))}
    if hasattr(estimador, "explained_variance_ratio_"):
        metricas["varianza_explicada_acumulada"] = float(
            np.sum(estimador.explained_variance_ratio_))
    return ResultadoReduccion(estimador=estimador, X_reducido=X_red, metricas=metricas)


@dataclass
class ResultadoAnomalias:
    estimador: Any
    etiquetas: np.ndarray
    puntajes: np.ndarray
    metricas: dict


# Puntaje continuo de anomalia, mayor = mas normal (mismo signo para las 4
# librerias del catalogo, asi el grafico/metrica no tiene que saber cual es).
def _puntajes(estimador, X: np.ndarray) -> np.ndarray:
    if hasattr(estimador, "negative_outlier_factor_"):  # LocalOutlierFactor
        return np.asarray(estimador.negative_outlier_factor_, dtype=float)
    if hasattr(estimador, "score_samples"):
        return np.asarray(estimador.score_samples(X), dtype=float)
    return np.asarray(estimador.decision_function(X), dtype=float)


def evaluar_anomalias(nombre: str, X: np.ndarray, log) -> ResultadoAnomalias:
    estimador = catalogo.ANOMALIAS[nombre]()
    diagnostico_covarianza = None
    if nombre == "elliptic_envelope" and X.shape[1] >= X.shape[0]:
        diagnostico_covarianza = (
            f"Estimación de covarianza potencialmente singular: {X.shape[1]} features "
            f"para {X.shape[0]} plantas; interpretar las anomalías con cautela.")
        log.warning("%s", diagnostico_covarianza)
    etiquetas = estimador.fit_predict(X)  # 1 normal, -1 anomalia
    puntajes = _puntajes(estimador, X)

    normal, anomalo = puntajes[etiquetas == 1], puntajes[etiquetas == -1]
    metricas = {"anomalias_pct": round(100 * (etiquetas == -1).mean(), 2)}
    if diagnostico_covarianza:
        metricas["diagnostico_covarianza"] = diagnostico_covarianza
    if len(normal) and len(anomalo):
        # Cohen's d entre normal y anomalo: cuantos desvios estandar separan
        # los dos grupos en el puntaje. 0 = no se distinguen, cuanto mas alto mejor.
        desvio = float(np.std(puntajes)) or 1e-9
        metricas["separacion_puntaje"] = float((normal.mean() - anomalo.mean()) / desvio)
        sil = _silhouette(X, np.where(etiquetas == -1, 1, 0))
        if sil is not None:
            metricas["silhouette_anomalias"] = sil

    return ResultadoAnomalias(estimador=estimador, etiquetas=etiquetas,
                              puntajes=puntajes, metricas=metricas)
