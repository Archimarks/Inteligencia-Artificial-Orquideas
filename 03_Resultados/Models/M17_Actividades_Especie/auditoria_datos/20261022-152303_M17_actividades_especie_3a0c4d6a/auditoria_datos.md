# Auditoria de datos - M17_actividades_especie

Conjunto `actividad_especie[superclase]` (multietiqueta).

| indicador | valor |
|---|---|
| unidades_iniciales | 60 |
| unidades_evaluables | 60 |
| grupos_iniciales | 44 |
| grupos_evaluables | 44 |
| columna_grupo | ID_ARTICULO |
| variables | 20 |
| variables_constantes | 0 |
| celdas_nulas | 0 |
| filas_X_duplicadas | 3 |
| unidades por grupo (min / mediana / max) | 1 / 1.0 / 5 |

Clases o etiquetas evaluables (16): Antioxidante, Antiinflamatorio, Anticancerigeno, Antibacteriano, Antimicrobiano, Antiviral, Hepatoprotector, Neuroprotector, Analgesico, Antihipertensivo, Hipolipemiante, Antidiabetico, Antiobesidad, Antienvejecimiento, Cardioprotector, Inmunomodulador

Notas:
- Unidad = especie x articulo (casi siempre una por articulo). Actividades mayoritariamente bibliograficas: positivos sin negativos verificados (PU). Solo se incluyen especies con alguna actividad registrada.

Archivos: `distribucion_clases.csv`, `clases_descartadas.csv` (si hay), `descripcion_variables.csv`, `unidades_por_grupo.csv/.png`, `resumen_datos.json`.