# M01_modo_ionizacion - Modo de ionizacion (ESI+ / ESI-) a partir de la quimica del compuesto

- Ejecucion: `20261022-122116_M01_modo_ionizacion_341e48ea` (2026-10-22T12:21:16, 261.7 s)
- Configuracion: `M01_modo_ionizacion.yaml` (huella `341e48ea0b91`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿La composicion elemental y la superclase de un metabolito permiten anticipar si se detecta en ESI positivo o negativo, en articulos no vistos?

## Diseno
Unidad = (articulo, metabolito) detectado en un solo modo, solo en articulos que adquirieron ambos modos. X = descriptores de la formula (C, H, N, O, P, S, DBE, H/C, O/C, indice de aromaticidad...) + superclase. Sin m/z, aducto ni RT (fuga). Grupos = articulo.

## Unidad de analisis y precauciones
- Solo articulos con adquisicion en ESI+ y ESI-; se excluyen 142 pares detectados en ambos modos. No se usan m/z, aducto ni RT (codifican el modo). EI (GC-MS) no se incluye: depende de la plataforma, no del compuesto.

## Datos evaluados
- Unidades: 69686 de 69686 (grupos: 46 de 46; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 2 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 46

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 1.000 | 0.565 | 0.500 | 0.361 | 0.408 | 0.000 |
| baseline_estratificada | 1.000 | 0.512 | 0.503 | 0.503 | 0.512 | 0.006 |
| logistica | 1.600 | 0.618 | 0.620 | 0.616 | 0.619 | 0.237 |
| random_forest | 7.500 | 0.688 | 0.686 | 0.685 | 0.689 | 0.370 |
| lightgbm | 4.200 | 0.684 | 0.682 | 0.681 | 0.685 | 0.362 |
| xgboost | 8.100 | 0.685 | 0.682 | 0.681 | 0.685 | 0.362 |
| catboost | 35.600 | 0.683 | 0.680 | 0.679 | 0.683 | 0.359 |

Mejor modelo: **random_forest**. balanced_accuracy = 0.686 frente a 0.503 del baseline (ganancia sobre la mejor referencia +0.183); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.702.

Variables mas influyentes del modelo final: `O_C [O_C]` (0.119), `masa_formula [masa_formula]` (0.077), `H_C [H_C]` (0.075), `N_C [N_C]` (0.073), `dbe_C [dbe_C]` (0.068), `ai_mod [ai_mod]` (0.067), `n_O [n_O]` (0.063), `heteroatomos [heteroatomos]` (0.057).

## Como interpretar
Los acidos (carboxilos, fenoles, fosfatos) tienden a ionizar en negativo y las bases nitrogenadas en positivo. Un rendimiento moderado es esperable: muchos compuestos ionizan en ambos modos y la eleccion depende del metodo.

## Graficas
- `graficas\20261022-122116_M01_modo_ionizacion_341e48ea\comparacion_modelos.png`
- `graficas\20261022-122116_M01_modo_ionizacion_341e48ea\distribucion_clases.png`
- `graficas\20261022-122116_M01_modo_ionizacion_341e48ea\importancia_variables.png`
- `graficas\20261022-122116_M01_modo_ionizacion_341e48ea\matriz_confusion.png`
- `graficas\20261022-122116_M01_modo_ionizacion_341e48ea\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-122116_M01_modo_ionizacion_341e48ea/manifiesto.json`. Reejecutar: `python main.py ejecutar M01_modo_ionizacion`.
