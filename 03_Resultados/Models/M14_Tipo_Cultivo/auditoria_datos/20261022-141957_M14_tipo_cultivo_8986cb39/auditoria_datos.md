# Auditoria de datos - M14_tipo_cultivo

Conjunto `perfil_muestra[ID_TIPO_CULTIVO|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 918 |
| unidades_evaluables | 882 |
| grupos_iniciales | 49 |
| grupos_evaluables | 49 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 576 |
| unidades por grupo (min / mediana / max) | 3 / 12.0 / 120 |

Clases o etiquetas evaluables (5): In vitro, Cultivo convencional en campo, Invernadero o condiciones controladas, Silvestre, Material comercial

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.