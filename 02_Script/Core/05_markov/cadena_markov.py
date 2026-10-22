#
# Archivo: cadena_markov.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Cadena de Markov de orden 1 sobre el orden de elucion cromatografica: en
# cada muestra, los metabolitos identificados salen ordenados por
# TIEMPO_RETENCION_MINUTOS (el orden real en el que salen de la columna), cada
# uno representado por su clase quimica (el "estado"). La cadena aprende
# P(clase siguiente | clase actual): que clase quimica tiende a eluir justo
# despues de cual otra.
#
# No es un estimador de scikit-learn (no hay fit/predict generico para esto),
# asi que tiene su propio entrenar() en vez de pasar por
# Core.evaluacion_no_supervisada / Core.modelos_no_supervisados -- pero
# reutiliza Core.no_supervisado.cargar()/finalizar() para guardar los
# artefactos igual que el resto de 02_No_supervisado.
#
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .. import submodulo

config = submodulo("00_fundamentos.config")
registro = submodulo("00_fundamentos.registro")


@dataclass
class CadenaMarkov:
    estados: list[str]              # nombre de cada estado (ID_CLASE_QUIMICA), orden fijo
    matriz_transicion: np.ndarray   # [n_estados, n_estados]; fila i = P(siguiente | estado i)


def _indice(estados: list[str]) -> dict[str, int]:
    return {e: i for i, e in enumerate(estados)}


# Suavizado aditivo: sin esto, una transicion no vista en entrenamiento tendria
# probabilidad cero y arruinaria la log-verosimilitud del conjunto de prueba.
def ajustar(secuencias: list[list[str]], estados_conocidos: list[str] | None = None,
            suavizado: float = 0.1) -> CadenaMarkov:
    if suavizado <= 0:
        raise ValueError("El suavizado de Markov debe ser positivo.")
    estados = sorted(set(estados_conocidos or ()) |
                     {e for seq in secuencias for e in seq})
    if not estados:
        raise ValueError("No hay estados químicos para entrenar la cadena de Markov.")
    idx = _indice(estados)
    n = len(estados)
    conteo = np.full((n, n), suavizado)
    for seq in secuencias:
        for a, b in zip(seq, seq[1:]):
            conteo[idx[a], idx[b]] += 1
    matriz = conteo / conteo.sum(axis=1, keepdims=True)
    return CadenaMarkov(estados=estados, matriz_transicion=matriz)


# precision_siguiente_estado: de cada transicion real del conjunto de prueba,
# que fraccion de las veces el estado mas probable segun la cadena (arg max de
# la fila) coincidio con el que realmente vino despues -- un "accuracy" para
# cadenas de Markov. log_verosimilitud_media: promedio de log P(estado real
# | estado anterior); mas cerca de 0 (menos negativo) es mejor, y es sensible
# a que tan mal calibradas estan las probabilidades, no solo al top-1.
def _distribucion_orden_cero(
        secuencias: list[list[str]], estados: list[str], suavizado: float = 0.1
        ) -> np.ndarray:
    conteos = np.full(len(estados), suavizado, dtype=float)
    indice = _indice(estados)
    for secuencia in secuencias:
        for estado in secuencia[1:]:
            if estado in indice:
                conteos[indice[estado]] += 1
    return conteos / conteos.sum()


def evaluar(cadena: CadenaMarkov, secuencias: list[list[str]],
            distribucion_orden_cero: np.ndarray | None = None) -> dict:
    idx = _indice(cadena.estados)
    aciertos = total = transiciones_conocidas = siguiente_conocido = 0
    log_verosimilitud = 0.0
    aciertos_orden_cero = 0
    log_verosimilitud_orden_cero = 0.0
    fuera_vocabulario = 0
    for seq in secuencias:
        for a, b in zip(seq, seq[1:]):
            total += 1
            if b in idx:
                siguiente_conocido += 1
                if distribucion_orden_cero is not None:
                    posicion_siguiente = idx[b]
                    mas_frecuente = int(np.argmax(distribucion_orden_cero))
                    aciertos_orden_cero += int(posicion_siguiente == mas_frecuente)
                    log_verosimilitud_orden_cero += float(
                        np.log(distribucion_orden_cero[posicion_siguiente]))
            if a not in idx or b not in idx:
                fuera_vocabulario += 1
                continue
            fila = cadena.matriz_transicion[idx[a]]
            if cadena.estados[int(np.argmax(fila))] == b:
                aciertos += 1
            log_verosimilitud += float(np.log(fila[idx[b]]))
            transiciones_conocidas += 1
    resultado = {
        "precision_siguiente_estado": aciertos / total if total else 0.0,
        "log_verosimilitud_media": (
            log_verosimilitud / transiciones_conocidas if transiciones_conocidas else 0.0),
        "n_transiciones_evaluadas": total,
        "n_transiciones_en_vocabulario": transiciones_conocidas,
        "n_siguiente_estado_en_vocabulario": siguiente_conocido,
        "n_estados": len(cadena.estados),
        "transiciones_fuera_vocabulario": fuera_vocabulario,
        "cobertura_vocabulario_pct": (
            100 * transiciones_conocidas / total if total else 0.0),
    }
    if cadena.estados:
        resultado["precision_azar_uniforme"] = 1 / len(cadena.estados)
    if distribucion_orden_cero is not None and total:
        resultado["precision_baseline_orden_cero"] = aciertos_orden_cero / total
        resultado["log_verosimilitud_baseline_orden_cero"] = (
            log_verosimilitud_orden_cero / siguiente_conocido
            if siguiente_conocido else 0.0)
        resultado["mejora_precision_vs_orden_cero_pp"] = 100 * (
            resultado["precision_siguiente_estado"]
            - resultado["precision_baseline_orden_cero"])
    return resultado


