# M14_tipo_cultivo - Tipo de cultivo a partir del perfil quimico

- Ejecucion: `20261022-091302_M14_tipo_cultivo_d2e28473` (2026-10-22T09:13:02, 382.2 s)
- Configuracion: `M14_tipo_cultivo.yaml` (huella `d2e284736d2e`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿El perfil quimico distingue el tipo de cultivo (silvestre, campo, invernadero, in vitro...) en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 882 de 918 (grupos: 49 de 49; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 5 (descartadas: 3; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.452 | 0.200 | 0.125 | 0.282 | 0.000 | 0.646 |
| baseline_estratificada | 0.100 | 0.338 | 0.196 | 0.193 | 0.319 | -0.015 | 0.567 |
| logistica | 0.200 | 0.346 | 0.282 | 0.283 | 0.335 | 0.020 | 0.756 |
| random_forest | 10.800 | 0.501 | 0.354 | 0.325 | 0.418 | 0.199 | 0.864 |
| lightgbm | 3.800 | 0.393 | 0.334 | 0.326 | 0.361 | 0.060 | 0.731 |

Mejor modelo: **random_forest**. balanced_accuracy = 0.354 frente a 0.200 del baseline y 0.142 del control solo-plataforma (ganancia sobre la mejor referencia +0.154); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.961. Sin agrupar por ID_ARTICULO la metrica sube +0.608: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Diterpenoids [clase_240]` (0.063), `clase: Indoles and derivatives [clase_364]` (0.045), `clase: Quinolines and derivatives [clase_661]` (0.044), `clase: Organonitrogen compounds [clase_505]` (0.040), `clase: otras [clase_otras]` (0.038), `clase: Aldehyde compounds [clase_31]` (0.036), `clase: Pyridine alkaloids [clase_629]` (0.033), `clase: Flavonoids [clase_285]` (0.031).

## Como interpretar
El tipo de cultivo suele ser constante dentro de un estudio; la senal puede deberse al estudio.

## Graficas
- `graficas/20261022-091302_M14_tipo_cultivo_d2e28473/comparacion_modelos.png`
- `graficas/20261022-091302_M14_tipo_cultivo_d2e28473/distribucion_clases.png`
- `graficas/20261022-091302_M14_tipo_cultivo_d2e28473/importancia_variables.png`
- `graficas/20261022-091302_M14_tipo_cultivo_d2e28473/matriz_confusion.png`
- `graficas/20261022-091302_M14_tipo_cultivo_d2e28473/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-091302_M14_tipo_cultivo_d2e28473/manifiesto.json`. Reejecutar: `python main.py ejecutar M14_tipo_cultivo`.
