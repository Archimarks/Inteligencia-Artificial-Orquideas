#
# Archivo: visualizacion_supervisado.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Graficos profesionales de cada entrenamiento SUPERVISADO (Clasificacion /
# Regresion), guardados como PNG en <carpeta_del_entrenamiento>/graficos/.
#
# Los graficos se eligen segun:
#     - el tipo de tarea (clasificacion vs regresion),
#     - el algoritmo (arboles/boosting -> importancia por ganancia; modelos
#       lineales -> magnitud del coeficiente; el resto -> importancia por
#       permutacion), y
#     - los datos disponibles de la validacion (conjunto holdout, predicciones
#       out-of-fold, o datos de entrenamiento).
#
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.base import clone

from .. import submodulo
from .visualizacion_estilo import (
    PALETA, _GRIS, _GRIS_CLARO, _TINTA, _distribucion_grid, _estimador_base,
    _guardar_figura, _recortar, plt,
)

config = submodulo("00_fundamentos.config")
Evaluacion = submodulo("01_catalogos.evaluacion").Evaluacion


# Todo lo que un grafico puede necesitar de un entrenamiento.
@dataclass
class Contexto:
    modelo: str
    paradigma: str
    tarea: str
    objetivo: str
    es_clasificacion: bool
    estimador: Any
    X: np.ndarray
    y: np.ndarray
    nombres_features: list[str]
    clases: list[str] | None
    evaluacion: Evaluacion


# Genera todos los graficos que apliquen y devuelve las rutas escritas.
def generar(carpeta_entrenamiento: str | Path, ctx: Contexto, log) -> list[Path]:
    destino = Path(carpeta_entrenamiento) / "graficos"
    destino.mkdir(parents=True, exist_ok=True)

    if ctx.es_clasificacion:
        funciones = [_g_matriz_confusion, _g_metricas_por_clase, _g_curva_roc,
                     _g_curva_precision_recall, _g_distribucion_clases]
    else:
        funciones = [_g_prediccion_vs_real, _g_residuos_vs_prediccion, _g_histograma_residuos]
    funciones += [_g_distribucion_features, _g_importancia_features, _g_curva_aprendizaje, _g_ficha]

    generados: list[Path] = []
    for funcion in funciones:
        try:
            ruta = funcion(destino, ctx)
            if ruta is not None:
                generados.append(ruta)
        except Exception as exc:
            log.error("Grafico '%s' fallo: %s", funcion.__name__.removeprefix("_g_"), exc)
    return generados


# --- utilidades -----------------------------------------------------------
def _subtitulo(ctx: Contexto) -> str:
    return f"{ctx.modelo}  ·  {ctx.objetivo}  ·  {ctx.evaluacion.validacion}"


def _guardar(fig, destino: Path, nombre: str, ctx: Contexto) -> Path:
    return _guardar_figura(fig, destino, nombre, _subtitulo(ctx), ctx.evaluacion.metricas)


