# M03_clase_taxonomica - Clase taxonomica a partir del perfil quimico

- Ejecucion: `20261022-083948_M03_clase_taxonomica_ef8707f2` (2026-10-22T08:39:48, 20.5 s)
- Configuracion: `M03_clase_taxonomica.yaml` (huella `ef8707f27484`), semilla 42
- Estado: **completado** - Veredicto: **sin senal**

## Pregunta cientifica
¿El perfil quimico separa Magnoliopsida de Liliopsida (monocotiledoneas, incluidas las orquideas) en articulos no vistos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 909 de 942 (grupos: 48 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 2 (descartadas: 2; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultados (validacion agrupada, predicciones fuera de particion)
| modelo | segundos | accuracy | balanced_accuracy | f1_macro | f1_weighted | mcc |
|---|---|---|---|---|---|---|
| baseline_mayoritaria | 0.100 | 0.865 | 0.500 | 0.464 | 0.802 | 0.000 |
| baseline_estratificada | 0.100 | 0.777 | 0.521 | 0.521 | 0.776 | 0.042 |
| logistica | 0.100 | 0.693 | 0.486 | 0.482 | 0.723 | -0.022 |
| random_forest | 11.000 | 0.794 | 0.459 | 0.443 | 0.766 | -0.109 |
| lightgbm | 1.500 | 0.809 | 0.468 | 0.447 | 0.773 | -0.096 |

Mejor modelo: **logistica**. balanced_accuracy = 0.486 frente a 0.521 del baseline (ganancia -0.035); p de permutacion = 0.806; control solo-plataforma = 0.389; evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.514: la evaluacion ingenua sobrestimaria el rendimiento.

Variables mas influyentes del modelo final: `clase_774` (0.042), `clase_549` (0.037), `clase_583` (0.037), `clase_505` (0.037), `clase_661` (0.037), `clase_553` (0.036), `clase_120` (0.035), `clase_otras` (0.034).

## Como interpretar
Liliopsida esta representada por pocos articulos; una prediccion correcta podria reflejar la plataforma de esos estudios.

## Graficas
- `graficas/20261022-083948_M03_clase_taxonomica_ef8707f2/comparacion_modelos.png`
- `graficas/20261022-083948_M03_clase_taxonomica_ef8707f2/distribucion_clases.png`
- `graficas/20261022-083948_M03_clase_taxonomica_ef8707f2/importancia_variables.png`
- `graficas/20261022-083948_M03_clase_taxonomica_ef8707f2/matriz_confusion.png`
- `graficas/20261022-083948_M03_clase_taxonomica_ef8707f2/prueba_permutacion.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-083948_M03_clase_taxonomica_ef8707f2/manifiesto.json`. Reejecutar: `python main.py ejecutar M03_clase_taxonomica`.
