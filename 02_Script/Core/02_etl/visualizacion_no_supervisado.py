#
# Archivo: visualizacion_no_supervisado.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Graficos de las tareas de 02_No_supervisado (Clustering, Reduccion de
# dimensionalidad, Deteccion de anomalias, Reglas de asociacion, Cadenas de
# Markov), guardados como PNG en <carpeta_del_entrenamiento>/graficos/.
#
# A diferencia de visualizacion_supervisado.Contexto (ligado a
# Core.evaluacion.Evaluacion), ContextoNS deja que cada tarea llene solo los
# campos que le aplican; el resto queda None.
#
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .. import submodulo
from .visualizacion_estilo import (
    PALETA, _GRIS, _GRIS_CLARO, _TINTA, _distribucion_grid, _guardar_figura, _recortar, plt,
)

config = submodulo("00_fundamentos.config")


@dataclass
class ContextoNS:
    modelo: str
    paradigma: str
    tarea: str
    metricas: dict
    nombres_features: list[str]
    n_filas: int
    X: np.ndarray | None = None            # clustering / anomalias / reduccion (entrada)
    etiquetas: np.ndarray | None = None    # clustering (grupo) / anomalias (1 normal, -1 anomalia)
    es_anomalia: bool = False              # distingue el significado de "-1" en etiquetas
    X_reducido: np.ndarray | None = None   # reduccion
    puntajes: np.ndarray | None = None     # anomalias (continuo, mayor = mas normal)
    estimador: Any = None                  # reduccion, para varianza_explicada_ratio_
    reglas: list | None = None             # reglas de asociacion
    estados: list[str] | None = None               # cadenas de markov
    matriz_transicion: np.ndarray | None = None    # cadenas de markov


def _subtitulo_ns(ctx: ContextoNS) -> str:
    return f"{ctx.modelo}  ·  {ctx.tarea}"


def _guardar_ns(fig, destino: Path, nombre: str, ctx: ContextoNS) -> Path:
    return _guardar_figura(fig, destino, nombre, _subtitulo_ns(ctx), ctx.metricas)


def _g_distribucion_features_ns(destino: Path, ctx: ContextoNS) -> Path | None:
    return _distribucion_grid(destino, ctx.X, ctx.nombres_features, _guardar_ns, ctx)


# Clustering y Deteccion de anomalias comparten esta: proyecta X a 2D (PCA si
# tiene mas de 2 columnas) y colorea por etiqueta.
def _g_proyeccion_2d(destino: Path, ctx: ContextoNS):
    if ctx.X is None or ctx.etiquetas is None:
        return None
    if ctx.X.shape[1] > 2:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2, random_state=config.SEMILLA)
        X2 = pca.fit_transform(ctx.X)
        varianza = 100 * pca.explained_variance_ratio_
        etiquetas_ejes = [f"Componente {i + 1} ({varianza[i]:.1f}%)" for i in range(2)]
    elif ctx.X.shape[1] == 2:
        X2 = ctx.X
        etiquetas_ejes = ["Feature 1", "Feature 2"]
    else:
        X2 = np.column_stack((ctx.X[:, 0], np.zeros(len(ctx.X))))
        etiquetas_ejes = ["Feature 1", "Feature 2"]

    fig, ax = plt.subplots(figsize=(7, 6))
    valores = sorted(set(ctx.etiquetas))
    for i, valor in enumerate(valores):
        m = ctx.etiquetas == valor
        if ctx.es_anomalia:
            nombre_grupo = "Anomalía" if valor == -1 else "Normal"
            color = PALETA[1] if valor == -1 else PALETA[0]
        else:
            nombre_grupo, color = ("Ruido", _GRIS_CLARO) if valor == -1 else (
                f"Grupo {valor}", PALETA[i % len(PALETA)])
        ax.scatter(X2[m, 0], X2[m, 1], s=26, alpha=0.75, color=color,
                  label=nombre_grupo, edgecolor="white", linewidth=0.3)
    ax.set_xlabel(etiquetas_ejes[0])
    ax.set_ylabel(etiquetas_ejes[1])
    ax.set_title("Proyección PCA a 2D")
    ax.legend(loc="best", fontsize=7, ncols=2 if len(valores) > 8 else 1)
    return _guardar_ns(fig, destino, "proyeccion_2d", ctx)


