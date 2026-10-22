# Inteligencia Artificial Orquideas

Sistema de IA para descubrir patrones quimicos en orquideas y plantas medicinales a partir de 52 articulos y 57 lotes
de metabolomica (LC/GC-MS).

| Carpeta | Contenido |
|---|---|
| `01_Datos/Base` | Catalogos, muestras, registro de actividades y `Dataset.csv` (entrada, solo lectura) |
| `02_Script` | Codigo (`main.py`, `src/orquideas`), configuraciones YAML de los 18 experimentos y pruebas |
| `03_Modelos_Entrenados` | Modelos finales por experimento y ejecucion |
| `04_Resultados` | Auditoria, ejecuciones, metricas, predicciones, graficas e informes |
| `05_Documentacion` | Arquitectura, diccionario de datos, metodologia, guia de modelos, limitaciones e informe cientifico |

Inicio rapido:

```bash
python -m pip install -r requirements.txt
cd 02_Script
python main.py auditoria
python main.py ejecutar-todos
python main.py resumen
```

Detalles en `02_Script/README.md`. Resultados en `04_Resultados/informes/resumen_ejecutivo.md` y
`05_Documentacion/informe_cientifico.md`.
