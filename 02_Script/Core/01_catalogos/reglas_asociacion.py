#
# Archivo: reglas_asociacion.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Apriori a mano (mlxtend no esta instalado) para la tarea Reglas de
# asociacion. Trabaja sobre la version BINARIA del perfil quimico por especie
# (Core.construir_dataset_no_supervisado): cada fila es una especie, cada
# columna una clase recurrente (1) o no recurrente (0), segun su prevalencia
# entre corridas clasificadas. Una
# regla antecedente -> consecuente dice "si esta(n) presente(s) esta(s)
# clase(s) quimica(s), tiende a estar tambien esta otra".
#
# Poda estandar de Apriori: un itemset de tamano k solo puede ser frecuente si
# todos sus subconjuntos de tamano k-1 tambien lo son, asi que se construye
# nivel por nivel (1, 2, 3, ...) y se descartan los candidatos por debajo del
# soporte minimo antes de pasar al siguiente nivel -- evita la explosion
# combinatoria de probar todas las combinaciones posibles de entrada.
#
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from .. import submodulo

config = submodulo("00_fundamentos.config")


@dataclass
class Regla:
    antecedente: tuple[str, ...]
    consecuente: str
    soporte: float
    confianza: float
    lift: float


def _soporte(transacciones: list[frozenset], candidatos: list[frozenset]) -> dict[frozenset, float]:
    n = len(transacciones)
    conteo = dict.fromkeys(candidatos, 0)
    for t in transacciones:
        for c in candidatos:
            if c <= t:
                conteo[c] += 1
    return {c: v / n for c, v in conteo.items()}


def _candidatos(frecuentes: list[frozenset], tamano: int) -> list[frozenset]:
    frecuentes_set = set(frecuentes)
    if tamano == 2:
        items = sorted({i for fs in frecuentes for i in fs})
        return [frozenset(par) for par in combinations(items, 2)]
    candidatos = set()
    for a in frecuentes:
        for b in frecuentes:
            union = a | b
            if len(union) == tamano and all(
                    frozenset(subconjunto) in frecuentes_set
                    for subconjunto in combinations(union, tamano - 1)):
                candidatos.add(union)
    return sorted(candidatos, key=lambda conjunto: tuple(sorted(conjunto)))


# X: matriz binaria (0/1), columnas: nombre de cada columna (misma cantidad
# que X.shape[1]). Devuelve las reglas con soporte/confianza suficientes,
# ordenadas por lift descendente (mas fuerte primero).
def entrenar(X: np.ndarray, columnas: list[str],
            min_soporte: float = config.REGLAS_MIN_SOPORTE,
            min_confianza: float = config.REGLAS_MIN_CONFIANZA,
            tamano_max: int = config.REGLAS_TAMANO_MAX_ITEMSET) -> list[Regla]:
    if X.ndim != 2 or X.shape[0] == 0:
        raise ValueError("Apriori requiere una matriz con al menos una transacción.")
    if X.shape[1] != len(columnas):
        raise ValueError("La cantidad de nombres de features no coincide con X.")
    if not np.isin(X, (0, 1)).all():
        raise ValueError("Apriori requiere una matriz binaria (solo 0 y 1).")
    if not 0 < min_soporte <= 1 or not 0 <= min_confianza <= 1:
        raise ValueError("min_soporte debe estar en (0, 1] y min_confianza en [0, 1].")
    if tamano_max < 2:
        raise ValueError("tamano_max debe ser al menos 2 para generar reglas.")

    transacciones = [frozenset(columnas[i] for i in np.nonzero(fila)[0]) for fila in X]

    soporte: dict[frozenset, float] = {}
    niveles: list[list[frozenset]] = []

    nivel = [fs for fs, s in _soporte(transacciones, [frozenset((c,)) for c in columnas]).items()
             if s >= min_soporte]
    soporte.update(_soporte(transacciones, nivel))
    niveles.append(nivel)

    tamano = 2
    while nivel and tamano <= tamano_max:
        candidatos = _candidatos(nivel, tamano)
        if not candidatos:
            break
        sop = _soporte(transacciones, candidatos)
        nivel = [fs for fs, s in sop.items() if s >= min_soporte]
        soporte.update({fs: sop[fs] for fs in nivel})
        niveles.append(nivel)
        tamano += 1

    reglas: list[Regla] = []
    for nivel in niveles[1:]:  # itemsets de tamano >= 2: hacen falta 2 para una regla
        for itemset in nivel:
            for consecuente in itemset:
                antecedente = itemset - {consecuente}
                sop_ant = soporte.get(antecedente)
                sop_cons = soporte.get(frozenset((consecuente,)))
                if not sop_ant or not sop_cons:
                    continue
                confianza = soporte[itemset] / sop_ant
                if confianza < min_confianza:
                    continue
                reglas.append(Regla(
                    antecedente=tuple(sorted(antecedente)), consecuente=consecuente,
                    soporte=soporte[itemset], confianza=confianza,
                    lift=confianza / sop_cons))

    reglas.sort(key=lambda r: (
        -r.lift, -r.confianza, -r.soporte, r.antecedente, r.consecuente))
    return reglas
