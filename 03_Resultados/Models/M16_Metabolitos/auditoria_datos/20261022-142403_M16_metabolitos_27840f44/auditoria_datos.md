# Auditoria de datos - M16_metabolitos

Conjunto `presencia_metabolitos` (multietiqueta).

| indicador | valor |
|---|---|
| unidades_iniciales | 129 |
| unidades_evaluables | 129 |
| grupos_iniciales | 49 |
| grupos_evaluables | 49 |
| columna_grupo | ID_ARTICULO |
| variables | 129 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 36 |
| unidades por grupo (min / mediana / max) | 1 / 2.0 / 20 |

Clases o etiquetas evaluables (60): Guanine, Adenosine, Adenine, Betaine, Citric acid, cytidine, quercetin, l-phenylalanine, 4-Hydroxybenzaldehyde, Arbutin, Uridine, Raffinose, Choline, Indole, 2-Hydroxycinnamic acid, Phloretin, L-Aspartic acid, L-Histidine, Coniferin, Caffeic acid, Azelaic acid, L-Tyrosine, Guanosine, L-Glutamic acid, Trigonelline, L-Lysine, Vanillic acid, pyridoxine, Cytosine, Salicin, Salidroside, Ferulic acid, Fumaric acid, L-Arginine, Jasmonic acid, Syringic acid, suberic acid, Gluconic acid, N-acetyl-l-phenylalanine, Salicylic acid...

Notas:
- Etiquetas = 60 metabolitos presentes en >= 5 articulos. Un metabolito ausente puede no estar en la biblioteca del laboratorio: la presencia mezcla quimica de la planta y cobertura de la biblioteca (por eso se compara con un control que solo usa la plataforma).

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.