# --- clasificacion -------------------------------------------------------
def _g_matriz_confusion(destino: Path, ctx: Contexto) -> Path:
    from sklearn.metrics import confusion_matrix

    y_true, y_pred = ctx.evaluacion.y_true, ctx.evaluacion.y_pred
    k_real = len(ctx.clases)
    tope = config.MAX_CLASES_MATRIZ_CONFUSION

    if k_real <= tope:
        etiquetas = list(range(k_real))
        nombres = list(ctx.clases)
        titulo = "Matriz de confusión (normalizada por fila)"
    else:
        # Demasiadas clases para una matriz k x k (Clasificacion/METABOLITO
        # tiene 32000+): se queda con las de mas soporte en el conjunto
        # evaluado y el resto se junta en una fila/columna "Otras".
        top = [clase for clase, _ in Counter(y_true).most_common(tope)]
        top_set = set(top)
        OTRAS = -1
        y_true = np.array([c if c in top_set else OTRAS for c in y_true])
        y_pred = np.array([c if c in top_set else OTRAS for c in y_pred])
        etiquetas = top + [OTRAS]
        nombres = [ctx.clases[c] for c in top] + ["(Otras)"]
        titulo = (f"Matriz de confusión — top {tope} clases de {k_real} "
                  "(normalizada por fila)")

    k = len(etiquetas)
    cm = confusion_matrix(y_true, y_pred, labels=etiquetas, normalize="true")

    lado = float(np.clip(0.45 * k + 3, 4.5, 22))
    fig, ax = plt.subplots(figsize=(lado, lado * 0.86))
    imagen = ax.imshow(cm, cmap="Blues", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(k))
    ax.set_yticks(range(k))
    if k <= 30:
        ax.set_xticklabels(nombres, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(nombres, fontsize=8)
    else:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    if k <= config.MAX_CLASES_ANOTAR:
        for i in range(k):
            for j in range(k):
                valor = cm[i, j]
                if valor > 0:
                    ax.text(j, i, f"{valor:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if valor > 0.55 else _TINTA)
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    ax.set_title(titulo)
    ax.grid(False)
    fig.colorbar(imagen, ax=ax, fraction=0.046, pad=0.04)
    return _guardar(fig, destino, "matriz_confusion", ctx)


def _g_metricas_por_clase(destino: Path, ctx: Contexto) -> Path:
    from sklearn.metrics import classification_report

    reporte = classification_report(
        ctx.evaluacion.y_true, ctx.evaluacion.y_pred,
        labels=list(range(len(ctx.clases))), target_names=ctx.clases,
        output_dict=True, zero_division=0)

    filas = [(clase, reporte[clase]["precision"], reporte[clase]["recall"],
              reporte[clase]["f1-score"], reporte[clase]["support"])
             for clase in ctx.clases if clase in reporte and reporte[clase]["support"] > 0]
    # Con muchas clases se muestran solo las 25 con mas soporte (las demas
    # tienen apenas 1-2 muestras y su F1 no es informativo).
    if len(filas) > 25:
        filas.sort(key=lambda fila: fila[4], reverse=True)
        filas = filas[:25]
    filas.sort(key=lambda fila: fila[3])

    posiciones = np.arange(len(filas))
    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.34 * len(filas) + 1.2)))
    ax.barh(posiciones - 0.26, [f[1] for f in filas], height=0.26, label="Precisión", color=PALETA[0])
    ax.barh(posiciones, [f[2] for f in filas], height=0.26, label="Recall", color=PALETA[2])
    ax.barh(posiciones + 0.26, [f[3] for f in filas], height=0.26, label="F1", color=PALETA[3])
    ax.set_yticks(posiciones)
    ax.set_yticklabels([_recortar(f[0], 34) for f in filas], fontsize=8)
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Puntaje")
    ax.set_title("Métricas por clase")
    ax.legend(loc="lower right")
    return _guardar(fig, destino, "metricas_por_clase", ctx)


def _g_curva_roc(destino: Path, ctx: Contexto):
    score = ctx.evaluacion.y_score
    if score is None:
        return None
    from sklearn.metrics import auc, roc_curve
    from sklearn.preprocessing import label_binarize

    score = np.asarray(score, dtype=float)
    y_true = ctx.evaluacion.y_true
    k = len(ctx.clases)

    fig, ax = plt.subplots(figsize=(6.5, 6))
    if k == 2:
        positivo = score[:, 1] if score.ndim == 2 else score
        fpr, tpr, _ = roc_curve(y_true, positivo)
        ax.plot(fpr, tpr, color=PALETA[0], lw=2.2, label=f"AUC = {auc(fpr, tpr):.3f}")
        ax.set_title("Curva ROC")
    else:
        if score.ndim != 2 or score.shape[1] != k:
            plt.close(fig)
            return None
        binarizado = label_binarize(y_true, classes=list(range(k)))
        mostrar_cada = k <= 12
        areas = []
        for i in range(k):
            if binarizado[:, i].sum() == 0:
                continue
            fpr, tpr, _ = roc_curve(binarizado[:, i], score[:, i])
            area = auc(fpr, tpr)
            areas.append(area)
            if mostrar_cada:
                ax.plot(fpr, tpr, lw=1.1, alpha=0.75,
                        label=f"{_recortar(ctx.clases[i], 22)} ({area:.2f})")
        fpr_micro, tpr_micro, _ = roc_curve(binarizado.ravel(), score.ravel())
        ax.plot(fpr_micro, tpr_micro, color=_TINTA, lw=2.6,
                label=f"micro-promedio (AUC = {auc(fpr_micro, tpr_micro):.3f})")
        media = float(np.mean(areas)) if areas else float("nan")
        ax.set_title(f"Curvas ROC uno-vs-resto  (macro AUC = {media:.3f})")

    ax.plot([0, 1], [0, 1], ls="--", color=_GRIS_CLARO, lw=1.0)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("Tasa de falsos positivos")
    ax.set_ylabel("Tasa de verdaderos positivos")
    ax.legend(loc="lower right", fontsize=7)
    return _guardar(fig, destino, "curva_roc", ctx)


