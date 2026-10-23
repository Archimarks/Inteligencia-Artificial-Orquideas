# Auditoria de datos - M17b_actividades_metabolito

Conjunto `actividad_metabolito` (multietiqueta).

| indicador | valor |
|---|---|
| unidades_iniciales | 93 |
| unidades_evaluables | 93 |
| grupos_iniciales | 75 |
| grupos_evaluables | 75 |
| columna_grupo | FORMULA_MOLECULAR |
| variables | 35 |
| variables_constantes | 8 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 16 |
| unidades por grupo (min / mediana / max) | 1 / 1.0 / 4 |

Clases o etiquetas evaluables (6): Antioxidante, Antiinflamatorio, Anticancerigeno, Antimicrobiano, Neuroprotector, Antidiabetico

Notas:
- Etiquetas positivas-no etiquetadas (PU): una actividad no registrada no significa inactividad. Solo hay metabolitos con alguna actividad citada, de modo que el modelo aprende que actividad, no si es activo.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.