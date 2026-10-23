# M08_superclase_quimica - Superclase quimica a partir de la formula molecular

- Ejecucion: `20261022-122538_M08_superclase_quimica_b36a204e` (2026-10-22T12:25:38, 1084.0 s)
- Configuracion: `M08_superclase_quimica.yaml` (huella `b36a204ece39`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿La composicion elemental de un metabolito (solo su formula) permite asignar su superclase quimica, incluso para formulas no vistas?

## Diseno
Unidad = metabolito identificado con formula interpretable y clase conocida. X = 24 descriptores elementales. Grupos = formula molecular (los isomeros nunca se reparten entre entrenamiento y prueba).

## Unidad de analisis y precauciones
- Grupos = formula molecular: los isomeros comparten formula y nunca quedan repartidos entre entrenamiento y prueba. Las formulas deuteradas (estandares internos) y las no interpretables se excluyen.

## Datos evaluados
- Unidades: 31055 de 31115 (grupos: 12851 de 12900; columna de grupo `FORMULA`)
- Clases/etiquetas evaluables: 13 (descartadas: 6; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 24

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.300 | 0.245 | 0.077 | 0.030 | 0.097 | 0.000 | 0.441 |
| baseline_estratificada | 0.300 | 0.168 | 0.078 | 0.078 | 0.168 | 0.001 | 0.342 |
| logistica | 7.500 | 0.481 | 0.530 | 0.328 | 0.512 | 0.414 | 0.768 |
| random_forest | 4.800 | 0.633 | 0.537 | 0.498 | 0.633 | 0.562 | 0.871 |
| lightgbm | 23.900 | 0.603 | 0.520 | 0.483 | 0.615 | 0.532 | 0.864 |
| xgboost | 70.100 | 0.597 | 0.556 | 0.483 | 0.611 | 0.528 | 0.859 |
| catboost | 42.300 | 0.585 | 0.575 | 0.450 | 0.602 | 0.518 | 0.847 |

Mejor modelo: **catboost**. balanced_accuracy = 0.575 frente a 0.078 del baseline (ganancia sobre la mejor referencia +0.497); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.589.

Variables mas influyentes del modelo final: `N_C [N_C]` (0.191), `O_C [O_C]` (0.141), `dbe_C [dbe_C]` (0.109), `H_C [H_C]` (0.082), `heteroatomos [heteroatomos]` (0.076), `dbe [dbe]` (0.065), `n_O [n_O]` (0.048), `masa_formula [masa_formula]` (0.045).

## Como interpretar
La formula restringe la clase (p. ej. N para alcaloides, O/C alto para glicosidos), pero muchos isomeros pertenecen a clases distintas: hay un techo de rendimiento irreducible sin estructura.

## Graficas
- `graficas\20261022-122538_M08_superclase_quimica_b36a204e\comparacion_modelos.png`
- `graficas\20261022-122538_M08_superclase_quimica_b36a204e\distribucion_clases.png`
- `graficas\20261022-122538_M08_superclase_quimica_b36a204e\importancia_variables.png`
- `graficas\20261022-122538_M08_superclase_quimica_b36a204e\matriz_confusion.png`
- `graficas\20261022-122538_M08_superclase_quimica_b36a204e\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-122538_M08_superclase_quimica_b36a204e/manifiesto.json`. Reejecutar: `python main.py ejecutar M08_superclase_quimica`.
