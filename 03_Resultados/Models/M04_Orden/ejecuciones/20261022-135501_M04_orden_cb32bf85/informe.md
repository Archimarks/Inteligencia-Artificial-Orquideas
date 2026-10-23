# M04_orden - Orden taxonomico a partir del perfil quimico

- Ejecucion: `20261022-135501_M04_orden_cb32bf85` (2026-10-22T13:55:01, 201.5 s)
- Configuracion: `M04_orden.yaml` (huella `cb32bf8519fb`), semilla 42
- Estado: **completado** - Veredicto: **senal debil**

## Pregunta cientifica
¿El perfil composicional permite reconocer el orden taxonomico de una planta de un estudio no visto?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 746 de 942 (grupos: 38 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 9 (descartadas: 12; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.109 | 0.111 | 0.022 | 0.021 | 0.000 | 0.290 |
| baseline_estratificada | 0.100 | 0.121 | 0.116 | 0.109 | 0.122 | 0.005 | 0.350 |
| logistica | 0.200 | 0.273 | 0.225 | 0.210 | 0.266 | 0.194 | 0.460 |
| random_forest | 4.300 | 0.277 | 0.253 | 0.220 | 0.265 | 0.194 | 0.446 |
| lightgbm | 3.700 | 0.294 | 0.236 | 0.227 | 0.300 | 0.211 | 0.444 |
| xgboost | 17.600 | 0.253 | 0.209 | 0.171 | 0.226 | 0.165 | 0.438 |
| catboost | 31.700 | 0.261 | 0.203 | 0.193 | 0.260 | 0.177 | 0.462 |

Mejor modelo: **random_forest**. balanced_accuracy = 0.253 frente a 0.116 del baseline y 0.189 del control solo-plataforma (ganancia sobre la mejor referencia +0.064); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.747: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Shikimates and Phenylpropanoids [clase_682]` (0.036), `clase: Steroids [clase_705]` (0.034), `clase: Tryptophan alkaloids [clase_784]` (0.031), `clase: LPC [clase_417]` (0.030), `clase: Quinolines and derivatives [clase_661]` (0.030), `clase: Amino acids and derivatives [clase_45]` (0.029), `clase: Organic acids [clase_479]` (0.029), `clase: Fatty Acids and Conjugates [clase_262]` (0.027).

## Como interpretar
Cada orden se representa por pocos articulos; los ordenes con un unico articulo se descartan.

## Graficas
- `graficas\20261022-135501_M04_orden_cb32bf85\comparacion_modelos.png`
- `graficas\20261022-135501_M04_orden_cb32bf85\distribucion_clases.png`
- `graficas\20261022-135501_M04_orden_cb32bf85\importancia_variables.png`
- `graficas\20261022-135501_M04_orden_cb32bf85\matriz_confusion.png`
- `graficas\20261022-135501_M04_orden_cb32bf85\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-135501_M04_orden_cb32bf85/manifiesto.json`. Reejecutar: `python main.py ejecutar M04_orden`.
