# Auditoria de datos - M15_metodo_extraccion

Conjunto `perfil_muestra[ID_METODO_EXTRACCION|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 906 |
| unidades_evaluables | 541 |
| grupos_iniciales | 49 |
| grupos_evaluables | 32 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 571 |
| unidades por grupo (min / mediana / max) | 5 / 12.0 / 120 |

Clases o etiquetas evaluables (6): Metanol:acetonitrilo:agua (2:2:1, v/v/v), Metanol 70% (v/v), Metanol 70% (v/v) a 4 C durante la noche, Metanol 70% pre-enfriado (-20 C) con estandar interno, Metanol 80% pre-enfriado, Metanol:agua (7:3, v/v)

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.