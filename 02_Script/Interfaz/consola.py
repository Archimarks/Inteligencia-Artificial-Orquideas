#
# Archivo: consola.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Interfaz de consola del pipeline.
#
#   1) Iniciar entrenamiento
#        a) muestra la configuracion de hardware (CPU, RAM, GPUs) y la que se va
#           a usar -- se elige sola: todas las GPU que pasan la prueba;
#        b) se elige uno o varios paradigmas;
#        c) se entrena, paradigma por paradigma, TODOS los modelos de cada
#           tarea/objetivo; al terminar se regenera el reporte global.
#   2) Comparar resultados -> reporte global (mejores por grupo, tabla completa)
#      en consola y en 03_Resultados/Global/comparacion.txt.
#
# La pantalla se limpia y se redibuja cada vez que se toma una decision. Sin
# argumentos de linea de comandos.
#
from __future__ import annotations

import os
from typing import Callable

import Entrenamiento
from Core import submodulo

dataset_en_memoria = submodulo("03_datasets.dataset_en_memoria")
perfiles = submodulo("00_fundamentos.perfiles")
registro = submodulo("00_fundamentos.registro")
rutas = submodulo("00_fundamentos.rutas")

_log = registro.obtener()
_ANCHO = 62
_PARADIGMAS_ENTRENABLES = ("No supervisado",)


# Limpia la pantalla de la consola.
def _limpiar() -> None:
    os.system("cls" if os.name == "nt" else "clear")


# Imprime un titulo enmarcado.
def _titulo(texto: str) -> None:
    print("\n" + "=" * _ANCHO)
    print(f" {texto}")
    print("=" * _ANCHO)


# Encabezado del menu principal.
def _cabecera() -> None:
    _titulo("Pipeline de Entrenamiento - Inteligencia Artificial")
    print(" Quimica de productos naturales + Machine Learning")
    perfil = perfiles.activo()
    if perfil is not None:
        print(f" Hardware: {perfil.nombre}")


# Detiene el flujo hasta que el usuario pulsa Enter (para poder leer los resultados).
def _pausa() -> None:
    try:
        input("\nEnter para volver al menu... ")
    except (KeyboardInterrupt, EOFError):
        pass


# Muestra las opciones numeradas y devuelve la elegida (None si se cancela con 0).
def _elegir(titulo: str, opciones: list[str]) -> str | None:
    print(f"\n{titulo}:")
    for i, opcion in enumerate(opciones, 1):
        print(f"  {i}) {opcion}")
    print("  0) Volver")
    while True:
        respuesta = input("  > ").strip()
        if respuesta in {"0", "", "q"}:
            return None
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            return opciones[int(respuesta) - 1]
        print("  Elegi un numero de la lista.")


# Como _elegir pero admite varias opciones ('1,2' o '1 3' o 'todos'). None si se cancela.
def _elegir_varios(titulo: str, opciones: list[str]) -> list[str] | None:
    print(f"\n{titulo}   (una o varias: '1,2' o 'todos')")
    for i, opcion in enumerate(opciones, 1):
        print(f"  {i}) {opcion}")
    print("  0) Volver")
    while True:
        respuesta = input("  > ").strip().lower()
        if respuesta in {"0", "", "q"}:
            return None
        if respuesta in {"todos", "todas", "*"}:
            return list(opciones)
        numeros = respuesta.replace(",", " ").replace(" y ", " ").split()
        if numeros and all(t.isdigit() and 1 <= int(t) <= len(opciones) for t in numeros):
            return [opciones[int(t) - 1] for t in dict.fromkeys(numeros)]
        print("  Elegi numeros de la lista (ej. '1,2').")


# Pregunta si/no; True solo ante una respuesta afirmativa explicita.
def _confirmar(pregunta: str) -> bool:
    return input(f"{pregunta} [s/N] > ").strip().lower() in {"s", "si", "y", "yes"}


_equipo = None
_pruebas = None


# Escanea el equipo y corre la prueba de rendimiento UNA vez por sesion (cacheado).
def _analizar_equipo():
    global _equipo, _pruebas
    if _equipo is None:
        from Core import submodulo
        benchmark = submodulo("01_catalogos.benchmark")
        hardware = submodulo("01_catalogos.hardware")

        _equipo = hardware.escanear()
        print("\n  Analizando el equipo y midiendo rendimiento (unos segundos)...")
        _pruebas = benchmark.ejecutar(_equipo)
    return _equipo, _pruebas


