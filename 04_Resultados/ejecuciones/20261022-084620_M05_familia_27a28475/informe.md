# M05_familia - Familia botanica a partir del perfil quimico

- Ejecucion: `20261022-084620_M05_familia_27a28475` (2026-10-22T08:46:20, 24.0 s)
- Configuracion: `M05_familia.yaml` (huella `27a284757de6`), semilla 42
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
| logistica | 0.200 | 0.330 | 0.263 | 0.188 | 0.283 | 0.246 | 0.407 |
| random_forest | 7.700 | 0.320 | 0.237 | 0.184 | 0.303 | 0.237 | 0.440 |
| lightgbm | 3.700 | 0.149 | 0.158 | 0.120 | 0.147 | 0.056 | 0.758 |

Mejor modelo: **logistica**. balanced_accuracy = 0.263 frente a 0.111 del baseline (ganancia +0.151); p de permutacion = 0.032; control solo-plataforma = 0.074; evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.737: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase_553` (0.028), `clase_324` (0.026), `clase_705` (0.025), `clase_418` (0.025), `clase_381` (0.025), `clase_60` (0.024), `clase_679` (0.024), `clase_777` (0.023).

## Como interpretar
Orchidaceae tiene dos articulos (Gastrodia elata y Dendrobium officinale) con plataformas distintas.

## Graficas
- `graficas/20261022-084620_M05_familia_27a28475/comparacion_modelos.png`
- `graficas/20261022-084620_M05_familia_27a28475/distribucion_clases.png`
- `graficas/20261022-084620_M05_familia_27a28475/importancia_variables.png`
- `graficas/20261022-084620_M05_familia_27a28475/matriz_confusion.png`
- `graficas/20261022-084620_M05_familia_27a28475/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-084620_M05_familia_27a28475/manifiesto.json`. Reejecutar: `python main.py ejecutar M05_familia`.
