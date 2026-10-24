"""Interfaz de consola del sistema (se abre con `python main.py` sin argumentos).

Menu principal:
  1) Entrenar modelos - asistente paso a paso:
       1. Maquina: CPU, RAM, sistema y todas las GPU NVIDIA, con una prueba real de cada GPU; se elige con que
          entrenar (todas las GPU que pasan la prueba, algunas, o solo CPU).
       2. Datos: comprueba que 01_Datos/Dataset tenga los CSV reales (no punteros de Git LFS).
       3. Modelos: tabla de los experimentos por categoria con su ultimo resultado; se eligen uno, varios o todos.
       4. Opciones: modo completo o rapido y algoritmos a entrenar.
       5. Confirmacion y entrenamiento con progreso; al final, tabla de resultados y resumen ejecutivo.
  2) Ver resultados (ultima ejecucion de cada modelo; abre la carpeta de un modelo).
  3) Auditoria de datos.
  4) Revisar el equipo.
  5) Validar configuraciones.
La pantalla se limpia en cada paso. Ctrl+C durante el entrenamiento detiene la cola tras pedir confirmacion.
"""
from __future__ import annotations

import os
import platform
import subprocess
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..config.esquema import ErrorConfiguracion, cargar_config, listar_configs
from ..data.catalogos import CATALOGOS, ErrorDatos, ruta_catalogo, verificar_archivo_datos
from ..utils import gpu as hw
from ..utils.rutas import ruta, ruta_global, ruta_modelo

consola = Console(highlight=False)


class Confirm(Prompt):
    """Pregunta si/no en espanol: acepta s/si/y/yes y n/no."""
    response_type = bool
    validate_error_message = "[prompt.invalid]Responda s (si) o n (no)"
    choices = ["s", "n"]

    def render_default(self, default):  # type: ignore[override]
        return Text(f"({'s' if default else 'n'})", style="prompt.default")

    def process_response(self, value: str) -> bool:  # type: ignore[override]
        v = value.strip().lower()
        if v in ("s", "si", "sí", "y", "yes"):
            return True
        if v in ("n", "no"):
            return False
        from rich.prompt import InvalidResponse
        raise InvalidResponse(self.validate_error_message)

CATEGORIAS = [
    ("A", "Quimica del compuesto", ["M01", "M08", "M09", "M10", "M17b"]),
    ("B", "Taxonomia de la planta", ["M02", "M03", "M04", "M05", "M06", "M07"]),
    ("C", "Muestra y plataforma analitica", ["M11", "M12", "M13", "M14", "M15"]),
    ("D", "Metabolitos y actividades biologicas", ["M16", "M17"]),
    ("E", "Patrones quimicos (modelo central)", ["M18"]),
]
COLOR_VEREDICTO = {"senal robusta": "bold green", "senal debil": "green", "sin senal": "yellow",
                   "confundido con plataforma": "magenta", "evidencia insuficiente": "yellow",
                   "no viable": "dim", "descriptivo": "cyan", "error": "bold red"}
ALGORITMOS_GPU = {"xgboost", "catboost"}


# ---------------------------------------------------------------------------------------------------------------------
# utilidades de pantalla
# ---------------------------------------------------------------------------------------------------------------------
def _cabecera(paso: str | None = None) -> None:
    consola.clear()
    titulo = Text("IA para el descubrimiento de patrones quimicos en orquideas", style="bold white")
    sub = Text("Metabolomica de 52 articulos y 57 lotes - validacion agrupada por articulo", style="dim")
    consola.print(Panel(Text.assemble(titulo, "\n", sub), box=box.DOUBLE, border_style="cyan", padding=(0, 2)))
    if paso:
        consola.print(f"[bold cyan]{paso}[/]\n")


def _pausa(texto: str = "Pulse Enter para continuar") -> None:
    try:
        consola.input(f"\n[dim]{texto}...[/] ")
    except (KeyboardInterrupt, EOFError):
        pass