# Perfil automatico: todas las GPU que pasan la prueba; si ninguna, CPU.
def _perfil_automatico(pruebas):
    gpus_ok = [int(p.componente.split()[1]) for p in pruebas
               if p.componente.startswith("GPU ") and p.ok]
    if gpus_ok:
        return perfiles.Perfil("GPU " + "+".join(map(str, gpus_ok)), gpus_ok)
    return perfiles.Perfil("CPU", [])


# Muestra la configuracion de hardware + la que se va a usar y fija el perfil.
# Devuelve False si CPU/RAM fallan la prueba (no se puede entrenar).
def _configurar_hardware() -> bool:
    equipo, pruebas = _analizar_equipo()

    _titulo("Configuracion de hardware")
    print(f"  CPU   {equipo.cpu_nombre}")
    print(f"        {equipo.cpu_nucleos_fisicos} nucleos fisicos / "
          f"{equipo.cpu_nucleos_logicos} logicos")
    print(f"  RAM   {equipo.ram_disponible_gb} GB libres de {equipo.ram_total_gb} GB")
    for gpu in equipo.gpus:
        print(f"  GPU {gpu.indice} {gpu.nombre}  ({gpu.memoria_gb} GB)")
    if not equipo.gpus:
        print("  GPU   ninguna GPU CUDA detectada")

    print()
    for p in pruebas:
        print(f"   [{'OK   ' if p.ok else 'FALLO'}] {p.componente:8} {p.detalle}")

    if not all(p.ok for p in pruebas if not p.componente.startswith("GPU ")):
        print("\n  CPU o RAM fallaron la prueba: no se puede entrenar.")
        return False

    perfil = _perfil_automatico(pruebas)
    perfiles.establecer(perfil)

    _titulo("Configuracion que se va a usar")
    print(f"  Perfil: {perfil.nombre}")
    if perfil.usa_gpu:
        print(f"  - GPU {', '.join(map(str, perfil.dispositivos))}: xgboost y catboost "
              "(repartidos entre las tarjetas).")
        print("  - CPU: el resto de modelos. scikit-learn y el wheel de lightgbm no "
              "tienen backend de GPU;")
        print("    no existe forma de correrlos en CUDA en este entorno.")
    else:
        print("  Sin GPU utilizable: todo corre en CPU.")
    return True


# Que archivo de 01_Datos/Dataset alimenta cada tarea/objetivo de Supervisado
# -- solo informativo (para el resumen previo). 02_Dataset_Metabolito.csv no
# aparece: todo lo que usa la tabla de metabolitos ya lee
# 03_Dataset_Metabolito_Identificados.csv (mismo filtro a identificados, mas
# chico), asi que serian dos nombres para el mismo dataset final.
_ARCHIVO_DE_OBJETIVO: dict[tuple[str, str], str] = {
    ("Clasificación", "ACTIVIDAD_BIOLOGICA"): "01_Dataset_Actividad_biologica.csv",
    ("Regresión", "ACTIVIDAD_BIOLOGICA"): "01_Dataset_Actividad_biologica.csv",
    ("Clasificación", "METABOLITO"): "03_Dataset_Metabolito_Identificados.csv",
    ("Regresión", "METABOLITO"): "03_Dataset_Metabolito_Identificados.csv",
}
_ARCHIVOS_NO_SUPERVISADOS = {
    "PATRONES_QUIMICOS": "04_Dataset_Patrones_Quimicos_Unificado.csv",
    "CALIDAD_BATCH": "04_Informe_Calidad_Por_Batch.csv",
    "CALIDAD_MUESTRA": "04_Informe_Calidad_Por_Muestra.csv",
    "METABOLITOS_SIN_CLASE": "04_Metabolitos_Sin_Clase_Quimica.csv",
}


def _archivo_de(tarea: str, objetivo: str) -> str:
    if objetivo == "PATRONES_QUIMICOS":
        carpeta = rutas.DATOS / "Dataset"
        for nombre in (
                "04_Dataset_Patrones_Quimicos_Unificado.csv",
                "04_Dataset_Patrones_Quimicos.csv"):
            if (carpeta / nombre).is_file():
                return nombre
    return _ARCHIVO_DE_OBJETIVO.get(
        (tarea, objetivo), _ARCHIVOS_NO_SUPERVISADOS.get(objetivo, "desconocido"))


