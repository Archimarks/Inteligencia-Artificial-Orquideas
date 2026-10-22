#
# Archivo: visualizacion_estilo.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Estilo global de matplotlib y helpers compartidos por
# visualizacion_supervisado.py y visualizacion_no_supervisado.py: paleta de
# colores, guardado de una figura (PNG + <nombre>.txt de interpretacion) y la
# grilla de distribucion de columnas (usada por ambos tipos de Contexto).
#
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .. import submodulo  # noqa: E402

config = submodulo("00_fundamentos.config")  # noqa: E402

# Paleta sobria y con suficiente contraste en impresion.
PALETA = ["#2563eb", "#dc2626", "#16a34a", "#d97706",
          "#7c3aed", "#0891b2", "#db2777", "#4b5563"]
_GRIS = "#64748b"
_GRIS_CLARO = "#94a3b8"
_TINTA = "#0f172a"


# Ajusta el estilo global de matplotlib para todos los graficos del proyecto.
def _estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": config.GRAFICOS_DPI,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.edgecolor": "#334155",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#e2e8f0",
        "grid.linewidth": 0.6,
        "xtick.color": "#334155",
        "ytick.color": "#334155",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })


_estilo()


def _recortar(texto: str, limite: int) -> str:
    texto = str(texto)
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def _estimador_base(estimador):
    pasos = getattr(estimador, "steps", None)
    return pasos[-1][1] if pasos else estimador


# Guardado comun a Contexto (supervisado) y ContextoNS (no supervisado):
# subtitulo + PNG + <nombre>.txt de interpretacion. _guardar/_guardar_ns (en
# cada modulo especifico) solo calculan el subtitulo y las metricas segun su
# tipo de Contexto.
def _guardar_figura(fig, destino: Path, nombre: str, subtitulo: str, metricas: dict) -> Path:
    try:
        fig.suptitle(subtitulo, fontsize=8.5, color=_GRIS)
        fig.tight_layout(rect=(0, 0, 1, 0.97))
    except Exception:
        pass
    Path(destino).mkdir(parents=True, exist_ok=True)
    ruta = destino / f"{nombre}.png"
    fig.savefig(ruta)
    plt.close(fig)
    # <nombre>.txt: para que sirve la grafica y como interpretarla
    interpretacion_graficos = submodulo("01_catalogos.interpretacion_graficos")
    interpretacion_graficos.escribir(destino, nombre, metricas)
    return ruta


# Grilla de histograma + densidad (KDE) de las features de mayor varianza (las
# mas informativas de mirar; con cientos/miles de columnas no entrarian todas
# en una grilla legible, ver config.MAX_FEATURES_DISTRIBUCION). Se sub-muestrean
# las filas (config.MAX_FILAS_DISTRIBUCION_FEATURES): es un diagnostico, no una
# metrica, y el KDE es O(n) por punto evaluado. Comun a Contexto y ContextoNS
# (guardar_fn es _guardar o _guardar_ns, segun quien llame).
def _distribucion_grid(destino: Path, X: np.ndarray | None, nombres: list[str],
                       guardar_fn, ctx) -> Path | None:
    if X is None or X.shape[1] == 0:
        return None
    from scipy.stats import gaussian_kde

    if len(X) > config.MAX_FILAS_DISTRIBUCION_FEATURES:
        rng = np.random.default_rng(config.SEMILLA)
        indices_fila = rng.choice(len(X), config.MAX_FILAS_DISTRIBUCION_FEATURES, replace=False)
        X = X[indices_fila]

    varianzas = np.var(X, axis=0)
    top = np.sort(np.argsort(varianzas)[::-1][: config.MAX_FEATURES_DISTRIBUCION])

    ncols = min(4, len(top))
    nrows = int(np.ceil(len(top) / ncols))
    fig, ejes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 2.7 * nrows), squeeze=False)
    ejes = ejes.ravel()

    for ax, i in zip(ejes, top):
        columna = X[:, i]
        ax.hist(columna, bins=30, density=True, color=PALETA[0], alpha=0.65, edgecolor="white")
        if np.std(columna) > 0 and len(np.unique(columna)) > 1:
            try:
                kde = gaussian_kde(columna)
                xs = np.linspace(columna.min(), columna.max(), 200)
                ax.plot(xs, kde(xs), color=PALETA[1], lw=1.6)
            except Exception:
                pass
        ax.set_title(_recortar(nombres[i], 26), fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_yticks([])
    for ax in ejes[len(top):]:
        ax.axis("off")

    # fig.text (no fig.suptitle): _guardar()/_guardar_ns() ya usan suptitle
    # para el subtitulo modelo/objetivo/validacion -- una segunda llamada a
    # suptitle lo reemplazaria en vez de sumarse.
    fig.text(0.5, 1.02, f"Distribución de columnas (top {len(top)} por varianza)",
             ha="center", fontsize=11, fontweight="bold", color=_TINTA)
    return guardar_fn(fig, destino, "distribucion_features", ctx)
