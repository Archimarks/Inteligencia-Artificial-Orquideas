"""Punto de entrada del sistema de IA para patrones quimicos en orquideas y plantas medicinales.

Uso (desde la carpeta 02_Script):
    python main.py auditoria                 # auditoria completa de 01_Datos/Base
    python main.py listar                    # experimentos configurados
    python main.py validar [ID ...]          # valida configuraciones YAML sin ejecutar
    python main.py ejecutar M12 [M13 ...]    # ejecuta uno o varios experimentos
    python main.py ejecutar-todos            # ejecuta todos (M01..M18)
    python main.py resumen                   # tabla ejecutiva con la ultima ejecucion de cada experimento
    python main.py reinformar                # regenera los informes de todas las ejecuciones sin reentrenar
    python main.py predecir RUN_ID datos.csv # aplica un modelo guardado a un CSV con las mismas variables
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from orquideas.config.esquema import ErrorConfiguracion, cargar_config, listar_configs  # noqa: E402


def cmd_auditoria(a: argparse.Namespace) -> None:
    from datetime import datetime

    from orquideas.audit.auditoria import ejecutar_auditoria
    run = a.etiqueta or datetime.now().strftime("%Y%m%d-%H%M%S")
    print(ejecutar_auditoria(run))


def cmd_listar(_: argparse.Namespace) -> None:
    for p in listar_configs():
        try:
            c = cargar_config(p)
            print(f"{c['id']:<34} {c['tarea']:<12} {c['nombre']}")
        except ErrorConfiguracion as e:
            print(f"{p.stem:<34} INVALIDA: {e}")


def cmd_validar(a: argparse.Namespace) -> None:
    from orquideas.config.esquema import buscar_config
    rutas = [buscar_config(i) for i in a.ids] if a.ids else listar_configs()
    errores = 0
    for p in rutas:
        try:
            cargar_config(p)
            print(f"OK       {p.name}")
        except ErrorConfiguracion as e:
            errores += 1
            print(f"ERROR    {e}")
    sys.exit(1 if errores else 0)


def cmd_ejecutar(a: argparse.Namespace) -> None:
    from orquideas.pipeline.ejecutor import ejecutar_experimento
    for i in a.ids:
        r = ejecutar_experimento(i, a.etiqueta)
        print(f"{r['id_experimento']}: {r.get('estado')} | {r.get('veredicto', '')} | {r['run_id']}")


def cmd_ejecutar_todos(a: argparse.Namespace) -> None:
    a.ids = [p.stem for p in listar_configs()]
    cmd_ejecutar(a)
    cmd_resumen(a)


def cmd_resumen(_: argparse.Namespace) -> None:
    from orquideas.pipeline.ejecutor import ultimas_ejecuciones
    from orquideas.pipeline.interpretacion import guia_modelos, resumen_ejecutivo
    df = ultimas_ejecuciones()
    print(guia_modelos(df))
    if df.empty:
        print("No hay ejecuciones registradas.")
        return
    print(resumen_ejecutivo(df))


def cmd_reinformar(_: argparse.Namespace) -> None:
    """Regenera informe.md de todas las ejecuciones a partir de sus resultados guardados (sin reentrenar)."""
    from pathlib import Path as P

    from orquideas.config.esquema import cargar_config
    from orquideas.pipeline.interpretacion import escribir_informe
    from orquideas.utils.es import guardar_json, leer_json
    from orquideas.utils.rutas import ruta
    for d in sorted(ruta("salidas", "ejecuciones").glob("*/resultado.json")):
        r, man = leer_json(d), leer_json(d.parent / "manifiesto.json")
        cfg = cargar_config(P(man["archivo_config"]))
        cfg["_huella"] = man["huella_config"]
        salida = {k: P(v) for k, v in man["salidas"].items()}
        escribir_informe(cfg, r, man, salida)
        guardar_json(r, d)
        print(d.parent.name, r.get("veredicto"))


def cmd_predecir(a: argparse.Namespace) -> None:
    import joblib
    import pandas as pd

    from orquideas.utils.rutas import ruta
    cand = list(ruta("salidas", "modelos").glob(f"*/{a.run_id}/modelo.joblib"))
    if not cand:
        sys.exit(f"No se encontro modelo para la ejecucion {a.run_id}")
    paq = joblib.load(cand[0])
    X = pd.read_csv(a.csv, sep=None, engine="python")
    faltan = [c for c in paq["columnas"] if c not in X.columns]
    if faltan:
        sys.exit(f"Faltan columnas requeridas por el modelo: {faltan[:15]}")
    pipe = paq["pipeline"]
    Xn = X[paq["columnas"]].to_numpy(float)
    out = X.copy()
    if paq["tipo"] == "multiclase":
        pred = pipe.predict(Xn)
        out["prediccion"] = paq["codificador"].inverse_transform(pred)
        out["prediccion_nombre"] = [paq["nombres_clases"][i] for i in pred]
        out["probabilidad"] = pipe.predict_proba(Xn).max(1)
    else:
        pred = pipe.predict(Xn)
        for j, n in enumerate(paq["nombres_clases"]):
            out[f"pred_{n}"] = pred[:, j]
    destino = Path(a.salida or Path(a.csv).with_suffix(".predicciones.csv"))
    out.to_csv(destino, sep=";", index=False, encoding="utf-8-sig")
    print(destino)


def main() -> None:
    ap = argparse.ArgumentParser(description="IA para el descubrimiento de patrones quimicos en orquideas")
    sub = ap.add_subparsers(dest="comando", required=True)
    s = sub.add_parser("auditoria"); s.add_argument("--etiqueta"); s.set_defaults(f=cmd_auditoria)
    s = sub.add_parser("listar"); s.set_defaults(f=cmd_listar)
    s = sub.add_parser("validar"); s.add_argument("ids", nargs="*"); s.set_defaults(f=cmd_validar)
    s = sub.add_parser("ejecutar"); s.add_argument("ids", nargs="+"); s.add_argument("--etiqueta")
    s.set_defaults(f=cmd_ejecutar)
    s = sub.add_parser("ejecutar-todos"); s.add_argument("--etiqueta"); s.set_defaults(f=cmd_ejecutar_todos)
    s = sub.add_parser("resumen"); s.set_defaults(f=cmd_resumen)
    s = sub.add_parser("reinformar"); s.set_defaults(f=cmd_reinformar)
    s = sub.add_parser("predecir"); s.add_argument("run_id"); s.add_argument("csv"); s.add_argument("--salida")
    s.set_defaults(f=cmd_predecir)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