# Resumen INSTANTANEO de un paradigma: tareas/objetivos, de que archivo salen
# y que algoritmos aplican -- nada de esto arma el dataset (Core.rutas /
# Core.modelos_supervisados son puro catalogo, no tocan los CSV).
def _mostrar_resumen_paradigma(paradigma: str) -> None:
    entrenador = Entrenamiento.para(paradigma)
    plan = rutas.plan_entrenamiento(paradigma)
    if not plan:
        print(f"   {paradigma}: sin datasets.")
        return
    print(f"   {paradigma}:")
    por_archivo: dict[str, list[tuple[str, str, list[str]]]] = {}
    for tarea, objetivo in plan:
        modelos = entrenador.modelos_disponibles(tarea)
        archivo = _archivo_de(tarea, objetivo)
        por_archivo.setdefault(archivo, []).append((tarea, objetivo, modelos))
    for archivo, analisis in por_archivo.items():
        print(f"      - Dataset: {archivo}")
        print("          análisis disponibles:")
        for tarea, objetivo, modelos in analisis:
            print(f"            - {tarea} / {objetivo or '(único)'}")
            print(f"                algoritmos: {', '.join(modelos)}")


# Imprime tareas/objetivos/algoritmos/forma del dataset de un paradigma (arma
# cada dataset para saber filas x features: se llama recien despues de elegir
# el paradigma, es el momento en que ese costo hace falta de verdad).
# Devuelve la cantidad de modelos que entrenaria (0 si no tiene datasets).
def _mostrar_plan_paradigma(paradigma: str) -> int:
    entrenador = Entrenamiento.para(paradigma)
    plan = rutas.plan_entrenamiento(paradigma)
    if not plan:
        print(f"   {paradigma}: sin datasets.")
        return 0
    print(f"   {paradigma}:")
    total = 0
    for tarea, objetivo in plan:
        modelos = entrenador.modelos_disponibles(tarea)
        total += len(modelos)
        try:
            ds = dataset_en_memoria.cargar(paradigma, tarea, objetivo, requiere_objetivo=False)
            forma = f"{ds.n_filas} filas x {ds.n_features} features"
        except Exception as exc:
            _log.error(
                "No se pudo preparar %s para %s/%s: %s",
                _archivo_de(tarea, objetivo), tarea, objetivo, exc)
            forma = "?"
        print(f"      - {tarea} / {objetivo or '(único)'}  "
              f"<- {_archivo_de(tarea, objetivo)} ({forma})")
        print(f"          algoritmos: {', '.join(modelos)}")
    return total


# Unica opcion: configura el hardware, muestra que datasets hay y para que
# algoritmos sirven, elige paradigma(s), y entrena TODO de una, sin pedir una
# segunda confirmacion.
def _accion_entrenar() -> None:
    if not _configurar_hardware():
        return

    _titulo("Datasets disponibles")
    paradigmas_disponibles = [
        paradigma for paradigma in _PARADIGMAS_ENTRENABLES
        if paradigma in rutas.listar_paradigmas()
    ]
    for paradigma in paradigmas_disponibles:
        _mostrar_resumen_paradigma(paradigma)

    paradigmas = _elegir_varios("Paradigma(s)", paradigmas_disponibles)
    if not paradigmas:
        return
    entrenadores = {p: Entrenamiento.para(p) for p in paradigmas}

    _titulo("Plan de entrenamiento")
    total = 0
    for paradigma in paradigmas:
        total += _mostrar_plan_paradigma(paradigma)  # ya en cache, instantaneo

    if total == 0:
        print("\nNo hay nada para entrenar (ningun dataset.csv disponible).")
        return

    from Core import submodulo
    ejecutor = submodulo("04_entrenamiento.ejecutor")

    _titulo(f"Entrenando {total} modelos")
    resumenes: list[dict] = []
    for paradigma in paradigmas:
        plan = rutas.plan_entrenamiento(paradigma)
        if not plan:
            continue
        _titulo(f"Entrenando  {paradigma}")
        resumenes += ejecutor.entrenar_plan(
            paradigma, plan, entrenadores[paradigma].modelos_disponibles)

    _mostrar_resumenes(resumenes)
    _generar_reporte()