def _g_curva_precision_recall(destino: Path, ctx: Contexto):
    # Complementa a la ROC: con clases desbalanceadas (todos los objetivos de
    # este proyecto lo estan -- Clasificacion/METABOLITO tiene clases con
    # apenas decenas de muestras) la ROC puede verse bien aunque el modelo
    # acierte poco sobre la clase positiva; precision-recall no se infla asi.
    score = ctx.evaluacion.y_score
    if score is None:
        return None
    from sklearn.metrics import average_precision_score, precision_recall_curve
    from sklearn.preprocessing import label_binarize

    score = np.asarray(score, dtype=float)
    y_true = ctx.evaluacion.y_true
    k = len(ctx.clases)

    fig, ax = plt.subplots(figsize=(6.5, 6))
    if k == 2:
        positivo = score[:, 1] if score.ndim == 2 else score
        precision, recall, _ = precision_recall_curve(y_true, positivo)
        ap = average_precision_score(y_true, positivo)
        ax.plot(recall, precision, color=PALETA[1], lw=2.2, label=f"AP = {ap:.3f}")
        prevalencia = float(np.mean(y_true == 1))
        ax.axhline(prevalencia, ls="--", color=_GRIS_CLARO, lw=1.0,
                   label=f"azar (prevalencia = {prevalencia:.2f})")
        ax.set_title("Curva precisión-recall")
    else:
        if score.ndim != 2 or score.shape[1] != k:
            plt.close(fig)
            return None
        binarizado = label_binarize(y_true, classes=list(range(k)))
        mostrar_cada = k <= 12
        aps = []
        for i in range(k):
            if binarizado[:, i].sum() == 0:
                continue
            precision, recall, _ = precision_recall_curve(binarizado[:, i], score[:, i])
            ap = average_precision_score(binarizado[:, i], score[:, i])
            aps.append(ap)
            if mostrar_cada:
                ax.plot(recall, precision, lw=1.1, alpha=0.75,
                        label=f"{_recortar(ctx.clases[i], 22)} ({ap:.2f})")
        precision_micro, recall_micro, _ = precision_recall_curve(
            binarizado.ravel(), score.ravel())
        ax.plot(recall_micro, precision_micro, color=_TINTA, lw=2.6,
                label=f"micro-promedio (AP = {average_precision_score(binarizado, score, average='micro'):.3f})")
        media = float(np.mean(aps)) if aps else float("nan")
        ax.set_title(f"Curvas precisión-recall uno-vs-resto  (macro AP = {media:.3f})")

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precisión")
    ax.legend(loc="lower left", fontsize=7)
    return _guardar(fig, destino, "curva_precision_recall", ctx)


def _g_distribucion_clases(destino: Path, ctx: Contexto) -> Path:
    conteo = Counter(ctx.evaluacion.y_true)
    pares = sorted(conteo.items(), key=lambda kv: kv[1], reverse=True)
    if len(pares) > 40:
        pares = pares[:40]
    nombres = [_recortar(ctx.clases[i], 24) for i, _ in pares]
    valores = [v for _, v in pares]

    fig, ax = plt.subplots(figsize=(max(6.0, 0.3 * len(nombres) + 2), 4.2))
    ax.bar(range(len(nombres)), valores, color=PALETA[0])
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("Muestras")
    ax.set_title("Distribución de clases (conjunto evaluado)")
    return _guardar(fig, destino, "distribucion_clases", ctx)


