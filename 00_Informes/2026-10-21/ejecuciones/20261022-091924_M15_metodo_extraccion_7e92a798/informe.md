# M15_metodo_extraccion - Metodo de extraccion a partir del perfil quimico

- Ejecucion: `20261022-091924_M15_metodo_extraccion_7e92a798` (2026-10-22T09:19:24, 21.5 s)
- Configuracion: `M15_metodo_extraccion.yaml` (huella `7e92a798bb29`), semilla 42
- Estado: **completado** - Veredicto: **confundido con plataforma**

## Pregunta cientifica
¿El perfil quimico delata el metodo de extraccion (solvente) en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 541 de 906 (grupos: 32 de 49; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 6 (descartadas: 20; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.248 | 0.167 | 0.066 | 0.098 | 0.000 | 0.492 |
| baseline_estratificada | 0.100 | 0.211 | 0.136 | 0.137 | 0.225 | -0.023 | 0.532 |
| logistica | 0.100 | 0.553 | 0.515 | 0.455 | 0.535 | 0.423 | 0.845 |
| random_forest | 7.700 | 0.407 | 0.349 | 0.314 | 0.389 | 0.231 | 0.861 |
| lightgbm | 2.400 | 0.651 | 0.468 | 0.450 | 0.635 | 0.530 | 0.845 |

Mejor modelo: **logistica**. balanced_accuracy = 0.515 frente a 0.167 del baseline y 0.543 del control solo-plataforma (ganancia sobre la mejor referencia -0.028); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.485: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

Variables mas influyentes del modelo final: `clase: Isoflavones [clase_381]` (0.031), `clase: Other Flavonoids [clase_513]` (0.029), `clase: Anthocyanidins [clase_60]` (0.028), `clase: Isoflavonoids [clase_384]` (0.026), `clase: Vitamin [clase_795]` (0.025), `clase: Flavonols [clase_288]` (0.024), `clase: otras [clase_otras]` (0.024), `clase: Aldehyde compounds [clase_31]` (0.023).

## Como interpretar
Metodos frecuentes (p. ej. metanol 70 %) dominan; muchos metodos aparecen en un solo articulo y se descartan.

## Graficas
- `graficas/20261022-091924_M15_metodo_extraccion_7e92a798/comparacion_modelos.png`
- `graficas/20261022-091924_M15_metodo_extraccion_7e92a798/distribucion_clases.png`
- `graficas/20261022-091924_M15_metodo_extraccion_7e92a798/importancia_variables.png`
- `graficas/20261022-091924_M15_metodo_extraccion_7e92a798/matriz_confusion.png`
- `graficas/20261022-091924_M15_metodo_extraccion_7e92a798/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-091924_M15_metodo_extraccion_7e92a798/manifiesto.json`. Reejecutar: `python main.py ejecutar M15_metodo_extraccion`.
