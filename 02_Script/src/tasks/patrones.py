"""Modelo central de patrones quimicos (no supervisado, asociacion y estadistica de enriquecimiento).

Unidad base: especie x articulo x parte de la planta (suma de las muestras biologicas que comparten esos atributos).
Agregar reduce la pseudorreplicacion: decenas de replicas de un mismo extracto no cuentan como evidencia independiente.
Todos los contrastes entre niveles taxonomicos exigen que cada nivel este representado en >= 2 articulos.
"""
from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score, silhouette_score
from statsmodels.stats.multitest import multipletests

from ..data.catalogos import cargar_catalogo, mapa_etiquetas
from ..features.conjuntos import CATALOGO_DE
from ..features.perfiles import agregar, clr, conteos_por_muestra, presencias, tabla_muestras
from ..utils.es import guardar_json, guardar_tabla
from ..visualization import graficas

UNIDAD = ["ID_ARTICULO", "ID_ESPECIE", "ID_PARTE_ESTUDIADA"]


def _nombre(col: str, v: Any) -> str:
    return mapa_etiquetas(CATALOGO_DE[col]).get(int(v), str(v)) if col in CATALOGO_DE else str(v)


def _nombre_cat(c: str) -> str:
    """'superclase_7' -> nombre de la superclase; 'clase_123' -> nombre de la clase."""
    if c.endswith("_otras"):
        return "Otras"
    nivel, k = c.rsplit("_", 1)
    return mapa_etiquetas("superclases" if nivel == "superclase" else "clases_quim").get(int(k), c)


def unidades(nivel: str, min_metabolitos: int, min_articulos: int, max_categorias: int | None
             ) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = conteos_por_muestra(nivel, min_articulos, max_categorias)
    meta = tabla_muestras().loc[c.index]
    c, m = agregar(c, meta, UNIDAD)
    keep = c.sum(axis=1) >= min_metabolitos
    return c[keep], m[keep]


def _bh(p: pd.Series) -> np.ndarray:
    return multipletests(p.fillna(1).to_numpy(), method="fdr_bh")[1] if len(p) else np.array([])


# ---------------------------------------------------------------------------------------------------------------------
def enriquecimiento(c: pd.DataFrame, m: pd.DataFrame, factores: list[str], salida: dict[str, Path], alfa: float,
                    hall: list[str]) -> None:
    """Cada nivel del factor frente al resto: Mann-Whitney sobre CLR por unidad; q de Benjamini-Hochberg."""
    X0 = clr(c)
    for f in factores:
        art = m.groupby(f)["ID_ARTICULO"].nunique()
        niveles = [v for v in art.index if v > 0 and art[v] >= 2]
        # la unidad de contraste es (articulo, nivel): las unidades de un mismo estudio no son independientes
        clave = m["ID_ARTICULO"].astype(str) + "|" + m[f].astype(str)
        X = X0.groupby(clave.to_numpy()).mean()
        nivel_de = m.groupby(clave.to_numpy())[f].first().loc[X.index]
        filas = []
        for v in niveles:
            dentro = (nivel_de == v).to_numpy()
            for col in X.columns:
                a, b = X.loc[dentro, col], X.loc[~dentro, col]
                if a.nunique() + b.nunique() <= 2:
                    continue
                p = mannwhitneyu(a, b, alternative="two-sided").pvalue
                filas.append({"factor": f, "nivel": _nombre(f, v), "categoria": _nombre_cat(col), "variable": col,
                              "n_articulos_nivel": int(dentro.sum()), "n_articulos_resto": int((~dentro).sum()),
                              "efecto_mediana_clr": float(a.median() - b.median()), "p": p})
        t = pd.DataFrame(filas)
        if t.empty:
            hall.append(f"Enriquecimiento por {f}: ningun nivel aparece en >= 2 articulos.")
            continue
        t["q"] = _bh(t["p"])
        t = t.sort_values("q")
        guardar_tabla(t, salida["tablas"] / f"enriquecimiento_{f}.csv")
        sig = t[t["q"] < alfa]
        hall.append(f"Enriquecimiento por {f}: {len(niveles)} niveles con >= 2 articulos; {len(sig)} de {len(t)} contrastes "
                    f"con q < {alfa}." + (" Mas fuertes: " + "; ".join(
                        f"{r.categoria} {'mayor' if r.efecto_mediana_clr > 0 else 'menor'} en {r.nivel} (q={r.q:.2g})"
                        for r in sig.head(4).itertuples()) if len(sig) else ""))
        if len(sig):
            piv = t.pivot_table(index="categoria", columns="nivel", values="efecto_mediana_clr")
            piv = piv.where(t.pivot_table(index="categoria", columns="nivel", values="q") < alfa)
            piv = piv.dropna(how="all").dropna(axis=1, how="all")
            if not piv.empty:
                graficas.mapa_calor(piv.fillna(0), salida["graficas"] / f"enriquecimiento_{f}.png",
                                    f"Categorias quimicas enriquecidas por {f} (q < {alfa})", f.replace("ID_", ""),
                                    "Categoria quimica", cmap="RdBu_r", center=0, cbar_label="Diferencia de medianas CLR",
                                    nota="Rojo = categoria mas representada en ese nivel que en el resto; azul = menos. "
                                         "Solo celdas significativas tras BH; unidad de contraste = articulo x nivel (>= 2 articulos por nivel).")


