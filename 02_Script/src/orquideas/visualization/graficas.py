"""Utilidades de graficacion: cada figura lleva titulo, ejes, leyenda cuando aplica y una nota interpretativa."""
from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from ..utils.rutas import config_global  # noqa: E402

sns.set_theme(style=config_global()["graficas"].get("estilo", "whitegrid"), context="notebook")


def guardar(fig: plt.Figure, p: Path, nota: str | None = None, dpi: int | None = None) -> Path:
    """Guarda la figura; `nota` se imprime al pie como interpretacion breve."""
    if nota:
        fig.text(0.01, 0.005, "\n".join(textwrap.wrap(nota, 160)), fontsize=7.5, style="italic", va="bottom", ha="left")
        fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, 0.12 + 0.025 * nota.count(" ") / 25))
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=dpi or config_global()["graficas"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    return p


def barras(serie: pd.Series, p: Path, titulo: str, xlabel: str, ylabel: str, nota: str | None = None,
           horizontal: bool = True, top: int | None = 30, log: bool = False) -> Path:
    s = serie.sort_values(ascending=False)
    if top:
        s = s.head(top)
    alto = max(3.5, 0.28 * len(s) + 1.5) if horizontal else 5
    fig, ax = plt.subplots(figsize=(9, alto))
    if horizontal:
        sns.barplot(x=s.values, y=[str(i)[:60] for i in s.index], ax=ax, color="#3b7dd8", orient="h")
        ax.set_xlabel(ylabel); ax.set_ylabel(xlabel)
        if log:
            ax.set_xscale("log")
    else:
        sns.barplot(x=[str(i)[:30] for i in s.index], y=s.values, ax=ax, color="#3b7dd8")
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=60)
        if log:
            ax.set_yscale("log")
    ax.set_title(titulo)
    return guardar(fig, p, nota)


def mapa_calor(df: pd.DataFrame, p: Path, titulo: str, xlabel: str, ylabel: str, nota: str | None = None,
               cmap: str = "viridis", fmt: str | None = None, center: float | None = None, cbar_label: str = "") -> Path:
    h = max(4, 0.25 * df.shape[0] + 2)
    w = max(6, 0.3 * df.shape[1] + 3)
    fig, ax = plt.subplots(figsize=(min(w, 30), min(h, 40)))
    sns.heatmap(df, ax=ax, cmap=cmap, annot=fmt is not None and df.size <= 400, fmt=fmt or ".2f", center=center,
                cbar_kws={"label": cbar_label}, linewidths=0.2 if df.size < 2500 else 0)
    ax.set_title(titulo); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", labelsize=7, rotation=90); ax.tick_params(axis="y", labelsize=7)
    return guardar(fig, p, nota)


def matriz_confusion(cm: np.ndarray, etiquetas: list[str], p: Path, titulo: str, nota: str | None = None) -> Path:
    cmn = cm / np.clip(cm.sum(axis=1, keepdims=True), 1, None)
    n = len(etiquetas)
    fig, ax = plt.subplots(figsize=(max(5, 0.45 * n + 3), max(4, 0.45 * n + 2)))
    sns.heatmap(cmn, annot=n <= 20, fmt=".2f", cmap="Blues", vmin=0, vmax=1, ax=ax,
                xticklabels=[e[:28] for e in etiquetas], yticklabels=[e[:28] for e in etiquetas],
                cbar_kws={"label": "Proporcion por clase real"})
    ax.set_xlabel("Clase predicha"); ax.set_ylabel("Clase real"); ax.set_title(titulo)
    ax.tick_params(axis="x", rotation=90, labelsize=7); ax.tick_params(axis="y", labelsize=7)
    return guardar(fig, p, nota)


def dispersion_2d(coords: np.ndarray, etiquetas: pd.Series, p: Path, titulo: str, xlabel: str, ylabel: str,
                  nota: str | None = None, textos: list[str] | None = None, max_leyenda: int = 15) -> Path:
    fig, ax = plt.subplots(figsize=(9, 7))
    et = etiquetas.astype(str).values
    cats = pd.Series(et).value_counts()
    top = set(cats.index[:max_leyenda])
    et2 = np.array([e if e in top else "Otros" for e in et])
    pal = sns.color_palette("tab20", n_colors=len(set(et2)))
    for i, c in enumerate(sorted(set(et2), key=lambda x: (x == "Otros", x))):
        m = et2 == c
        ax.scatter(coords[m, 0], coords[m, 1], s=28, alpha=0.8, label=f"{c[:30]} ({m.sum()})", color=pal[i % len(pal)])
    if textos is not None and len(textos) <= 90:
        for (x, y), t in zip(coords, textos):
            ax.annotate(t[:22], (x, y), fontsize=6, alpha=0.75)
    ax.set_title(titulo); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(fontsize=7, bbox_to_anchor=(1.01, 1), loc="upper left", title="Grupo (n)")
    return guardar(fig, p, nota)


def comparacion_modelos(df: pd.DataFrame, metrica: str, p: Path, titulo: str, nota: str | None = None,
                        error: str | None = None, referencia: float | None = None) -> Path:
    fig, ax = plt.subplots(figsize=(8, max(3, 0.5 * len(df) + 1.5)))
    d = df.sort_values(metrica)
    ax.barh(d["modelo"], d[metrica], xerr=d[error] if error and error in d else None, color="#2a9d8f", capsize=3)
    if referencia is not None:
        ax.axvline(referencia, color="red", ls="--", label=f"Referencia (baseline) = {referencia:.3f}")
        ax.legend(fontsize=8)
    ax.set_xlabel(metrica); ax.set_ylabel("Modelo"); ax.set_title(titulo)
    return guardar(fig, p, nota)
