# M13_parte_planta - Parte de la planta a partir del perfil quimico

- Ejecucion: `20261022-141838_M13_parte_planta_b6fb0605` (2026-10-22T14:18:38, 78.3 s)
- Configuracion: `M13_parte_planta.yaml` (huella `b6fb06059d81`), semilla 42
- Estado: **completado** - Veredicto: **sin senal**

## Pregunta cientifica
¿El perfil quimico permite reconocer el organo analizado (hoja, raiz, fruto, flor...) en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 772 de 930 (grupos: 44 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 9 (descartadas: 19; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.303 | 0.111 | 0.052 | 0.141 | 0.000 | 0.392 |
| baseline_estratificada | 0.100 | 0.149 | 0.093 | 0.087 | 0.140 | -0.021 | 0.240 |
| logistica | 0.300 | 0.161 | 0.141 | 0.134 | 0.160 | 0.027 | 0.342 |
| random_forest | 4.500 | 0.181 | 0.069 | 0.053 | 0.135 | -0.011 | 0.354 |
| lightgbm | 4.500 | 0.170 | 0.077 | 0.070 | 0.146 | -0.008 | 0.541 |
| xgboost | 23.600 | 0.084 | 0.039 | 0.042 | 0.086 | -0.079 | 0.391 |
| catboost | 31.900 | 0.181 | 0.098 | 0.100 | 0.164 | 0.000 | 0.370 |

Mejor modelo: **logistica**. balanced_accuracy = 0.141 frente a 0.111 del baseline y 0.086 del control solo-plataforma (ganancia sobre la mejor referencia +0.030); p de permutacion = 0.065; evaluacion sin agrupar = 0.886. Sin agrupar por ID_ARTICULO la metrica sube +0.744: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Steroids [clase_705]` (0.034), `clase: Triterpene [clase_774]` (0.031), `clase: Other Flavonoids [clase_513]` (0.028), `clase: otras [clase_otras]` (0.026), `clase: Lactones [clase_403]` (0.025), `clase: Phenylpropanoids (C6-C3) [clase_562]` (0.024), `clase: Pyridines and derivatives [clase_633]` (0.022), `clase: Imidazopyrimidines [clase_352]` (0.022).

## Como interpretar
Comparar con M18 (varianza intra-articulo por parte) para separar quimica del organo y efecto del estudio.

## Graficas
- `graficas\20261022-141838_M13_parte_planta_b6fb0605\comparacion_modelos.png`
- `graficas\20261022-141838_M13_parte_planta_b6fb0605\distribucion_clases.png`
- `graficas\20261022-141838_M13_parte_planta_b6fb0605\importancia_variables.png`
- `graficas\20261022-141838_M13_parte_planta_b6fb0605\matriz_confusion.png`
- `graficas\20261022-141838_M13_parte_planta_b6fb0605\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-141838_M13_parte_planta_b6fb0605/manifiesto.json`. Reejecutar: `python main.py ejecutar M13_parte_planta`.
