# M10_aducto - Tipo de aducto a partir de la quimica del compuesto y el modo

- Ejecucion: `20261022-132211_M10_aducto_504ff3b8` (2026-10-22T13:22:11, 1436.1 s)
- Configuracion: `M10_aducto.yaml` (huella `504ff3b8ee86`), semilla 42
- Estado: **completado** - Veredicto: **senal debil**

## Pregunta cientifica
¿La formula, la superclase y el modo de ionizacion permiten anticipar que aducto se informara para un metabolito en un estudio no visto?

## Diseno
Unidad = (articulo, metabolito, aducto) con aducto informado (15 aductos mas frecuentes entre articulos). X = descriptores de formula + modo + superclase. m/z excluida (m/z - masa = masa del aducto). Grupos = articulo. Control instrumental = solo el modo.

## Unidad de analisis y precauciones
- Se modelan los 15 aductos informados en mas articulos. m/z queda excluida: m/z - masa = masa del aducto (fuga directa). El control instrumental usa solo el modo de ionizacion.

## Datos evaluados
- Unidades: 57550 de 57550 (grupos: 38 de 38; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 15 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 47

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.900 | 0.345 | 0.067 | 0.034 | 0.177 | 0.000 | 0.358 |
| baseline_estratificada | 0.900 | 0.225 | 0.066 | 0.066 | 0.225 | -0.000 | 0.238 |
| logistica | 8.400 | 0.306 | 0.213 | 0.161 | 0.382 | 0.231 | 0.570 |
| random_forest | 8.700 | 0.434 | 0.236 | 0.205 | 0.491 | 0.334 | 0.748 |
| lightgbm | 38.600 | 0.419 | 0.235 | 0.202 | 0.480 | 0.324 | 0.745 |
| xgboost | 104.400 | 0.395 | 0.242 | 0.199 | 0.464 | 0.307 | 0.712 |
| catboost | 62.500 | 0.381 | 0.245 | 0.195 | 0.453 | 0.296 | 0.686 |

Mejor modelo: **catboost**. balanced_accuracy = 0.245 frente a 0.067 del baseline y 0.137 del control solo-plataforma (ganancia sobre la mejor referencia +0.108); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.335.

Variables mas influyentes del modelo final: `MODO_IONIZACION: Positivo [ID_MODO_IONIZACION_1]` (0.256), `O_C [O_C]` (0.072), `masa_formula [masa_formula]` (0.063), `N_C [N_C]` (0.053), `n_H [n_H]` (0.053), `dbe_C [dbe_C]` (0.052), `H_C [H_C]` (0.047), `MODO_IONIZACION: Negativo [ID_MODO_IONIZACION_2]` (0.039).

## Como interpretar
El modo determina la polaridad del aducto ([M+H]+ vs [M-H]-); el valor de la quimica se mide como la mejora sobre el control que solo usa el modo.

## Graficas
- `graficas\20261022-132211_M10_aducto_504ff3b8\comparacion_modelos.png`
- `graficas\20261022-132211_M10_aducto_504ff3b8\distribucion_clases.png`
- `graficas\20261022-132211_M10_aducto_504ff3b8\importancia_variables.png`
- `graficas\20261022-132211_M10_aducto_504ff3b8\matriz_confusion.png`
- `graficas\20261022-132211_M10_aducto_504ff3b8\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-132211_M10_aducto_504ff3b8/manifiesto.json`. Reejecutar: `python main.py ejecutar M10_aducto`.
