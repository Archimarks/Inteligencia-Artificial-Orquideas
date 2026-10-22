# M17_actividades_especie - Actividades biologicas de una especie a partir de su perfil quimico

- Ejecucion: `20261022-092041_M17_actividades_especie_c5142b20` (2026-10-22T09:20:41, 267.2 s)
- Configuracion: `M17_actividades_especie.yaml` (huella `c5142b2026c4`), semilla 42
- Estado: **completado** - Veredicto: **confundido con plataforma**

## Pregunta cientifica
¿El perfil composicional de una especie (superclases quimicas) permite anticipar que actividades biologicas se le atribuyen?

## Diseno
Unidad = especie x articulo con actividad registrada y perfil (>= 20 metabolitos). Y = actividades (multietiqueta) con >= 8 unidades positivas. X = CLR por superclase. Grupos = articulo.

## Unidad de analisis y precauciones
- Unidad = especie x articulo (casi siempre una por articulo). Actividades mayoritariamente bibliograficas: positivos sin negativos verificados (PU). Solo se incluyen especies con alguna actividad registrada.

## Datos evaluados
- Unidades: 60 de 60 (grupos: 44 de 44; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 16 (descartadas: 0; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 20

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | f1_micro | f1_macro | hamming_loss | subset_accuracy | roc_auc_macro | average_precision_macro | prevalencia_media |
|---|---|---|---|---|---|---|---|---|
| baseline_prior | 0.200 | 0.541 | 0.164 | 0.249 | 0.033 | 0.272 | 0.300 | 0.355 |
| logistica | 0.400 | 0.476 | 0.392 | 0.412 | 0.000 | 0.499 | 0.396 | 0.355 |
| random_forest | 5.000 | 0.564 | 0.302 | 0.263 | 0.017 | 0.473 | 0.416 | 0.355 |
| knn | 0.300 | 0.547 | 0.360 | 0.318 | 0.033 | 0.509 | 0.405 | 0.355 |

Mejor modelo: **random_forest**. average_precision_macro = 0.416 frente a 0.300 del baseline y 0.437 del control solo-plataforma (ganancia sobre la mejor referencia -0.022); p de permutacion = 0.020 (minimo alcanzable con 50 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.700. Sin agrupar por ID_ARTICULO la metrica sube +0.285: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

Variables mas influyentes del modelo final: `superclase: Organic nitrogen compounds [superclase_14]` (0.084), `superclase: Organoheterocyclic compounds [superclase_17]` (0.073), `superclase: Homogeneous non-metal compounds [superclase_4]` (0.071), `superclase: Organosulfur compounds [superclase_20]` (0.068), `superclase: Lignans, neolignans and related compounds [superclase_7]` (0.066), `superclase: Alkaloids and derivatives [superclase_1]` (0.061), `superclase: Benzenoids [superclase_2]` (0.055), `superclase: Phenylpropanoids and polyketides [superclase_21]` (0.049).

## Como interpretar
Etiquetas positivas-no etiquetadas: una actividad ausente puede no haberse estudiado. Con ~60 unidades la incertidumbre es grande; solo una mejora clara sobre la prevalencia y p < 0.05 sugiere senal.

## Graficas
- `graficas/20261022-092041_M17_actividades_especie_c5142b20/ap_por_etiqueta.png`
- `graficas/20261022-092041_M17_actividades_especie_c5142b20/comparacion_modelos.png`
- `graficas/20261022-092041_M17_actividades_especie_c5142b20/distribucion_clases.png`
- `graficas/20261022-092041_M17_actividades_especie_c5142b20/importancia_variables.png`
- `graficas/20261022-092041_M17_actividades_especie_c5142b20/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-092041_M17_actividades_especie_c5142b20/manifiesto.json`. Reejecutar: `python main.py ejecutar M17_actividades_especie`.