def _curveball(B: np.ndarray, n_intercambios: int, rng: np.random.Generator) -> np.ndarray:
    """Aleatoriza una matriz 0/1 conservando los totales de filas y columnas (Strona et al. 2014)."""
    filas = [set(np.flatnonzero(r)) for r in B]
    n = len(filas)
    for _ in range(n_intercambios):
        a, b = rng.choice(n, 2, replace=False)
        sa, sb = filas[a], filas[b]
        solo_a, solo_b = list(sa - sb), list(sb - sa)
        if not solo_a or not solo_b:
            continue
        pool = solo_a + solo_b
        rng.shuffle(pool)
        na = len(solo_a)
        comun = sa & sb
        filas[a] = comun | set(pool[:na])
        filas[b] = comun | set(pool[na:])
    out = np.zeros_like(B)
    for i, f in enumerate(filas):
        out[i, list(f)] = 1
    return out


def coocurrencia(pres: pd.DataFrame, salida: dict[str, Path], alfa: float, max_aristas: int, n_nulos: int, semilla: int,
                 hall: list[str]) -> None:
    """Pares de categorias que coaparecen mas de lo esperado dado cuantas categorias tiene cada unidad (riqueza,
    reflejo de la profundidad de anotacion del laboratorio) y cuan comun es cada categoria: nulo curveball."""
    import networkx as nx
    B = pres.to_numpy(np.int8)
    B = B[:, (B.sum(0) >= 3) & (B.sum(0) < len(B))]
    cols = [c for c, ok in zip(pres.columns, (pres.sum(0) >= 3) & (pres.sum(0) < len(pres))) if ok]
    obs = B.T.astype(int) @ B.astype(int)
    rng = np.random.default_rng(semilla)
    mayor = np.zeros_like(obs, dtype=int)
    suma = np.zeros_like(obs, dtype=float)
    suma2 = np.zeros_like(obs, dtype=float)
    Bn = B.copy()
    for _ in range(n_nulos):
        Bn = _curveball(Bn, 5 * len(B), rng)
        nul = Bn.T.astype(int) @ Bn.astype(int)
        mayor += nul >= obs
        suma += nul
        suma2 += nul.astype(float) ** 2
    media = suma / n_nulos
    de = np.sqrt(np.maximum(suma2 / n_nulos - media ** 2, 1e-9))
    filas = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            filas.append({"a": _nombre_cat(cols[i]), "b": _nombre_cat(cols[j]), "n_ambos": int(obs[i, j]),
                          "esperado_nulo": float(media[i, j]), "z": float((obs[i, j] - media[i, j]) / de[i, j]),
                          "jaccard": float(obs[i, j] / max(obs[i, i] + obs[j, j] - obs[i, j], 1)),
                          "p": float((1 + mayor[i, j]) / (1 + n_nulos))})
    t = pd.DataFrame(filas)
    if t.empty:
        hall.append("Coocurrencia: no hay pares evaluables.")
        return
    t["q"] = _bh(t["p"])
    t = t.sort_values(["q", "z"], ascending=[True, False])
    guardar_tabla(t, salida["tablas"] / "coocurrencia_categorias.csv")
    sig = t[(t["q"] < alfa) & (t["z"] > 0)].head(max_aristas)
    hall.append(f"Coocurrencia (nulo curveball que conserva la riqueza de cada unidad, {n_nulos} aleatorizaciones): "
                f"{int(((t['q'] < alfa) & (t['z'] > 0)).sum())} de {len(t)} pares de clases quimicas coaparecen mas de lo "
                f"esperado (q < {alfa})." + (" Mas fuertes: " + "; ".join(f"{r.a} + {r.b} (z={r.z:.1f})"
                                                                      for r in sig.head(4).itertuples()) if len(sig) else ""))
    if len(sig):
        import matplotlib.pyplot as plt
        G = nx.Graph()
        for r in sig.itertuples():
            G.add_edge(r.a[:30], r.b[:30], weight=r.z)
        fig, ax = plt.subplots(figsize=(11, 9))
        pos = nx.spring_layout(G, seed=42, k=0.6)
        w = np.array([G[u][v]["weight"] for u, v in G.edges])
        nx.draw_networkx_edges(G, pos, ax=ax, width=1 + 3 * w / max(w.max(), 1), alpha=0.4, edge_color="#555")
        deg = dict(G.degree)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=[80 + 40 * deg[k] for k in G.nodes], node_color="#2a9d8f")
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=7)
        ax.set_title("Red de coocurrencia de clases quimicas (q < %.2f, nulo curveball)" % alfa); ax.axis("off")
        ax.plot([], [], color="#555", lw=3, label="Grosor = z frente al nulo"); ax.legend(loc="lower left", fontsize=8)
        graficas.guardar(fig, salida["graficas"] / "red_coocurrencia.png",
                         nota="Aristas = clases que coaparecen en unidades especie x articulo x parte mas de lo esperado "
                              "conservando la riqueza de cada unidad. Bibliotecas compartidas pueden inducir coocurrencias.")
        nx.write_graphml(G, salida["tablas"] / "red_coocurrencia.graphml")


