"""Entrenamiento y evaluacion supervisada con validacion agrupada, baselines, control de confusion y permutaciones."""
from __future__ import annotations

import logging
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.validation import has_fit_parameter

from ..evaluation import metricas
from ..evaluation.validacion import filtrar_clases, filtrar_etiquetas, particiones
from ..features.conjuntos import Conjunto
from ..models.registro_modelos import MODELOS_GPU, construir_pipeline, disponible
from ..utils.gpu import seleccionar_gpus
from ..utils.paralelo import ColaDispositivos, cpu_ayuda_gpu, hilo_en_segundo_plano, nucleos, paralelo_interno
from ..utils.es import guardar_json, guardar_tabla
from ..visualization import graficas


# ---------------------------------------------------------------------------------------------------------------------
# Utilidades de prediccion
# ---------------------------------------------------------------------------------------------------------------------
def _ajustar(pipe, X, y, w):
    est = pipe.steps[-1][1]
    if w is not None and has_fit_parameter(est, "sample_weight"):
        pipe.fit(X, y, modelo__sample_weight=w)
    else:
        pipe.fit(X, y)
    return pipe


def _proba_multiclase(pipe, X, n_clases: int) -> np.ndarray:
    p = pipe.predict_proba(X)
    out = np.zeros((len(X), n_clases))
    out[:, pipe.classes_.astype(int)] = p
    return out


def _proba_multietiqueta(pipe, X, n_etiquetas: int) -> np.ndarray:
    p = pipe.predict_proba(X)
    if isinstance(p, np.ndarray) and p.ndim == 2 and p.shape[1] == n_etiquetas:
        return p
    out = np.zeros((len(X), n_etiquetas))
    clases = pipe.steps[-1][1].classes_   # lista con las clases vistas por cada etiqueta
    for k, pk in enumerate(p):
        ck = np.asarray(clases[k])
        if 1 in ck:
            out[:, k] = pk[:, list(ck).index(1)]
    return out


def asignar_gpus(nombre: str, n_particiones: int, gpus: list[int]) -> list[list[int] | None]:
    """GPU de cada particion: XGBoost y CatBoost reparten las particiones entre las GPU (una GPU por particion,
    entrenadas en paralelo); el resto de modelos, CPU."""
    if not gpus or nombre not in MODELOS_GPU:
        return [None] * n_particiones
    return [[gpus[i % len(gpus)]] for i in range(n_particiones)]


