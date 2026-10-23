# Auditoria de datos - M05_familia

Conjunto `perfil_muestra[ID_FAMILIA|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 942 |
| unidades_evaluables | 582 |
| grupos_iniciales | 50 |
| grupos_evaluables | 28 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 596 |
| unidades por grupo (min / mediana / max) | 3 / 12.0 / 120 |

Clases o etiquetas evaluables (9): Convolvulaceae, Fabaceae, Lamiaceae, Moraceae, Orchidaceae, Rosaceae, Rubiaceae, Solanaceae, Theaceae

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.