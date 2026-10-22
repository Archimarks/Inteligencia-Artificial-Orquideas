# M11_columna_cromatografica - Columna cromatografica a partir del perfil quimico

- Ejecucion: `20261022-090851_M11_columna_cromatografica_b5aeecbc` (2026-10-22T09:08:51, 25.7 s)
- Configuracion: `M11_columna_cromatografica.yaml` (huella `b5aeecbc9120`), semilla 42
- Estado: **completado** - Veredicto: **senal robusta**

## Pregunta cientifica
¿El perfil de metabolitos identificados delata la columna cromatografica usada (efecto de plataforma)?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 649 de 868 (grupos: 38 de 47; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 5 (descartadas: 9; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc | top3_accuracy |
|---|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.516 | 0.200 | 0.136 | 0.351 | 0.000 | 0.706 |
| baseline_estratificada | 0.100 | 0.357 | 0.191 | 0.188 | 0.355 | 0.004 | 0.575 |
| logistica | 0.200 | 0.720 | 0.401 | 0.361 | 0.668 | 0.565 | 0.968 |
| random_forest | 10.100 | 0.743 | 0.392 | 0.361 | 0.687 | 0.607 | 0.820 |
| lightgbm | 2.600 | 0.692 | 0.355 | 0.332 | 0.655 | 0.518 | 0.941 |

Mejor modelo: **logistica**. balanced_accuracy = 0.401 frente a 0.200 del baseline y 0.096 del control solo-plataforma (ganancia sobre la mejor referencia +0.201); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.599: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase: Amines [clase_41]` (0.035), `clase: Aldehyde compounds [clase_31]` (0.031), `clase: Triterpene [clase_774]` (0.030), `clase: Chalcones [clase_181]` (0.028), `clase: Steroids [clase_705]` (0.028), `clase: Heterocyclic compounds [clase_324]` (0.027), `clase: Flavonoids [clase_285]` (0.024), `clase: Glycerophospholipids [clase_316]` (0.024).

## Como interpretar
Este modelo mide el efecto de plataforma: si la columna se predice bien, los perfiles reflejan el metodo analitico y no solo la planta.

## Graficas
- `graficas/20261022-090851_M11_columna_cromatografica_b5aeecbc/comparacion_modelos.png`
- `graficas/20261022-090851_M11_columna_cromatografica_b5aeecbc/distribucion_clases.png`
- `graficas/20261022-090851_M11_columna_cromatografica_b5aeecbc/importancia_variables.png`
- `graficas/20261022-090851_M11_columna_cromatografica_b5aeecbc/matriz_confusion.png`
- `graficas/20261022-090851_M11_columna_cromatografica_b5aeecbc/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-090851_M11_columna_cromatografica_b5aeecbc/manifiesto.json`. Reejecutar: `python main.py ejecutar M11_columna_cromatografica`.