def _abrir_carpeta(p: Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(str(p))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:  # noqa: BLE001
        consola.print(f"[yellow]No se pudo abrir la carpeta ({e}). Ruta:[/] {p}")


def _categoria(id_exp: str) -> tuple[str, str]:
    prefijo = id_exp.split("_")[0]
    for letra, nombre, ids in CATEGORIAS:
        if prefijo in ids:
            return letra, nombre
    return "Z", "Otros"


def _ultimas() -> dict[str, dict[str, Any]]:
    from ..pipeline.ejecutor import ultimas_ejecuciones
    from ..pipeline.interpretacion import veredicto
    df = ultimas_ejecuciones()
    out = {}
    for r in ([] if df.empty else df.to_dict("records")):
        r.setdefault("tarea", "patrones" if str(r["id_experimento"]).startswith("M18") else "supervisado")
        r["_veredicto"] = veredicto(r)[0]
        out[r["id_experimento"]] = r
    return out


def _fmt_veredicto(v: str | None) -> str:
    return f"[{COLOR_VEREDICTO.get(v or '', 'white')}]{v}[/]" if v else "[dim]-[/]"


# ---------------------------------------------------------------------------------------------------------------------
# Paso 1: maquina
# ---------------------------------------------------------------------------------------------------------------------
def _tabla_equipo(eq: dict[str, Any], pruebas: dict[int, tuple[bool, str]] | None) -> None:
    t = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 1))
    t.add_column(style="bold"); t.add_column()
    t.add_row("CPU", f"{eq['cpu']}  ({eq['nucleos_logicos']} hilos)")
    if eq["ram_total_gb"]:
        t.add_row("RAM", f"{eq['ram_libre_gb']} GB libres de {eq['ram_total_gb']} GB")
    t.add_row("Sistema", f"{eq['sistema']}  |  Python {eq['python']}")
    consola.print(t)
    g = Table(title="GPU NVIDIA detectadas", box=box.ROUNDED, title_justify="left")
    for c in ["#", "GPU", "Memoria", "Compute", "Driver", "Prueba"]:
        g.add_column(c)
    if not eq["gpus"]:
        g.add_row("-", "[yellow]ninguna GPU NVIDIA detectada (nvidia-smi no disponible o sin GPU)[/]", "", "", "", "")
    for x in eq["gpus"]:
        prueba = "[dim]...[/]"
        if pruebas is not None:
            ok, det = pruebas.get(x["indice"], (False, "sin probar"))
            prueba = f"[green]OK[/] {det}" if ok else f"[red]FALLO[/] {det}"
        cc = x.get("compute_capability") or "?"
        aviso = " [red](XGBoost 2.1 exige >= 6.0)[/]" if cc not in ("?", None) and float(cc) < 6.0 else ""
        g.add_row(str(x["indice"]), x["nombre"], f"{x['memoria_mb']} MB" if x.get("memoria_mb") else "?",
                  f"{cc}{aviso}", x.get("driver") or "?", prueba)
    consola.print(g)


def paso_maquina() -> list[int] | None:
    _cabecera("Paso 1 de 4 - Maquina con la que se va a entrenar")
    eq = hw.descripcion_equipo()
    pruebas: dict[int, tuple[bool, str]] = {}
    if eq["gpus"]:
        with consola.status("Probando cada GPU con un entrenamiento corto de XGBoost..."):
            for x in eq["gpus"]:
                pruebas[x["indice"]] = hw.probar_gpu(x["indice"])
        _cabecera("Paso 1 de 4 - Maquina con la que se va a entrenar")
    _tabla_equipo(eq, pruebas if eq["gpus"] else None)
    ok = [i for i, (bien, _) in pruebas.items() if bien]
    consola.print("\n[bold]Uso de la GPU:[/] XGBoost reparte las particiones entre las GPU elegidas (una por GPU, en "
                  "paralelo) y CatBoost entrena cada modelo con todas a la vez. LightGBM, Random Forest, regresion "
                  "logistica y KNN usan la CPU.\n")
    opciones = []
    if ok:
        opciones.append(("1", f"Todas las GPU que pasaron la prueba: {ok}  [green](recomendado)[/]", ok))
    if eq["gpus"]:
        opciones.append(("2", "Elegir GPU manualmente", "elegir"))
    opciones.append(("3", "Solo CPU", []))
    for k, txt, _ in opciones:
        consola.print(f"  [bold]{k}[/]) {txt}")
    consola.print("  [bold]0[/]) Volver al menu")
    r = Prompt.ask("Opcion", choices=[k for k, _, _ in opciones] + ["0"], default=opciones[0][0])
    if r == "0":
        return None
    eleccion = next(v for k, _, v in opciones if k == r)
    if eleccion == "elegir":
        disponibles = [x["indice"] for x in eq["gpus"]]
        txt = Prompt.ask(f"Indices de GPU separados por coma (disponibles {disponibles})",
                         default=",".join(map(str, ok or disponibles)))
        eleccion = [int(t) for t in txt.replace(" ", "").split(",") if t.isdigit() and int(t) in disponibles]
        malas = [i for i in eleccion if i in pruebas and not pruebas[i][0]]
        if malas and not Confirm.ask(f"[yellow]Las GPU {malas} fallaron la prueba. ¿Usarlas igualmente?[/]", default=False):
            eleccion = [i for i in eleccion if i not in malas]
    return list(eleccion)


