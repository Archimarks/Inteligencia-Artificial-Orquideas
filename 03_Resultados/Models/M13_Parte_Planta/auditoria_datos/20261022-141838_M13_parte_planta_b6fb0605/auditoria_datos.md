# Auditoria de datos - M13_parte_planta

Conjunto `perfil_muestra[ID_PARTE_ESTUDIADA|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 930 |
| unidades_evaluables | 772 |
| grupos_iniciales | 50 |
| grupos_evaluables | 44 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 584 |
| unidades por grupo (min / mediana / max) | 3 / 12.0 / 120 |

Clases o etiquetas evaluables (9): Raiz, Tallo, Hoja, Flor, Fruto, Semilla, Rizoma, Tuberculo, Petalo

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.