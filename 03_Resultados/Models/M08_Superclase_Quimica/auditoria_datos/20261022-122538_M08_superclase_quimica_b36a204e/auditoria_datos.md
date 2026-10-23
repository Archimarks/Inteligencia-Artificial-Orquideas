# Auditoria de datos - M08_superclase_quimica

Conjunto `metabolito_quimica[ID_SUPERCLASE_QUIMICA]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 31115 |
| unidades_evaluables | 31055 |
| grupos_iniciales | 12900 |
| grupos_evaluables | 12851 |
| columna_grupo | FORMULA |
| variables | 24 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 18229 |
| unidades por grupo (min / mediana / max) | 1 / 1.0 / 85 |

Clases o etiquetas evaluables (13): No especificado, Alkaloids and derivatives, Benzenoids, Hydrocarbons, Lignans, neolignans and related compounds, Lipids and lipid-like molecules, Nucleosides, nucleotides, and analogues, Organic acids and derivatives, Organic nitrogen compounds, Organic oxygen compounds, Organoheterocyclic compounds, Organosulfur compounds, Phenylpropanoids and polyketides

Notas:
- Grupos = formula molecular: los isomeros comparten formula y nunca quedan repartidos entre entrenamiento y prueba. Las formulas deuteradas (estandares internos) y las no interpretables se excluyen.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.