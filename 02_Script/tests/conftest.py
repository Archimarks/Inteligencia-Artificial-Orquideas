import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orquideas.utils.rutas import ruta  # noqa: E402

HAY_DATOS = ruta("datos", "dataset").exists() and ruta("datos", "dataset").stat().st_size > 10_000_000
requiere_datos = pytest.mark.skipif(not HAY_DATOS, reason="01_Datos/Base/Dataset.csv no disponible")
