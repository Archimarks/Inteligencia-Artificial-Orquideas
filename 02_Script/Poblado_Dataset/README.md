# Poblado de 01_Datos/Dataset

Scripts que generan los catálogos, la tabla pivote y `Dataset.csv` a partir de
`01_Datos/Data/Batch` (57 batches) y `01_Datos/Data/Articulos` (52 artículos).

1. `python parse.py` — lee cada batch y lo normaliza a formato largo (pickles en `parsed/`).
2. `python build.py` — arma los catálogos, `06_Muestras_Batch.csv`,
   `05_Pivotes/Registo_Actividades_biologicas.csv` y `Dataset.csv`.
3. `python validate.py ../../01_Datos/Dataset` — verifica todas las claves foráneas.

La información curada a mano (taxonomía, partes, cultivo, extracción, columnas,
actividades por artículo y valores medidos) está en `catalogos_def.py`,
`batch_def.py`, `actividades_def.py` y `medidas.py`; `notas_articulos.md`
resume la revisión de cada artículo.
