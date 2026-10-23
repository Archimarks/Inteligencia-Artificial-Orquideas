# M05_familia - Familia botanica a partir del perfil quimico

- Ejecucion: `20261022-135823_M05_familia_7d7e0fbc` (2026-10-22T13:58:23, 65.9 s)
- Configuracion: `M05_familia.yaml` (huella `7d7e0fbc2ac7`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿El perfil composicional permite reconocer la familia botanica (p. ej. Orchidaceae) de una planta de un estudio no visto?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 582 de 942 (grupos: 28 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 9 (descartadas: 22; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.268 | 0.111 | 0.056 | 0.135 | 0.069 | 0.479 |
| baseline_estratificada | 0.100 | 0.107 | 0.090 | 0.085 | 0.119 | -0.020 | 0.352 |
| logistica | 0.100 | 0.330 | 0.263 | 0.188 | 0.283 | 0.246 | 0.407 |
| random_forest | 3.900 | 0.320 | 0.237 | 0.184 | 0.303 | 0.237 | 0.440 |
| lightgbm | 3.000 | 0.149 | 0.158 | 0.120 | 0.147 | 0.056 | 0.758 |
| xgboost | 14.800 | 0.196 | 0.186 | 0.197 | 0.217 | 0.109 | 0.794 |
| catboost | 32.500 | 0.345 | 0.257 | 0.187 | 0.316 | 0.255 | 0.440 |

Mejor modelo: **logistica**. balanced_accuracy = 0.263 frente a 0.111 del baseline y 0.074 del control solo-plataforma (ganancia sobre la mejor referencia +0.151); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.737: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Phenols [clase_553]` (0.028), `clase: Heterocyclic compounds [clase_324]` (0.026), `clase: Steroids [clase_705]` (0.025), `clase: LPE [clase_418]` (0.025), `clase: Isoflavones [clase_381]` (0.025), `clase: Anthocyanidins [clase_60]` (0.024), `clase: Sesquiterpenoids [clase_679]` (0.024), `clase: Triterpenoids [clase_777]` (0.023).

## Como interpretar
Orchidaceae tiene dos articulos (Gastrodia elata y Dendrobium officinale) con plataformas distintas.

## Graficas
- `graficas\20261022-135823_M05_familia_7d7e0fbc\comparacion_modelos.png`
- `graficas\20261022-135823_M05_familia_7d7e0fbc\distribucion_clases.png`
- `graficas\20261022-135823_M05_familia_7d7e0fbc\importancia_variables.png`
- `graficas\20261022-135823_M05_familia_7d7e0fbc\matriz_confusion.png`
- `graficas\20261022-135823_M05_familia_7d7e0fbc\prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-135823_M05_familia_7d7e0fbc/manifiesto.json`. Reejecutar: `python main.py ejecutar M05_familia`.
