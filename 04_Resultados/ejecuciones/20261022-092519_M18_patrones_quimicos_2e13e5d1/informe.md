# M18_patrones_quimicos - Patrones quimicos: enriquecimiento, coocurrencia, reglas, agrupamiento y particion de varianza

- Ejecucion: `20261022-092519_M18_patrones_quimicos_2e13e5d1` (2026-10-22T09:25:19, 54.3 s)
- Configuracion: `M18_patrones_quimicos.yaml` (huella `2e13e5d138c9`), semilla 42
- Estado: **completado** - Veredicto: **descriptivo**

## Pregunta cientifica
¿Que patrones quimicos (categorias enriquecidas por taxon u organo, categorias que coaparecen, reglas taxon -> quimica, grupos de especies con perfil similar, perfiles atipicos y asociaciones quimica-actividad) se sostienen cuando se controla que cada articulo aporta su propia plataforma y biblioteca de anotacion?

## Diseno
Unidad = especie x articulo x parte de la planta (suma de muestras biologicas). Perfil = numero de metabolitos identificados por superclase (o clase) quimica, transformado con CLR. Contrastes Mann-Whitney con correccion BH, coocurrencias con Fisher exacto + BH, FP-growth, K-means con estabilidad bootstrap, PERMANOVA (R2 marginal con permutaciones; version intra-articulo centrando por estudio), Isolation Forest, enriquecimiento superclase-actividad y firma descriptiva de Orchidaceae.

## Unidad de analisis y precauciones
- Unidad = especie x articulo x parte (suma de muestras biologicas). Perfil = conteo de metabolitos identificados por categoria quimica (CLR). Las intensidades no se comparan entre lotes.

## Hallazgos
- Enriquecimiento por ID_CLASE_TAXONOMICA: 2 niveles con >= 2 articulos; 0 de 40 contrastes con q < 0.05.
- Enriquecimiento por ID_ORDEN: 9 niveles con >= 2 articulos; 0 de 180 contrastes con q < 0.05.
- Enriquecimiento por ID_FAMILIA: 9 niveles con >= 2 articulos; 2 de 180 contrastes con q < 0.05. Mas fuertes: Organometallic compounds mayor en Rosaceae (q=0.038); Organic 1,3-dipolar compounds mayor en Rosaceae (q=0.038)
- Enriquecimiento por ID_PARTE_ESTUDIADA: 10 niveles con >= 2 articulos; 0 de 200 contrastes con q < 0.05.
- Enriquecimiento por ID_TIPO_MUESTRA: 3 niveles con >= 2 articulos; 0 de 60 contrastes con q < 0.05.
- Coocurrencia (nulo curveball que conserva la riqueza de cada unidad, 300 aleatorizaciones): 160 de 1770 pares de clases quimicas coaparecen mas de lo esperado (q < 0.05). Mas fuertes: Organic acids + Fatty Acyls (z=6.1); Glycerophospholipids + Steroids and steroid derivatives (z=5.4); Flavones + Flavanones (z=5.2); Glycerophospholipids + Fatty Acids and Conjugates (z=5.1)
- Reglas de asociacion: 4693 reglas entre clases quimicas (soporte >= 0.2, confianza >= 0.9, lift >= 1.5); 105 reglas taxon -> clase quimica sostenidas por >= 2 articulos. Ejemplos: FAMILIA=Moraceae => Phenylpropanoids (C6-C3) (conf 1.00, lift 4.83, 2 art.); FAMILIA=Lamiaceae => Amines (conf 1.00, lift 4.62, 3 art.); FAMILIA=Solanaceae => Amines (conf 1.00, lift 4.62, 4 art.); FAMILIA=Lamiaceae => Tryptophan alkaloids (conf 1.00, lift 3.96, 3 art.)
- Agrupamiento: k=3 (silueta 0.50), estabilidad ARI bootstrap 0.81 +/- 0.27. Concordancia (AMI) de los clusters con orden taxonomico 0.13, con columna cromatografica 0.12 y con articulo 0.16. PC1+PC2 explican 66% de la varianza.
- Particion de varianza: ID_ARTICULO R2=1.00 (ajustado 0.99, nulo 0.45, p=0.002, permutacion libre); ID_FAMILIA R2=0.79 (ajustado 0.71, nulo 0.67, p=0.026, permutacion por articulo); ID_METODO_EXTRACCION R2=0.51 (ajustado 0.38, nulo 0.51, p=0.498, permutacion por articulo); ID_ORDEN R2=0.48 (ajustado 0.35, nulo 0.47, p=0.456, permutacion por articulo); ID_PARTE_ESTUDIADA R2=0.36 (ajustado 0.14, nulo 0.26, p=0.004, permutacion libre); ID_COLUMNA_CROMATOGRAFICA R2=0.34 (ajustado 0.23, nulo 0.34, p=0.466, permutacion por articulo); ID_CLASE_TAXONOMICA R2=0.05 (ajustado 0.02, nulo 0.07, p=0.610, permutacion por articulo).
- Particion de varianza intra-articulo: ID_PARTE_ESTUDIADA R2=0.02 (ajustado -0.06, nulo 0.02, p=0.552, permutacion intra-articulo).
- Particion de varianza intra-articulo: ID_TIPO_CULTIVO R2=0.01 (ajustado -0.03, nulo 0.01, p=0.204, permutacion intra-articulo).
- Particion de varianza intra-articulo: ID_ESPECIE R2=0.02 (ajustado -0.10, nulo 0.01, p=0.114, permutacion intra-articulo).
- Atipicos: 26 de 111 unidades; las mas atipicas: Nicotiana tabacum L. (art. 11), Ipomoea batatas (L.) Lam. (art. 37), Spatholobus suberectus Dunn (art. 15), Medicago sativa L. (art. 22), Actinidia chinensis Planch. (art. 45).
- Red quimica-actividad: 102 metabolitos con actividad citada; 0 asociaciones superclase-actividad enriquecidas (q < 0.05).
- Orquideas: 2 articulos de Orchidaceae; 2783 metabolitos identificados en ellas, 73 presentes en todos sus articulos; de estos, 5 aparecen en <= 10 % de los otros 49 articulos (candidatos a marcadores, a confirmar).

## Como interpretar
Un patron es candidato a hallazgo solo si (1) aparece en varios articulos independientes, (2) sobrevive a la correccion por comparaciones multiples y (3) no se explica mejor por columna/plataforma (comparar R2 de articulo y columna con el de orden/familia). Las coocurrencias pueden deberse a bibliotecas compartidas (p. ej. MRM de Metware). La firma de orquideas es descriptiva: solo hay dos estudios de Orchidaceae.

## Graficas
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/composicion_orquideas_vs_resto.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/enriquecimiento_ID_FAMILIA.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/particion_varianza.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/particion_varianza_intra_ID_ESPECIE.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/particion_varianza_intra_ID_PARTE_ESTUDIADA.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/particion_varianza_intra_ID_TIPO_CULTIVO.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/pca_atipicos.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/pca_clusters_kmeans.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/pca_unidades_por_columna.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/pca_unidades_por_orden.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/red_coocurrencia.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/red_superclase_actividad.png`
- `graficas/20261022-092519_M18_patrones_quimicos_2e13e5d1/umap_unidades_por_orden.png`

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-092519_M18_patrones_quimicos_2e13e5d1/manifiesto.json`. Reejecutar: `python main.py ejecutar M18_patrones_quimicos`.
