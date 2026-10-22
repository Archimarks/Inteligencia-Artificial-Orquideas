# M06_genero - Genero a partir del perfil quimico

- Ejecucion: `20261022-084644_M06_genero_d8f1dc95` (2026-10-22T08:46:44, 25.7 s)
- Configuracion: `M06_genero.yaml` (huella `d8f1dc95580b`), semilla 42
- Estado: **completado** - Veredicto: **evidencia insuficiente**

## Pregunta cientifica
¿El perfil quimico identifica el genero en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 84 de 942 (grupos: 8 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 3 (descartadas: 44; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.429 | 0.333 | 0.200 | 0.257 | 0.000 |
| baseline_estratificada | 0.100 | 0.321 | 0.286 | 0.274 | 0.302 | -0.071 |
| logistica | 0.100 | 0.393 | 0.352 | 0.329 | 0.367 | 0.045 |
| random_forest | 7.500 | 0.214 | 0.167 | 0.118 | 0.151 | -0.376 |
| lightgbm | 0.300 | 0.500 | 0.495 | 0.521 | 0.518 | 0.242 |

Mejor modelo: **lightgbm**. balanced_accuracy = 0.495 frente a 0.333 del baseline y 0.167 del control solo-plataforma (ganancia sobre la mejor referencia +0.161); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.505: la evaluacion ingenua sobrestimaria el rendimiento. Solo 8 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

Variables mas influyentes del modelo final: `clase: Amino acids and derivatives [clase_45]` (0.372), `clase: Sesquiterpenoids [clase_679]` (0.148), `clase: Triterpene [clase_774]` (0.137), `clase: Phenolic acids [clase_551]` (0.062), `clase: Organic acids [clase_479]` (0.055), `clase: Phenols [clase_553]` (0.033), `clase: Benzene and substituted derivatives [clase_101]` (0.026), `clase: Flavonols [clase_288]` (0.021).

## Como interpretar
Pocos generos aparecen en mas de un articulo (Camellia, Ipomoea, Morus); es esperable poca o ninguna senal evaluable.

## Graficas
- `graficas/20261022-084644_M06_genero_d8f1dc95/comparacion_modelos.png`
- `graficas/20261022-084644_M06_genero_d8f1dc95/distribucion_clases.png`
- `graficas/20261022-084644_M06_genero_d8f1dc95/importancia_variables.png`
- `graficas/20261022-084644_M06_genero_d8f1dc95/matriz_confusion.png`
- `graficas/20261022-084644_M06_genero_d8f1dc95/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-084644_M06_genero_d8f1dc95/manifiesto.json`. Reejecutar: `python main.py ejecutar M06_genero`.
