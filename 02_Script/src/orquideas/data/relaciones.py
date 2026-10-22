"""Verificacion de claves foraneas y cardinalidades antes de combinar tablas."""
from __future__ import annotations

import pandas as pd

from .catalogos import CATALOGOS, FK_DATASET, cargar_catalogo
from .dataset import cargar_dataset


def verificar_fks_catalogos() -> pd.DataFrame:
    """Para cada FK entre catalogos: valores huerfanos y cardinalidad observada."""
    filas = []
    for cat in CATALOGOS.values():
        df = cargar_catalogo(cat.nombre)
        for col, ref in cat.fks.items():
            ref_df = cargar_catalogo(ref)
            pks = set(ref_df[CATALOGOS[ref].pk])
            huerf = sorted(set(df[col]) - pks)
            card = df.groupby(col).size()
            filas.append({"tabla": cat.nombre, "columna": col, "referencia": ref, "filas": len(df),
                          "valores_distintos": df[col].nunique(), "huerfanos": len(huerf), "ejemplo_huerfanos": huerf[:5],
                          "max_filas_por_valor": int(card.max()), "relacion": f"N:1 ({cat.nombre} -> {ref})"})
    return pd.DataFrame(filas)


def verificar_fks_dataset() -> pd.DataFrame:
    df = cargar_dataset()
    filas = []
    for col, ref in FK_DATASET.items():
        pks = set(cargar_catalogo(ref)[CATALOGOS[ref].pk])
        vals = pd.Series(df[col].unique())
        huerf = sorted(set(vals) - pks)
        filas.append({"columna": col, "referencia": ref, "valores_distintos": len(vals), "huerfanos": len(huerf),
                      "ejemplo_huerfanos": huerf[:5], "pct_cero": round(100 * float((df[col] == 0).mean()), 2)})
    return pd.DataFrame(filas)


def verificar_consistencia_jerarquica() -> pd.DataFrame:
    """Comprueba que la cadena taxonomica del Dataset coincide con la de los catalogos y que cada muestra
    tiene un unico conjunto de atributos (lote, especie, parte, tipo, cultivo, metodo)."""
    df = cargar_dataset()
    res = []
    esp = cargar_catalogo("especies").merge(cargar_catalogo("generos"), on="ID_GENERO", suffixes=("", "_g"))
    gen_fam = dict(zip(cargar_catalogo("generos")["ID_GENERO"], cargar_catalogo("generos")["ID_FAMILIA"]))
    esp_gen = dict(zip(esp["ID_ESPECIE"], esp["ID_GENERO"]))
    sub = df[["ID_ESPECIE", "ID_GENERO", "ID_FAMILIA"]].drop_duplicates()
    sub = sub[sub["ID_ESPECIE"] > 0]
    mal_gen = sub[sub["ID_ESPECIE"].map(esp_gen) != sub["ID_GENERO"]]
    mal_fam = sub[sub["ID_GENERO"].map(gen_fam) != sub["ID_FAMILIA"]]
    res.append({"chequeo": "especie->genero coherente con catalogo", "inconsistencias": len(mal_gen)})
    res.append({"chequeo": "genero->familia coherente con catalogo", "inconsistencias": len(mal_fam)})
    attrs = ["ID_BATCH", "ID_ESPECIE", "ID_PARTE_ESTUDIADA", "ID_TIPO_MUESTRA", "ID_TIPO_CULTIVO", "ID_METODO_EXTRACCION"]
    por_muestra = df[["ID_MUESTRA"] + attrs].drop_duplicates().groupby("ID_MUESTRA").size()
    res.append({"chequeo": "muestra con atributos unicos", "inconsistencias": int((por_muestra > 1).sum())})
    mu = cargar_catalogo("muestras").set_index("ID_MUESTRA")
    d2 = df.loc[df["ID_MUESTRA"] > 0, ["ID_MUESTRA"] + attrs].drop_duplicates().set_index("ID_MUESTRA")
    comun = d2.index.intersection(mu.index)
    dif = (d2.loc[comun, attrs] != mu.loc[comun, attrs]).any(axis=1).sum()
    res.append({"chequeo": "atributos de muestra iguales en Dataset y 06_Muestras_Batch (ID_MUESTRA>0)", "inconsistencias": int(dif)})
    res.append({"chequeo": "filas con ID_MUESTRA=0 (senal sin valores por muestra; atributos a nivel de lote)",
                "inconsistencias": int((df["ID_MUESTRA"] == 0).sum())})
    art = dict(zip(cargar_catalogo("batches")["ID_BATCH"], cargar_catalogo("batches")["ID_ARTICULO"]))
    ba = df[["ID_BATCH", "ID_ARTICULO"]].drop_duplicates()
    res.append({"chequeo": "lote->articulo coherente con 02_Batches", "inconsistencias": int((ba["ID_BATCH"].map(art) != ba["ID_ARTICULO"]).sum())})
    return pd.DataFrame(res)
