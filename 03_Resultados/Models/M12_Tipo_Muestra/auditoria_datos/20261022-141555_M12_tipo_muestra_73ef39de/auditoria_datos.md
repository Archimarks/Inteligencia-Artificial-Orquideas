# Auditoria de datos - M12_tipo_muestra

Conjunto `perfil_muestra[ID_TIPO_MUESTRA|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 939 |
| unidades_evaluables | 915 |
| grupos_iniciales | 50 |
| grupos_evaluables | 47 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 593 |
| unidades por grupo (min / mediana / max) | 5 / 12.0 / 120 |

Clases o etiquetas evaluables (3): Tejido fresco, Tejido seco, Material curado o envejecido

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.