def reglas(pres: pd.DataFrame, m: pd.DataFrame, cfg: dict[str, Any], salida: dict[str, Path], hall: list[str]) -> None:
    """(a) FP-growth entre clases quimicas; (b) reglas taxon -> clase quimica con soporte en >= 2 articulos."""
    from mlxtend.frequent_patterns import association_rules, fpgrowth
    T = pres.astype(bool).copy()
    T.columns = [_nombre_cat(c)[:45] for c in T.columns]
    T = T.loc[:, ~T.columns.duplicated()]
    T = T.loc[:, T.mean() <= cfg.get("max_soporte_item", 0.8)]   # items casi universales no informan
    fi = fpgrowth(T, min_support=cfg.get("min_soporte", 0.2), use_colnames=True, max_len=cfg.get("max_longitud", 3))
    cols = ["antecedentes", "consecuentes", "support", "confidence", "lift"]
    n_r = 0
    if not fi.empty:
        r = association_rules(fi, metric="confidence", min_threshold=cfg.get("min_confianza", 0.9))
        r = r[r["lift"] >= cfg.get("min_lift", 1.5)].sort_values(["lift", "confidence"], ascending=False)
        r["antecedentes"] = r["antecedents"].map(lambda s: " + ".join(sorted(s)))
        r["consecuentes"] = r["consequents"].map(lambda s: " + ".join(sorted(s)))
        n_r = len(r)
        guardar_tabla(r[cols].head(cfg.get("max_reglas_guardadas", 2000)), salida["tablas"] / "reglas_asociacion_quimica.csv")
    # taxon -> clase quimica
    filas = []
    for f in cfg.get("items_taxonomicos", ["ID_ORDEN", "ID_FAMILIA"]):
        art = m.groupby(f)["ID_ARTICULO"].nunique()
        for v in art[(art >= 2) & (art.index > 0)].index:
            dentro = (m[f] == v).to_numpy()
            for c in T.columns:
                tiene = T[c].to_numpy()
                n_ab = int((dentro & tiene).sum())
                arts_ab = m.loc[dentro & tiene, "ID_ARTICULO"].nunique()
                if arts_ab < 2:
                    continue
                conf = n_ab / dentro.sum()
                lift = conf / tiene.mean()
                filas.append({"antecedentes": f"{f.replace('ID_', '')}={_nombre(f, v)}", "consecuentes": c,
                              "support": n_ab / len(T), "confidence": conf, "lift": lift, "articulos": arts_ab})
    tx = pd.DataFrame(filas)
    if not tx.empty:
        tx = tx[(tx["confidence"] >= cfg.get("min_confianza_taxon", 0.8)) & (tx["lift"] >= cfg.get("min_lift", 1.5))]
        tx = tx.sort_values(["lift", "confidence"], ascending=False)
        guardar_tabla(tx, salida["tablas"] / "reglas_taxon_a_quimica.csv")
    hall.append(f"Reglas de asociacion: {n_r} reglas entre clases quimicas (soporte >= {cfg.get('min_soporte', 0.2)}, "
                f"confianza >= {cfg.get('min_confianza', 0.9)}, lift >= {cfg.get('min_lift', 1.5)}); {len(tx)} reglas taxon -> "
                "clase quimica sostenidas por >= 2 articulos." +
                (" Ejemplos: " + "; ".join(f"{a} => {b} (conf {c:.2f}, lift {l:.2f}, {n} art.)" for a, b, c, l, n in
                                          tx[["antecedentes", "consecuentes", "confidence", "lift", "articulos"]].head(4)
                                          .itertuples(index=False)) if len(tx) else ""))


