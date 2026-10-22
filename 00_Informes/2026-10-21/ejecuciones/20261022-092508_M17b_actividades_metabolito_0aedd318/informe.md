# M17b_actividades_metabolito - Actividades biologicas de un metabolito a partir de su formula y superclase

- Ejecucion: `20261022-092508_M17b_actividades_metabolito_0aedd318` (2026-10-22T09:25:08, 11.0 s)
- Configuracion: `M17b_actividades_metabolito.yaml` (huella `0aedd318762e`), semilla 42
- Estado: **completado** - Veredicto: **senal debil**

## Pregunta cientifica
¿La composicion elemental y la superclase de un metabolito con actividad citada permiten anticipar que tipo de actividad se le atribuye?

## Diseno
Unidad = metabolito con actividad registrada en la literatura citada por los articulos. Y = actividades con >= 10 metabolitos. X = descriptores de formula + superclase. Grupos = formula.

## Unidad de analisis y precauciones
- Etiquetas positivas-no etiquetadas (PU): una actividad no registrada no significa inactividad. Solo hay metabolitos con alguna actividad citada, de modo que el modelo aprende que actividad, no si es activo.

## Datos evaluados
- Unidades: 93 de 93 (grupos: 75 de 75; columna de grupo `FORMULA_MOLECULAR`)
- Clases/etiquetas evaluables: 6 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 35

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | f1_micro | f1_macro | hamming_loss | subset_accuracy | roc_auc_macro | average_precision_macro | prevalencia_media |
|---|---|---|---|---|---|---|---|---|
| baseline_prior | 0.100 | 0.535 | 0.227 | 0.296 | 0.194 | 0.351 | 0.292 | 0.341 |
| logistica | 0.200 | 0.480 | 0.438 | 0.427 | 0.043 | 0.517 | 0.395 | 0.341 |
| random_forest | 3.700 | 0.477 | 0.325 | 0.310 | 0.161 | 0.595 | 0.419 | 0.341 |
| knn | 0.200 | 0.522 | 0.375 | 0.319 | 0.172 | 0.608 | 0.436 | 0.341 |

Mejor modelo: **knn**. average_precision_macro = 0.436 frente a 0.292 del baseline (ganancia sobre la mejor referencia +0.144); p de permutacion = 0.039; evaluacion sin agrupar = 0.496.

## Como interpretar
Muy pocos metabolitos (~90) y sesgo de publicacion: compuestos famosos acumulan muchas actividades citadas.

## Graficas
- `graficas/20261022-092508_M17b_actividades_metabolito_0aedd318/ap_por_etiqueta.png`
- `graficas/20261022-092508_M17b_actividades_metabolito_0aedd318/comparacion_modelos.png`
- `graficas/20261022-092508_M17b_actividades_metabolito_0aedd318/distribucion_clases.png`
- `graficas/20261022-092508_M17b_actividades_metabolito_0aedd318/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-092508_M17b_actividades_metabolito_0aedd318/manifiesto.json`. Reejecutar: `python main.py ejecutar M17b_actividades_metabolito`.
