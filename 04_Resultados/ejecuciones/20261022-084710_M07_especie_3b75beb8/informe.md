# M07_especie - Especie a partir del perfil quimico

- Ejecucion: `20261022-084710_M07_especie_3b75beb8` (2026-10-22T08:47:10, 12.0 s)
- Configuracion: `M07_especie.yaml` (huella `3b75beb8641b`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿El perfil quimico identifica la especie en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 48 de 942 (grupos: 4 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 2 (descartadas: 66; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.000 | 0.000 | 0.000 | 0.000 | -1.000 |
| baseline_estratificada | 0.000 | 0.396 | 0.394 | 0.393 | 0.398 | -0.210 |
| logistica | 0.100 | 0.562 | 0.500 | 0.360 | 0.405 | 0.000 |
| random_forest | 5.300 | 0.312 | 0.278 | 0.238 | 0.268 | -0.509 |
| lightgbm | 0.100 | 0.750 | 0.714 | 0.709 | 0.723 | 0.545 |

Mejor modelo: **lightgbm**. balanced_accuracy = 0.714 frente a 0.394 del baseline (ganancia +0.320); p de permutacion = 0.032; control solo-plataforma = 0.000; evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.286: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase_45` (0.737), `clase_479` (0.147), `clase_551` (0.060), `clase_265` (0.030), `clase_506` (0.013), `clase_101` (0.007), `clase_172` (0.003), `clase_595` (0.003).

## Como interpretar
Casi cada especie aparece en un solo articulo, por lo que la prediccion entre articulos no es evaluable; dentro de un articulo la especie se confunde con el lote. Se espera 'no viable' o sin senal.

## Graficas
- `graficas/20261022-084710_M07_especie_3b75beb8/comparacion_modelos.png`
- `graficas/20261022-084710_M07_especie_3b75beb8/distribucion_clases.png`
- `graficas/20261022-084710_M07_especie_3b75beb8/importancia_variables.png`
- `graficas/20261022-084710_M07_especie_3b75beb8/matriz_confusion.png`
- `graficas/20261022-084710_M07_especie_3b75beb8/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-084710_M07_especie_3b75beb8/manifiesto.json`. Reejecutar: `python main.py ejecutar M07_especie`.