# Metrica por la que se ordena cada grupo de resultados.
def _metrica_principal(tarea: str, metricas: dict) -> str:
    for candidata in ("f1_macro", "r2", "silhouette", "trustworthiness", "lift_medio",
                      "separacion_puntaje"):
        if candidata in metricas:
            return candidata
    return next(iter(metricas), "")


# Imprime los resultados agrupados por tarea/objetivo, cada grupo ordenado por
# su metrica principal.
def _mostrar_resumenes(resumenes: list[dict]) -> None:
    if not resumenes:
        print("\nNo se completo ningun entrenamiento.")
        return
    from itertools import groupby

    clave = lambda r: (r["tarea"], r["objetivo"])
    for (tarea, objetivo), grupo in groupby(sorted(resumenes, key=clave), key=clave):
        grupo = list(grupo)
        exitosos = [r for r in grupo if r.get("estado") != "FALLIDO" and "error" not in r]
        fallidos = [r for r in grupo if r.get("estado") == "FALLIDO" or "error" in r]
        print(f"\n{tarea} / {objetivo or '(único)'}  <- "
              f"{grupo[0].get('archivo_fuente') or grupo[0].get('dataset', 'fuente desconocida')}")
        if exitosos:
            validacion = exitosos[0].get("validacion")
            if validacion:
                print(f"  Evaluación: {validacion}")
            principal = _metrica_principal(tarea, exitosos[0].get("metricas", {}))
            print(f"  Completados ({len(exitosos)}), ordenados por {principal or 'modelo'}:")
            ordenados = sorted(
                exitosos,
                key=lambda r: r.get("metricas", {}).get(principal, float("-inf")),
                reverse=True,
            )
            for r in ordenados:
                partes = []
                for k, v in r.get("metricas", {}).items():
                    partes.append(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}")
                alertas = r.get("alertas_interpretacion") or []
                if alertas:
                    partes.append(f"alertas={'; '.join(alertas)}")
                estado = (
                    "ATENCIÓN" if r.get("estado") == "COMPLETADO_CON_ALERTAS" else "OK")
                print(
                    f"    [{estado}] {r['modelo']:<22} [{r.get('dispositivo', 'cpu'):<7}] "
                    f"{'  '.join(partes)}")
        if fallidos:
            print(f"  Fallidos ({len(fallidos)}):")
        for r in fallidos:
            print(f"    [ERROR] {r['modelo']}: {r.get('error', 'Error no especificado')}")
            if r.get("recomendacion"):
                print(f"      Siguiente paso: {r['recomendacion']}")
            if r.get("directorio_resultados"):
                print(f"      Detalle: {r['directorio_resultados']}\\error.json")


# Regenera el reporte global y avisa donde quedo el .txt.
def _generar_reporte() -> None:
    from Core import submodulo
    reporte_global = submodulo("01_catalogos.reporte_global")

    _, ruta = reporte_global.generar()
    if ruta is not None:
        print(f"\nReporte global actualizado: {ruta}")


# Opcion 2: muestra el reporte global (comparacion de todos los resultados).
def _accion_comparar() -> None:
    from Core import submodulo
    reporte_global = submodulo("01_catalogos.reporte_global")

    texto, ruta = reporte_global.generar()
    _titulo("Comparacion global de resultados")
    print(texto)
    if ruta is not None:
        print(f"\n(guardado en {ruta})")


# Menu principal: clave -> (texto, accion).
_OPCIONES: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Iniciar entrenamiento", _accion_entrenar),
    "2": ("Comparar resultados (reporte global)", _accion_comparar),
}


# Bucle del menu principal. Redibuja la pantalla en cada vuelta. Devuelve el
# codigo de salida del proceso.
def ejecutar() -> int:
    while True:
        _limpiar()
        _cabecera()
        print()
        for clave, (texto, _) in _OPCIONES.items():
            print(f"  {clave}) {texto}")
        print("  0) Salir")

        eleccion = input("\nOpcion > ").strip().lower()
        if eleccion in {"0", "q", "salir", "exit"}:
            print("Hasta luego.")
            return 0

        entrada = _OPCIONES.get(eleccion)
        if entrada is None:
            continue

        try:
            entrada[1]()
        except (KeyboardInterrupt, EOFError):
            print("\nOperacion cancelada.")
        except Exception as exc:
            _log.error("Error: %s", exc)

        _pausa()