# --- regresion ---------------------------------------------------------
def _g_prediccion_vs_real(destino: Path, ctx: Contexto) -> Path:
    from sklearn.metrics import r2_score

    y_true, y_pred = ctx.evaluacion.y_true, ctx.evaluacion.y_pred
    fig, ax = plt.subplots(figsize=(6.4, 6))
    ax.scatter(y_true, y_pred, s=28, alpha=0.6, color=PALETA[0],
               edgecolor="white", linewidth=0.4)
    lo = float(min(y_true.min(), y_pred.min()))
    hi = float(max(y_true.max(), y_pred.max()))
    ax.plot([lo, hi], [lo, hi], ls="--", color=_GRIS_CLARO, lw=1.2, label="Ideal (y = x)")
    ax.set_xlabel("Valor real")
    ax.set_ylabel("Predicción")
    ax.set_title(f"Predicción vs. real  (R² = {r2_score(y_true, y_pred):.3f})")
    ax.legend(loc="upper left")
    return _guardar(fig, destino, "prediccion_vs_real", ctx)


def _g_residuos_vs_prediccion(destino: Path, ctx: Contexto) -> Path:
    y_true, y_pred = ctx.evaluacion.y_true, ctx.evaluacion.y_pred
    residuos = y_true - y_pred
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(y_pred, residuos, s=28, alpha=0.6, color=PALETA[4],
               edgecolor="white", linewidth=0.4)
    ax.axhline(0.0, ls="--", color=_GRIS_CLARO, lw=1.2)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Residuo (real − predicción)")
    ax.set_title("Residuos vs. predicción")
    return _guardar(fig, destino, "residuos_vs_prediccion", ctx)


