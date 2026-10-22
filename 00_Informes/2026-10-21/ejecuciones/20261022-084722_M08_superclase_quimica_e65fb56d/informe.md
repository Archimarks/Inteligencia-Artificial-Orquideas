# M08_superclase_quimica - Superclase quimica a partir de la formula molecular

- Ejecucion: `20261022-084722_M08_superclase_quimica_e65fb56d` (2026-10-22T08:47:22, 343.9 s)
- Configuracion: `M08_superclase_quimica.yaml` (huella `e65fb56de316`), semilla 42
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
| baseline_mayoritaria | 0.400 | 0.245 | 0.077 | 0.030 | 0.097 | 0.000 | 0.441 |
| baseline_estratificada | 0.400 | 0.168 | 0.078 | 0.078 | 0.168 | 0.001 | 0.342 |
| logistica | 21.200 | 0.481 | 0.530 | 0.328 | 0.512 | 0.415 | 0.767 |
| random_forest | 13.000 | 0.633 | 0.537 | 0.498 | 0.633 | 0.562 | 0.871 |
| lightgbm | 35.800 | 0.603 | 0.520 | 0.483 | 0.615 | 0.532 | 0.864 |

Mejor modelo: **random_forest**. balanced_accuracy = 0.537 frente a 0.078 del baseline (ganancia sobre la mejor referencia +0.459); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.561.

Variables mas influyentes del modelo final: `O_C [O_C]` (0.109), `heteroatomos [heteroatomos]` (0.091), `dbe_C [dbe_C]` (0.083), `H_C [H_C]` (0.077), `n_O [n_O]` (0.072), `N_C [N_C]` (0.072), `masa_formula [masa_formula]` (0.066), `ai_mod [ai_mod]` (0.065).

## Como interpretar
La formula restringe la clase (p. ej. N para alcaloides, O/C alto para glicosidos), pero muchos isomeros pertenecen a clases distintas: hay un techo de rendimiento irreducible sin estructura.

## Graficas
- `graficas/20261022-084722_M08_superclase_quimica_e65fb56d/comparacion_modelos.png`
- `graficas/20261022-084722_M08_superclase_quimica_e65fb56d/distribucion_clases.png`
- `graficas/20261022-084722_M08_superclase_quimica_e65fb56d/importancia_variables.png`
- `graficas/20261022-084722_M08_superclase_quimica_e65fb56d/matriz_confusion.png`
- `graficas/20261022-084722_M08_superclase_quimica_e65fb56d/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-084722_M08_superclase_quimica_e65fb56d/manifiesto.json`. Reejecutar: `python main.py ejecutar M08_superclase_quimica`.