def agrupamiento(X: pd.DataFrame, m: pd.DataFrame, cfg: dict[str, Any], salida: dict[str, Path], semilla: int,
                 hall: list[str]) -> np.ndarray:
    pca = PCA(n_components=min(5, X.shape[1]), random_state=semilla).fit(X)
    Z = pca.transform(X)
    ev = pca.explained_variance_ratio_
    orden = m["ID_ORDEN"].map(lambda v: _nombre("ID_ORDEN", v))
    columna = m["ID_COLUMNA_CROMATOGRAFICA"].map(lambda v: _nombre("ID_COLUMNA_CROMATOGRAFICA", v)[:35])
    for etq, nom in [(orden, "orden"), (columna, "columna")]:
        graficas.dispersion_2d(Z[:, :2], etq, salida["graficas"] / f"pca_unidades_por_{nom}.png",
                               f"PCA del perfil quimico (CLR) coloreado por {nom}", f"PC1 ({ev[0]:.0%})", f"PC2 ({ev[1]:.0%})",
                               nota="Cada punto es una unidad especie x articulo x parte. Si los colores por columna "
                                    "cromatografica se separan mas que por orden, domina el efecto de plataforma.")
    ks = range(2, min(cfg.get("k_max", 8), len(X) - 1) + 1)
    sil = {k: silhouette_score(X, KMeans(k, n_init=10, random_state=semilla).fit_predict(X)) for k in ks}
    k = max(sil, key=sil.get)
    etiquetas = KMeans(k, n_init=10, random_state=semilla).fit_predict(X)
    rng = np.random.default_rng(semilla)
    aris = []
    for _ in range(cfg.get("n_bootstrap", 30)):
        idx = rng.choice(len(X), int(0.8 * len(X)), replace=False)
        e2 = KMeans(k, n_init=10, random_state=int(rng.integers(1e9))).fit_predict(X.iloc[idx])
        aris.append(adjusted_rand_score(etiquetas[idx], e2))
    ami_orden = adjusted_mutual_info_score(orden, etiquetas)
    ami_col = adjusted_mutual_info_score(columna, etiquetas)
    ami_art = adjusted_mutual_info_score(m["ID_ARTICULO"], etiquetas)
    guardar_tabla(pd.DataFrame({"k": list(sil), "silueta": list(sil.values())}), salida["tablas"] / "silueta_kmeans.csv")
    asign = m[UNIDAD].reset_index(drop=True)
    asign["cluster"] = etiquetas
    asign["especie"] = m["ID_ESPECIE"].map(lambda v: _nombre("ID_ESPECIE", v)).to_numpy()
    asign["orden"] = orden.to_numpy()
    asign["columna"] = columna.to_numpy()
    guardar_tabla(asign, salida["tablas"] / "clusters_unidades.csv")
    graficas.dispersion_2d(Z[:, :2], pd.Series([f"Cluster {e}" for e in etiquetas]),
                           salida["graficas"] / "pca_clusters_kmeans.png", f"K-means (k={k}) sobre el perfil quimico",
                           f"PC1 ({ev[0]:.0%})", f"PC2 ({ev[1]:.0%})",
                           nota=f"k elegido por silueta ({sil[k]:.2f}). Estabilidad bootstrap ARI = {np.mean(aris):.2f}. "
                                f"AMI con orden = {ami_orden:.2f}, con columna = {ami_col:.2f}, con articulo = {ami_art:.2f}.")
    hall.append(f"Agrupamiento: k={k} (silueta {sil[k]:.2f}), estabilidad ARI bootstrap {np.mean(aris):.2f} +/- {np.std(aris):.2f}. "
                f"Concordancia (AMI) de los clusters con orden taxonomico {ami_orden:.2f}, con columna cromatografica "
                f"{ami_col:.2f} y con articulo {ami_art:.2f}. PC1+PC2 explican {ev[:2].sum():.0%} de la varianza.")
    try:
        import umap
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            U = umap.UMAP(n_neighbors=min(15, len(X) - 1), random_state=semilla).fit_transform(X)
        graficas.dispersion_2d(U, orden, salida["graficas"] / "umap_unidades_por_orden.png",
                               "UMAP del perfil quimico coloreado por orden", "UMAP 1", "UMAP 2",
                               nota="Proyeccion no lineal; las distancias globales entre grupos no son interpretables.")
    except Exception:  # noqa: BLE001
        pass
    return Z


def _r2(X: np.ndarray, g: np.ndarray) -> float:
    """R2 de PERMANOVA con distancia euclidea (Aitchison sobre CLR) = SS entre grupos / SS total."""
    mu = X.mean(0)
    sst = ((X - mu) ** 2).sum()
    ssw = sum(((X[g == k] - X[g == k].mean(0)) ** 2).sum() for k in np.unique(g))
    return 1 - ssw / sst if sst > 0 else 0.0


