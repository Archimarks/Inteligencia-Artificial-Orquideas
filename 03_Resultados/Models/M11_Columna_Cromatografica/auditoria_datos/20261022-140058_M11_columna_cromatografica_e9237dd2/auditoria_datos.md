# Auditoria de datos - M11_columna_cromatografica

Conjunto `perfil_muestra[ID_COLUMNA_CROMATOGRAFICA|clase]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 868 |
| unidades_evaluables | 649 |
| grupos_iniciales | 47 |
| grupos_evaluables | 38 |
| columna_grupo | ID_ARTICULO |
| variables | 61 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 537 |
| unidades por grupo (min / mediana / max) | 5 / 12.0 / 120 |

Clases o etiquetas evaluables (5): Waters ACQUITY Premier HSS T3 (1.8 um, 2.1 x 100 mm), Agilent SB-C18 (1.8 um, 2.1 x 100 mm), Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm), Hypersil GOLD (1.9 um, 100 x 2.1 mm), Waters ACQUITY UPLC BEH C18 (1.7 um, 2.1 x 100 mm)

Notas:
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.