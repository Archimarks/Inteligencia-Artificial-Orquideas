# Inteligencia Artificial 

Sistema de IA para descubrir patrones quimicos en plantas medicinales a partir de 52 articulos y 57 lotes
de metabolomica (LC/GC-MS).

| Carpeta | Contenido |
|---|---|
| `01_Datos/Base` | Catalogos, muestras, registro de actividades y `Dataset.csv` (entrada, solo lectura) |
| `02_Script` | Codigo (`main.py`, `src/`), configuraciones YAML de los 18 experimentos y pruebas |
| `03_Resultados/Global` | Auditoria general de datos, resumen ejecutivo, informe cientifico y comparacion de modelos |
| `03_Resultados/Models/<Modelo>` | Por modelo: auditoria_datos, ejecuciones, metricas, graficas, predicciones, informes y modelo_entrenado |
| `05_Documentacion` | Arquitectura, diccionario de datos, metodologia, guia de modelos, limitaciones e informe cientifico |

Inicio rapido:

```bash
cd 02_Script
python -m pip install -r requirements.txt
python main.py                 # interfaz: maquina -> datos -> modelos -> opciones -> entrenamiento
python main.py hardware        # GPU detectadas (se usan todas)
python main.py auditoria
python main.py ejecutar-todos
python main.py resumen
```

Detalles en `02_Script/README.md`. Resultados en `03_Resultados/Global/resumen_ejecutivo.md` y
`05_Documentacion/informe_cientifico.md`.
