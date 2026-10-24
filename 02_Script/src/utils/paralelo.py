"""Aprovechamiento de todo el hardware: varios experimentos a la vez y trabajo en paralelo dentro de cada uno.

Configuracion (config_global.yaml):

    hardware:
      experimentos_paralelos: auto   # 1 = uno tras otro | auto = uno por GPU + uno en CPU | N = N a la vez
      paralelo_interno: true         # particiones y permutaciones en paralelo dentro de cada experimento
      cpu_ayuda_gpu: true            # en las permutaciones de XGBoost/CatBoost la CPU entrena junto con las GPU

Niveles de paralelismo:

1. Entre experimentos (`ejecutar_experimentos`): cada "ranura" es un proceso independiente con su dispositivo
   (GPU 0, GPU 1, ..., CPU) y su parte de los nucleos. Los experimentos con XGBoost/CatBoost van preferentemente a
   las ranuras con GPU y los demas (p. ej. M18) a la ranura de CPU. Con 2 GPU y `auto`: tres experimentos a la vez.
2. Dentro de un experimento (tasks/supervisado.py): los modelos de CPU se entrenan mientras los de GPU usan las
   GPU; las particiones de la validacion cruzada y las permutaciones se reparten entre nucleos y GPU.

Los resultados no cambian: semillas, particiones y permutaciones son las mismas que en la ejecucion secuencial
(las permutaciones se generan antes de repartirlas). Solo puede variar el dispositivo que entrena XGBoost/CatBoost
(GPU o CPU), lo que produce diferencias numericas minimas, nunca de calidad; queda registrado en el manifiesto.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import queue
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from .rutas import config_global

_NUCLEOS_SESION: int | None = None
GB_POR_RANURA = 3.0


def hardware() -> dict[str, Any]:
    return config_global().get("hardware", {}) or {}


def establecer_nucleos_sesion(n: int | None) -> None:
    """Limita los nucleos de este proceso (lo usa cada ranura de `ejecutar_experimentos`)."""
    global _NUCLEOS_SESION
    _NUCLEOS_SESION = None if n is None else max(1, int(n))


def nucleos(n_jobs: int | None = -1) -> int:
    """Nucleos disponibles para entrenar: los de la ranura, o `n_jobs` de la configuracion (-1 = todos)."""
    total = os.cpu_count() or 1
    if _NUCLEOS_SESION is not None:
        return _NUCLEOS_SESION
    if n_jobs is None or int(n_jobs) < 0:
        return max(1, total + 1 + int(n_jobs or -1))
    return max(1, min(int(n_jobs), total))


def paralelo_interno() -> bool:
    return bool(hardware().get("paralelo_interno", True))


def cpu_ayuda_gpu() -> bool:
    return bool(hardware().get("cpu_ayuda_gpu", True))


# ---------------------------------------------------------------------------------------------------------------------
# Dispositivos compartidos entre hilos (permutaciones de modelos GPU)
# ---------------------------------------------------------------------------------------------------------------------
class ColaDispositivos:
    """Reparte dispositivos libres entre hilos: cada tarea toma uno (lista de GPU, o [] = CPU) y lo devuelve al
    terminar, de modo que cada GPU entrena un modelo a la vez y la CPU toma tareas cuando queda libre."""

    def __init__(self, dispositivos: list[list[int]]):
        self._cola: queue.Queue[list[int]] = queue.Queue()
        for d in dispositivos:
            self._cola.put(list(d))
        self.n = len(dispositivos)

    @contextmanager
    def tomar(self) -> Iterator[list[int]]:
        d = self._cola.get()
        try:
            yield d
        finally:
            self._cola.put(d)


# ---------------------------------------------------------------------------------------------------------------------
# Experimentos en paralelo
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Ranura:
    """Un proceso de entrenamiento: sus GPU (vacio = solo CPU) y sus nucleos."""
    nombre: str
    gpus: tuple[int, ...]
    nucleos: int

    @property
    def con_gpu(self) -> bool:
        return bool(self.gpus)


def plan_ranuras(pedido: int | str | None = None, gpus: list[int] | None = None,
                 total_nucleos: int | None = None) -> list[Ranura]:
    """Ranuras para `pedido` experimentos simultaneos (None = config_global.yaml).

    auto: una ranura por GPU y otra solo CPU (si hay nucleos y RAM suficientes); sin GPU, una sola ranura con todos
    los nucleos (cada experimento ya reparte su trabajo entre ellos). N: N ranuras repartidas en GPU, GPU, ..., CPU.
    """
    from .gpu import seleccionar_gpus
    gpus = seleccionar_gpus() if gpus is None else list(gpus)
    total = total_nucleos or nucleos(config_global().get("n_jobs", -1))
    pedido = hardware().get("experimentos_paralelos", "auto") if pedido is None else pedido
    if str(pedido).strip().lower() in ("auto", "todo", "todos"):
        n = len(gpus) + 1 if gpus and total >= 2 * (len(gpus) + 1) else max(1, len(gpus))
        if total_nucleos is None:   # cada ranura carga su copia de los datos (~3 GB con Dataset.csv completo)
            from .gpu import memoria_ram_gb
            libre = memoria_ram_gb()[1]
            if libre:
                n = max(1, min(n, int(libre // GB_POR_RANURA)))
    else:
        try:
            n = max(1, int(pedido))
        except (TypeError, ValueError):
            n = 1
    n = min(n, total)   # al menos un nucleo por ranura
    if n == 1:
        return [Ranura("todo el equipo", tuple(gpus), total)]
    dispositivos = [(g,) for g in gpus] + [()]
    ranuras = []
    for k in range(n):
        d = dispositivos[k % len(dispositivos)]
        ranuras.append(Ranura(f"GPU {d[0]}" if d else "CPU", d, 0))
    # reparto de nucleos: cada ranura recibe su parte; el resto va a la(s) de CPU, que entrenan sin acelerador
    base, resto = divmod(total, n)
    cpu = [i for i, r in enumerate(ranuras) if not r.con_gpu] or list(range(n))
    extra = {i: resto // len(cpu) + (1 if j < resto % len(cpu) else 0) for j, i in enumerate(cpu)}
    nombres: dict[str, int] = {}
    out = []
    for i, r in enumerate(ranuras):
        nombres[r.nombre] = nombres.get(r.nombre, 0) + 1
        nombre = r.nombre if [x.nombre for x in ranuras].count(r.nombre) == 1 else f"{r.nombre} #{nombres[r.nombre]}"
        out.append(Ranura(nombre, r.gpus, base + extra.get(i, 0)))
    return out


def describir_ranuras(ranuras: list[Ranura]) -> str:
    return "; ".join(f"{r.nombre} ({r.nucleos} nucleos" + (f", GPU {','.join(map(str, r.gpus))})" if r.gpus else ")")
                     for r in ranuras)


def requiere_gpu(identificador: str, ajustes: dict[str, Any] | None = None) -> bool:
    """True si el experimento entrena XGBoost o CatBoost (le conviene una ranura con GPU)."""
    from ..config.esquema import _fusionar, buscar_config, cargar_config
    from ..models.registro_modelos import MODELOS_GPU, disponible
    try:
        cfg = cargar_config(buscar_config(str(identificador)))
    except Exception:  # noqa: BLE001
        return False
    if ajustes:
        cfg = _fusionar(cfg, ajustes)
    return cfg.get("tarea") == "supervisado" and any(
        m["nombre"] in MODELOS_GPU and disponible(m["nombre"]) for m in cfg.get("modelos", []))


def _trabajador(identificador: str, etiqueta: str | None, ajustes: dict[str, Any] | None, ranura: Ranura) -> dict[str, Any]:
    """Se ejecuta en el proceso de la ranura: fija sus GPU y nucleos y entrena el experimento."""
    from threadpoolctl import threadpool_limits

    from ..pipeline.ejecutor import ejecutar_experimento
    from .gpu import establecer_gpus_sesion
    establecer_gpus_sesion(list(ranura.gpus))
    establecer_nucleos_sesion(ranura.nucleos)
    t = time.time()
    try:
        with threadpool_limits(limits=ranura.nucleos):
            r = ejecutar_experimento(identificador, etiqueta, ajustes)
    except Exception as e:  # noqa: BLE001
        r = {"id_experimento": str(identificador), "estado": "error", "motivo": f"{type(e).__name__}: {e}",
             "run_id": "-"}
    r["_ranura"] = ranura.nombre
    r["_segundos"] = time.time() - t
    return r


def _inicializar_ranura() -> None:
    import warnings
    warnings.filterwarnings("ignore")


def ejecutar_experimentos(ids: list[str], etiqueta: str | None = None, ranuras: list[Ranura] | None = None,
                          ajustes: dict[str, dict[str, Any] | None] | None = None,
                          al_iniciar: Callable[[str, Ranura], None] | None = None,
                          al_terminar: Callable[[dict[str, Any]], None] | None = None,
                          trabajador: Callable[..., dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Ejecuta los experimentos repartidos en las ranuras (un proceso por ranura). Devuelve los resultados en el
    orden de `ids`. Con una sola ranura se ejecuta en este mismo proceso, uno tras otro. `trabajador` (pruebas)
    sustituye a la funcion que entrena en cada ranura."""
    ranuras = ranuras or plan_ranuras()
    ajustes = ajustes or {}
    resultados: dict[int, dict[str, Any]] = {}
    if len(ranuras) == 1 or len(ids) == 1:
        from ..pipeline.ejecutor import ejecutar_experimento
        from . import gpu
        anteriores = gpu._GPUS_SESION
        r0 = ranuras[0] if len(ranuras) == 1 else Ranura(
            "todo el equipo", tuple(sorted({g for r in ranuras for g in r.gpus})), sum(r.nucleos for r in ranuras))
        for k, i in enumerate(ids):
            if al_iniciar:
                al_iniciar(i, r0)
            gpu.establecer_gpus_sesion(list(r0.gpus))
            establecer_nucleos_sesion(r0.nucleos)
            try:
                t = time.time()
                r = ejecutar_experimento(i, etiqueta, ajustes.get(i))
                r["_segundos"] = time.time() - t
            finally:
                establecer_nucleos_sesion(None)
                gpu.establecer_gpus_sesion(anteriores)
            r["_ranura"] = r0.nombre
            resultados[k] = r
            if al_terminar:
                al_terminar(r)
        return [resultados[k] for k in range(len(ids))]

    pendientes = [(k, i, requiere_gpu(i, ajustes.get(i))) for k, i in enumerate(ids)]
    n_gpu = sum(r.con_gpu for r in ranuras)
    ctx = mp.get_context("spawn")   # igual en Windows y Linux; evita heredar estados de CUDA/OpenMP
    ejecutores = [ProcessPoolExecutor(max_workers=1, mp_context=ctx, initializer=_inicializar_ranura) for _ in ranuras]
    libres = list(range(len(ranuras)))
    en_curso: dict[Any, tuple[int, int, str]] = {}

    def elegir(r: Ranura) -> int | None:
        if not pendientes:
            return None
        if r.con_gpu:   # GPU: primero los que entrenan XGBoost/CatBoost
            return next((j for j, p in enumerate(pendientes) if p[2]), 0)
        sin = next((j for j, p in enumerate(pendientes) if not p[2]), None)
        if sin is not None:
            return sin
        # solo quedan experimentos con modelos GPU: la CPU toma uno si las GPU tienen cola suficiente
        return 0 if n_gpu == 0 or len(pendientes) > n_gpu else None

    try:
        while pendientes or en_curso:
            for s in list(libres):
                j = elegir(ranuras[s])
                if j is None:
                    continue
                k, i, _ = pendientes.pop(j)
                if al_iniciar:
                    al_iniciar(i, ranuras[s])
                fut = ejecutores[s].submit(trabajador or _trabajador, i, etiqueta, ajustes.get(i), ranuras[s])
                en_curso[fut] = (s, k, i)
                libres.remove(s)
                time.sleep(1.1)   # run ids con marca de tiempo distinta y arranque escalonado
            if not en_curso:
                break
            hechos, _ = wait(list(en_curso), return_when=FIRST_COMPLETED)
            for f in hechos:
                s, k, i = en_curso.pop(f)
                libres.append(s)
                try:
                    r = f.result()
                except Exception as e:  # noqa: BLE001  (p. ej. el proceso murio por falta de memoria)
                    r = {"id_experimento": i, "estado": "error", "motivo": f"{type(e).__name__}: {e}", "run_id": "-",
                         "_ranura": ranuras[s].nombre}
                resultados[k] = r
                if al_terminar:
                    al_terminar(r)
    except KeyboardInterrupt:
        for e in ejecutores:
            e.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        for e in ejecutores:
            e.shutdown(wait=True, cancel_futures=True)
    return [resultados[k] for k in sorted(resultados)]


def hilo_en_segundo_plano(funcion: Callable[[], Any]) -> Callable[[], Any]:
    """Lanza `funcion` en un hilo y devuelve una funcion que espera y entrega su resultado (o relanza su error)."""
    caja: dict[str, Any] = {}

    def correr() -> None:
        try:
            caja["r"] = funcion()
        except BaseException as e:  # noqa: BLE001
            caja["e"] = e

    h = threading.Thread(target=correr, daemon=True)
    h.start()

    def esperar() -> Any:
        h.join()
        if "e" in caja:
            raise caja["e"]
        return caja.get("r")
    return esperar