def particion_varianza(X: pd.DataFrame, m: pd.DataFrame, factores: list[str], n_perm: int, semilla: int,
                       salida: dict[str, Path], hall: list[str], estratos: pd.Series | None = None, sufijo: str = "") -> None:
    rng = np.random.default_rng(semilla)
    Xn = X.to_numpy(float)
    if estratos is not None:  # se elimina la media de cada articulo: solo queda la variacion intra-estudio
        Xn = Xn - X.groupby(estratos.to_numpy()).transform("mean").to_numpy(float)
    filas = []
    for f in factores:
        g = m[f].astype(str).to_numpy()
        if len(np.unique(g)) < 2:
            continue
        r2 = _r2(Xn, g)
        k = len(np.unique(g))
        r2_adj = 1 - (1 - r2) * (len(g) - 1) / max(len(g) - k, 1)
        art = m["ID_ARTICULO"].to_numpy()
        constante = estratos is None and f != "ID_ARTICULO" and (m.groupby("ID_ARTICULO")[f].nunique() == 1).all()
        if constante:  # el factor no varia dentro del articulo: se permutan articulos completos
            lab_art = pd.Series(g, index=art).groupby(level=0).first()
        nulos = []
        for _ in range(n_perm):
            if constante:
                gp = pd.Series(rng.permutation(lab_art.to_numpy()), index=lab_art.index).loc[art].to_numpy()
            elif estratos is None:
                gp = rng.permutation(g)
            else:  # permutacion dentro de cada articulo (contraste intra-estudio)
                gp = g.copy()
                for s in np.unique(estratos):
                    i = np.where(estratos.to_numpy() == s)[0]
                    gp[i] = rng.permutation(g[i])
            nulos.append(_r2(Xn, gp))
        filas.append({"factor": f, "niveles": k, "R2": r2, "R2_ajustado": r2_adj, "R2_nulo_medio": float(np.mean(nulos)),
                      "permutacion": "por articulo" if constante else ("intra-articulo" if estratos is not None else "libre"),
                      "p": float((1 + np.sum(np.array(nulos) >= r2)) / (1 + n_perm))})
    t = pd.DataFrame(filas).sort_values("R2", ascending=False)
    guardar_tabla(t, salida["tablas"] / f"particion_varianza{sufijo}.csv")
    if not t.empty:
        graficas.barras(t.set_index("factor")["R2"], salida["graficas"] / f"particion_varianza{sufijo}.png",
                        f"Varianza del perfil quimico explicada por cada factor{' (intra-articulo)' if estratos is not None else ''}",
                        "Factor", "R2 (PERMANOVA, distancia de Aitchison)",
                        nota="R2 marginal de cada factor por separado. Los factores constantes dentro de un articulo (familia, "
                             "columna...) se contrastan permutando articulos completos; el R2 del articulo es casi 1 porque "
                             "hay ~2 unidades por articulo (ver R2 ajustado en la tabla).")
        hall.append(f"Particion de varianza{' intra-articulo' if estratos is not None else ''}: " +
                    "; ".join(f"{r.factor} R2={r.R2:.2f} (ajustado {r.R2_ajustado:.2f}, nulo {r.R2_nulo_medio:.2f}, p={r.p:.3f}, "
                              f"permutacion {r.permutacion})" for r in t.itertuples()) + ".")


def atipicos(X: pd.DataFrame, m: pd.DataFrame, Z: np.ndarray, semilla: int, salida: dict[str, Path], hall: list[str]) -> None:
    iso = IsolationForest(n_estimators=500, contamination="auto", random_state=semilla).fit(X)
    s = -iso.score_samples(X)
    t = m.reset_index()[UNIDAD].copy()
    t["especie"] = m["ID_ESPECIE"].map(lambda v: _nombre("ID_ESPECIE", v)).to_numpy()
    t["puntaje_atipicidad"] = s
    t["atipico"] = iso.predict(X) == -1
    t = t.sort_values("puntaje_atipicidad", ascending=False)
    guardar_tabla(t, salida["tablas"] / "unidades_atipicas.csv")
    graficas.dispersion_2d(Z[:, :2], pd.Series(np.where(iso.predict(X) == -1, "Atipica", "Tipica")),
                           salida["graficas"] / "pca_atipicos.png", "Unidades con perfil quimico atipico (Isolation Forest)",
                           "PC1", "PC2", nota="Atipico = perfil poco frecuente respecto al conjunto; puede reflejar una quimica "
                                              "singular o una biblioteca de anotacion distinta.")
    hall.append(f"Atipicos: {int(t['atipico'].sum())} de {len(t)} unidades; las mas atipicas: " +
                ", ".join(f"{r.especie} (art. {r.ID_ARTICULO})" for r in t.head(5).itertuples()) + ".")


