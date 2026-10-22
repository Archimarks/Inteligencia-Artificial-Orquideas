#
# Archivo: modelos_no_supervisados.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Catalogo de estimadores para las 3 tareas de 02_No_supervisado que son un
# estimador fit/predict de scikit-learn: Clustering, Reduccion de
# dimensionalidad, Deteccion de anomalias. Reglas de asociacion no entra aca
# (no es un estimador, ver Core.reglas_asociacion).
#
# Los nombres de tarea son los internos sin tilde (iguales a la carpeta en
# disco, ver Core.rutas), no las claves con tilde de TAXONOMIA -- la traduccion
# la hace Entrenamiento/02_No_supervisado/__init__.py, igual que en Supervisado.
#
from __future__ import annotations

from typing import Callable

from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.covariance import EllipticEnvelope
from sklearn.decomposition import PCA, KernelPCA
from sklearn.ensemble import IsolationForest
from sklearn.manifold import TSNE, Isomap
from sklearn.mixture import GaussianMixture
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

from .. import submodulo

config = submodulo("00_fundamentos.config")

# Componentes de salida para los reductores que lo piden (TSNE va aparte a 2:
# es para visualizar, no tiene sentido pedirle 10 componentes).
N_COMPONENTES = 10

# Los que toman n_clusters/n_components: Core.no_supervisado busca el mejor
# valor por silhouette antes de entrenar la version final (no hay Y para
# elegirlo de otra forma). DBSCAN no entra: es por densidad, no por cantidad.
CLUSTERING_CON_K: frozenset[str] = frozenset({"kmeans", "agglomerative", "gaussian_mixture"})

CLUSTERING: dict[str, Callable[[int], object]] = {
    "kmeans": lambda k: KMeans(n_clusters=k, random_state=config.SEMILLA, n_init=20),
    "agglomerative": lambda k: AgglomerativeClustering(n_clusters=k),
    "gaussian_mixture": lambda k: GaussianMixture(
        n_components=k, covariance_type="diag", reg_covar=1e-5,
        n_init=3, random_state=config.SEMILLA),
    "dbscan": lambda k=None: DBSCAN(),
}

REDUCCION: dict[str, Callable[[], object]] = {
    "pca": lambda: PCA(n_components=N_COMPONENTES, random_state=config.SEMILLA),
    "kernel_pca": lambda: KernelPCA(n_components=N_COMPONENTES, random_state=config.SEMILLA),
    "isomap": lambda: Isomap(n_components=N_COMPONENTES),
    "tsne": lambda: TSNE(n_components=2, random_state=config.SEMILLA, init="pca",
                         perplexity=30.0),
}

ANOMALIAS: dict[str, Callable[[], object]] = {
    "isolation_forest": lambda: IsolationForest(
        n_estimators=300, contamination="auto", random_state=config.SEMILLA, n_jobs=-1),
    "local_outlier_factor": lambda: LocalOutlierFactor(n_neighbors=20, contamination="auto"),
    "one_class_svm": lambda: OneClassSVM(),
    "elliptic_envelope": lambda: EllipticEnvelope(random_state=config.SEMILLA),
}

_CATALOGOS: dict[str, dict] = {
    "Clustering": CLUSTERING,
    "Reduccion de dimensionalidad": REDUCCION,
    "Deteccion de anomalias": ANOMALIAS,
}


def modelos(tarea: str) -> list[str]:
    return list(_CATALOGOS.get(tarea, {}))


def fabrica(tarea: str, nombre: str):
    catalogo = _CATALOGOS.get(tarea)
    if catalogo is None or nombre not in catalogo:
        raise ValueError(f"Modelo desconocido para {tarea}: {nombre!r}. "
                         f"Opciones: {list(catalogo or {})}")
    return catalogo[nombre]
