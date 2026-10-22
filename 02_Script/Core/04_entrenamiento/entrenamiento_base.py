#
# Archivo: entrenamiento_base.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Flujo comun de un entrenamiento supervisado, reutilizado por las tareas de
# cada paradigma (01_Supervisado/Clasificacion.py, 01_Supervisado/Regresion.py,
# y las tareas equivalentes de semi-supervisado, etc.).
#
# Se encarga de: exigir un perfil de hardware, cargar el dataset, codificar el
# objetivo si es clasificacion, evaluar (Core.evaluacion), generar los graficos
# (Core.visualizacion) y guardar modelo.joblib + resumen.json + graficos/ + fila
# en el leaderboard bajo 03_Resultados/Models.
#
# La carpeta del modelo (.../<objetivo>/<modelo>/) se borra y se rehace en cada
# entrenamiento: no se acumulan corridas. Si el entrenamiento FALLA, en cambio,
# la carpeta NO se borra: queda con el entrenamiento.log parcial y el traceback
# completo, para poder diagnosticar que paso (antes se perdia todo salvo el
# mensaje de la excepcion).
#
from __future__ import annotations

import platform
import time
import traceback
import warnings
from typing import Callable

import numpy as np
from sklearn.preprocessing import LabelEncoder

from .. import submodulo

config = submodulo("00_fundamentos.config")
dataset_en_memoria = submodulo("03_datasets.dataset_en_memoria")
evaluacion = submodulo("01_catalogos.evaluacion")
modelos_supervisados = submodulo("01_catalogos.modelos_supervisados")
perfiles = submodulo("00_fundamentos.perfiles")
registro = submodulo("00_fundamentos.registro")
resultados = submodulo("00_fundamentos.resultados")
rutas = submodulo("00_fundamentos.rutas")
visualizacion = submodulo("02_etl.visualizacion_supervisado")

# XGBoost en GPU avisa una vez que los datos de prediccion estan en CPU; es solo
# una nota de rendimiento, el entrenamiento corre igual en la GPU.
warnings.filterwarnings("ignore", message=".*mismatched devices.*")
# En la validacion cruzada no estratificada (clases raras) sklearn avisa que un
# fold no vio todas las clases; ya es el comportamiento buscado.
warnings.filterwarnings("ignore", message=".*Number of classes in training fold.*")


# "1m 23.4s" o "45.2s" -- para que el log sea legible sin hacer la cuenta.
def _formatear_duracion(segundos: float) -> str:
    minutos, resto = divmod(segundos, 60)
    return f"{int(minutos)}m {resto:.1f}s" if minutos else f"{resto:.1f}s"


