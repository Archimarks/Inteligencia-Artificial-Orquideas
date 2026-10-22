#
# Archivo: config.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Constantes de entrenamiento compartidas. Un solo lugar para tocar la semilla,
# la proporcion de la particion de prueba y el numero de folds.
#
from __future__ import annotations

# Semilla global para todo lo que tenga aleatoriedad (particiones, modelos, CV).
SEMILLA: int = 42

# Proporcion de filas reservadas para la particion de prueba (holdout).
PROPORCION_PRUEBA: float = 0.25

# Minimo de filas para permitir una particion holdout en vez de validacion cruzada.
MIN_FILAS_HOLDOUT: int = 40

# En clasificacion, minimo de ejemplares por clase para poder estratificar el holdout.
MIN_EJEMPLARES_CLASE_HOLDOUT: int = 4

# Tope de folds para la validacion cruzada.
MAX_FOLDS: int = 5

# Minimo de filas para hacer validacion cruzada (por debajo: metricas de entrenamiento).
MIN_FILAS_CV: int = 10

# Valor con el que se rellenan features numericas ausentes.
RELLENO_FEATURES: float = 0.0

# Por encima de esta cantidad de filas, los modelos de
# Core.modelos_supervisados.MODELOS_LENTOS (svm/svr, knn, el GradientBoosting de
# scikit-learn) se entrenan sobre una submuestra al azar en vez del dataset
# completo. Sin esto, KNN por ejemplo compara CADA fila de prueba contra CADA
# fila de entrenamiento (distancia par a par): con ~2.5 millones de filas son
# del orden de 1e13-1e14 operaciones, horas o dias en un CPU sin GPU. El resto
# del catalogo (arboles, boosting, lineales) escala bien y no se toca.
LIMITE_FILAS_MODELOS_LENTOS: int = 100_000

# Tope para algoritmos no supervisados con coste o memoria cuadráticos en
# cantidad de muestras (p. ej. DBSCAN, Agglomerative, LOF y KernelPCA).
MAX_FILAS_MODELOS_NO_SUPERVISADOS: int = 5_000

# --- Graficos ---
# Resolucion (dpi) de los PNG generados por Core.visualizacion.
GRAFICOS_DPI: int = 160

# Cantidad de features a mostrar en el grafico de importancia.
TOP_FEATURES_GRAFICO: int = 20

# Maximo de clases para anotar celda a celda la matriz de confusion.
MAX_CLASES_ANOTAR: int = 20

# Con mas clases que esto no se calculan probabilidades para la curva ROC
# (una ROC de decenas de clases no se lee y duplica el coste de la validacion).
MAX_CLASES_ROC: int = 25

# Maximo de filas usadas para la importancia por permutacion (acota el tiempo).
MAX_FILAS_PERMUTACION: int = 300

# Con mas clases que esto, la matriz de confusion se arma solo con las N clases
# de mas soporte + una fila/columna "Otras" -- por encima de esto una matriz
# k x k completa (Clasificacion/METABOLITO tiene 32000+ clases) no entra en
# memoria y tampoco se puede leer.
MAX_CLASES_MATRIZ_CONFUSION: int = 60

# Filas usadas para la curva de aprendizaje (se sub-muestrea igual que en la
# importancia por permutacion: es un diagnostico, no hace falta el dataset
# entero, y algunos modelos del catalogo -- svm, knn -- son lentos).
MAX_FILAS_CURVA_APRENDIZAJE: int = 6000
# Proporciones del conjunto de entrenamiento que se prueban en la curva.
PUNTOS_CURVA_APRENDIZAJE: tuple[float, ...] = (0.2, 0.4, 0.6, 0.8, 1.0)

# Cantidad de features mostradas en la grilla de distribucion de columnas
# (histograma + densidad): las de mayor varianza, las mas informativas de ver
# -- datasets con cientos/miles de columnas (p.ej. el perfil quimico, 337
# clases) no entrarian enteros en una sola grilla legible.
MAX_FEATURES_DISTRIBUCION: int = 12

# Filas usadas para el histograma/densidad de distribucion de columnas: es un
# diagnostico (no hace falta el dataset entero) y la densidad (KDE) es O(n) por
# punto evaluado -- con millones de filas se vuelve lenta sin aportar mas
# informacion visual que con una muestra.
MAX_FILAS_DISTRIBUCION_FEATURES: int = 20_000

# Filas usadas para trustworthiness (Reduccion de dimensionalidad): es O(n^2).
MAX_FILAS_TRUSTWORTHINESS: int = 6000

# Muestreo determinista para métricas de clustering costosas (silhouette).
MAX_FILAS_SILHOUETTE: int = 3000
# Repeticiones para medir la estabilidad de clustering ante submuestreo.
REPETICIONES_ESTABILIDAD_CLUSTERING: int = 20
# En perfiles por especie, no aceptar soluciones dominadas por grupos de una o
# dos plantas: minimo 5% de las especies, con suelo de 2.
FRACCION_MINIMA_CLUSTER: float = 0.05
TAMANO_MINIMO_CLUSTER: int = 2
# Umbrales de cobertura química para el análisis de sensibilidad de clustering.
UMBRALES_COBERTURA_CLUSTERING: tuple[float, ...] = (10.0, 30.0, 50.0)

# --- Reglas de asociacion (Core.reglas_asociacion) ---
# Un itemset (clase quimica o combinacion) necesita aparecer en al menos esta
# fraccion de las muestras para seguir en la busqueda (poda de Apriori).
REGLAS_MIN_SOPORTE: float = 0.15
# De las reglas con soporte suficiente, solo se quedan las que aciertan al
# menos esta fraccion de las veces que aparece el antecedente.
REGLAS_MIN_CONFIANZA: float = 0.70
# Una clase se considera recurrente en una especie si aparece en al menos esta
# fraccion de sus muestras biologicas clasificadas (modos instrumentales de
# una misma muestra no cuentan como replicas independientes).
REGLAS_MIN_PREVALENCIA_MUESTRAS: float = 0.50
# Cobertura del vocabulario de estados esperada para interpretar transferencia
# de una cadena de Markov a batches no vistos.
MARKOV_COBERTURA_MINIMA_ALERTA_PCT: float = 50.0
# Itemsets de a lo sumo esta cantidad de clases quimicas (antecedente + consecuente).
REGLAS_TAMANO_MAX_ITEMSET: int = 3
# Máximo de reglas guardadas en el diagnóstico legible (el modelo conserva todas).
REGLAS_MAX_DIAGNOSTICO: int = 200

# --- Prueba de rendimiento del equipo (Core.benchmark) ---
# Tiempo maximo por multiplicacion de matrices en CPU para dar el OK.
BENCH_CPU_MAX_SEG: float = 3.0

# Tamano del bloque para la prueba de ancho de banda de RAM.
BENCH_RAM_MB: int = 512

# Ancho de banda minimo de RAM (GB/s) para dar el OK.
BENCH_RAM_MIN_GBS: float = 1.0
