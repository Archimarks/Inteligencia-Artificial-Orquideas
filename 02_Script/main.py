"""Punto de entrada del sistema de IA para patrones quimicos plantas medicinales.

Sin argumentos (`python main.py` o el boton Ejecutar de VS Code) abre la interfaz: maquina -> datos -> modelos ->
opciones -> entrenamiento -> resultados.

Uso por comandos (desde la carpeta 02_Script):
    python main.py auditoria                 # auditoria completa de 01_Datos/Dataset
    python main.py listar                    # experimentos configurados
    python main.py hardware                  # CPU y GPU detectadas y GPU que se usaran
    python main.py validar [ID ...]          # valida configuraciones YAML sin ejecutar
    python main.py datos [ID ...]            # archivos y columnas que usa cada experimento para entrenar
    python main.py datos M05 --variables     # ademas construye el conjunto y lista las variables de entrada
    python main.py ejecutar M12 [M13 ...]    # ejecuta uno o varios experimentos
    python main.py ejecutar-todos            # ejecuta todos (M01..M18)
    python main.py resumen                   # tabla ejecutiva con la ultima ejecucion de cada experimento
    python main.py reinformar                # regenera los informes de todas las ejecuciones sin reentrenar
    python main.py predecir RUN_ID datos.csv # aplica un modelo guardado a un CSV con las mismas variables
    python main.py construir-dataset         # llena 01_Datos/Dataset (40 CSV) desde 01_Datos/Data (articulos y lotes)
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"

# modulo importable -> paquete de pip (02_Script/requirements.txt)
DEPENDENCIAS = {
    "yaml": "PyYAML", "pandas": "pandas", "numpy": "numpy", "pyarrow": "pyarrow", "sklearn": "scikit-learn",
    "lightgbm": "lightgbm", "joblib": "joblib", "xgboost": "xgboost", "catboost": "catboost", "scipy": "scipy",
    "statsmodels": "statsmodels", "mlxtend": "mlxtend", "networkx": "networkx", "umap": "umap-learn",
    "matplotlib": "matplotlib", "seaborn": "seaborn", "rich": "rich", "openpyxl": "openpyxl", "xlrd": "xlrd",
}


def verificar_dependencias() -> None:
    """Comprueba que las librerias esten instaladas en ESTE Python y ofrece instalarlas si faltan."""
    faltan = [pip for mod, pip in DEPENDENCIAS.items() if importlib.util.find_spec(mod) is None]
    if not faltan:
        return
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    print(f"Faltan librerias en este Python ({sys.executable}, version {sys.version.split()[0]}):")
    print("  " + ", ".join(faltan))
    print("\nPara instalarlas ejecute:")
    print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    if sys.stdin is not None and sys.stdin.isatty():
        r = input("\n¿Instalarlas ahora? [s/N]: ").strip().lower()
        if r in ("s", "si", "sí", "y", "yes"):
            if subprocess.run(cmd).returncode == 0:
                importlib.invalidate_caches()
                faltan = [pip for mod, pip in DEPENDENCIAS.items() if importlib.util.find_spec(mod) is None]
                if not faltan:
                    print("\nDependencias instaladas correctamente.\n")
                    return
            print("\nLa instalacion no se completo; revise los mensajes de pip.")
    sys.exit(1)


verificar_dependencias()
sys.path.insert(0, str(SCRIPT_DIR))

from src.config.esquema import ErrorConfiguracion, cargar_config, listar_configs  # noqa: E402
from src.data.catalogos import ErrorDatos  # noqa: E402
from src.utils.gpu import ErrorGPU  # noqa: E402


def cmd_auditoria(a: argparse.Namespace) -> None:
    from datetime import datetime

    from src.audit.auditoria import ejecutar_auditoria
    run = a.etiqueta or datetime.now().strftime("%Y%m%d-%H%M%S")
    print(ejecutar_auditoria(run))


def cmd_hardware(_: argparse.Namespace) -> None:
    from src.utils.gpu import resumen_hardware
    hw = resumen_hardware()
    print(f"Nucleos CPU: {hw['cpu_nucleos']}")
    print(f"GPU detectadas: {len(hw['gpus'])}")
    for g in hw["gpus"]:
        print(f"  GPU {g['indice']}: {g['nombre']} | {g['memoria_mb']} MB | compute {g.get('compute_capability')} | "
              f"driver {g.get('driver')}")
    print(f"GPU que se usaran para entrenar (XGBoost/CatBoost): {hw['gpus_usadas'] or 'ninguna (CPU)'}")


def cmd_listar(_: argparse.Namespace) -> None:
    for p in listar_configs():
        try:
            c = cargar_config(p)
            print(f"{c['id']:<34} {c['tarea']:<12} {c['nombre']}")
        except ErrorConfiguracion as e:
            print(f"{p.stem:<34} INVALIDA: {e}")


def cmd_validar(a: argparse.Namespace) -> None:
    from src.config.esquema import buscar_config
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


def cmd_datos(a: argparse.Namespace) -> None:
    """Archivos y columnas de entrenamiento (bloque `datos_entrenamiento` de config/modelos/*.yaml)."""
    from src.config.esquema import buscar_config
    from src.features import fuentes
    from src.features.conjuntos import construir
    rutas = [buscar_config(i) for i in a.ids] if a.ids else listar_configs()
    for p in rutas:
        cfg = cargar_config(p)
        fuentes.fijar_archivos(cfg)
        conj, descartadas = None, None
        if a.variables and cfg["tarea"] == "supervisado":
            conj = construir(cfg["conjunto"]["nombre"], cfg["conjunto"].get("parametros", {}))
            descartadas = fuentes.seleccionar_variables(conj, cfg)
        print(fuentes.texto(fuentes.describir(cfg, conj, descartadas)) + "\n")


def cmd_ejecutar(a: argparse.Namespace) -> None:
    from src.pipeline.ejecutor import ejecutar_experimento
    for i in a.ids:
        r = ejecutar_experimento(i, a.etiqueta)
        print(f"{r['id_experimento']}: {r.get('estado')} | {r.get('veredicto', '')} | {r['run_id']}")


def cmd_ejecutar_todos(a: argparse.Namespace) -> None:
    a.ids = [p.stem for p in listar_configs()]
    cmd_ejecutar(a)
    cmd_resumen(a)


def cmd_resumen(_: argparse.Namespace) -> None:
    from src.pipeline.ejecutor import ultimas_ejecuciones
    from src.pipeline.interpretacion import guia_modelos, resumen_ejecutivo
    df = ultimas_ejecuciones()
    print(guia_modelos(df))
    if df.empty:
        print("No hay ejecuciones registradas.")
        return
    print(resumen_ejecutivo(df))


def cmd_reinformar(_: argparse.Namespace) -> None:
    """Regenera informe.md de todas las ejecuciones a partir de sus resultados guardados (sin reentrenar)."""
    from pathlib import Path as P

    from src.config.esquema import cargar_config
    from src.pipeline.interpretacion import completar, escribir_informe
    from src.utils.es import guardar_json, leer_json
    from src.utils.rutas import ruta
    for d in sorted(ruta("salidas", "modelos").glob("*/ejecuciones/*/resultado.json")):
        r, man = completar(leer_json(d), d.parent), leer_json(d.parent / "manifiesto.json")
        cfg = cargar_config(P(man["archivo_config"]))
        cfg["_huella"] = man["huella_config"]
        salida = {k: P(v) for k, v in man["salidas"].items()}
        escribir_informe(cfg, r, man, salida)
        guardar_json(r, d)
        print(d.parent.name, r.get("veredicto"))


def cmd_predecir(a: argparse.Namespace) -> None:
    import joblib
    import pandas as pd

    from src.utils.rutas import ruta
    cand = list(ruta("salidas", "modelos").glob(f"*/modelo_entrenado/{a.run_id}/modelo.joblib"))
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
        proba = pipe.predict_proba(Xn)
        pred = pipe.classes_[proba.argmax(1)].astype(int)
        out["prediccion"] = paq["codificador"].inverse_transform(pred)
        out["prediccion_nombre"] = [paq["nombres_clases"][i] for i in pred]
        out["probabilidad"] = proba.max(1)
    else:
        pred = pipe.predict(Xn)
        for j, n in enumerate(paq["nombres_clases"]):
            out[f"pred_{n}"] = pred[:, j]
    destino = Path(a.salida or Path(a.csv).with_suffix(".predicciones.csv"))
    out.to_csv(destino, sep=";", index=False, encoding="utf-8-sig")
    print(destino)


def cmd_construir_dataset(a: argparse.Namespace) -> None:
    from src.construccion.constructor import ejecutar
    from src.utils.rutas import raiz_proyecto, ruta
    base = Path(a.lotes_dir) if a.lotes_dir else raiz_proyecto() / "01_Datos" / "Data" / "Batch"
    salida = Path(a.salida) if a.salida else ruta("datos", "base")
    print(f"Lotes: {base}\nSalida: {salida}")
    r = ejecutar(base, salida, lotes=a.lotes or None, respetar_cabeceras=not a.ignorar_plantillas,
                 con_dataset=not a.sin_dataset)
    print(f"\nListo en {r['segundos']} s. Avisos: {len(r['avisos'])}. Informe: {salida / 'INFORME_CONSTRUCCION.md'}")


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="IA para el descubrimiento de patrones quimicos en orquideas. "
                                             "Sin argumentos abre un menu.")
    sub = ap.add_subparsers(dest="comando", required=True)
    s = sub.add_parser("auditoria", help="auditoria general de 01_Datos/Dataset"); s.add_argument("--etiqueta")
    s.set_defaults(f=cmd_auditoria)
    s = sub.add_parser("listar", help="lista los experimentos configurados"); s.set_defaults(f=cmd_listar)
    s = sub.add_parser("hardware", help="CPU y GPU detectadas"); s.set_defaults(f=cmd_hardware)
    s = sub.add_parser("validar", help="valida las configuraciones YAML"); s.add_argument("ids", nargs="*")
    s.set_defaults(f=cmd_validar)
    s = sub.add_parser("datos", help="archivos y columnas que usa cada experimento para entrenar")
    s.add_argument("ids", nargs="*")
    s.add_argument("--variables", action="store_true", help="construye el conjunto y lista las variables de entrada")
    s.set_defaults(f=cmd_datos)
    s = sub.add_parser("ejecutar", help="entrena uno o varios experimentos"); s.add_argument("ids", nargs="+")
    s.add_argument("--etiqueta"); s.set_defaults(f=cmd_ejecutar)
    s = sub.add_parser("ejecutar-todos", help="entrena todos los experimentos"); s.add_argument("--etiqueta")
    s.set_defaults(f=cmd_ejecutar_todos)
    s = sub.add_parser("resumen", help="resumen ejecutivo y guia de modelos"); s.set_defaults(f=cmd_resumen)
    s = sub.add_parser("reinformar", help="regenera informes sin reentrenar"); s.set_defaults(f=cmd_reinformar)
    s = sub.add_parser("predecir", help="aplica un modelo guardado a un CSV"); s.add_argument("run_id")
    s.add_argument("csv"); s.add_argument("--salida"); s.set_defaults(f=cmd_predecir)
    s = sub.add_parser("construir-dataset", help="llena 01_Datos/Dataset desde los articulos y lotes de 01_Datos/Data")
    s.add_argument("--salida", help="carpeta de salida (por defecto datos.base de rutas.yaml)")
    s.add_argument("--lotes-dir", help="carpeta con los archivos BATxxxx (por defecto 01_Datos/Data/Batch)")
    s.add_argument("--lotes", nargs="*", type=int, help="solo estos lotes (por defecto los 57)")
    s.add_argument("--sin-dataset", action="store_true", help="no genera 10_Dataset_final/Dataset.csv")
    s.add_argument("--ignorar-plantillas", action="store_true",
                   help="no respeta las cabeceras de los CSV existentes (usa el esquema propio)")
    s.set_defaults(f=cmd_construir_dataset)
    return ap


def ejecutar_comando(argv: list[str]) -> int:
    a = construir_parser().parse_args(argv)
    try:
        a.f(a)
    except (ErrorConfiguracion, ErrorDatos, ErrorGPU, FileExistsError) as e:
        print(f"\nERROR: {e}")
        return 1
    except SystemExit as e:   # p. ej. `validar` con errores: en el menu no debe cerrar el programa
        return int(e.code or 0)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        return ejecutar_comando(argv)
    if not (sys.stdin is not None and sys.stdin.isatty()):
        construir_parser().print_help()
        return 0
    from src.interfaz.consola import ejecutar as interfaz
    return interfaz()


if __name__ == "__main__":
    sys.exit(main())
