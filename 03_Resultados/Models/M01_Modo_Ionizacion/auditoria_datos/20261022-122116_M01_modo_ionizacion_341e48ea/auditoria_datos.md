# Auditoria de datos - M01_modo_ionizacion

Conjunto `metabolito_modo` (multiclase).

| indicador | valor |
|---|---|
| unidades_iniciales | 69686 |
| unidades_evaluables | 69686 |
| grupos_iniciales | 46 |
| grupos_evaluables | 46 |
| columna_grupo | ID_ARTICULO |
| variables | 46 |
| variables_constantes | 4 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 47478 |
| unidades por grupo (min / mediana / max) | 11 / 1147.0 / 7479 |

Clases o etiquetas evaluables (2): Positivo, Negativo

Notas:
- Solo articulos con adquisicion en ESI+ y ESI-; se excluyen 142 pares detectados en ambos modos. No se usan m/z, aducto ni RT (codifican el modo). EI (GC-MS) no se incluye: depende de la plataforma, no del compuesto.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.