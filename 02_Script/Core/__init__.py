#
# Paquete: Core
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Codigo general compartido por el resto del pipeline, agrupado en subcarpetas
# por fase (orden de dependencia, no de ejecucion estricta -- ver mas abajo):
#
#     00_fundamentos      config, rutas, registro, resultados, perfiles,
#                         dependencias --
#                         sin dependencias entre si.
#     01_catalogos        datos, hardware, benchmark, torch_modelos,
#                         modelos_no_supervisados, reglas_asociacion,
#                         modelos_supervisados, evaluacion, reporte_global,
#                         interpretacion_graficos -- dependen solo de 00_fundamentos
#                         (y entre si: modelos_supervisados usa torch_modelos).
#     02_etl              construir_dataset, evaluacion_no_supervisada,
#                         visualizacion_estilo (estilo matplotlib + helpers
#                         compartidos), visualizacion_supervisado,
#                         visualizacion_no_supervisado -- ETL de Supervisado y
#                         graficos/metricas de No supervisado.
#     03_datasets         construir_dataset_no_supervisado, dataset_en_memoria --
#                         ETL de No supervisado y el punto unico de entrada al
#                         Dataset de cualquier paradigma/tarea/objetivo.
#     04_entrenamiento    entrenamiento_base, no_supervisado, ejecutor -- flujo
#                         comun de un entrenamiento y el paralelizador GPU/CPU.
#     05_markov           cadena_markov -- aparte porque no es un estimador
#                         fit/predict de scikit-learn.
#
# Las subcarpetas empiezan con un digito (para que se lean en orden en el
# explorador de archivos), asi que NO son importables con una sentencia
# `import`/`from` literal (`from .00_fundamentos import x` es un error de
# sintaxis: un segmento despues de un punto tiene que ser un identificador
# valido). Por eso toda referencia CRUZADA entre carpetas usa el helper
# submodulo() de aca abajo, que llama a importlib.import_module con la ruta
# como texto. Dentro de una misma carpeta, en cambio, `from . import x` sigue
# funcionando normal (el "." se resuelve por la ubicacion real del archivo en
# tiempo de ejecucion, no por texto literal) -- mismo mecanismo que ya usaba
# Entrenamiento/__init__.py para cargar Entrenamiento/01_Supervisado/.
#
from __future__ import annotations

import importlib


def submodulo(ruta: str):
    return importlib.import_module(f"Core.{ruta}")
