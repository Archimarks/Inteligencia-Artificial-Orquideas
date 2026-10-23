# Auditoria de datos - M09_clase_quimica

Conjunto `metabolito_quimica[ID_CLASE_QUIMICA]` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 31115 |
| unidades_evaluables | 23337 |
| grupos_iniciales | 12900 |
| grupos_evaluables | 10284 |
| columna_grupo | FORMULA |
| variables | 24 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 18229 |
| unidades por grupo (min / mediana / max) | 1 / 1.0 / 79 |

Clases o etiquetas evaluables (40): Alkaloids, Amines, Amino acids and derivatives, Anthocyanidins, Benzene and substituted derivatives, Carboxylic acids and derivatives, Cinnamic acids and derivatives, Coumarins, Coumarins and derivatives, Ditepenoids, Diterpenoids, Fatty Acyls, Flavanones, Flavones, Flavonoids, Flavonols, Free fatty acids, Glycerolipids, Glycerophospholipids, Heterocyclic compounds, Indoles and derivatives, Isoflavones, Isoflavonoids, Ketone compounds, Lactones, Lignans, Monoterpenoids, Nucleotides and derivatives, Organic acids, Organonitrogen compounds, Organooxygen compounds, Other Flavonoids, Phenolic acids, Phenols, Prenol lipids, Saccharides, Sesquiterpenoids, Steroids and steroid derivatives, Terpenoids, Triterpene

Notas:
- Grupos = formula molecular: los isomeros comparten formula y nunca quedan repartidos entre entrenamiento y prueba. Las formulas deuteradas (estandares internos) y las no interpretables se excluyen.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.