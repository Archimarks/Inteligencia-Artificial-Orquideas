# Resumen ejecutivo de experimentos

Ultima ejecucion de cada experimento. Metricas sobre validacion agrupada por articulo (o formula para los modelos de compuesto). `control_plataforma` = mismo modelo con solo variables instrumentales; `sin_agrupar` = validacion ingenua (optimista).

Veredictos (ganancia = valor - max(baseline, control_plataforma)): **senal robusta** (ganancia >= 0.15 y p < 0.05); **senal debil** (ganancia 0.05-0.15 y p < 0.05); **confundido con plataforma** (el control instrumental rinde igual); **sin senal**; **evidencia insuficiente** (< 10 grupos independientes o mediana < 3 grupos por clase); **no viable** (clases/grupos insuficientes para evaluar).

| experimento | estado | unidades | grupos | clases | mejor_modelo | metrica | valor | baseline | control_plataforma | sin_agrupar | p_permutacion | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M01_modo_ionizacion | completado | 69686 | 46.000 | 2.000 | random_forest | balanced_accuracy | 0.686 | 0.503 |  | 0.702 | 0.048 | senal robusta |
| M02_filo | no_viable | 909 | 48.000 | 1.000 | nan | nan |  |  |  |  |  | no viable |
| M03_clase_taxonomica | completado | 909 | 48.000 | 2.000 | logistica | balanced_accuracy | 0.486 | 0.521 | 0.389 | 1.000 | 0.806 | sin senal |
| M04_orden | completado | 746 | 38.000 | 9.000 | random_forest | balanced_accuracy | 0.253 | 0.116 | 0.189 | 1.000 | 0.032 | senal debil |
| M05_familia | completado | 582 | 28.000 | 9.000 | logistica | balanced_accuracy | 0.263 | 0.111 | 0.074 | 1.000 | 0.032 | senal robusta |
| M06_genero | completado | 84 | 8.000 | 3.000 | lightgbm | balanced_accuracy | 0.495 | 0.333 | 0.167 | 1.000 | 0.032 | evidencia insuficiente |
| M07_especie | completado | 48 | 4.000 | 2.000 | lightgbm | balanced_accuracy | 0.714 | 0.394 | 0.000 | 1.000 | 0.032 | evidencia insuficiente |
| M08_superclase_quimica | completado | 31055 | 12851.000 | 13.000 | random_forest | balanced_accuracy | 0.537 | 0.078 |  | 0.561 | 0.048 | senal robusta |
| M09_clase_quimica | completado | 23337 | 10284.000 | 40.000 | random_forest | balanced_accuracy | 0.404 | 0.025 |  | 0.429 | 0.048 | senal robusta |
| M10_aducto | completado | 57550 | 38.000 | 15.000 | random_forest | balanced_accuracy | 0.236 | 0.067 | 0.134 | 0.329 | 0.048 | senal debil |
| M11_columna_cromatografica | completado | 649 | 38.000 | 5.000 | logistica | balanced_accuracy | 0.401 | 0.200 | 0.096 | 1.000 | 0.032 | senal robusta |
| M12_tipo_muestra | completado | 915 | 47.000 | 3.000 | lightgbm | balanced_accuracy | 0.327 | 0.333 | 0.287 | 0.998 | 0.710 | sin senal |
| M13_parte_planta | completado | 772 | 44.000 | 9.000 | logistica | balanced_accuracy | 0.141 | 0.111 | 0.086 | 0.886 | 0.065 | sin senal |
| M14_tipo_cultivo | completado | 882 | 49.000 | 5.000 | random_forest | balanced_accuracy | 0.354 | 0.200 | 0.142 | 0.961 | 0.032 | senal robusta |
| M15_metodo_extraccion | completado | 541 | 32.000 | 6.000 | logistica | balanced_accuracy | 0.515 | 0.167 | 0.543 | 1.000 | 0.032 | confundido con plataforma |
| M16_metabolitos | completado | 128 | 48.000 | 60.000 | logistica | average_precision_macro | 0.454 | 0.359 | 0.583 | 0.883 | 0.258 | confundido con plataforma |
| M17_actividades_especie | completado | 60 | 44.000 | 16.000 | random_forest | average_precision_macro | 0.416 | 0.300 | 0.437 | 0.700 | 0.020 | confundido con plataforma |
| M17b_actividades_metabolito | completado | 93 | 75.000 | 6.000 | knn | average_precision_macro | 0.436 | 0.292 |  | 0.496 | 0.039 | senal debil |
| M18_patrones_quimicos | completado | 111 |  |  | nan | nan |  |  |  |  |  | descriptivo |