def _g_tamano_clusters(destino: Path, ctx: ContextoNS):
    if ctx.etiquetas is None:
        return None
    conteo = Counter(ctx.etiquetas)
    pares = sorted(conteo.items(), key=lambda kv: (kv[0] == -1, -kv[1]))
    if len(pares) > 25:
        pares = pares[:25]
    nombres = ["Ruido" if v == -1 else f"Grupo {v}" for v, _ in pares]
    valores = [n for _, n in pares]

    fig, ax = plt.subplots(figsize=(max(5.0, 0.6 * len(nombres) + 2), 4.2))
    colores = [_GRIS_CLARO if n == "Ruido" else PALETA[i % len(PALETA)]
              for i, n in enumerate(nombres)]
    ax.bar(range(len(nombres)), valores, color=colores)
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Muestras")
    sufijo = " (25 mayores)" if len(conteo) > 25 else ""
    ax.set_title(f"Tamaño de cada grupo{sufijo}")
    return _guardar_ns(fig, destino, "tamano_clusters", ctx)


def _g_perfiles_quimicos_grupos(destino: Path, ctx: ContextoNS):
    if ctx.X is None or ctx.etiquetas is None or not ctx.nombres_features:
        return None
    grupos = (sorted(set(ctx.etiquetas)) if ctx.es_anomalia else
              [g for g in sorted(set(ctx.etiquetas)) if g != -1])
    if len(grupos) < 2:
        return None

    cantidad_grupos = len(grupos)
    if cantidad_grupos > 20:
        grupos = sorted(
            sorted(grupos, key=lambda grupo: int((ctx.etiquetas == grupo).sum()),
                   reverse=True)[:20])
    medias = np.vstack([ctx.X[ctx.etiquetas == grupo].mean(axis=0) for grupo in grupos])
    indices = np.argsort(np.var(medias, axis=0))[::-1][:25]
    valores = medias[:, indices]
    limite = float(np.percentile(np.abs(valores), 98)) or 1.0

    fig, ax = plt.subplots(figsize=(max(9, 0.42 * len(indices)), max(3.5, 0.55 * len(grupos) + 2)))
    imagen = ax.imshow(valores, aspect="auto", cmap="RdBu_r", vmin=-limite, vmax=limite)
    ax.set_xticks(np.arange(len(indices)))
    ax.set_xticklabels([_recortar(ctx.nombres_features[i], 22) for i in indices],
                       rotation=55, ha="right", fontsize=7)
    if ctx.es_anomalia:
        nombres_grupos = ["Anomalía" if grupo == -1 else "Normal" for grupo in grupos]
    else:
        nombres_grupos = [f"Grupo {grupo}" for grupo in grupos]
    ax.set_yticks(np.arange(len(grupos)))
    ax.set_yticklabels(nombres_grupos, fontsize=8)
    texto_grupos = (f" (20 mayores de {cantidad_grupos})" if cantidad_grupos > 20 else "")
    ax.set_title(f"Firmas químicas medias por grupo{texto_grupos} (perfiles Hellinger)")
    fig.colorbar(imagen, ax=ax, fraction=0.025, pad=0.02, label="Abundancia relativa transformada")
    return _guardar_ns(fig, destino, "perfiles_quimicos_grupos", ctx)


def _g_varianza_explicada(destino: Path, ctx: ContextoNS):
    if ctx.estimador is None or not hasattr(ctx.estimador, "explained_variance_ratio_"):
        return None
    ratios = np.asarray(ctx.estimador.explained_variance_ratio_, dtype=float)
    acumulada = np.cumsum(ratios)

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(1, len(ratios) + 1)
    ax.bar(x, ratios, color=PALETA[0], alpha=0.5, label="Por componente")
    ax.plot(x, acumulada, "o-", color=PALETA[1], lw=2, label="Acumulada")
    ax.set_xticks(x)
    ax.set_xlabel("Componente")
    ax.set_ylabel("Varianza explicada")
    ax.set_ylim(0, 1.02)
    ax.set_title("Varianza explicada por componente")
    ax.legend(loc="center right")
    return _guardar_ns(fig, destino, "varianza_explicada", ctx)


