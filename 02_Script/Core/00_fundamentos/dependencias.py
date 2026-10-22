#
# Archivo: dependencias.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Comprueba e instala, solo si faltan, las dependencias principales del flujo
# de entrenamiento no supervisado.
#
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from importlib import metadata

_MODULOS_DISTRIBUCIONES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "sklearn": "scikit-learn",
    "joblib": "joblib",
    "matplotlib": "matplotlib",
    "psutil": "psutil",
}
_PATRON_REQUISITO = re.compile(r"^([A-Za-z0-9_.-]+)\s*(==[^;\s]+)")


def verificar_e_instalar() -> None:
    """Instala desde requirements.txt las dependencias de ejecución ausentes."""
    raiz = Path(__file__).resolve().parents[3]
    archivo_requisitos = raiz / "requirements.txt"
    versiones: dict[str, str] = {}
    with archivo_requisitos.open(encoding="utf-8") as archivo:
        for linea in archivo:
            coincidencia = _PATRON_REQUISITO.match(linea.strip())
            if coincidencia:
                nombre, pin = coincidencia.groups()
                normalizado = re.sub(r"[-_.]+", "-", nombre).lower()
                versiones[normalizado] = f"{nombre}{pin}"

    faltantes = []
    for modulo, distribucion in _MODULOS_DISTRIBUCIONES.items():
        nombre_normalizado = re.sub(r"[-_.]+", "-", distribucion).lower()
        requisito = versiones.get(nombre_normalizado)
        if requisito is None:
            raise RuntimeError(
                f"{distribucion} es necesaria pero no tiene una version fijada en "
                f"{archivo_requisitos}.")
        version_requerida = requisito.split("==", 1)[1]
        try:
            version_instalada = metadata.version(distribucion)
        except metadata.PackageNotFoundError:
            version_instalada = None
        if (importlib.util.find_spec(modulo) is None or
                version_instalada != version_requerida):
            faltantes.append((modulo, distribucion, requisito, version_instalada))

    if not faltantes:
        print("Dependencias principales: verificadas.")
        return

    a_instalar = []
    for _, distribucion, requisito, _ in faltantes:
        a_instalar.append(requisito)

    print("Dependencias ausentes o con version distinta: " +
          ", ".join(distribucion for _, distribucion, _, _ in faltantes))
    print("Instalando versiones fijadas en requirements.txt...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *a_instalar],
        check=True,
    )
    print("Dependencias instaladas correctamente.")