# ---------------------------------------------------------------------------------------------------------------------
# Paso 2: datos
# ---------------------------------------------------------------------------------------------------------------------
def paso_datos() -> bool:
    _cabecera("Paso 2 de 4 - Comprobacion de los datos (01_Datos/Dataset)")
    t = Table(box=box.SIMPLE)
    for c in ["Archivo", "Tamano", "Estado"]:
        t.add_column(c)
    errores = 0
    archivos = [ruta_catalogo(n) for n in CATALOGOS] + [ruta("datos", "dataset")]
    base = ruta("datos", "base")
    for p in archivos:
        try:
            verificar_archivo_datos(p)
            b = p.stat().st_size
            tam = f"{b / 2**20:,.1f} MB" if b >= 2**20 else f"{b / 2**10:,.1f} KB"
            t.add_row(str(p.relative_to(base)), tam, "[green]OK[/]")
        except ErrorDatos as e:
            errores += 1
            t.add_row(str(p.relative_to(base)) if p.is_relative_to(base) else str(p), "-", f"[red]{e}[/]")
    consola.print(t)
    if errores:
        consola.print(f"[bold red]{errores} archivo(s) con problemas.[/] Copie los CSV procesados en {base}.")
        _pausa("Pulse Enter para volver al menu")
        return False
    cache = list(ruta("salidas", "cache").glob("dataset_*.parquet")) if ruta("salidas", "cache").exists() else []
    consola.print("[green]Datos completos.[/] " + ("Cache Parquet disponible (carga rapida)." if cache else
                                                   "La primera carga de Dataset.csv tardara alrededor de 1 minuto."))
    _pausa()
    return True


