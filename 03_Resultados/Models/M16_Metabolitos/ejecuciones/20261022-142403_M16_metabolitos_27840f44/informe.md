# M16_metabolitos - Presencia de metabolitos frecuentes a partir de taxonomia y tipo de muestra

- Ejecucion: `20261022-142403_M16_metabolitos_27840f44` (2026-10-22T14:24:03, 3540.4 s)
- Configuracion: `M16_metabolitos.yaml` (huella `27840f4487cb`), semilla 42
- Estado: **completado** - Veredicto: **confundido con plataforma**

## Pregunta cientifica
Dado el taxon (clase, orden, familia), la parte de la planta, el tipo de muestra, el cultivo y la extraccion, ¿que metabolitos frecuentes cabe esperar en una planta de un estudio no visto?

## Diseno
Unidad = grupo de muestras (lote x especie x parte x tipo x cultivo x metodo). Y = presencia (0/1) de los 60 metabolitos presentes en mas articulos (>= 5). X = one-hot de taxonomia y atributos de muestra. Multietiqueta, grupos = articulo. Control = solo plataforma (columna, modos, profundidad de identificacion).

## Unidad de analisis y precauciones
- Etiquetas = 60 metabolitos presentes en >= 5 articulos. Un metabolito ausente puede no estar en la biblioteca del laboratorio: la presencia mezcla quimica de la planta y cobertura de la biblioteca (por eso se compara con un control que solo usa la plataforma).

## Datos evaluados
- Unidades: 129 de 129 (grupos: 49 de 49; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 60 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 129

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | f1_micro | f1_macro | hamming_loss | subset_accuracy | roc_auc_macro | average_precision_macro | prevalencia_media |
|---|---|---|---|---|---|---|---|---|
| baseline_prior | 0.400 | 0.285 | 0.160 | 0.461 | 0.000 | 0.358 | 0.364 | 0.426 |
| logistica | 3.100 | 0.492 | 0.477 | 0.434 | 0.000 | 0.550 | 0.499 | 0.426 |
| random_forest | 4.400 | 0.389 | 0.344 | 0.507 | 0.000 | 0.435 | 0.413 | 0.426 |
| knn | 0.400 | 0.293 | 0.268 | 0.522 | 0.000 | 0.460 | 0.424 | 0.426 |
| xgboost | 216.000 | 0.440 | 0.429 | 0.551 | 0.000 | 0.448 | 0.443 | 0.426 |
| catboost | 3287.800 | 0.495 | 0.482 | 0.478 | 0.000 | 0.525 | 0.473 | 0.426 |

Mejor modelo: **logistica**. average_precision_macro = 0.499 frente a 0.364 del baseline y 0.591 del control solo-plataforma (ganancia sobre la mejor referencia -0.091); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.881. Sin agrupar por ID_ARTICULO la metrica sube +0.382: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

Variables mas influyentes del modelo final: `FAMILIA: Asphodelaceae [ID_FAMILIA_6]` (0.019), `FAMILIA: Orchidaceae [ID_FAMILIA_21]` (0.019), `FAMILIA: Pedaliaceae [ID_FAMILIA_24]` (0.018), `FAMILIA: Rosaceae [ID_FAMILIA_29]` (0.018), `FAMILIA: Ericaceae [ID_FAMILIA_13]` (0.017), `METODO_EXTRACCION: Metanol 80% con 2-clorofenilalanina como estandar interno [ID_METODO_EXTRACCION_17]` (0.017), `METODO_EXTRACCION: Metanol:acetonitrilo:agua (2:2:1, v/v/v) [ID_METODO_EXTRACCION_7]` (0.016), `TIPO_CULTIVO: Material comercial [ID_TIPO_CULTIVO_8]` (0.016).

## Como interpretar
La presencia depende de la biblioteca del laboratorio tanto como de la planta: si el control solo-plataforma iguala al modelo, lo que se predice es la cobertura de la biblioteca, no la quimica del taxon. La precision promedio debe compararse con la prevalencia de cada metabolito.

## Graficas
- `graficas\20261022-142403_M16_metabolitos_27840f44\ap_por_etiqueta.png`
- `graficas\20261022-142403_M16_metabolitos_27840f44\comparacion_modelos.png`
- `graficas\20261022-142403_M16_metabolitos_27840f44\distribucion_clases.png`
- `graficas\20261022-142403_M16_metabolitos_27840f44\importancia_variables.png`
- `graficas\20261022-142403_M16_metabolitos_27840f44\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-142403_M16_metabolitos_27840f44/manifiesto.json`. Reejecutar: `python main.py ejecutar M16_metabolitos`.
