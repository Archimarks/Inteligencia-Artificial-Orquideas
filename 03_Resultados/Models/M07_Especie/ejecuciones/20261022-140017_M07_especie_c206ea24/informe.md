# M07_especie - Especie a partir del perfil quimico

- Ejecucion: `20261022-140017_M07_especie_c206ea24` (2026-10-22T14:00:17, 40.8 s)
- Configuracion: `M07_especie.yaml` (huella `c206ea24a918`), semilla 42
- Estado: **completado** - Veredicto: **evidencia insuficiente**

## Pregunta cientifica
¿El perfil quimico identifica la especie en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 48 de 942 (grupos: 4 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 2 (descartadas: 66; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | -1.000 |
| baseline_estratificada | 0.000 | 0.396 | 0.394 | 0.393 | 0.398 | -0.210 |
| logistica | 0.100 | 0.562 | 0.500 | 0.360 | 0.405 | 0.000 |
| random_forest | 2.700 | 0.312 | 0.278 | 0.238 | 0.268 | -0.509 |
| lightgbm | 0.100 | 0.750 | 0.714 | 0.709 | 0.723 | 0.545 |
| xgboost | 1.400 | 0.750 | 0.714 | 0.709 | 0.723 | 0.545 |
| catboost | 29.300 | 0.000 | 0.000 | 0.000 | 0.000 | -1.000 |

Mejor modelo: **lightgbm**. balanced_accuracy = 0.714 frente a 0.394 del baseline y 0.000 del control solo-plataforma (ganancia sobre la mejor referencia +0.320); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.286: la evaluacion ingenua sobrestimaria el rendimiento. Solo 4 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

Variables mas influyentes del modelo final: `clase: Amino acids and derivatives [clase_45]` (0.737), `clase: Organic acids [clase_479]` (0.147), `clase: Phenolic acids [clase_551]` (0.060), `clase: Fatty Acyls [clase_265]` (0.030), `clase: Organooxygen compounds [clase_506]` (0.013), `clase: Benzene and substituted derivatives [clase_101]` (0.007), `clase: Carboxylic acids and derivatives [clase_172]` (0.003), `clase: Prenol lipids [clase_595]` (0.003).

## Como interpretar
Casi cada especie aparece en un solo articulo, por lo que la prediccion entre articulos no es evaluable; dentro de un articulo la especie se confunde con el lote. Se espera 'no viable' o sin senal.

## Graficas
- `graficas\20261022-140017_M07_especie_c206ea24\comparacion_modelos.png`
- `graficas\20261022-140017_M07_especie_c206ea24\distribucion_clases.png`
- `graficas\20261022-140017_M07_especie_c206ea24\importancia_variables.png`
- `graficas\20261022-140017_M07_especie_c206ea24\matriz_confusion.png`
- `graficas\20261022-140017_M07_especie_c206ea24\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-140017_M07_especie_c206ea24/manifiesto.json`. Reejecutar: `python main.py ejecutar M07_especie`.
