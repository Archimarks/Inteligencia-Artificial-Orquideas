#
# Archivo: datos.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Empaqueta un dataset ya armado (ver Core/construir_dataset.py y
# Core/construir_dataset_no_supervisado.py) en un objeto Dataset: X (features),
# y (objetivo, None si no supervisado) y referencias (metadatos), separados.
#
# Convencion de columnas (comun a todos los datasets del proyecto):
#     - Primera columna  -> identificador de fila. Pasa a indice.
#     - Columna Y        -> objetivo (etiqueta o valor a predecir). Texto en
#                           clasificacion (asi Dataset.es_clasificacion lo
#                           detecta solo), numero en regresion.
#     - Columnas REF_*   -> metadatos de trazabilidad. NO son features, se separan.
#     - El resto         -> features numericas.
#
from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd

from .. import submodulo

config = submodulo("00_fundamentos.config")

COLUMNA_OBJETIVO = "Y"
PREFIJO_REFERENCIA = "REF_"


# El texto CSV no cumple la convencion de columnas esperada.
class DatasetError(ValueError):
    pass


# Un dataset ya separado en features (X), objetivo (y, None si no supervisado)
# y referencias.
#     n_filas / n_features: tamano de X.
#     es_clasificacion: True si el objetivo es categorico (False si y es None).
@dataclass
class Dataset:
    nombre: str
    X: pd.DataFrame
    y: pd.Series | None
    referencias: pd.DataFrame
    archivo_fuente: str | None = None

    @property
    def n_filas(self) -> int:
        return len(self.X)

    @property
    def n_features(self) -> int:
        return self.X.shape[1]

    @property
    def es_clasificacion(self) -> bool:
        return self.y is not None and not pd.api.types.is_numeric_dtype(self.y)


# Arma un Dataset a partir de texto CSV (';' como separador) ya en memoria.
#     - Descarta filas sin objetivo; rellena features ausentes con config.RELLENO_FEATURES.
#     - requiere_objetivo=False (no supervisado): no exige la columna Y (y queda None).
#     - Lanza DatasetError si falta Y (y se exige) o quedan features no numericas.
def desde_texto(nombre: str, texto_csv: str, requiere_objetivo: bool = True,
                archivo_fuente: str | None = None) -> Dataset:
    df = pd.read_csv(io.StringIO(texto_csv), sep=";")
    tiene_y = COLUMNA_OBJETIVO in df.columns
    if requiere_objetivo and not tiene_y:
        raise DatasetError(f"{nombre}: falta la columna objetivo {COLUMNA_OBJETIVO!r}.")

    columna_id = df.columns[0]
    df = df.set_index(columna_id)

    y = df[COLUMNA_OBJETIVO] if (tiene_y and requiere_objetivo) else None
    referencias = df[[c for c in df.columns if c.startswith(PREFIJO_REFERENCIA)]]
    features = df[[c for c in df.columns
                   if c != COLUMNA_OBJETIVO and not c.startswith(PREFIJO_REFERENCIA)]]

    if features.shape[1] == 0:
        raise DatasetError(f"{nombre}: no se detecto ninguna feature.")

    no_numericas = [c for c in features.columns
                    if not pd.api.types.is_numeric_dtype(features[c])]
    if no_numericas:
        raise DatasetError(f"{nombre}: features no numericas: {no_numericas[:10]}")

    if y is not None and y.isna().any():
        validas = y.notna()
        features, y, referencias = features[validas], y[validas], referencias[validas]
    if features.isna().any().any():
        features = features.fillna(config.RELLENO_FEATURES)

    return Dataset(
        nombre=nombre, X=features, y=y, referencias=referencias,
        archivo_fuente=archivo_fuente,
    )
