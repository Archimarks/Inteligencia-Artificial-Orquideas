"""Metricas de clasificacion multiclase y multietiqueta."""
from __future__ import annotations

import warnings

import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score, f1_score, hamming_loss,
                             matthews_corrcoef, roc_auc_score, top_k_accuracy_score)

METRICA_PRINCIPAL = {"multiclase": "balanced_accuracy", "multietiqueta": "average_precision_macro"}


def multiclase(y: np.ndarray, pred: np.ndarray, proba: np.ndarray | None = None, clases: np.ndarray | None = None
               ) -> dict[str, float]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = {
            "accuracy": accuracy_score(y, pred),
            "balanced_accuracy": balanced_accuracy_score(y, pred),
            "f1_macro": f1_score(y, pred, average="macro", zero_division=0),
            "f1_weighted": f1_score(y, pred, average="weighted", zero_division=0),
            "mcc": matthews_corrcoef(y, pred),
        }
        if proba is not None and clases is not None and len(clases) > 3:
            try:
                m["top3_accuracy"] = top_k_accuracy_score(y, proba, k=3, labels=clases)
            except ValueError:
                pass
    return {k: float(v) for k, v in m.items()}


def multietiqueta(Y: np.ndarray, pred: np.ndarray, proba: np.ndarray) -> dict[str, float]:
    """AUC y precision promedio solo sobre etiquetas con positivos y negativos en el conjunto evaluado."""
    validas = (Y.sum(axis=0) > 0) & (Y.sum(axis=0) < len(Y))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = {
            "f1_micro": f1_score(Y, pred, average="micro", zero_division=0),
            "f1_macro": f1_score(Y, pred, average="macro", zero_division=0),
            "hamming_loss": hamming_loss(Y, pred),
            "subset_accuracy": accuracy_score(Y, pred),
        }
        if validas.any():
            m["roc_auc_macro"] = roc_auc_score(Y[:, validas], proba[:, validas], average="macro")
            m["average_precision_macro"] = average_precision_score(Y[:, validas], proba[:, validas], average="macro")
            m["prevalencia_media"] = float(Y[:, validas].mean())
    return {k: float(v) for k, v in m.items()}


def por_etiqueta(Y: np.ndarray, proba: np.ndarray, nombres: list[str]) -> list[dict[str, float | str]]:
    filas = []
    for j, n in enumerate(nombres):
        y = Y[:, j]
        f: dict[str, float | str] = {"etiqueta": n, "positivos": int(y.sum()), "prevalencia": float(y.mean())}
        if 0 < y.sum() < len(y):
            f["roc_auc"] = float(roc_auc_score(y, proba[:, j]))
            f["average_precision"] = float(average_precision_score(y, proba[:, j]))
        filas.append(f)
    return filas