def _g_histograma_residuos(destino: Path, ctx: Contexto) -> Path:
    residuos = ctx.evaluacion.y_true - ctx.evaluacion.y_pred
    bins = int(np.clip(len(residuos) // 5, 10, 30))
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(residuos, bins=bins, color=PALETA[0], alpha=0.85, edgecolor="white")
    ax.axvline(0.0, ls="--", color=_GRIS_CLARO, lw=1.2)
    ax.set_xlabel("Residuo")
    ax.set_ylabel("Frecuencia")
    ax.set_title(f"Distribución de residuos  (μ = {residuos.mean():.3g}, σ = {residuos.std():.3g})")
    return _guardar(fig, destino, "histograma_residuos", ctx)


def _g_distribucion_features(destino: Path, ctx: Contexto) -> Path | None:
    return _distribucion_grid(destino, ctx.X, ctx.nombres_features, _guardar, ctx)


# --- especifico del algoritmo -----------------------------------------
def _g_importancia_features(destino: Path, ctx: Contexto):
    base = _estimador_base(ctx.estimador)
    nombres = np.asarray(ctx.nombres_features)

    if hasattr(base, "feature_importances_"):
        valores = np.asarray(base.feature_importances_, dtype=float)
        fuente = "ganancia del modelo"
    elif hasattr(base, "coef_"):
        coeficientes = np.asarray(base.coef_, dtype=float)
        valores = (np.abs(coeficientes).mean(axis=0) if coeficientes.ndim > 1
                   else np.abs(coeficientes).ravel())
        fuente = "coeficiente |β|"
    else:
        from sklearn.inspection import permutation_importance

        X, y = ctx.X, ctx.y
        if len(X) > config.MAX_FILAS_PERMUTACION:
            rng = np.random.default_rng(config.SEMILLA)
            indices = rng.choice(len(X), config.MAX_FILAS_PERMUTACION, replace=False)
            X, y = X[indices], y[indices]
        resultado = permutation_importance(
            ctx.estimador, X, y, n_repeats=8, random_state=config.SEMILLA, n_jobs=-1)
        valores = np.asarray(resultado.importances_mean, dtype=float)
        fuente = "permutación"

    if valores is None or len(valores) != len(nombres):
        return None

    top = np.argsort(valores)[::-1][: config.TOP_FEATURES_GRAFICO][::-1]
    fig, ax = plt.subplots(figsize=(8, max(3.0, 0.34 * len(top) + 1.2)))
    ax.barh(range(len(top)), valores[top], color=PALETA[0])
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([_recortar(n, 44) for n in nombres[top]], fontsize=8)
    ax.set_xlabel("Importancia")
    ax.set_title(f"Top {len(top)} features — {fuente}")
    return _guardar(fig, destino, "importancia_features", ctx)


# Diagnostico de sesgo/varianza: puntaje de entrenamiento vs. validacion a
# medida que crece el tamano de entrenamiento. Curvas separadas y bajas -> mas
# datos ayudarian (o el modelo es debil); separadas con la de entrenamiento
# muy alta -> sobreajuste; juntas y bajas -> el modelo no da para mas con estas
# features. Se sub-muestrea (config.MAX_FILAS_CURVA_APRENDIZAJE) porque es un
# diagnostico, no una metrica final, y reentrena el modelo varias veces.
def _g_curva_aprendizaje(destino: Path, ctx: Contexto):
    from sklearn.model_selection import KFold, learning_curve

    X, y = ctx.X, ctx.y
    if len(X) > config.MAX_FILAS_CURVA_APRENDIZAJE:
        rng = np.random.default_rng(config.SEMILLA)
        indices = rng.choice(len(X), config.MAX_FILAS_CURVA_APRENDIZAJE, replace=False)
        X, y = X[indices], y[indices]
    if len(X) < 40:
        return None

    cv = KFold(n_splits=3, shuffle=True, random_state=config.SEMILLA)
    tamanos, puntaje_train, puntaje_val = learning_curve(
        clone(ctx.estimador), X, y, cv=cv, n_jobs=-1, shuffle=True,
        random_state=config.SEMILLA,
        train_sizes=np.array(config.PUNTOS_CURVA_APRENDIZAJE))

    fig, ax = plt.subplots(figsize=(7, 5))
    for datos, color, etiqueta in ((puntaje_train, PALETA[0], "Entrenamiento"),
                                   (puntaje_val, PALETA[1], "Validación")):
        media, desvio = datos.mean(axis=1), datos.std(axis=1)
        ax.plot(tamanos, media, "o-", color=color, lw=2, label=etiqueta)
        ax.fill_between(tamanos, media - desvio, media + desvio, color=color, alpha=0.15)
    ax.set_xlabel(f"Filas de entrenamiento (de una muestra de {len(X)})")
    ax.set_ylabel("Accuracy" if ctx.es_clasificacion else "R²")
    ax.set_title("Curva de aprendizaje")
    ax.legend(loc="lower right")
    return _guardar(fig, destino, "curva_aprendizaje", ctx)


# --- ficha resumen ---------------------------------------------------
def _g_ficha(destino: Path, ctx: Contexto) -> Path:
    ev = ctx.evaluacion
    lineas = [
        ("Modelo", ctx.modelo),
        ("Paradigma / tarea", f"{ctx.paradigma} / {ctx.tarea}"),
        ("Objetivo", ctx.objetivo),
        ("Muestras × features", f"{len(ctx.y)} × {len(ctx.nombres_features)}"),
        ("Validación", ev.validacion),
    ]
    if ctx.clases is not None:
        lineas.append(("Clases", str(len(ctx.clases))))
    for clave, valor in ev.metricas.items():
        lineas.append((clave, f"{valor:.4f}"))

    fig, ax = plt.subplots(figsize=(7.2, 0.5 * len(lineas) + 1.3))
    ax.axis("off")
    ax.text(0.02, 0.98, "Ficha del entrenamiento", fontsize=13, fontweight="bold",
            va="top", transform=ax.transAxes)
    for i, (clave, valor) in enumerate(lineas):
        y = 0.86 - i * (0.78 / max(len(lineas), 1))
        ax.text(0.02, y, clave, fontsize=9.5, color=_GRIS, va="top", transform=ax.transAxes)
        ax.text(0.44, y, _recortar(valor, 60), fontsize=9.5, color=_TINTA, va="top",
                transform=ax.transAxes)
    return _guardar(fig, destino, "ficha", ctx)
