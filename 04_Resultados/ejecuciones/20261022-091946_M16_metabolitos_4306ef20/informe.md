# M16_metabolitos - Presencia de metabolitos frecuentes a partir de taxonomia y tipo de muestra

- Ejecucion: `20261022-091946_M16_metabolitos_4306ef20` (2026-10-22T09:19:46, 55.1 s)
- Configuracion: `M16_metabolitos.yaml` (huella `4306ef20065b`), semilla 42
- Estado: **completado** - Veredicto: **confundido con plataforma**

## Pregunta cientifica
Dado el taxon (clase, orden, familia), la parte de la planta, el tipo de muestra, el cultivo y la extraccion, ¿que metabolitos frecuentes cabe esperar en una planta de un estudio no visto?

## Diseno
Unidad = grupo de muestras (lote x especie x parte x tipo x cultivo x metodo). Y = presencia (0/1) de los 60 metabolitos presentes en mas articulos (>= 5). X = one-hot de taxonomia y atributos de muestra. Multietiqueta, grupos = articulo. Control = solo plataforma (columna, modos, profundidad de identificacion).

## Unidad de analisis y precauciones
- Etiquetas = 60 metabolitos presentes en >= 5 articulos. Un metabolito ausente puede no estar en la biblioteca del laboratorio: la presencia mezcla quimica de la planta y cobertura de la biblioteca (por eso se compara con un control que solo usa la plataforma).

## Datos evaluados
- Unidades: 128 de 128 (grupos: 48 de 48; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 60 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 128

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | f1_micro | f1_macro | hamming_loss | subset_accuracy | roc_auc_macro | average_precision_macro | prevalencia_media |
|---|---|---|---|---|---|---|---|---|
| baseline_prior | 0.400 | 0.232 | 0.130 | 0.475 | 0.000 | 0.334 | 0.359 | 0.432 |
| logistica | 2.800 | 0.446 | 0.435 | 0.497 | 0.000 | 0.479 | 0.454 | 0.432 |
| random_forest | 8.500 | 0.417 | 0.388 | 0.524 | 0.000 | 0.432 | 0.417 | 0.432 |
| knn | 0.500 | 0.277 | 0.246 | 0.484 | 0.000 | 0.456 | 0.427 | 0.432 |

Mejor modelo: **logistica**. average_precision_macro = 0.454 frente a 0.359 del baseline y 0.583 del control solo-plataforma (ganancia sobre la mejor referencia -0.129); p de permutacion = 0.258; evaluacion sin agrupar = 0.883. Sin agrupar por ID_ARTICULO la metrica sube +0.429: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

Variables mas influyentes del modelo final: `FAMILIA: Asphodelaceae [ID_FAMILIA_6]` (0.019), `FAMILIA: Orchidaceae [ID_FAMILIA_21]` (0.019), `FAMILIA: Pedaliaceae [ID_FAMILIA_24]` (0.018), `FAMILIA: Rosaceae [ID_FAMILIA_29]` (0.017), `FAMILIA: Ericaceae [ID_FAMILIA_13]` (0.017), `METODO_EXTRACCION: Metanol 80% con 2-clorofenilalanina como estandar interno [ID_METODO_EXTRACCION_17]` (0.017), `METODO_EXTRACCION: Metanol 80%, ultrasonido 30 min a 35-40 C [ID_METODO_EXTRACCION_27]` (0.016), `TIPO_CULTIVO: Material comercial [ID_TIPO_CULTIVO_8]` (0.016).

## Como interpretar
La presencia depende de la biblioteca del laboratorio tanto como de la planta: si el control solo-plataforma iguala al modelo, lo que se predice es la cobertura de la biblioteca, no la quimica del taxon. La precision promedio debe compararse con la prevalencia de cada metabolito.

## Graficas
- `graficas/20261022-091946_M16_metabolitos_4306ef20/ap_por_etiqueta.png`
- `graficas/20261022-091946_M16_metabolitos_4306ef20/comparacion_modelos.png`
- `graficas/20261022-091946_M16_metabolitos_4306ef20/distribucion_clases.png`
- `graficas/20261022-091946_M16_metabolitos_4306ef20/importancia_variables.png`
- `graficas/20261022-091946_M16_metabolitos_4306ef20/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-091946_M16_metabolitos_4306ef20/manifiesto.json`. Reejecutar: `python main.py ejecutar M16_metabolitos`.