def red_actividades(salida: dict[str, Path], alfa: float, hall: list[str]) -> None:
    """Superclase del metabolito x actividad citada (registro por metabolito): Fisher + BH y heatmap de conteos."""
    r = cargar_catalogo("registro_actividades")
    r = r[(r["ID_METABOLITO"] > 1) & (r["ID_ACTIVIDAD_BIOLOGICA"] > 0)]
    met = cargar_catalogo("metabolitos").set_index("ID_METABOLITO")["ID_CLASE_QUIMICA"]
    cq = cargar_catalogo("clases_quim").set_index("ID_CLASE_QUIMICA")["ID_SUPERCLASE_QUIMICA"]
    r = r.assign(SUP=r["ID_METABOLITO"].map(met).map(cq).fillna(0).astype(int))
    r = r[r["SUP"] > 0].drop_duplicates(["ID_METABOLITO", "ID_ACTIVIDAD_BIOLOGICA"])
    sup_n = mapa_etiquetas("superclases"); act_n = mapa_etiquetas("actividades")
    mets = r.drop_duplicates("ID_METABOLITO")[["ID_METABOLITO", "SUP"]]
    N = len(mets)
    filas = []
    for a, ga in r.groupby("ID_ACTIVIDAD_BIOLOGICA"):
        con = set(ga["ID_METABOLITO"])
        for s, gs in mets.groupby("SUP"):
            en = set(gs["ID_METABOLITO"])
            n11 = len(con & en); n10 = len(en - con); n01 = len(con - en); n00 = N - n11 - n10 - n01
            if n11 == 0:
                continue
            orr, p = fisher_exact([[n11, n10], [n01, n00]], alternative="greater")
            filas.append({"actividad": act_n.get(a, a), "superclase": sup_n.get(s, s), "metabolitos": n11,
                          "odds_ratio": orr, "p": p})
    t = pd.DataFrame(filas)
    if t.empty:
        return
    t["q"] = _bh(t["p"])
    guardar_tabla(t.sort_values("q"), salida["tablas"] / "enriquecimiento_superclase_actividad.csv")
    piv = t.pivot_table(index="superclase", columns="actividad", values="metabolitos", fill_value=0)
    graficas.mapa_calor(piv, salida["graficas"] / "red_superclase_actividad.png",
                        "Metabolitos con actividad citada por superclase quimica", "Actividad biologica", "Superclase",
                        cmap="YlOrRd", fmt=".0f", cbar_label="Numero de metabolitos",
                        nota=f"{N} metabolitos con actividad bibliografica registrada. Conteos de evidencia citada, no de "
                             "actividad medida; superclases muy estudiadas acumulan mas citas.")
    sig = t[t["q"] < alfa]
    hall.append(f"Red quimica-actividad: {N} metabolitos con actividad citada; {len(sig)} asociaciones superclase-actividad "
                f"enriquecidas (q < {alfa})" + (": " + "; ".join(f"{x.superclase} -> {x.actividad} (OR {x.odds_ratio:.1f}, "
                                                                   f"q={x.q:.2g})" for x in sig.sort_values('q').head(4).itertuples())
                                              if len(sig) else ".") )