def _ajustar_particion(nombre: str, semilla: int, multi: bool, seleccion: dict | None, hiper: dict | None,
                       n_columnas: int, n_clases: int, n_jobs: int, gpus: list[int] | None, X: np.ndarray,
                       y: np.ndarray, w: np.ndarray | None, tr: np.ndarray, te: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Entrena una particion y devuelve (indices de prueba, probabilidades). Funcion de modulo para poder
    ejecutarse en otro proceso."""
    pipe = construir_pipeline(nombre, semilla, n_jobs, multi, seleccion, hiper, n_columnas, gpus=gpus)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _ajustar(pipe, X[tr], y[tr], None if w is None else w[tr])
        p = _proba_multietiqueta(pipe, X[te], n_clases) if multi else _proba_multiclase(pipe, X[te], n_clases)
    return te, p


def validar_cruzado(nombre: str, cfg_modelo: dict[str, Any], X: np.ndarray, y: np.ndarray, w: np.ndarray | None,
                    splits: list, tipo: str, n_clases: int, semilla: int, n_jobs: int, seleccion: dict | None,
                    columnas: list[str], gpus: list[int] | None = None,
                    paralelo: bool | None = None) -> tuple[np.ndarray, np.ndarray, list[dict[str, float]]]:
    """Predicciones fuera de particion (OOF) y metricas por particion.

    `gpus` fija los dispositivos (None = los de la sesion; [] = solo CPU). Con `paralelo` (por defecto
    hardware.paralelo_interno) las particiones se entrenan a la vez: XGBoost/CatBoost una por GPU (hilos) y los
    modelos de CPU repartiendo los nucleos entre procesos. Cada particion usa la misma semilla que en serie.
    """
    from joblib import Parallel, delayed
    multi = tipo == "multietiqueta"
    gpus = seleccionar_gpus() if gpus is None else list(gpus)
    asignacion = asignar_gpus(nombre, len(splits), gpus)
    paralelo = paralelo_interno() if paralelo is None else paralelo
    total = nucleos(n_jobs)
    fijos = (nombre, semilla, multi, seleccion, cfg_modelo.get("hiperparametros"), len(columnas), n_clases)
    con_gpu = asignacion[0] is not None
    if paralelo and len(splits) > 1 and con_gpu and len(gpus) > 1:
        # una particion por GPU al mismo tiempo (hilos: XGBoost y CatBoost liberan el GIL mientras entrenan)
        nj = max(1, total // len(gpus))
        resultados = Parallel(n_jobs=len(gpus), backend="threading")(
            delayed(_ajustar_particion)(*fijos, nj, asignacion[i], X, y, w, tr, te) for i, (tr, te) in enumerate(splits))
    elif paralelo and len(splits) > 1 and not con_gpu and total > 1 and not nombre.startswith("baseline"):
        # modelos de CPU: varias particiones a la vez, cada una con su parte de los nucleos
        procesos = min(len(splits), total)
        nj = max(1, total // procesos)
        resultados = Parallel(n_jobs=procesos, backend="loky")(
            delayed(_ajustar_particion)(*fijos, nj, None, X, y, w, tr, te) for tr, te in splits)
    else:
        resultados = [_ajustar_particion(*fijos, total, asignacion[i], X, y, w, tr, te) for i, (tr, te) in enumerate(splits)]
    proba = np.zeros((len(X), n_clases))
    por_part = []
    for i, (te, p) in enumerate(resultados):
        proba[te] = p
        if multi:
            m = metricas.multietiqueta(y[te], (p >= 0.5).astype(int), p)
        else:
            m = metricas.multiclase(y[te], p.argmax(1), p, np.arange(n_clases))
        m["particion"] = i
        m["n_prueba"] = len(te)
        m["gpu"] = "cpu" if asignacion[i] is None else ",".join(map(str, asignacion[i]))
        por_part.append(m)
    pred = (proba >= 0.5).astype(int) if multi else proba.argmax(1)
    return proba, pred, por_part


def _valor_permutacion(nombre: str, cfg_modelo: dict[str, Any], X: np.ndarray, yp: np.ndarray, w: np.ndarray | None,
                       splits: list, tipo: str, n_clases: int, semilla: int, n_jobs: int, seleccion: dict | None,
                       columnas: list[str], gpus: list[int], principal: str) -> float:
    """Metrica principal con las etiquetas permutadas `yp` (misma validacion agrupada)."""
    p, pr, _ = validar_cruzado(nombre, cfg_modelo, X, yp, w, splits, tipo, n_clases, semilla, n_jobs, seleccion,
                               columnas, gpus=gpus, paralelo=False)
    return _metricas_globales(tipo, yp, pr, p, n_clases).get(principal, np.nan)


def permutaciones(nombre: str, cfg_modelo: dict[str, Any], X: np.ndarray, y: np.ndarray, w: np.ndarray | None,
                  splits: list, tipo: str, n_clases: int, semilla: int, n_jobs: int, seleccion: dict | None,
                  columnas: list[str], n_perm: int, principal: str) -> np.ndarray:
    """Distribucion nula de la metrica principal. Las permutaciones se generan primero (mismo generador y orden que
    en serie) y luego se reparten: modelos GPU entre las GPU (y la CPU si hardware.cpu_ayuda_gpu), modelos de CPU
    entre procesos con su parte de los nucleos."""
    from joblib import Parallel, delayed
    rng = np.random.default_rng(semilla)
    perms = [rng.permutation(len(y)) for _ in range(n_perm)]
    gpus = seleccionar_gpus()
    total = nucleos(n_jobs)
    args = (nombre, cfg_modelo, X)
    resto = (w, splits, tipo, n_clases, semilla)
    sel_cols = (seleccion, columnas)
    if not paralelo_interno() or n_perm < 2:
        nulos = [_valor_permutacion(*args, y[pi], *resto, total, *sel_cols, gpus, principal) for pi in perms]
    elif nombre in MODELOS_GPU and gpus:
        dispositivos = [[g] for g in gpus] + ([[]] if cpu_ayuda_gpu() and total > len(gpus) else [])
        cola = ColaDispositivos(dispositivos)
        nj_cpu = max(1, total - len(gpus))

        def una(pi: np.ndarray) -> float:
            with cola.tomar() as d:
                return _valor_permutacion(*args, y[pi], *resto, 1 if d else nj_cpu, *sel_cols, d, principal)
        nulos = Parallel(n_jobs=cola.n, backend="threading")(delayed(una)(pi) for pi in perms)
    elif total > 1:
        procesos = min(n_perm, total)
        nj = max(1, total // procesos)
        nulos = Parallel(n_jobs=procesos, backend="loky")(
            delayed(_valor_permutacion)(*args, y[pi], *resto, nj, *sel_cols, [], principal) for pi in perms)
    else:
        nulos = [_valor_permutacion(*args, y[pi], *resto, total, *sel_cols, [], principal) for pi in perms]
    return np.array(nulos, dtype=float)


def _metricas_globales(tipo: str, y, pred, proba, n_clases: int) -> dict[str, float]:
    if tipo == "multietiqueta":
        return metricas.multietiqueta(y, pred, proba)
    return metricas.multiclase(y, pred, proba, np.arange(n_clases))


def _importancias(pipe, columnas: list[str]) -> pd.Series | None:
    try:
        nombres = pipe[:-1].get_feature_names_out(np.array(columnas, dtype=object))
    except Exception:  # noqa: BLE001
        return None
    est = pipe.steps[-1][1]
    if hasattr(est, "feature_importances_"):
        v = est.feature_importances_
    elif hasattr(est, "coef_"):
        v = np.abs(est.coef_).mean(axis=0)
    elif hasattr(est, "estimators_") and all(hasattr(e, "feature_importances_") for e in est.estimators_):
        v = np.mean([e.feature_importances_ for e in est.estimators_], axis=0)
    elif hasattr(est, "estimators_") and all(hasattr(e, "coef_") for e in est.estimators_):
        v = np.mean([np.abs(e.coef_).ravel() for e in est.estimators_], axis=0)
    else:
        return None
    v = np.asarray(v, dtype=float)
    if len(v) != len(nombres):
        return None
    s = pd.Series(v / (v.sum() or 1), index=nombres).sort_values(ascending=False)
    return s


def auditar_conjunto(conj: Conjunto, X: pd.DataFrame, grupos: pd.Series, nombres: list[str], cfg: dict[str, Any],
                     salida: dict[str, Path], res: dict[str, Any]) -> None:
    """Auditoria de los datos que usa este modelo (03_Resultados/Models/<Modelo>/auditoria_datos/<run_id>)."""
    d = salida["auditoria"]
    desc = conj.X.describe().T
    desc["nulos"] = conj.X.isna().sum()
    desc["pct_nulos"] = (100 * desc["nulos"] / max(len(conj.X), 1)).round(2)
    desc["constante"] = conj.X.nunique() <= 1
    guardar_tabla(desc.reset_index(names="variable"), d / "descripcion_variables.csv")
    upg = grupos.value_counts().rename_axis(str(grupos.name)).rename("unidades").reset_index()
    guardar_tabla(upg, d / "unidades_por_grupo.csv")
    duplicadas = int(conj.X.duplicated().sum())
    resumen = {"conjunto": conj.nombre, "tipo": conj.tipo, "unidades_iniciales": int(len(conj.X)),
               "unidades_evaluables": int(len(X)), "grupos_iniciales": int(conj.grupos.nunique()),
               "grupos_evaluables": int(grupos.nunique()), "columna_grupo": str(conj.grupos.name),
               "variables": int(conj.X.shape[1]), "variables_constantes": int(desc["constante"].sum()),
               "celdas_nulas": int(desc["nulos"].sum()), "filas_X_duplicadas": duplicadas,
               "unidades_por_grupo": {"min": int(upg["unidades"].min()) if len(upg) else 0,
                                      "mediana": float(upg["unidades"].median()) if len(upg) else 0.0,
                                      "max": int(upg["unidades"].max()) if len(upg) else 0},
               "clases_evaluables": nombres, "variables_instrumentales": None if conj.X_instrumental is None
               else list(conj.X_instrumental.columns)}
    guardar_json(resumen, d / "resumen_datos.json")
    if cfg["outputs"].get("save_plots", True) and len(upg):
        graficas.barras(upg.set_index(str(grupos.name))["unidades"], d / "unidades_por_grupo.png",
                        f"{cfg['id']}: unidades por grupo ({grupos.name})", str(grupos.name), "Unidades", top=40,
                        nota="Grupos con muchas unidades pesan mas en el entrenamiento salvo que se usen pesos 1/n por grupo; "
                             "la validacion nunca reparte un grupo entre entrenamiento y prueba.")
    L = [f"# Auditoria de datos - {cfg['id']}", "", f"Conjunto `{conj.nombre}` ({conj.tipo}).", "",
         "| indicador | valor |", "|---|---|"]
    for k in ["unidades_iniciales", "unidades_evaluables", "grupos_iniciales", "grupos_evaluables", "columna_grupo",
              "variables", "variables_constantes", "celdas_nulas", "filas_X_duplicadas"]:
        L.append(f"| {k} | {resumen[k]} |")
    u = resumen["unidades_por_grupo"]
    L += [f"| unidades por grupo (min / mediana / max) | {u['min']} / {u['mediana']} / {u['max']} |", "",
          f"Clases o etiquetas evaluables ({len(nombres)}): " + ", ".join(nombres[:40]) + ("..." if len(nombres) > 40 else ""),
          "", "Notas:"] + [f"- {n}" for n in conj.notas] + [
          "", "Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, "
          "`unidades_por_grupo.csv/.png`, `resumen_datos.json`."]
    (d / "auditoria_datos.md").write_text("\n".join(L), encoding="utf-8")
    res["filas_X_duplicadas"] = duplicadas


# ---------------------------------------------------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------------------------------------------------
def ejecutar(conj: Conjunto, cfg: dict[str, Any], salida: dict[str, Path], log: logging.Logger) -> dict[str, Any]:
    t0 = time.time()
    semilla, n_jobs = cfg["semilla"], cfg.get("n_jobs", -1)
    sp, ev = cfg["split"], cfg["evaluation"]
    tipo = conj.tipo
    multi = tipo == "multietiqueta"
    res: dict[str, Any] = {"conjunto": conj.nombre, "tipo": tipo, "notas": conj.notas,
                           "unidades_iniciales": int(len(conj.X)), "grupos_iniciales": int(conj.grupos.nunique()),
                           "columna_grupo": str(conj.grupos.name)}

    # 1. Clases evaluables ---------------------------------------------------------------------------------------------
    if multi:
        filt = filtrar_etiquetas(conj.y, conj.grupos, sp["min_groups_per_class"], sp["min_samples_per_class"])
    else:
        filt = filtrar_clases(conj.y, conj.grupos, sp["min_groups_per_class"], sp["min_samples_per_class"],
                              cfg.get("max_clases"))
    if not filt.descartadas.empty:
        d = filt.descartadas.copy()
        d["nombre"] = d["clase"].map(lambda c: conj.etiquetas.get(c, str(c)))
        guardar_tabla(d, salida["tablas"] / "clases_descartadas.csv")
    m = filt.mascara
    X = conj.X.loc[m].reset_index(drop=True)
    grupos = conj.grupos.loc[m].reset_index(drop=True)
    meta = conj.meta.loc[m].reset_index(drop=True)
    w = conj.pesos.loc[m].to_numpy() if conj.pesos is not None and cfg.get("usar_pesos", True) else None
    Xi = conj.X_instrumental.loc[m].reset_index(drop=True) if conj.X_instrumental is not None else None
    if multi:
        Ydf = conj.y.loc[m, filt.conservadas].reset_index(drop=True)
        y = Ydf.to_numpy().astype(int)
        nombres = [conj.etiquetas.get(c, str(c)) for c in filt.conservadas]
        n_clases = y.shape[1]
        y_estrat = y.argmax(1)
    else:
        yser = conj.y.loc[m].reset_index(drop=True)
        le = LabelEncoder().fit(yser)
        y = le.transform(yser)
        nombres = [conj.etiquetas.get(c, str(c)) for c in le.classes_]
        n_clases = len(le.classes_)
        y_estrat = y
    res.update({"unidades": int(len(X)), "grupos": int(grupos.nunique()), "clases_evaluables": n_clases,
                "clases": nombres, "clases_descartadas": int(len(filt.descartadas)), "variables": int(X.shape[1])})
    auditar_conjunto(conj, X, grupos, nombres, cfg, salida, res)
    if n_clases < 2 or grupos.nunique() < 3:
        res["estado"] = "no_viable"
        res["motivo"] = (f"Tras exigir >= {sp['min_groups_per_class']} grupos y >= {sp['min_samples_per_class']} unidades "
                         f"por clase quedan {n_clases} clases y {grupos.nunique()} grupos; no es posible una evaluacion "
                         "agrupada honesta.")
        log.warning(res["motivo"])
        return res

    # Distribucion de clases
    if multi:
        dist = pd.Series(y.sum(0), index=nombres, name="positivos")
    else:
        dist = pd.Series(np.bincount(y, minlength=n_clases), index=nombres, name="unidades")
    gpc = (pd.DataFrame({"c": y_estrat if not multi else 0, "g": grupos}) if not multi else None)
    tabla_dist = dist.to_frame()
    if gpc is not None:
        tabla_dist["grupos"] = gpc.groupby("c")["g"].nunique().reindex(range(n_clases)).to_numpy()
    guardar_tabla(tabla_dist.reset_index(names="clase"), salida["tablas"] / "distribucion_clases.csv")
    if "grupos" in tabla_dist:
        res["min_grupos_por_clase"] = int(tabla_dist["grupos"].min())
        res["mediana_grupos_por_clase"] = float(tabla_dist["grupos"].median())
    if cfg["outputs"]["save_plots"]:
        graficas.barras(dist, salida["graficas"] / "distribucion_clases.png",
                        f"{cfg['id']}: distribucion de clases evaluables", "Clase",
                        "Unidades positivas" if multi else "Unidades",
                        nota=f"{len(X)} unidades de {grupos.nunique()} grupos ({grupos.name}). Desbalance max/min = "
                             f"{dist.max() / max(dist.min(), 1):.1f}.")

    # 2. Particiones ----------------------------------------------------------------------------------------------------
    Xn = X.to_numpy(dtype=float)
    g = grupos.astype(str).to_numpy()
    splits = particiones(sp["strategy"], y_estrat, g, sp["n_splits"], semilla, multi)
    res["particiones"] = len(splits)
    log.info(f"{len(X)} unidades, {grupos.nunique()} grupos, {n_clases} clases, {len(splits)} particiones ({sp['strategy']})")

    # 3. Modelos -------------------------------------------------------------------------------------------------------
    principal = metricas.METRICA_PRINCIPAL[tipo]
    filas, por_part_todas, oof = [], [], {}
    omitidos = [mc["nombre"] for mc in cfg["modelos"] if not disponible(mc["nombre"])]
    if omitidos:
        res["modelos_omitidos"] = omitidos
        log.warning(f"Modelos omitidos porque su libreria no esta instalada: {omitidos} "
                    "(python -m pip install -r requirements.txt)")
    cfg = {**cfg, "modelos": [mc for mc in cfg["modelos"] if mc["nombre"] not in omitidos]}

    def evaluar(mc: dict[str, Any], nj: int) -> tuple[dict[str, Any], pd.DataFrame, np.ndarray, np.ndarray]:
        nombre = mc["nombre"]
        t = time.time()
        proba, pred, pp = validar_cruzado(nombre, mc, Xn, y, w, splits, tipo, n_clases, semilla, nj,
                                          cfg.get("seleccion_variables"), list(X.columns))
        glob = _metricas_globales(tipo, y, pred, proba, n_clases)
        dfp = pd.DataFrame(pp)
        fila = {"modelo": nombre, "es_baseline": nombre.startswith("baseline"), "segundos": round(time.time() - t, 1)}
        for k in glob:
            fila[f"{k}"] = glob[k]
            if k in dfp:
                fila[f"{k}_media_particiones"] = dfp[k].mean()
                fila[f"{k}_de_particiones"] = dfp[k].std(ddof=1)
        dfp.insert(0, "modelo", nombre)
        log.info(f"  {nombre}: {principal}={glob.get(principal, np.nan):.3f} ({fila['segundos']} s)")
        return fila, dfp, proba, pred

    # Con GPU, XGBoost/CatBoost se entrenan en un hilo aparte mientras la CPU entrena los demas modelos.
    gpus_sesion, total = seleccionar_gpus(), nucleos(n_jobs)
    res["hardware_entrenamiento"] = {"nucleos": total, "gpus": gpus_sesion, "paralelo_interno": paralelo_interno()}
    de_gpu = [mc for mc in cfg["modelos"] if mc["nombre"] in MODELOS_GPU] if gpus_sesion and paralelo_interno() else []
    de_cpu = [mc for mc in cfg["modelos"] if mc not in de_gpu]
    hechos: dict[str, tuple] = {}
    if de_gpu and de_cpu and total > 1:
        reservados = min(len(gpus_sesion), total - 1)   # un nucleo por GPU para alimentarla
        esperar = hilo_en_segundo_plano(lambda: {mc["nombre"]: evaluar(mc, reservados) for mc in de_gpu})
        hechos.update({mc["nombre"]: evaluar(mc, total - reservados) for mc in de_cpu})
        hechos.update(esperar())
    else:
        hechos.update({mc["nombre"]: evaluar(mc, total) for mc in cfg["modelos"]})
    for mc in cfg["modelos"]:
        fila, dfp, proba, pred = hechos[mc["nombre"]]
        filas.append(fila)
        por_part_todas.append(dfp)
        oof[mc["nombre"]] = (proba, pred)
    tabla = pd.DataFrame(filas)
    guardar_tabla(tabla, salida["metricas"] / "metricas_modelos.csv")
    guardar_tabla(pd.concat(por_part_todas), salida["metricas"] / "metricas_por_particion.csv")

    candidatos = tabla[~tabla["es_baseline"]]
    mejor = candidatos.sort_values(principal, ascending=False).iloc[0]["modelo"]
    base = tabla[tabla["es_baseline"]]
    ref = float(base[principal].max()) if not base.empty else None
    cfg_mejor = next(mc for mc in cfg["modelos"] if mc["nombre"] == mejor)
    res.update({"metrica_principal": principal, "mejor_modelo": mejor,
                "valor_mejor": float(tabla.set_index("modelo").loc[mejor, principal]), "valor_baseline": ref,
                "metricas_mejor": {k: float(v) for k, v in tabla.set_index("modelo").loc[mejor].items()
                                   if isinstance(v, (int, float, np.floating)) and k != "es_baseline"}})
    if cfg["outputs"]["save_plots"]:
        de = f"{principal}_de_particiones"
        graficas.comparacion_modelos(tabla, principal, salida["graficas"] / "comparacion_modelos.png",
                                     f"{cfg['id']}: comparacion de modelos ({principal}, validacion agrupada)",
                                     nota=f"Valores sobre predicciones fuera de particion; barras de error = DE entre "
                                          f"particiones. La linea roja es el mejor baseline: un modelo util debe superarla.",
                                     error=de if de in tabla else None, referencia=ref)

    # 4. Predicciones OOF y diagnostico del mejor modelo ----------------------------------------------------------------
    proba, pred = oof[mejor]
    pred_df = meta.copy()
    pred_df["GRUPO"] = g
    if multi:
        for j, n in enumerate(filt.conservadas):
            pred_df[f"real_{n}"] = y[:, j]
            pred_df[f"proba_{n}"] = proba[:, j].round(4)
        pe = pd.DataFrame(metricas.por_etiqueta(y, proba, nombres))
        guardar_tabla(pe, salida["metricas"] / "metricas_por_etiqueta.csv")
        if cfg["outputs"]["save_plots"] and "average_precision" in pe:
            s = pe.set_index("etiqueta")["average_precision"].dropna()
            graficas.barras(s, salida["graficas"] / "ap_por_etiqueta.png",
                            f"{cfg['id']}: precision promedio por etiqueta ({mejor})", "Etiqueta", "Precision promedio",
                            nota="La precision promedio de un clasificador aleatorio es igual a la prevalencia de la etiqueta; "
                                 "comparar con la columna 'prevalencia' de metricas_por_etiqueta.csv.")
    else:
        pred_df["real"] = le.inverse_transform(y)
        pred_df["predicho"] = le.inverse_transform(pred)
        pred_df["real_nombre"] = [nombres[i] for i in y]
        pred_df["predicho_nombre"] = [nombres[i] for i in pred]
        pred_df["proba_predicha"] = proba.max(1).round(4)
        cm = confusion_matrix(y, pred, labels=range(n_clases))
        guardar_tabla(pd.DataFrame(cm, index=nombres, columns=nombres).reset_index(names="real"),
                      salida["metricas"] / "matriz_confusion.csv")
        from sklearn.metrics import classification_report
        rep = pd.DataFrame(classification_report(y, pred, labels=range(n_clases), target_names=[n[:60] for n in nombres],
                                                 output_dict=True, zero_division=0)).T
        guardar_tabla(rep.reset_index(names="clase"), salida["metricas"] / "reporte_por_clase.csv")
        if cfg["outputs"]["save_plots"] and n_clases <= 40:
            graficas.matriz_confusion(cm, nombres, salida["graficas"] / "matriz_confusion.png",
                                      f"{cfg['id']}: matriz de confusion normalizada ({mejor})",
                                      nota="Filas = clase real (suman 1). La diagonal indica aciertos por clase en articulos/"
                                           "grupos no vistos durante el entrenamiento.")
    if cfg["outputs"]["save_predictions"]:
        guardar_tabla(pred_df, salida["predicciones"] / "predicciones_oof.csv")

    # 5. Evaluacion optimista (sin agrupar) para cuantificar la fuga --------------------------------------------------
    if ev.get("evaluacion_optimista", True) and sp["strategy"] != "stratified_kfold":
        sp_opt = particiones("stratified_kfold", y_estrat, g, sp["n_splits"], semilla, multi)
        p2, pr2, _ = validar_cruzado(mejor, cfg_mejor, Xn, y, w, sp_opt, tipo, n_clases, semilla, n_jobs,
                                     cfg.get("seleccion_variables"), list(X.columns))
        res["valor_optimista_sin_agrupar"] = _metricas_globales(tipo, y, pr2, p2, n_clases).get(principal)
        log.info(f"  Evaluacion no agrupada (optimista): {principal}={res['valor_optimista_sin_agrupar']:.3f}")

    # 6. Control de confusion: solo variables instrumentales ------------------------------------------------------------
    if ev.get("confounding_control", True) and Xi is not None and Xi.shape[1] > 0:
        p3, pr3, _ = validar_cruzado(mejor, cfg_mejor, Xi.to_numpy(float), y, w, splits, tipo, n_clases, semilla, n_jobs,
                                     None, list(Xi.columns))
        res["valor_control_instrumental"] = _metricas_globales(tipo, y, pr3, p3, n_clases).get(principal)
        res["variables_instrumentales"] = list(Xi.columns)[:50]
        log.info(f"  Control instrumental: {principal}={res['valor_control_instrumental']:.3f}")

    # 7. Prueba de permutacion -----------------------------------------------------------------------------------------
    n_perm = int(ev.get("n_permutations", 0)) if ev.get("permutation_test", True) else 0
    if n_perm > 0:
        t = time.time()
        nulos = permutaciones(mejor, cfg_mejor, Xn, y, w, splits, tipo, n_clases, semilla, n_jobs,
                              cfg.get("seleccion_variables"), list(X.columns), n_perm, principal)
        log.info(f"  {n_perm} permutaciones en {time.time() - t:.0f} s")
        obs = res["valor_mejor"]
        res["permutacion"] = {"n": n_perm, "media_nula": float(np.nanmean(nulos)), "p95_nula": float(np.nanpercentile(nulos, 95)),
                              "p_valor": float((1 + np.sum(nulos >= obs)) / (1 + n_perm))}
        guardar_tabla(pd.DataFrame({"valor_nulo": nulos}), salida["metricas"] / "permutaciones.csv")
        if cfg["outputs"]["save_plots"]:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.hist(nulos, bins=min(20, n_perm), color="#999999", label="Etiquetas permutadas")
            ax.axvline(obs, color="#c0392b", lw=2, label=f"Observado = {obs:.3f}")
            ax.set_xlabel(principal); ax.set_ylabel("Frecuencia"); ax.legend()
            ax.set_title(f"{cfg['id']}: prueba de permutacion ({mejor})")
            graficas.guardar(fig, salida["graficas"] / "prueba_permutacion.png",
                             nota=f"p = {res['permutacion']['p_valor']:.3f} con {n_perm} permutaciones. Las etiquetas se "
                                  "permutan entre unidades y se repite la misma validacion agrupada.")
        log.info(f"  Permutacion: p={res['permutacion']['p_valor']:.3f}")

    # 8. Modelo final con todos los datos -------------------------------------------------------------------------------
    final = construir_pipeline(mejor, semilla, nucleos(n_jobs), multi, cfg.get("seleccion_variables"), cfg_mejor.get("hiperparametros"),
                               X.shape[1], gpus=asignar_gpus(mejor, 1, seleccionar_gpus())[0])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _ajustar(final, Xn, y, w)
    imp = _importancias(final, list(X.columns))
    if imp is not None:
        guardar_tabla(imp.rename("importancia").rename_axis("variable").reset_index(), salida["metricas"] / "importancia_variables.csv")
        res["variables_principales"] = imp.head(10).round(4).to_dict()
        if cfg["outputs"]["save_plots"]:
            graficas.barras(imp, salida["graficas"] / "importancia_variables.png",
                            f"{cfg['id']}: variables mas influyentes ({mejor})", "Variable", "Importancia relativa", top=25,
                            nota="Importancia del modelo final ajustado con todos los datos (impureza o |coeficiente|). "
                                 "Indica asociacion predictiva, no causalidad.")
    if cfg["outputs"]["save_model"]:
        paquete = {"pipeline": final, "columnas": list(X.columns), "tipo": tipo, "clases": filt.conservadas,
                   "nombres_clases": nombres, "codificador": None if multi else le, "id_experimento": cfg["id"],
                   "conjunto": conj.nombre}
        joblib.dump(paquete, salida["modelo"] / "modelo.joblib", compress=3)
        res["archivo_modelo"] = str(salida["modelo"] / "modelo.joblib")
    res["estado"] = "completado"
    res["segundos"] = round(time.time() - t0, 1)
    guardar_json(res, salida["metricas"] / "resumen_metricas.json")
    return res
