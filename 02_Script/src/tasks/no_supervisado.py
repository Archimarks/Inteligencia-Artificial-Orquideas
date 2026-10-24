"""Entrenamiento no supervisado de un experimento supervisado: las mismas unidades, sin usar el objetivo.

Se agrupan las unidades (K-means y jerarquico de Ward sobre componentes principales), se elige el numero de grupos
por silueta, se mide la estabilidad de los grupos con remuestreo y se buscan unidades atipicas (Isolation Forest).
Solo despues se compara la particion encontrada con las referencias del YAML (`no_supervisado.referencias`): el
objetivo del supervisado, el articulo u otros atributos de la unidad. La pregunta es complementaria a la del
supervisado: ¿la estructura natural de los datos sigue al objetivo, o sigue al articulo/plataforma?

Configuracion (config/modelos/<ID>.yaml, valores por defecto en config_global.yaml):

    no_supervisado:
      activo: true
      matriz: entrada                  # entrada = variables X | objetivo = matriz multietiqueta (p. ej. M16)
      referencias: [objetivo, grupos]  # objetivo, grupos o columnas de la unidad (ID_FAMILIA, ID_ARTICULO, ...)
      componentes: 10                  # componentes principales tras estandarizar
      metodos: [kmeans, jerarquico]
      k_min: 2
      k_max: 10
      n_bootstrap: 20                  # remuestreos para la estabilidad
      contaminacion: 0.05              # fraccion esperada de atipicos
      max_unidades: 30000              # submuestra estratificada si hay mas unidades
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from ..features.conjuntos import Conjunto
from ..utils.es import guardar_json, guardar_tabla
from ..visualization import graficas

POR_DEFECTO: dict[str, Any] = {"activo": True, "matriz": "entrada", "referencias": ["objetivo", "grupos"],
                               "componentes": 10, "metodos": ["kmeans", "jerarquico"], "k_min": 2, "k_max": 10,
                               "n_bootstrap": 20, "contaminacion": 0.05, "max_unidades": 30000}
METODOS = {"kmeans", "jerarquico"}
MAX_JERARQUICO = 12000          # Ward necesita memoria cuadratica
MAX_SILUETA = 5000              # la silueta se estima sobre una muestra
MAX_GRUPOS_REFERENCIA = 300     # referencias con mas categorias (p. ej. formula) no son comparables
UMBRAL_SILUETA = 0.10
UMBRAL_ESTABILIDAD = 0.50
UMBRAL_ASOCIACION = 0.05


def configuracion(cfg: dict[str, Any]) -> dict[str, Any]:
    return {**POR_DEFECTO, **(cfg.get("no_supervisado") or {})}


def activo(cfg: dict[str, Any]) -> bool:
    """Solo si el YAML tiene bloque no_supervisado (python main.py datos --escribir-yaml lo anade)."""
    return (cfg.get("tarea") == "supervisado" and isinstance(cfg.get("no_supervisado"), dict)
            and bool(configuracion(cfg).get("activo")))


def validar(cfg: dict[str, Any]) -> list[str]:
    ns = cfg.get("no_supervisado")
    if ns is None:
        return []
    if not isinstance(ns, dict):
        return ["no_supervisado debe ser un diccionario"]
    if cfg.get("tarea") != "supervisado":
        return ["no_supervisado solo aplica a experimentos supervisados (tarea: patrones ya es no supervisado)"]
    e = [f"no_supervisado.{k} no es valida; opciones: {sorted(POR_DEFECTO)}" for k in ns if k not in POR_DEFECTO]
    c = {**POR_DEFECTO, **ns}
    if c["matriz"] not in ("entrada", "objetivo"):
        e.append("no_supervisado.matriz debe ser 'entrada' u 'objetivo'")
    if not isinstance(c["metodos"], list) or not c["metodos"] or set(c["metodos"]) - METODOS:
        e.append(f"no_supervisado.metodos debe ser una lista con {sorted(METODOS)}")
    if not isinstance(c["referencias"], list) or not all(isinstance(r, str) for r in c["referencias"]):
        e.append("no_supervisado.referencias debe ser una lista (objetivo, grupos o columnas de la unidad)")
    if not (2 <= int(c["k_min"]) <= int(c["k_max"])):
        e.append("no_supervisado: se requiere 2 <= k_min <= k_max")
    if c["matriz"] == "objetivo" and "objetivo" in (c["referencias"] or []):
        e.append("no_supervisado: con matriz 'objetivo' no se puede usar 'objetivo' como referencia (seria circular)")
    if not 0 < float(c["contaminacion"]) < 0.5:
        e.append("no_supervisado.contaminacion debe estar entre 0 y 0.5")
    return e


# ---------------------------------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------------------------------
def _v_cramer(a: np.ndarray, b: np.ndarray) -> float:
    t = pd.crosstab(a, b).to_numpy()
    if t.shape[0] < 2 or t.shape[1] < 2:
        return 0.0
    chi2 = chi2_contingency(t, correction=False)[0]
    return float(np.sqrt(chi2 / (t.sum() * (min(t.shape) - 1))))


def _pureza(grupos: np.ndarray, ref: np.ndarray) -> float:
    t = pd.crosstab(grupos, ref)
    return float(t.max(axis=1).sum() / t.to_numpy().sum())


def _submuestra(n: int, maximo: int, estratos: np.ndarray | None, rng: np.random.Generator) -> np.ndarray:
    if n <= maximo:
        return np.arange(n)
    if estratos is None:
        return np.sort(rng.choice(n, maximo, replace=False))
    s = pd.Series(estratos)
    frac = maximo / n
    idx = s.groupby(s, group_keys=False).apply(
        lambda g: g.sample(max(1, int(round(len(g) * frac))), random_state=int(rng.integers(1e9)))).index
    return np.sort(idx.to_numpy())


def _ajustar(metodo: str, Z: np.ndarray, k: int, semilla: int) -> np.ndarray:
    if metodo == "kmeans":
        return KMeans(k, n_init=10, random_state=semilla).fit_predict(Z)
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(Z)


def _silueta(Z: np.ndarray, e: np.ndarray, semilla: int) -> float:
    if len(set(e)) < 2:
        return float("nan")
    return float(silhouette_score(Z, e, sample_size=min(len(Z), MAX_SILUETA), random_state=semilla))


def _referencias(conj: Conjunto, nombres: list[str], idx: np.ndarray, multi: bool) -> dict[str, pd.DataFrame | pd.Series]:
    """Referencias externas para evaluar los grupos (solo se usan despues de agrupar)."""
    out: dict[str, Any] = {}
    meta = conj.meta.reset_index(drop=True)
    for r in nombres:
        if r == "objetivo":
            y = conj.y.iloc[idx].reset_index(drop=True)
            nombre = "objetivo" if multi else f"objetivo ({conj.y.name})"
            if multi:
                y.columns = [conj.etiquetas.get(c, str(c)) for c in y.columns]
                out[nombre] = y
            else:
                out[nombre] = y.map(lambda v: conj.etiquetas.get(v, str(v)))
        elif r == "grupos":
            g = conj.grupos.iloc[idx].reset_index(drop=True).astype(str)
            if g.nunique() <= MAX_GRUPOS_REFERENCIA:
                out[f"grupos ({conj.grupos.name})"] = g
        elif r in meta.columns:
            v = meta[r].iloc[idx].reset_index(drop=True)
            if 1 < v.nunique() <= MAX_GRUPOS_REFERENCIA:
                out[r] = v.astype(str)
    return out


def _asociacion(e: np.ndarray, ref: pd.Series | pd.DataFrame) -> dict[str, float]:
    """Concordancia entre los grupos encontrados y una referencia (multiclase o multietiqueta)."""
    if isinstance(ref, pd.DataFrame):   # multietiqueta: media por etiqueta
        vals = [adjusted_mutual_info_score(ref[c].to_numpy(), e) for c in ref.columns if ref[c].nunique() > 1]
        vcs = [_v_cramer(e, ref[c].to_numpy()) for c in ref.columns if ref[c].nunique() > 1]
        return {"ami": float(np.mean(vals)) if vals else float("nan"), "ari": float("nan"),
                "v_cramer": float(np.mean(vcs)) if vcs else float("nan"), "pureza": float("nan")}
    r = ref.to_numpy()
    return {"ami": float(adjusted_mutual_info_score(r, e)), "ari": float(adjusted_rand_score(r, e)),
            "v_cramer": _v_cramer(e, r), "pureza": _pureza(e, r)}


def veredicto(res: dict[str, Any]) -> tuple[str, str]:
    """Etiqueta del entrenamiento no supervisado."""
    if res.get("estado") != "completado":
        return res.get("estado", "sin evaluar"), res.get("motivo", "")
    sil, est = res["silueta"], res["estabilidad_ari"]
    asoc = res.get("asociacion", {})
    obj = next((v for k, v in asoc.items() if k.startswith("objetivo")), None)
    grp = next((v for k, v in asoc.items() if k.startswith("grupos")), None)
    texto = (f"{res['metodo']} con k={res['k']}: silueta {sil:.2f}, estabilidad (ARI bootstrap) {est:.2f}"
             + (f", AMI con el objetivo {obj['ami']:.2f}" if obj else "")
             + (f", AMI con los grupos {grp['ami']:.2f}" if grp else "") + ".")
    if sil < UMBRAL_SILUETA or est < UMBRAL_ESTABILIDAD:
        return "sin estructura clara", texto + " Los grupos son debiles o inestables."
    if obj and grp and grp["ami"] > obj["ami"] and grp["ami"] >= UMBRAL_ASOCIACION:
        return "estructura del articulo", texto + (" Los grupos naturales siguen mas al articulo que al objetivo: "
                                                   "domina el efecto de estudio/plataforma.")
    if obj and obj["ami"] >= UMBRAL_ASOCIACION:
        return "estructura alineada con el objetivo", texto + " La estructura natural de los datos refleja el objetivo."
    return "estructura no relacionada", texto + " Hay grupos estables, pero no corresponden al objetivo."


# ---------------------------------------------------------------------------------------------------------------------
# Flujo
# ---------------------------------------------------------------------------------------------------------------------
def ejecutar(conj: Conjunto, cfg: dict[str, Any], salida: dict[str, Path], log: logging.Logger) -> dict[str, Any]:
    t0 = time.time()
    c = configuracion(cfg)
    semilla = cfg["semilla"]
    rng = np.random.default_rng(semilla)
    multi = isinstance(conj.y, pd.DataFrame)
    d_m, d_g = salida["metricas"] / "no_supervisado", salida["graficas"] / "no_supervisado"
    d_m.mkdir(parents=True, exist_ok=True)
    d_g.mkdir(parents=True, exist_ok=True)

    M = (conj.y.astype(float) if c["matriz"] == "objetivo" else conj.X).reset_index(drop=True)
    estratos = None if multi else conj.y.reset_index(drop=True).to_numpy()
    idx = _submuestra(len(M), int(c["max_unidades"]), estratos, rng)
    M = M.iloc[idx].reset_index(drop=True)
    res: dict[str, Any] = {"matriz": c["matriz"], "unidades": int(len(M)), "unidades_totales": int(len(conj.X)),
                           "variables": int(M.shape[1])}
    if len(M) < 10 or M.shape[1] < 2:
        res.update(estado="no_viable", motivo=f"{len(M)} unidades y {M.shape[1]} variables: insuficiente para agrupar")
        log.warning(f"  No supervisado: {res['motivo']}")
        return res
    if len(idx) < len(conj.X):
        log.info(f"  Submuestra estratificada de {len(idx)} de {len(conj.X)} unidades (no_supervisado.max_unidades)")

    # 1. Estandarizar y reducir
    A = SimpleImputer(strategy="median").fit_transform(M.to_numpy(float))
    A = A[:, A.std(0) > 0]
    A = StandardScaler().fit_transform(A)
    n_comp = int(min(c["componentes"], A.shape[1], len(A) - 1))
    pca = PCA(n_components=n_comp, random_state=semilla).fit(A)
    Z = pca.transform(A)
    ev = pca.explained_variance_ratio_
    res["varianza_explicada_pca"] = float(ev.sum())
    log.info(f"  PCA: {n_comp} componentes explican {ev.sum():.0%} de la varianza")

    # 2. Numero de grupos por silueta
    ks = list(range(int(c["k_min"]), int(min(c["k_max"], len(Z) - 1)) + 1))
    metodos = [m for m in c["metodos"] if m != "jerarquico" or len(Z) <= MAX_JERARQUICO]
    if len(metodos) < len(c["metodos"]):
        log.info(f"  Jerarquico omitido: {len(Z)} unidades > {MAX_JERARQUICO}")
    filas = []
    for m in metodos:
        for k in ks:
            e = _ajustar(m, Z, k, semilla)
            filas.append({"metodo": m, "k": k, "silueta": _silueta(Z, e, semilla)})
        mejor_m = max((f for f in filas if f["metodo"] == m), key=lambda f: f["silueta"])
        log.info(f"  {m}: mejor k={mejor_m['k']} (silueta {mejor_m['silueta']:.3f}); probados k={ks[0]}..{ks[-1]}")
    tabla_k = pd.DataFrame(filas)
    guardar_tabla(tabla_k, d_m / "silueta_por_k.csv")
    mejor = tabla_k.loc[tabla_k["silueta"].idxmax()]
    metodo, k = str(mejor["metodo"]), int(mejor["k"])
    etiquetas = _ajustar(metodo, Z, k, semilla)
    res.update({"metodo": metodo, "k": k, "silueta": float(mejor["silueta"])})

    # 3. Estabilidad (remuestreo del 80 %)
    aris = []
    for b in range(int(c["n_bootstrap"])):
        sub = rng.choice(len(Z), int(0.8 * len(Z)), replace=False)
        e2 = _ajustar(metodo, Z[sub], k, int(rng.integers(1e9)))
        aris.append(adjusted_rand_score(etiquetas[sub], e2))
    res["estabilidad_ari"] = float(np.mean(aris)) if aris else float("nan")
    res["estabilidad_ari_de"] = float(np.std(aris)) if aris else float("nan")
    log.info(f"  Estabilidad ({len(aris)} remuestreos): ARI = {res['estabilidad_ari']:.3f} +/- {res['estabilidad_ari_de']:.3f}")

    # 4. Comparacion con las referencias (el objetivo solo se mira aqui)
    refs = _referencias(conj, list(c["referencias"]), idx, multi)
    asoc = {nombre: _asociacion(etiquetas, ref) for nombre, ref in refs.items()}
    res["asociacion"] = asoc
    guardar_tabla(pd.DataFrame(asoc).T.reset_index(names="referencia"), d_m / "asociacion_referencias.csv")
    for nombre, a in asoc.items():
        log.info(f"  Grupos vs {nombre}: AMI={a['ami']:.3f} V de Cramer={a['v_cramer']:.3f}"
                 + (f" pureza={a['pureza']:.3f}" if a["pureza"] == a["pureza"] else ""))

    # 5. Atipicos
    iso = IsolationForest(contamination=float(c["contaminacion"]), random_state=semilla).fit(Z)
    atip = iso.predict(Z) == -1
    res["atipicos"] = int(atip.sum())

    # 6. Tablas
    meta = conj.meta.reset_index(drop=True).iloc[idx].reset_index(drop=True)
    asign = meta.copy()
    asign["grupo"] = etiquetas
    asign["atipico"] = atip.astype(int)
    asign["puntaje_atipico"] = -iso.score_samples(Z).round(4)
    asign["PC1"] = Z[:, 0].round(4)
    asign["PC2"] = Z[:, 1].round(4) if Z.shape[1] > 1 else 0.0
    for nombre, ref in refs.items():
        if isinstance(ref, pd.Series):
            asign[nombre] = ref.to_numpy()
    if cfg["outputs"].get("save_predictions", True):
        guardar_tabla(asign, d_m / "grupos_unidades.csv")
    # perfil de cada grupo: media estandarizada de cada variable
    Mz = (M - M.mean()) / M.std(ddof=0).replace(0, 1)
    perfil = Mz.groupby(etiquetas).mean().T
    perfil.columns = [f"grupo_{g}" for g in perfil.columns]
    guardar_tabla(perfil.round(3).reset_index(names="variable"), d_m / "perfil_grupos.csv")
    res["variables_distintivas"] = {g: perfil[g].abs().sort_values(ascending=False).head(5).round(2).to_dict()
                                    for g in perfil.columns}
    tamanos = pd.Series(etiquetas).value_counts().sort_index()
    res["tamano_grupos"] = {int(g): int(n) for g, n in tamanos.items()}

    # 7. Graficas
    if cfg["outputs"].get("save_plots", True):
        _graficas(cfg, Z, ev, etiquetas, refs, tabla_k, metodo, k, res, perfil, d_g)
    et, tx = veredicto({**res, "estado": "completado"})
    res.update(estado="completado", veredicto=et, explicacion=tx, segundos=round(time.time() - t0, 1))
    guardar_json(res, d_m / "resumen_no_supervisado.json")
    log.info(f"  Veredicto no supervisado: {et} ({res['segundos']} s)")
    return res


def _graficas(cfg, Z, ev, etiquetas, refs, tabla_k, metodo, k, res, perfil, d_g) -> None:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    for m, d in tabla_k.groupby("metodo"):
        ax.plot(d["k"], d["silueta"], marker="o", label=m)
    ax.axvline(k, color="#c0392b", ls="--", label=f"elegido: {metodo}, k={k}")
    ax.set_xlabel("Numero de grupos (k)"); ax.set_ylabel("Silueta"); ax.legend(fontsize=8)
    ax.set_title(f"{cfg['id']}: eleccion del numero de grupos")
    graficas.guardar(fig, d_g / "silueta_por_k.png",
                     nota="Silueta > 0.25 indica grupos razonablemente separados; < 0.10, sin estructura clara.")
    x2, y2 = (f"PC1 ({ev[0]:.0%})", f"PC2 ({ev[1]:.0%})") if len(ev) > 1 else ("PC1", "PC2")
    Z2 = Z[:, :2] if Z.shape[1] > 1 else np.c_[Z[:, 0], np.zeros(len(Z))]
    graficas.dispersion_2d(Z2, pd.Series([f"Grupo {e}" for e in etiquetas]), d_g / "pca_grupos.png",
                           f"{cfg['id']}: grupos encontrados sin usar el objetivo ({metodo}, k={k})", x2, y2,
                           nota=f"Silueta {res['silueta']:.2f}; estabilidad ARI {res['estabilidad_ari']:.2f}.")
    for nombre, ref in refs.items():
        if isinstance(ref, pd.Series):
            seguro = nombre.split(" ")[0].replace("(", "").lower()
            graficas.dispersion_2d(Z2, ref, d_g / f"pca_por_{seguro}.png",
                                   f"{cfg['id']}: mismas coordenadas coloreadas por {nombre}", x2, y2,
                                   nota="Compare con pca_grupos.png: si los colores coinciden con los grupos, la "
                                        "estructura natural de los datos sigue a esta referencia.")
            t = pd.crosstab(pd.Series(etiquetas, name="grupo"), ref.rename(nombre))
            if t.shape[1] <= 40:
                graficas.mapa_calor((t.T / t.sum(axis=1)).T, d_g / f"grupos_vs_{seguro}.png",
                                    f"{cfg['id']}: composicion de cada grupo por {nombre}", nombre, "Grupo",
                                    nota="Fila = grupo encontrado; color = proporcion de sus unidades en cada categoria.",
                                    fmt=".2f", cbar_label="Proporcion")
    if not perfil.empty and perfil.shape[0] > 1:
        top = perfil.abs().max(axis=1).sort_values(ascending=False).head(25).index
        graficas.mapa_calor(perfil.loc[top], d_g / "perfil_grupos.png", f"{cfg['id']}: variables que distinguen los grupos",
                            "Grupo", "Variable", nota="Media estandarizada (z) de cada variable en cada grupo.",
                            cmap="RdBu_r", center=0, cbar_label="z medio")
