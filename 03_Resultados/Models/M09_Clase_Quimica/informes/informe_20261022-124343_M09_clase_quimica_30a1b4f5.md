# M09_clase_quimica - Clase quimica a partir de la formula molecular

- Ejecucion: `20261022-124343_M09_clase_quimica_30a1b4f5` (2026-10-22T12:43:43, 2308.1 s)
- Configuracion: `M09_clase_quimica.yaml` (huella `30a1b4f5f669`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿La formula molecular permite asignar la clase quimica (nivel fino de la ontologia) de un metabolito?

## Diseno
Igual que M08 pero con las 40 clases quimicas mas frecuentes (>= 50 metabolitos y >= 5 formulas). Grupos = formula.

## Unidad de analisis y precauciones
- Grupos = formula molecular: los isomeros comparten formula y nunca quedan repartidos entre entrenamiento y prueba. Las formulas deuteradas (estandares internos) y las no interpretables se excluyen.

## Datos evaluados
- Unidades: 23337 de 31115 (grupos: 10284 de 12900; columna de grupo `FORMULA`)
- Clases/etiquetas evaluables: 40 (descartadas: 678; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 24

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.200 | 0.123 | 0.025 | 0.005 | 0.027 | 0.000 | 0.141 |
| baseline_estratificada | 0.200 | 0.053 | 0.024 | 0.024 | 0.053 | 0.000 | 0.071 |
| logistica | 8.900 | 0.302 | 0.347 | 0.236 | 0.283 | 0.282 | 0.555 |
| random_forest | 5.300 | 0.431 | 0.404 | 0.353 | 0.426 | 0.404 | 0.715 |
| lightgbm | 69.000 | 0.423 | 0.352 | 0.342 | 0.424 | 0.393 | 0.725 |
| xgboost | 207.500 | 0.420 | 0.403 | 0.352 | 0.420 | 0.394 | 0.723 |
| catboost | 89.400 | 0.390 | 0.426 | 0.328 | 0.382 | 0.369 | 0.690 |

Mejor modelo: **catboost**. balanced_accuracy = 0.426 frente a 0.025 del baseline (ganancia sobre la mejor referencia +0.401); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.447.

Variables mas influyentes del modelo final: `O_C [O_C]` (0.140), `dbe [dbe]` (0.109), `dbe_C [dbe_C]` (0.104), `H_C [H_C]` (0.093), `n_C [n_C]` (0.077), `n_atomos_pesados [n_atomos_pesados]` (0.072), `N_C [N_C]` (0.070), `n_H [n_H]` (0.063).

## Como interpretar
Problema mas dificil que M08 por el numero de clases y los isomeros; comparar con top3_accuracy.

## Graficas
- `graficas\20261022-124343_M09_clase_quimica_30a1b4f5\comparacion_modelos.png`
- `graficas\20261022-124343_M09_clase_quimica_30a1b4f5\distribucion_clases.png`
- `graficas\20261022-124343_M09_clase_quimica_30a1b4f5\importancia_variables.png`
- `graficas\20261022-124343_M09_clase_quimica_30a1b4f5\matriz_confusion.png`
- `graficas\20261022-124343_M09_clase_quimica_30a1b4f5\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-124343_M09_clase_quimica_30a1b4f5/manifiesto.json`. Reejecutar: `python main.py ejecutar M09_clase_quimica`.