# ---------------------------------------------------------------------------------------------------------------------
# Paso 3: modelos
# ---------------------------------------------------------------------------------------------------------------------
def _interpretar_seleccion(texto: str, cfgs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    texto = texto.strip().lower()
    if texto in ("todos", "todo", "*", "t"):
        return list(cfgs)
    elegidos: list[int] = []
    for tok in texto.replace(",", " ").split():
        if tok.upper() in {c[0] for c in CATEGORIAS}:
            elegidos += [i for i, c in enumerate(cfgs) if _categoria(c["id"])[0] == tok.upper()]
        elif "-" in tok and all(x.isdigit() for x in tok.split("-", 1)):
            a, b = map(int, tok.split("-", 1))
            elegidos += [i - 1 for i in range(min(a, b), max(a, b) + 1) if 1 <= i <= len(cfgs)]
        elif tok.isdigit() and 1 <= int(tok) <= len(cfgs):
            elegidos.append(int(tok) - 1)
        else:
            coincide = [i for i, c in enumerate(cfgs) if c["id"].lower() == tok or c["id"].split("_")[0].lower() == tok]
            elegidos += coincide
    return [cfgs[i] for i in sorted(dict.fromkeys(elegidos))]


def paso_modelos() -> list[dict[str, Any]] | None:
    cfgs = []
    for p in listar_configs():
        try:
            cfgs.append(cargar_config(p))
        except ErrorConfiguracion as e:
            consola.print(f"[red]{p.name} invalida:[/] {e}")
    cfgs.sort(key=lambda c: (_categoria(c["id"])[0], c["id"]))
    ult = _ultimas()
    while True:
        _cabecera("Paso 3 de 4 - Modelos a entrenar")
        t = Table(box=box.ROUNDED, show_lines=False)
        for c, kw in [("#", {"justify": "right"}), ("Cat.", {}), ("Experimento", {"no_wrap": True}),
                      ("Que predice / analiza", {"max_width": 58}), ("Tipo", {"no_wrap": True}),
                      ("Ultimo resultado", {"no_wrap": True})]:
            t.add_column(c, **kw)
        cat_actual = None
        for i, c in enumerate(cfgs, 1):
            letra, nombre_cat = _categoria(c["id"])
            if letra != cat_actual:
                t.add_section()
                t.add_row("", f"[bold cyan]{letra}[/]", f"[bold cyan]{nombre_cat}[/]", "", "", "")
                cat_actual = letra
            n_alg = sum(not m["nombre"].startswith("baseline") for m in c.get("modelos", []))
            tipo = ("no supervisado" if c["tarea"] == "patrones" else
                    f"{'multietiqueta' if c['conjunto']['nombre'] in ('presencia_metabolitos', 'actividad_especie', 'actividad_metabolito') else 'clasificacion'}"
                    f" [dim]({n_alg} alg.)[/]")
            r = ult.get(c["id"])
            prev = f"{_fmt_veredicto(r['_veredicto'])} [dim]{str(r.get('inicio', ''))[:10]}[/]" if r else "[dim]nunca[/]"
            prioridad = " [bold yellow]*[/]" if c.get("prioridad") in ("alta", "central") else ""
            t.add_row(str(i), letra, f"{c['id']}{prioridad}", c["nombre"], tipo, prev)
        consola.print(t)
        consola.print("[dim]* prioridad alta/central.  Seleccion: numeros (1,3,5), rangos (2-7), categorias (A B), IDs "
                      "(M05) o 'todos'. 0 = volver.[/]")
        txt = Prompt.ask("Modelos", default="todos")
        if txt.strip() == "0":
            return None
        sel = _interpretar_seleccion(txt, cfgs)
        if not sel:
            consola.print("[red]La seleccion no coincide con ningun modelo.[/]")
            time.sleep(1.5)
            continue
        consola.print(f"\nSeleccionados ({len(sel)}): " + ", ".join(f"[bold]{c['id']}[/]" for c in sel))
        if Confirm.ask("¿Continuar con esta seleccion?", default=True):
            return sel


# ---------------------------------------------------------------------------------------------------------------------
# Paso 4: opciones
# ---------------------------------------------------------------------------------------------------------------------
def paso_opciones(sel: list[dict[str, Any]], gpus: list[int]) -> dict[str, Any] | None:
    _cabecera("Paso 4 de 4 - Opciones de entrenamiento")
    consola.print("  [bold]1[/]) Completo: baselines, todos los algoritmos, control de plataforma, validacion sin agrupar "
                  "y prueba de permutacion (lo que fija cada YAML).  [green](recomendado para resultados)[/]")
    consola.print("  [bold]2[/]) Rapido: igual pero sin permutaciones ni validacion sin agrupar (para probar el "
                  "flujo; el veredicto no evalua la significancia).")
    modo = Prompt.ask("Modo", choices=["1", "2"], default="1")
    algs = sorted({m["nombre"] for c in sel if c["tarea"] == "supervisado" for m in c["modelos"]
                   if not m["nombre"].startswith("baseline")})
    elegidos = algs
    if algs:
        consola.print("\nAlgoritmos configurados: " + ", ".join(
            f"{a}{' [green](GPU)[/]' if a in ALGORITMOS_GPU and gpus else ''}" for a in algs))
        txt = Prompt.ask("Algoritmos a entrenar (separados por coma o 'todos'; los baselines se entrenan siempre)",
                         default="todos")
        if txt.strip().lower() not in ("todos", "*", ""):
            elegidos = [a for a in algs if a in {t.strip() for t in txt.split(",")}] or algs
    return {"rapido": modo == "2", "algoritmos": elegidos}


def _ajustes(cfg: dict[str, Any], op: dict[str, Any]) -> dict[str, Any] | None:
    aj: dict[str, Any] = {}
    if op["rapido"]:
        aj["evaluation"] = {"permutation_test": False, "n_permutations": 0, "evaluacion_optimista": False}
        if cfg["tarea"] == "patrones":
            aj["patrones"] = {"n_permutaciones": 49, "n_nulos": 50}
    if cfg["tarea"] == "supervisado":
        mods = [m for m in cfg["modelos"] if m["nombre"].startswith("baseline") or m["nombre"] in op["algoritmos"]]
        if len(mods) != len(cfg["modelos"]) and any(not m["nombre"].startswith("baseline") for m in mods):
            aj["modelos"] = mods
    return aj or None


# ---------------------------------------------------------------------------------------------------------------------
# Entrenamiento
# ---------------------------------------------------------------------------------------------------------------------
def _confirmar(sel: list[dict[str, Any]], gpus: list[int], op: dict[str, Any]) -> bool:
    _cabecera("Resumen antes de entrenar")
    eq = hw.descripcion_equipo()
    nombres = {x["indice"]: x["nombre"] for x in eq["gpus"]}
    t = Table(box=box.SIMPLE, show_header=False)
    t.add_column(style="bold"); t.add_column()
    t.add_row("Maquina", f"{eq['cpu']} ({eq['nucleos_logicos']} hilos)")
    t.add_row("GPU", ", ".join(f"{i}: {nombres.get(i, '?')}" for i in gpus) if gpus else "ninguna (solo CPU)")
    t.add_row("Modelos", f"{len(sel)}: " + ", ".join(c["id"] for c in sel))
    t.add_row("Algoritmos", ", ".join(op["algoritmos"]) or "-")
    t.add_row("Modo", "rapido (sin permutaciones)" if op["rapido"] else "completo")
    t.add_row("Resultados", str(ruta("salidas", "modelos") / "<Modelo>"))
    consola.print(Panel(t, border_style="green"))
    return Confirm.ask("¿Iniciar el entrenamiento?", default=True)


def entrenar(sel: list[dict[str, Any]], op: dict[str, Any]) -> None:
    from ..pipeline.ejecutor import ejecutar_experimento, ultimas_ejecuciones
    from ..pipeline.interpretacion import guia_modelos, resumen_ejecutivo
    from ..utils.paralelo import describir_ranuras, ejecutar_experimentos, plan_ranuras
    _cabecera("Entrenamiento")
    resultados = []
    t0 = time.time()
    ranuras = plan_ranuras() if len(sel) > 1 else []
    if len(ranuras) > 1 and Confirm.ask(f"¿Entrenar {len(ranuras)} modelos a la vez para aprovechar todo el equipo? "
                                        f"[dim]({describir_ranuras(ranuras)})[/]", default=True):
        def inicio(i: str, r) -> None:
            consola.print(f"[cyan]-> {i}[/] en {r.nombre}  [dim](transcurrido {timedelta(seconds=int(time.time() - t0))})[/]")

        def fin(r: dict[str, Any]) -> None:
            v = r.get("veredicto") or r.get("estado")
            valor = f"{r['metrica_principal']} = {r['valor_mejor']:.3f} ({r.get('mejor_modelo')})" if r.get("valor_mejor") is not None else ""
            consola.print(f"[bold]=> {r['id_experimento']}:[/] {_fmt_veredicto(v)}  {valor}  "
                          f"[dim]{r.get('_segundos', 0):.0f} s en {r.get('_ranura')}[/]")
            if r.get("estado") == "error":
                consola.print(f"[red]{r.get('motivo')}[/]")
        try:
            resultados = ejecutar_experimentos([c["id"] for c in sel], ranuras=ranuras,
                                               ajustes={c["id"]: _ajustes(c, op) for c in sel},
                                               al_iniciar=inicio, al_terminar=fin)
        except KeyboardInterrupt:
            consola.print("[yellow]Entrenamiento detenido; los modelos terminados se conservan.[/]")
        sel = []
    for i, cfg in enumerate(sel, 1):
        transcurrido = time.time() - t0
        eta = f" | restante estimado {timedelta(seconds=int(transcurrido / (i - 1) * (len(sel) - i + 1)))}" if i > 1 else ""
        consola.rule(f"[bold cyan][{i}/{len(sel)}] {cfg['id']}[/] - {cfg['nombre']}"
                     f"[dim]  (transcurrido {timedelta(seconds=int(transcurrido))}{eta})[/]")
        ti = time.time()
        try:
            r = ejecutar_experimento(cfg["id"], ajustes=_ajustes(cfg, op))
        except KeyboardInterrupt:
            if Confirm.ask("\n[yellow]¿Detener el entrenamiento? (los modelos terminados se conservan)[/]", default=True):
                resultados.append({"id_experimento": cfg["id"], "estado": "interrumpido"})
                break
            continue
        except Exception as e:  # noqa: BLE001
            r = {"id_experimento": cfg["id"], "estado": "error", "motivo": f"{type(e).__name__}: {e}"}
        r["_segundos"] = time.time() - ti
        resultados.append(r)
        v = r.get("veredicto") or r.get("estado")
        valor = f"{r['metrica_principal']} = {r['valor_mejor']:.3f} ({r.get('mejor_modelo')})" if r.get("valor_mejor") is not None else ""
        consola.print(f"[bold]=> {cfg['id']}:[/] {_fmt_veredicto(v)}  {valor}  [dim]{r['_segundos']:.0f} s[/]")
        if r.get("estado") == "error":
            consola.print(f"[red]{r.get('motivo')}[/]")
    _cabecera("Resultados del entrenamiento")
    t = Table(box=box.ROUNDED)
    for c in ["Experimento", "Estado", "Veredicto", "Mejor algoritmo", "Metrica", "Valor", "Referencia", "Tiempo"]:
        t.add_column(c)
    for r in resultados:
        ref = None
        if r.get("valor_baseline") is not None:
            ref = max(r["valor_baseline"], r.get("valor_control_instrumental") or 0)
        t.add_row(r["id_experimento"], str(r.get("estado")), _fmt_veredicto(r.get("veredicto")), str(r.get("mejor_modelo") or "-"),
                  str(r.get("metrica_principal") or "-"),
                  f"{r['valor_mejor']:.3f}" if r.get("valor_mejor") is not None else "-",
                  f"{ref:.3f}" if ref is not None else "-", f"{r.get('_segundos', 0):.0f} s")
    consola.print(t)
    try:
        df = ultimas_ejecuciones()
        guia_modelos(df)
        p = resumen_ejecutivo(df) if not df.empty else None
        if p:
            consola.print(f"\nResumen ejecutivo actualizado: [bold]{p}[/]")
    except Exception as e:  # noqa: BLE001
        consola.print(f"[yellow]No se pudo actualizar el resumen: {e}[/]")
    consola.print(f"Resultados por modelo en: [bold]{ruta('salidas', 'modelos')}[/]")
    if Confirm.ask("¿Abrir la carpeta de resultados?", default=False):
        _abrir_carpeta(ruta("salidas", "resultados"))


def asistente_entrenamiento() -> None:
    gpus = paso_maquina()
    if gpus is None:
        return
    hw.establecer_gpus_sesion(gpus)
    if not paso_datos():
        return
    sel = paso_modelos()
    if not sel:
        return
    op = paso_opciones(sel, gpus)
    if op is None or not _confirmar(sel, gpus, op):
        return
    entrenar(sel, op)
    _pausa("Pulse Enter para volver al menu")


# ---------------------------------------------------------------------------------------------------------------------
# Otras pantallas
# ---------------------------------------------------------------------------------------------------------------------
def ver_resultados() -> None:
    _cabecera("Resultados (ultima ejecucion de cada modelo)")
    ult = _ultimas()
    if not ult:
        consola.print("[yellow]Todavia no hay ejecuciones. Use 'Entrenar modelos'.[/]")
        _pausa()
        return
    t = Table(box=box.ROUNDED)
    for c in ["#", "Experimento", "Veredicto", "Mejor algoritmo", "Valor", "Baseline", "Plataforma", "Fecha"]:
        t.add_column(c)
    ids = sorted(ult)
    for i, k in enumerate(ids, 1):
        r = ult[k]
        f = lambda x: f"{x:.3f}" if isinstance(x, (int, float)) and x == x else "-"  # noqa: E731
        t.add_row(str(i), k, _fmt_veredicto(r["_veredicto"]), str(r.get("mejor_modelo") or "-"), f(r.get("valor_mejor")),
                  f(r.get("valor_baseline")), f(r.get("valor_control_instrumental")), str(r.get("inicio", ""))[:16])
    consola.print(t)
    consola.print(f"[dim]Resumen completo: {ruta_global() / 'resumen_ejecutivo.md'}[/]")
    r = Prompt.ask("Numero de un modelo para abrir su carpeta (Enter = volver)", default="")
    if r.isdigit() and 1 <= int(r) <= len(ids):
        _abrir_carpeta(ruta_modelo(ids[int(r) - 1]))


def auditoria() -> None:
    from datetime import datetime

    from ..audit.auditoria import ejecutar_auditoria
    _cabecera("Auditoria de datos")
    if not paso_datos_silencioso():
        return
    with consola.status("Auditando 01_Datos/Dataset (catalogos, claves, distribuciones, cobertura)..."):
        out = ejecutar_auditoria(datetime.now().strftime("%Y%m%d-%H%M%S"))
    consola.print(f"[green]Auditoria terminada:[/] {out / 'informe_auditoria.md'}")
    if Confirm.ask("¿Abrir la carpeta?", default=False):
        _abrir_carpeta(out)
    _pausa()


def paso_datos_silencioso() -> bool:
    try:
        for n in CATALOGOS:
            verificar_archivo_datos(ruta_catalogo(n))
        verificar_archivo_datos(ruta("datos", "dataset"))
        return True
    except ErrorDatos as e:
        consola.print(f"[red]{e}[/]")
        _pausa()
        return False


def revisar_equipo() -> None:
    _cabecera("Equipo")
    eq = hw.descripcion_equipo()
    pruebas = {}
    if eq["gpus"]:
        with consola.status("Probando cada GPU..."):
            pruebas = {x["indice"]: hw.probar_gpu(x["indice"]) for x in eq["gpus"]}
        _cabecera("Equipo")
    _tabla_equipo(eq, pruebas if eq["gpus"] else None)
    consola.print(f"\nGPU que se usarian segun config_global.yaml: {hw.seleccionar_gpus() or 'ninguna (CPU)'}")
    _pausa()


def validar_configuraciones() -> None:
    _cabecera("Validacion de configuraciones (02_Script/config/modelos)")
    t = Table(box=box.SIMPLE)
    t.add_column("Archivo"); t.add_column("Estado")
    for p in listar_configs():
        try:
            cargar_config(p)
            t.add_row(p.name, "[green]OK[/]")
        except ErrorConfiguracion as e:
            t.add_row(p.name, f"[red]{e}[/]")
    consola.print(t)
    _pausa()


def ejecutar() -> int:
    """Menu principal."""
    opciones = [("1", "Entrenar modelos (asistente paso a paso)", asistente_entrenamiento),
                ("2", "Ver resultados", ver_resultados),
                ("3", "Auditoria de datos", auditoria),
                ("4", "Revisar el equipo (CPU y GPU)", revisar_equipo),
                ("5", "Validar configuraciones", validar_configuraciones)]
    while True:
        _cabecera()
        for k, txt, _ in opciones:
            consola.print(f"  [bold]{k}[/]) {txt}")
        consola.print("  [bold]0[/]) Salir")
        try:
            r = Prompt.ask("\nOpcion", choices=[k for k, _, _ in opciones] + ["0"], default="1")
        except (KeyboardInterrupt, EOFError):
            return 0
        if r == "0":
            return 0
        try:
            next(f for k, _, f in opciones if k == r)()
        except KeyboardInterrupt:
            continue
        except (ErrorConfiguracion, ErrorDatos, hw.ErrorGPU) as e:
            consola.print(f"[red]ERROR: {e}[/]")
            _pausa()
