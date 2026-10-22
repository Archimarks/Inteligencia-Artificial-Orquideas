# M12_tipo_muestra - Tipo de muestra a partir del perfil quimico

- Ejecucion: `20261022-090917_M12_tipo_muestra_59b87e4f` (2026-10-22T09:09:17, 193.5 s)
- Configuracion: `M12_tipo_muestra.yaml` (huella `59b87e4f5013`), semilla 42
- Estado: **completado** - Veredicto: **sin senal**

## Pregunta cientifica
¿El perfil composicional de metabolitos identificados (conteo por clase quimica, CLR) permite reconocer el tipo de muestra (tejido fresco, tejido seco, extractos...) en articulos no vistos durante el entrenamiento?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 915 de 939 (grupos: 47 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 3 (descartadas: 6; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.715 | 0.333 | 0.278 | 0.596 | 0.000 |
| baseline_estratificada | 0.100 | 0.613 | 0.325 | 0.319 | 0.579 | -0.014 |
| logistica | 0.200 | 0.544 | 0.295 | 0.296 | 0.553 | -0.002 |
| random_forest | 11.400 | 0.672 | 0.313 | 0.268 | 0.575 | -0.112 |
| lightgbm | 2.800 | 0.666 | 0.327 | 0.308 | 0.617 | 0.099 |

Mejor modelo: **lightgbm**. balanced_accuracy = 0.327 frente a 0.333 del baseline y 0.287 del control solo-plataforma (ganancia sobre la mejor referencia -0.006); p de permutacion = 0.710; evaluacion sin agrupar = 0.998. Sin agrupar por ID_ARTICULO la metrica sube +0.671: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Amino acids and derivatives [clase_45]` (0.069), `clase: Phenolic acids [clase_551]` (0.060), `clase: Organonitrogen compounds [clase_505]` (0.044), `clase: otras [clase_otras]` (0.041), `clase: Lactones [clase_403]` (0.035), `clase: Benzene and substituted derivatives [clase_101]` (0.032), `clase: Organic acids [clase_479]` (0.030), `clase: Pyridine alkaloids [clase_629]` (0.029).

## Como interpretar
El tipo de muestra esta casi completamente confundido con el articulo (cada estudio usa un unico tipo). Un rendimiento alto solo es creible si supera tanto al baseline como al control con variables de plataforma.

## Graficas
- `graficas/20261022-090917_M12_tipo_muestra_59b87e4f/comparacion_modelos.png`
- `graficas/20261022-090917_M12_tipo_muestra_59b87e4f/distribucion_clases.png`
- `graficas/20261022-090917_M12_tipo_muestra_59b87e4f/importancia_variables.png`
- `graficas/20261022-090917_M12_tipo_muestra_59b87e4f/matriz_confusion.png`
- `graficas/20261022-090917_M12_tipo_muestra_59b87e4f/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-090917_M12_tipo_muestra_59b87e4f/manifiesto.json`. Reejecutar: `python main.py ejecutar M12_tipo_muestra`.
