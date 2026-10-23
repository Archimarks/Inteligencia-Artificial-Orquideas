# Inteligencia Artificial Orquideas

Sistema de IA para descubrir patrones quimicos en plantas a partir de 52 articulos y 57 lotes de metabolomica
(LC/GC-MS) que abarcan especies de muchas familias botanicas (cultivos, plantas medicinales, frutales, cereales, etc.).

> **Sobre el nombre.** "Orquideas" es solo el nombre del proyecto. El estudio **no se centra en las orquideas**: analiza
> diferentes especies de plantas, y las orquideas (Orchidaceae) son apenas una familia mas dentro del conjunto de datos.

| Carpeta | Contenido |
|---|---|
| `01_Datos/Base` | Catalogos, muestras, registro de actividades y `Dataset.csv` (entrada, solo lectura) |
| `02_Script` | Codigo (`main.py`, `src/orquideas`), configuraciones YAML de los 18 experimentos y pruebas |
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