# Reagrupa eventos por corrida (no mezcla modos de ionizacion) y utiliza las
# etiquetas legibles de clase guardadas como referencias en el dataset.
def _secuencias_por_corrida(ds) -> dict[str, list[str]]:
    columna_secuencia = (
        "REF_SECUENCIA" if "REF_SECUENCIA" in ds.referencias
        else "REF_MUESTRA"
    )
    muestras = ds.referencias[columna_secuencia].astype(str).to_numpy()
    estados = (
        ds.referencias["REF_ESTADO"].astype(str).to_numpy()
        if "REF_ESTADO" in ds.referencias
        else ds.X.iloc[:, 0].astype(int).astype(str).to_numpy()
    )
    if len(muestras) != len(estados):
        raise ValueError("Las referencias de secuencia y sus estados no coinciden.")
    secuencias: dict[str, list[str]] = {}
    for muestra, estado in zip(muestras, estados):
        secuencias.setdefault(muestra, []).append(estado)
    return secuencias


# Entrena y guarda: holdout por batch cuando hay lotes suficientes (no por
# transición individual ni por muestra aleatoria, para medir transferencia).
def entrenar(paradigma: str, tarea: str, objetivo: str, modelo: str) -> dict:
    from .. import submodulo
    no_supervisado = submodulo("04_entrenamiento.no_supervisado")
    visualizacion = submodulo("02_etl.visualizacion_no_supervisado")

    log = registro.obtener()
    ds = no_supervisado.cargar(paradigma, tarea, objetivo)
    por_corrida = _secuencias_por_corrida(ds)

    ids = list(por_corrida)
    if len(ids) < 2:
        raise ValueError(
            "Cadenas de Markov requiere al menos dos corridas independientes "
            "para separar entrenamiento y prueba sin fuga de datos.")
    rng = np.random.default_rng(config.SEMILLA)
    columna_secuencia = (
        "REF_SECUENCIA" if "REF_SECUENCIA" in ds.referencias
        else "REF_MUESTRA"
    )
    faltantes = {columna_secuencia, "REF_BATCH"} - set(ds.referencias.columns)
    if faltantes:
        raise ValueError(
            "La validación por batch de Markov requiere las referencias: "
            + ", ".join(sorted(faltantes)))
    referencias = ds.referencias[[columna_secuencia, "REF_BATCH"]].drop_duplicates()
    batch_por_corrida = dict(zip(
        referencias[columna_secuencia].astype(str),
        referencias["REF_BATCH"].fillna("").astype(str),
    ))
    batches = sorted(set(batch_por_corrida.values()) - {""})
    if len(batches) >= 2:
        rng.shuffle(batches)
        corte_batches = min(len(batches) - 1, max(1, int(len(batches) * 0.75)))
        batches_train, batches_test = set(batches[:corte_batches]), set(batches[corte_batches:])
        train_ids = [corrida for corrida in ids
                     if batch_por_corrida.get(corrida) in batches_train]
        test_ids = [corrida for corrida in ids
                    if batch_por_corrida.get(corrida) in batches_test]
        validacion = (
            f"holdout 75/25 por batch ({len(batches_train)}/{len(batches_test)} batches; "
            f"{len(train_ids)}/{len(test_ids)} corridas)")
    else:
        rng.shuffle(ids)
        corte = min(len(ids) - 1, max(1, int(len(ids) * 0.75)))
        train_ids, test_ids = ids[:corte], ids[corte:]
        validacion = (
            f"holdout 75/25 por corrida ({len(train_ids)}/{len(test_ids)}); "
            "batches insuficientes")

    secuencias_train = [por_corrida[i] for i in train_ids]
    cadena = ajustar(secuencias_train)
    baseline = _distribucion_orden_cero(secuencias_train, cadena.estados)
    metricas = evaluar(
        cadena, [por_corrida[i] for i in test_ids], baseline)
    metricas.update({
        "n_secuencias": len(por_corrida),
        "n_muestras_unicas": int(ds.referencias["REF_MUESTRA"].nunique()),
        "n_modos_ionizacion": int(
            ds.referencias["REF_MODO_IONIZACION"].nunique(dropna=True)),
        "n_batches": len(batches),
    })
    log.info("Validación por grupos: %s", validacion)

    def graficos_fn(destino):
        ctx = visualizacion.ContextoNS(
            modelo=modelo, paradigma=paradigma, tarea=tarea, metricas=metricas,
            nombres_features=["ID_CLASE_QUIMICA"], n_filas=ds.n_filas,
            estados=cadena.estados, matriz_transicion=cadena.matriz_transicion)
        return visualizacion.generar_no_supervisado("Cadenas de Markov", destino, ctx, log)

    return no_supervisado.finalizar(paradigma, tarea, objetivo, modelo, cadena, ds, metricas,
                                    validacion, graficos_fn)