def firma_familias(c: pd.DataFrame, m: pd.DataFrame, salida: dict[str, Path], hall: list[str],
                   min_articulos: int = 2) -> None:
    """Descriptivo: para cada familia botanica con >= min_articulos articulos, metabolitos presentes en todos sus
    articulos y su especificidad frente al resto de plantas."""
    fam = cargar_catalogo("familias").set_index("ID_FAMILIA")["FAMILIA"]
    tm = tabla_muestras()
    tm = tm[~tm["ID_TIPO_MUESTRA"].isin([9, 10])]
    arts_fam = tm.groupby("ID_FAMILIA")["ID_ARTICULO"].unique()
    arts_fam = arts_fam[arts_fam.map(len) >= min_articulos]
    if arts_fam.empty:
        hall.append(f"Firmas por familia: ninguna familia tiene >= {min_articulos} articulos con metabolitos identificados.")
        return
    p = presencias().merge(tm[["ID_ARTICULO", "ID_FAMILIA"]], left_on="ID_MUESTRA", right_index=True)
    metn = cargar_catalogo("metabolitos").set_index("ID_METABOLITO")
    cq = cargar_catalogo("clases_quim").set_index("ID_CLASE_QUIMICA")
    X = c.div(c.sum(axis=1), axis=0)
    tablas, comp, resumen = [], {}, []
    for id_fam, arts in arts_fam.items():
        nombre = fam.get(id_fam, str(id_fam))
        arts = sorted(arts)
        n_otros = p.loc[~p["ID_ARTICULO"].isin(arts), "ID_ARTICULO"].nunique()
        por_met = p.groupby("ID_METABOLITO").agg(
            articulos_familia=("ID_ARTICULO", lambda s: s[s.isin(arts)].nunique()),
            articulos_otros=("ID_ARTICULO", lambda s: s[~s.isin(arts)].nunique()))
        por_met = por_met[por_met["articulos_familia"] > 0]
        por_met["frac_otros_articulos"] = por_met["articulos_otros"] / max(n_otros, 1)
        por_met["metabolito"] = metn.loc[por_met.index, "NOMBRE_METABOLITO"]
        por_met["formula"] = metn.loc[por_met.index, "FORMULA_MOLECULAR"]
        por_met["clase"] = metn.loc[por_met.index, "ID_CLASE_QUIMICA"].map(cq["CLASE_QUIMICA"])
        por_met.insert(0, "familia", nombre)
        por_met.insert(1, "n_articulos_familia", len(arts))
        tablas.append(por_met.sort_values(["articulos_familia", "frac_otros_articulos"], ascending=[False, True]))
        esp = por_met[por_met["articulos_familia"] == len(arts)]
        resumen.append(f"{nombre} ({len(arts)} art.): {len(esp)} en todos sus articulos, "
                       f"{int((esp['frac_otros_articulos'] <= 0.1).sum())} en <= 10 % del resto")
        # composicion por superclase de las unidades de la familia frente al resto (descriptivo)
        es_fam = (m["ID_FAMILIA"] == id_fam).to_numpy()
        if es_fam.any() and (~es_fam).any():
            comp[nombre] = X[es_fam].mean() - X[~es_fam].mean()
    guardar_tabla(pd.concat(tablas).reset_index(), salida["tablas"] / "metabolitos_familias_especificidad.csv")
    if comp:
        dif = pd.DataFrame(comp)
        dif.index = [_nombre_cat(i) for i in dif.index]
        guardar_tabla(dif.reset_index(names="superclase"), salida["tablas"] / "composicion_familias_vs_resto.csv")
        graficas.mapa_calor(dif.T, salida["graficas"] / "composicion_familias_vs_resto.png",
                            "Familias vs resto: diferencia en la fraccion de metabolitos por superclase", "Superclase",
                            "Familia", cmap="RdBu_r", center=0, cbar_label="Fraccion en la familia - fraccion en el resto",
                            nota=f"Descriptivo: familias con >= {min_articulos} articulos. Con pocos estudios por familia no "
                                 "se puede separar la quimica de la familia del protocolo de cada laboratorio.")
    hall.append(f"Firmas por familia ({len(arts_fam)} familias con >= {min_articulos} articulos; candidatos a marcadores, "
                "a confirmar): " + "; ".join(resumen) + ".")


