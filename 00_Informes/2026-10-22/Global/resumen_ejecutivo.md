# Resumen ejecutivo de experimentos

Ultima ejecucion de cada experimento. Metricas sobre validacion agrupada por articulo (o formula para los modelos de compuesto). `control_plataforma` = mismo modelo con solo variables instrumentales; `sin_agrupar` = validacion ingenua (optimista).

Veredictos (ganancia = valor - max(baseline, control_plataforma)): **senal robusta** (ganancia >= 0.15 y p < 0.05); **senal debil** (ganancia 0.05-0.15 y p < 0.05); **confundido con plataforma** (el control instrumental rinde igual); **sin senal**; **evidencia insuficiente** (< 10 grupos independientes o mediana < 3 grupos por clase); **no viable** (clases/grupos insuficientes para evaluar).

| experimento | estado | unidades | grupos | clases | mejor_modelo | metrica | valor | baseline | control_plataforma | sin_agrupar | p_permutacion | veredicto | carpeta |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M01_modo_ionizacion | completado | 69686 | 46 | 2 | random_forest | balanced_accuracy | 0.686 | 0.503 |  | 0.702 | 0.048 | senal robusta | Models/M01_Modo_Ionizacion |
| M02_filo | no_viable | 909 | 48 | 1 | nan | nan |  |  |  |  |  | no viable | Models/M02_Filo |
| M03_clase_taxonomica | completado | 909 | 48 | 2 | logistica | balanced_accuracy | 0.486 | 0.521 | 0.389 | 1.000 | 0.806 | sin senal | Models/M03_Clase_Taxonomica |
| M04_orden | completado | 746 | 38 | 9 | random_forest | balanced_accuracy | 0.253 | 0.116 | 0.189 | 1.000 | 0.032 | senal debil | Models/M04_Orden |
| M05_familia | completado | 582 | 28 | 9 | logistica | balanced_accuracy | 0.263 | 0.111 | 0.074 | 1.000 | 0.032 | senal robusta | Models/M05_Familia |
| M06_genero | completado | 84 | 8 | 3 | lightgbm | balanced_accuracy | 0.495 | 0.333 | 0.167 | 1.000 | 0.032 | evidencia insuficiente | Models/M06_Genero |
| M07_especie | completado | 48 | 4 | 2 | lightgbm | balanced_accuracy | 0.714 | 0.394 | 0.000 | 1.000 | 0.032 | evidencia insuficiente | Models/M07_Especie |
| M08_superclase_quimica | completado | 31055 | 12851 | 13 | catboost | balanced_accuracy | 0.575 | 0.078 |  | 0.589 | 0.048 | senal robusta | Models/M08_Superclase_Quimica |
| M09_clase_quimica | completado | 23337 | 10284 | 40 | catboost | balanced_accuracy | 0.426 | 0.025 |  | 0.447 | 0.048 | senal robusta | Models/M09_Clase_Quimica |
| M10_aducto | completado | 57550 | 38 | 15 | catboost | balanced_accuracy | 0.245 | 0.067 | 0.137 | 0.335 | 0.048 | senal debil | Models/M10_Aducto |
| M11_columna_cromatografica | completado | 649 | 38 | 5 | catboost | balanced_accuracy | 0.510 | 0.200 | 0.136 | 1.000 | 0.032 | senal robusta | Models/M11_Columna_Cromatografica |
| M12_tipo_muestra | completado | 915 | 47 | 3 | lightgbm | balanced_accuracy | 0.327 | 0.333 | 0.287 | 0.998 | 0.710 | sin senal | Models/M12_Tipo_Muestra |
| M13_parte_planta | completado | 772 | 44 | 9 | logistica | balanced_accuracy | 0.141 | 0.111 | 0.086 | 0.886 | 0.065 | sin senal | Models/M13_Parte_Planta |
| M14_tipo_cultivo | completado | 882 | 49 | 5 | random_forest | balanced_accuracy | 0.354 | 0.200 | 0.142 | 0.961 | 0.032 | senal robusta | Models/M14_Tipo_Cultivo |
| M15_metodo_extraccion | completado | 541 | 32 | 6 | logistica | balanced_accuracy | 0.515 | 0.167 | 0.543 | 1.000 | 0.032 | confundido con plataforma | Models/M15_Metodo_Extraccion |
| M16_metabolitos | completado | 129 | 49 | 60 | logistica | average_precision_macro | 0.499 | 0.364 | 0.591 | 0.881 | 0.032 | confundido con plataforma | Models/M16_Metabolitos |
| M17b_actividades_metabolito | completado | 93 | 75 | 6 | knn | average_precision_macro | 0.436 | 0.292 |  | 0.499 | 0.039 | senal debil | Models/M17b_Actividades_Metabolito |
