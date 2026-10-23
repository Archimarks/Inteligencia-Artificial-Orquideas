# Auditoria de datos - M10_aducto

Conjunto `metabolito_aducto` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 57550 |
| unidades_evaluables | 57550 |
| grupos_iniciales | 38 |
| grupos_evaluables | 38 |
| columna_grupo | ID_ARTICULO |
| variables | 47 |
| variables_constantes | 3 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 33199 |
| unidades por grupo (min / mediana / max) | 78 / 1171.5 / 7479 |

Clases o etiquetas evaluables (15): [M-H]-, [M+H]+, [M+NH4]+, [M+H-H2O]+, [M+Na]+, [M+FA-H]-, [M]+, [M-H2O-H]-, [2M-H]-, [M+K]+, [M+ACN+H]+, [M]-, [2M+H]+, [2M+Na]+, [M+CH3COO]-

Notas:
- Se modelan los 15 aductos informados en mas articulos. m/z queda excluida: m/z - masa = masa del aducto (fuga directa). El control instrumental usa solo el modo de ionizacion.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.