# ---------------------------------------------------------------------------------------------------------------------
def ejecutar(cfg: dict[str, Any], salida: dict[str, Path], log: logging.Logger) -> dict[str, Any]:
    semilla = cfg["semilla"]
    pc = cfg.get("patrones", {})
    alfa = pc.get("alfa", 0.05)
    hall: list[str] = []
    res: dict[str, Any] = {"tarea": "patrones", "notas": [
        "Unidad = especie x articulo x parte (suma de muestras biologicas). Perfil = conteo de metabolitos identificados "
        "por categoria quimica (CLR). Las intensidades no se comparan entre lotes."]}
    c, m = unidades("superclase", pc.get("min_metabolitos", 20), pc.get("min_articulos_categoria", 3), None)
    X = clr(c)
    res.update({"unidades": int(len(c)), "articulos": int(m["ID_ARTICULO"].nunique()),
                "especies": int(m["ID_ESPECIE"].nunique())})
    log.info(f"{len(c)} unidades, {m['ID_ARTICULO'].nunique()} articulos")
    guardar_tabla(c.assign(**{k: m[k] for k in UNIDAD}).reset_index(drop=True), salida["tablas"] / "perfil_unidades_superclase.csv")
    # auditoria de los datos de este modelo
    da = salida["auditoria"]
    upa = m.groupby("ID_ARTICULO").agg(unidades=("ID_ESPECIE", "size"), especies=("ID_ESPECIE", "nunique"),
                                       muestras=("N_MUESTRAS", "sum"), metabolitos_identificados=("N_IDENTIFICADOS", "sum"))
    guardar_tabla(upa.reset_index(), da / "unidades_por_articulo.csv")
    desc = c.describe().T
    desc.index = [_nombre_cat(i) for i in desc.index]
    guardar_tabla(desc.reset_index(names="superclase"), da / "descripcion_perfil_superclase.csv")
    guardar_json({"unidades": int(len(c)), "articulos": int(m["ID_ARTICULO"].nunique()),
                  "especies": int(m["ID_ESPECIE"].nunique()), "muestras": int(m["N_MUESTRAS"].sum()),
                  "categorias_superclase": int(c.shape[1]), "min_metabolitos_por_unidad": pc.get("min_metabolitos", 20)},
                 da / "resumen_datos.json")
    (da / "auditoria_datos.md").write_text(
        f"# Auditoria de datos - {cfg['id']}\n\nUnidades especie x articulo x parte: {len(c)} de "
        f"{m['ID_ARTICULO'].nunique()} articulos y {m['ID_ESPECIE'].nunique()} especies ({int(m['N_MUESTRAS'].sum())} muestras "
        f"biologicas). Perfil = numero de metabolitos identificados por superclase ({c.shape[1]} categorias).\n\n"
        "Archivos: `unidades_por_articulo.csv`, `descripcion_perfil_superclase.csv`, `resumen_datos.json`.\n",
        encoding="utf-8")
    a = pc.get("analisis", ["enriquecimiento", "coocurrencia", "reglas", "agrupamiento", "varianza", "atipicos",
                            "actividades", "familias"])
    if "enriquecimiento" in a:
        log.info("Enriquecimiento"); enriquecimiento(c, m, pc.get("factores_enriquecimiento", ["ID_ORDEN", "ID_FAMILIA",
                                                                                         "ID_PARTE_ESTUDIADA"]), salida, alfa, hall)
    if "coocurrencia" in a or "reglas" in a:
        cc, mc = unidades("clase", pc.get("min_metabolitos", 20), pc.get("min_articulos_clase", 5), pc.get("max_clases", 60))
        pres = (cc.drop(columns=[x for x in cc.columns if x.endswith("_otras")]) > 0).astype(int)
        if "coocurrencia" in a:
            log.info("Coocurrencia"); coocurrencia(pres, salida, alfa, pc.get("max_aristas", 120), pc.get("n_nulos", 300),
                                                 semilla, hall)
        if "reglas" in a:
            log.info("Reglas"); reglas(pres, mc, pc.get("reglas", {}), salida, hall)
    Z = None
    if "agrupamiento" in a:
        log.info("Agrupamiento"); Z = agrupamiento(X, m, pc.get("agrupamiento", {}), salida, semilla, hall)
    if "varianza" in a:
        log.info("Particion de varianza")
        particion_varianza(X, m, ["ID_ARTICULO", "ID_COLUMNA_CROMATOGRAFICA", "ID_METODO_EXTRACCION", "ID_ORDEN", "ID_FAMILIA",
                                  "ID_CLASE_TAXONOMICA", "ID_PARTE_ESTUDIADA"], pc.get("n_permutaciones", 499), semilla,
                           salida, hall)
        # intra-articulo: muestras de articulos con >= 2 partes/tipos/cultivos
        cs = conteos_por_muestra("superclase", pc.get("min_articulos_categoria", 3), None)
        cs = cs[cs.sum(axis=1) >= pc.get("min_metabolitos", 20)]
        ms = tabla_muestras().loc[cs.index]
        ms = ms[~ms["ID_TIPO_MUESTRA"].isin([9, 10])]
        cs = cs.loc[ms.index]
        for f in ["ID_PARTE_ESTUDIADA", "ID_TIPO_CULTIVO", "ID_ESPECIE"]:
            var = ms.groupby("ID_ARTICULO")[f].nunique()
            arts = var[var >= 2].index
            if len(arts) == 0:
                continue
            sel = ms["ID_ARTICULO"].isin(arts)
            particion_varianza(clr(cs[sel]), ms[sel], [f], pc.get("n_permutaciones", 499), semilla, salida, hall,
                               estratos=ms.loc[sel, "ID_ARTICULO"], sufijo=f"_intra_{f}")
    if "atipicos" in a:
        log.info("Atipicos")
        if Z is None:
            Z = PCA(n_components=2, random_state=semilla).fit_transform(X)
        atipicos(X, m, Z, semilla, salida, hall)
    if "actividades" in a:
        log.info("Red de actividades"); red_actividades(salida, alfa, hall)
    if "familias" in a:
        log.info("Firmas por familia"); firma_familias(c, m, salida, hall, pc.get("min_articulos_familia", 2))
    res["hallazgos"] = hall
    res["estado"] = "completado"
    guardar_json(res, salida["metricas"] / "resumen_patrones.json")
    for h in hall:
        log.info(f"  - {h}")
    return res