# Entrena un estimador supervisado y guarda sus artefactos.
#     fabrica: callable sin argumentos que devuelve el estimador sin entrenar.
#     es_clasificacion: True -> se codifica el objetivo y se usan metricas de clase.
#     params: hiperparametros opcionales para set_params.
# Devuelve el diccionario-resumen (tambien escrito como resumen.json).
def entrenar_supervisado(paradigma: str, tarea: str, objetivo: str, nombre_modelo: str,
                         fabrica: Callable[[], object], es_clasificacion: bool,
                         params: dict | None = None) -> dict:
    log = registro.obtener()
    perfil = perfiles.requerido()

    ds = dataset_en_memoria.cargar(paradigma, tarea, objetivo)

    marca = resultados.marca_tiempo()
    carpeta = resultados.preparar_carpeta(
        rutas.carpeta_resultados(paradigma, tarea, objetivo, nombre_modelo))
    handler = registro.agregar_archivo(carpeta / "entrenamiento.log")
    t_inicio = time.perf_counter()
    try:
        log.info("=== %s | %s | %s | %s ===", paradigma, tarea, objetivo, nombre_modelo)
        log.info("Perfil: %s", perfil.nombre)
        log.info("Dataset %s: %d filas x %d features", ds.nombre, ds.n_filas, ds.n_features)

        X = ds.X.to_numpy(dtype=float)
        if es_clasificacion:
            codificador = LabelEncoder()
            y = codificador.fit_transform(ds.y.astype(str))
            clases = [str(c) for c in codificador.classes_]
            log.info("Clasificacion: %d clases", len(clases))
        else:
            y = ds.y.to_numpy(dtype=float)
            clases = None
            log.info("Regresion: objetivo en [%.4g, %.4g]", float(y.min()), float(y.max()))

        if (nombre_modelo in modelos_supervisados.MODELOS_LENTOS
                and len(X) > config.LIMITE_FILAS_MODELOS_LENTOS):
            rng = np.random.default_rng(config.SEMILLA)
            indices = rng.choice(len(X), config.LIMITE_FILAS_MODELOS_LENTOS, replace=False)
            X, y = X[indices], y[indices]
            log.warning("'%s' escala mal con muchas filas (distancia par a par o, en "
                        "GradientBoosting, boosting secuencial sin GPU): se entrena sobre "
                        "una submuestra al azar de %d de las %d filas del dataset.",
                        nombre_modelo, len(X), ds.n_filas)

        base = fabrica()
        if params:
            base.set_params(**params)

        dispositivo = perfiles.dispositivo_de(base)
        log.info("Entrenando '%s' en %s...", nombre_modelo, dispositivo)
        t_entrenamiento = time.perf_counter()
        ev = evaluacion.evaluar(base, X, y, es_clasificacion, log)
        duracion_entrenamiento = time.perf_counter() - t_entrenamiento
        log.info("Validacion: %s", ev.validacion)
        for nombre, valor in ev.metricas.items():
            log.info("  %-18s %.4f", nombre, valor)
        log.info("Tiempo de entrenamiento ('%s'): %s", nombre_modelo,
                 _formatear_duracion(duracion_entrenamiento))

        ruta_modelo = resultados.guardar_modelo(ev.estimador, carpeta)

        contexto = visualizacion.Contexto(
            modelo=nombre_modelo, paradigma=paradigma, tarea=tarea, objetivo=objetivo,
            es_clasificacion=es_clasificacion, estimador=ev.estimador,
            X=X, y=y, nombres_features=list(ds.X.columns), clases=clases, evaluacion=ev)
        try:
            graficos = visualizacion.generar(carpeta, contexto, log)
            log.info("Graficos: %d en %s", len(graficos), carpeta / "graficos")
        except Exception as exc:
            log.error("No se pudieron generar los graficos: %s", exc)
            graficos = []

        resumen = {
            "paradigma": paradigma,
            "tarea": tarea,
            "objetivo": objetivo,
            "modelo": nombre_modelo,
            "params": params or {},
            "dataset": ds.nombre,
            "n_filas": len(X),
            "n_filas_dataset": ds.n_filas,
            "n_features": ds.n_features,
            "clases": clases,
            "marca_tiempo": marca,
            "perfil": perfil.nombre,
            "dispositivo": dispositivo,
            "validacion": ev.validacion,
            "metricas": ev.metricas,
            "graficos": sorted(p.name for p in graficos),
            "duracion_entrenamiento_seg": round(duracion_entrenamiento, 2),
            "duracion_total_seg": round(time.perf_counter() - t_inicio, 2),
            "entorno": {"python": platform.python_version()},
        }
        resultados.guardar_json(resumen, carpeta / "resumen.json")

        resultados.actualizar_leaderboard(
            rutas.carpeta_objetivo_resultados(paradigma, tarea, objetivo),
            resultados.fila_leaderboard(resumen))

        log.info("Modelo guardado: %s", ruta_modelo)
        log.info("Tiempo total ('%s'): %s", nombre_modelo,
                 _formatear_duracion(resumen["duracion_total_seg"]))
        return resumen
    except Exception:
        log.error("Fallo entrenando '%s' (%s/%s/%s):\n%s",
                  nombre_modelo, paradigma, tarea, objetivo, traceback.format_exc())
        raise
    finally:
        registro.quitar_archivo(handler)


# Entrena una lista de modelos con la funcion `entrenar_uno(paradigma, tarea, objetivo, nombre)`.
# Un modelo que falla no aborta a los demas: se registra el error y se sigue.
def entrenar_varios(paradigma: str, tarea: str, objetivo: str, nombres: list[str],
                    entrenar_uno: Callable[[str, str, str, str], dict]) -> list[dict]:
    log = registro.obtener()
    resumenes: list[dict] = []
    for nombre in nombres:
        try:
            resumenes.append(entrenar_uno(paradigma, tarea, objetivo, nombre))
        except Exception as exc:
            log.error("Modelo '%s' fallo: %s", nombre, exc)
    return resumenes