def _g_dispersion_componentes(destino: Path, ctx: ContextoNS):
    if ctx.X_reducido is None or ctx.X_reducido.shape[1] < 2:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.scatter(ctx.X_reducido[:, 0], ctx.X_reducido[:, 1], s=26, alpha=0.7,
              color=PALETA[0], edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Componente 1")
    ax.set_ylabel("Componente 2")
    ax.set_title("Dispersión en las 2 primeras componentes")
    return _guardar_ns(fig, destino, "dispersion_componentes", ctx)


def _g_puntajes_anomalia(destino: Path, ctx: ContextoNS):
    if ctx.puntajes is None or ctx.etiquetas is None:
        return None
    normal, anomalo = ctx.puntajes[ctx.etiquetas == 1], ctx.puntajes[ctx.etiquetas == -1]
    fig, ax = plt.subplots(figsize=(7, 5))
    bins = int(np.clip(len(ctx.puntajes) // 10, 10, 40))
    ax.hist(normal, bins=bins, color=PALETA[0], alpha=0.7, label=f"Normal ({len(normal)})")
    if len(anomalo):
        ax.hist(anomalo, bins=bins, color=PALETA[1], alpha=0.7,
               label=f"Anomalía ({len(anomalo)})")
    ax.set_xlabel("Puntaje (mayor = más normal)")
    ax.set_ylabel("Muestras")
    pct = ctx.metricas.get("anomalias_pct", 0.0)
    ax.set_title(f"Puntajes de anomalía  ({pct:.1f}% marcado)")
    ax.legend(loc="best")
    return _guardar_ns(fig, destino, "puntajes_anomalia", ctx)


def _g_reglas_top(destino: Path, ctx: ContextoNS):
    if not ctx.reglas:
        return None
    top = ctx.reglas[:15]
    etiquetas = [f"{' + '.join(_recortar(a, 18) for a in r.antecedente)}  →  "
                f"{_recortar(r.consecuente, 18)}" for r in top]
    lifts = [r.lift for r in top]

    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.4 * len(top) + 1.2)))
    ax.barh(range(len(top)), lifts, color=PALETA[4])
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(etiquetas, fontsize=7.5)
    ax.invert_yaxis()
    ax.axvline(1.0, ls="--", color=_GRIS_CLARO, lw=1.0)
    ax.set_xlabel("Lift")
    ax.set_title(f"Top {len(top)} reglas por lift (de {len(ctx.reglas)} encontradas)")
    return _guardar_ns(fig, destino, "reglas_top", ctx)


# Vista de conjunto de toda la matriz de transicion: sin etiquetas (con 300+
# estados no entran igual), pero el patron general -- bloques densos, cuan
# dispersa es -- ya dice algo. El detalle legible va en _g_transiciones_top.
def _g_matriz_transicion(destino: Path, ctx: ContextoNS):
    if ctx.matriz_transicion is None:
        return None
    fig, ax = plt.subplots(figsize=(7, 6.2))
    imagen = ax.imshow(ctx.matriz_transicion, cmap="Blues", vmin=0.0,
                       vmax=float(np.percentile(ctx.matriz_transicion, 99)))
    ax.set_xlabel("Estado siguiente (clase química)")
    ax.set_ylabel("Estado actual (clase química)")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Matriz de transición ({len(ctx.estados)} estados)")
    ax.grid(False)
    fig.colorbar(imagen, ax=ax, fraction=0.046, pad=0.04, label="P(siguiente | actual)")
    return _guardar_ns(fig, destino, "matriz_transicion", ctx)


def _g_transiciones_top(destino: Path, ctx: ContextoNS):
    if ctx.matriz_transicion is None or ctx.estados is None:
        return None
    M, estados = ctx.matriz_transicion, ctx.estados
    n = len(estados)
    # top transiciones EXCLUYENDO la diagonal (a -> a: co-elución de la misma
    # clase, casi siempre la mas alta y no es interesante repetirla 300 veces).
    pares = [(i, j, M[i, j]) for i in range(n) for j in range(n) if i != j]
    pares.sort(key=lambda t: t[2], reverse=True)
    top = pares[:15]
    etiquetas = [f"{_recortar(estados[i], 20)}  →  {_recortar(estados[j], 20)}" for i, j, _ in top]
    valores = [p for _, _, p in top]

    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.4 * len(top) + 1.2)))
    ax.barh(range(len(top)), valores, color=PALETA[5])
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(etiquetas, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("P(siguiente | actual)")
    ax.set_title("Transiciones más probables (sin contar A → A)")
    return _guardar_ns(fig, destino, "transiciones_top", ctx)


def _g_ficha_ns(destino: Path, ctx: ContextoNS):
    lineas = [
        ("Modelo", ctx.modelo),
        ("Paradigma / tarea", f"{ctx.paradigma} / {ctx.tarea}"),
        ("Muestras × features", f"{ctx.n_filas} × {len(ctx.nombres_features)}"),
    ]
    for clave, valor in ctx.metricas.items():
        lineas.append((clave, f"{valor:.4f}" if isinstance(valor, float) else str(valor)))

    fig, ax = plt.subplots(figsize=(7.2, 0.5 * len(lineas) + 1.3))
    ax.axis("off")
    ax.text(0.02, 0.98, "Ficha del entrenamiento", fontsize=13, fontweight="bold",
           va="top", transform=ax.transAxes)
    for i, (clave, valor) in enumerate(lineas):
        y = 0.86 - i * (0.78 / max(len(lineas), 1))
        ax.text(0.02, y, clave, fontsize=9.5, color=_GRIS, va="top", transform=ax.transAxes)
        ax.text(0.44, y, _recortar(valor, 60), fontsize=9.5, color=_TINTA, va="top",
               transform=ax.transAxes)
    return _guardar_ns(fig, destino, "ficha", ctx)


_FUNCIONES_NS = {
    "Clustering": [_g_distribucion_features_ns, _g_proyeccion_2d, _g_tamano_clusters,
                   _g_perfiles_quimicos_grupos],
    "Reduccion de dimensionalidad": [_g_distribucion_features_ns, _g_varianza_explicada,
                                     _g_dispersion_componentes],
    "Deteccion de anomalias": [_g_distribucion_features_ns, _g_proyeccion_2d,
                               _g_puntajes_anomalia, _g_perfiles_quimicos_grupos],
    "Reglas de asociacion": [_g_reglas_top],
    "Cadenas de Markov": [_g_matriz_transicion, _g_transiciones_top],
}


# Genera los graficos de una tarea de 02_No_supervisado (equivalente a
# visualizacion_supervisado.generar(), pero para ContextoNS). `tarea` es la
# clave interna sin tilde (igual a Core.modelos_no_supervisados / la carpeta en
# disco). `destino` es la carpeta "graficos" en si (mismo contrato que
# Core.no_supervisado.finalizar espera de graficos_fn), no la carpeta del modelo.
def generar_no_supervisado(tarea: str, destino: str | Path,
                           ctx: ContextoNS, log) -> list[Path]:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    generados: list[Path] = []
    fallos: list[str] = []
    for funcion in _FUNCIONES_NS.get(tarea, []) + [_g_ficha_ns]:
        try:
            ruta = funcion(destino, ctx)
            if ruta is not None:
                generados.append(ruta)
        except Exception as exc:
            nombre = funcion.__name__.removeprefix("_g_")
            fallos.append(f"{nombre}: {type(exc).__name__}: {exc}")
            log.exception("Grafico '%s' fallo", nombre)
    if fallos:
        raise RuntimeError(
            f"Falló la generación de {len(fallos)} gráfico(s): " + "; ".join(fallos))
    return generados
