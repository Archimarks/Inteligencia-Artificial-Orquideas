# Metodologia

## 1. Diagnostico de los datos (auditoria)

`python main.py auditoria` revisa los 22 catalogos y Dataset.csv:
- **Estructura:** filas, columnas y PK por archivo.
- **Integridad:** unicidad de PK, FK huerfanas (catalogos y Dataset) y coherencia jerarquica (especie -> genero ->
  familia; lote -> articulo; atributos unicos por muestra).
- **Calidad:** nulos, duplicados y cobertura de las variables numericas por lote.
- **Distribuciones:** desbalance de cada variable categorica, contado en articulos y no solo en filas.

Responde las 8 preguntas del diagnostico en `03_Resultados/Global/auditoria_datos/<run>/informe_auditoria.md`.

**Hallazgo estructural clave.** Cada articulo aporta su propia especie, plataforma (columna, equipo, modo) y
biblioteca de anotacion. Una evaluacion que mezcle muestras de un mismo articulo en entrenamiento y prueba mide la
capacidad de reconocer el articulo, no la quimica. Por eso:
- la unidad de generalizacion es el articulo;
- una clase solo es evaluable si aparece en >= 2 articulos.

## 2. Unidades de analisis

| Pregunta | Unidad | X | Grupo de validacion |
|---|---|---|---|
| Superclase / clase de un compuesto (M08, M09) | metabolito unico | descriptores de la formula | formula |
| Modo de ionizacion (M01) | articulo x metabolito (un solo modo) | formula + superclase | articulo |
| Aducto (M10) | articulo x metabolito x aducto | formula + modo + superclase | articulo |
| Actividad de un compuesto (M17b) | metabolito con actividad citada | formula + superclase | formula |
| Atributos de muestra (M02-M07, M11-M15) | muestra biologica | CLR por clase quimica | articulo |
| Presencia de metabolitos (M16) | lote x especie x parte x tipo x cultivo x metodo | taxonomia + atributos | articulo |
| Actividades de una especie (M17) | especie x articulo | CLR por superclase | articulo |
| Patrones (M18) | especie x articulo x parte | CLR por superclase/clase | articulo (contrastes) |

## 3. Ingenieria de variables

- **Descriptores elementales.** Se calculan a partir de la formula: conteos atomicos, DBE, cocientes de Van Krevelen,
  indice de aromaticidad modificado y masa calculada. Se excluyen las formulas deuteradas (estandares internos) y
  las no interpretables.
- **Perfil composicional.** Numero de metabolitos identificados distintos por categoria quimica en cada muestra o
  unidad:
  - solo categorias presentes en >= 3 (superclase) o >= 5 (clase) articulos, mas una categoria "otras";
  - transformacion CLR con pseudoconteo 0.5;
  - se exige un minimo de 20 metabolitos clasificados por muestra.
- **Variables excluidas por fuga.**
  - m/z (m/z - masa = aducto y modo), RT e intensidad (dependen del lote);
  - identificadores de lote, articulo y muestra;
  - el propio objetivo. Tampoco entra en el control instrumental.

  `verificar_fuga` lo comprueba en cada ejecucion.
- **Seleccion de variables.** Es opcional (`seleccion_variables: {metodo: anova|informacion_mutua, k}`) y siempre se
  hace dentro del Pipeline, es decir, se ajusta solo con los datos de entrenamiento de cada particion.

## 4. Entrenamiento y evaluacion

- **Particiones.**
  - `StratifiedGroupKFold` (5 particiones) para multiclase y `GroupKFold` para multietiqueta. Una asercion garantiza
    que ningun grupo aparece en entrenamiento y prueba.
  - Clases con < N grupos o < M unidades se descartan y se listan (`tablas/clases_descartadas.csv`). Si quedan
    < 2 clases o < 3 grupos, el experimento se declara **no viable**, sin entrenar.
- **Modelos.**
  - Baselines: clase mayoritaria, estratificado y prior.
  - Regresion logistica balanceada, Random Forest, LightGBM, XGBoost y CatBoost (estos dos en GPU si hay; ver
    `02_Script/README.md`, seccion GPU) y opcionalmente ExtraTrees, HistGradientBoosting y KNN.
  - Pesos 1/n por articulo en los modelos de muestra.
- **Metricas.**
  - Multiclase: exactitud balanceada (principal), F1 macro y ponderado, MCC, exactitud y top-3.
  - Multietiqueta: precision promedio macro (principal), ROC-AUC macro, F1 micro/macro y Hamming. Se calculan sobre
    predicciones fuera de particion, con media y DE entre particiones.
- **Controles.**
  1. *Baseline:* el modelo debe superarlo.
  2. *Control instrumental:* el mismo modelo con solo columna, modos y numero de senales/identificados. Si iguala al
     modelo quimico, la prediccion se atribuye a la plataforma.
  3. *Evaluacion no agrupada:* `StratifiedKFold` ignorando grupos. La diferencia con la agrupada cuantifica cuanto
     inflaria una evaluacion ingenua.
  4. *Permutacion:* las etiquetas se permutan entre unidades con las mismas particiones; p = (1 + #nulo >= obs) / (1 + n).
     Con n permutaciones el p minimo alcanzable es 1/(n+1): si ninguna permutacion iguala el valor observado se
     considera significativo y se informa ese minimo (se usan >= 20 permutaciones).
- **Veredicto automatico.** Se deriva solo de las metricas (`pipeline/interpretacion.py`):

  | Veredicto | Criterio |
  |---|---|
  | senal robusta | ganancia >= 0.15 sobre el baseline, p < 0.05 y supera al control por > 0.03 |
  | senal debil | ganancia entre 0.05 y 0.15, con las mismas condiciones |
  | confundido con plataforma | el control iguala al modelo |
  | sin senal | no cumple las condiciones anteriores |
  | evidencia insuficiente | < 10 grupos independientes o mediana < 3 grupos por clase (se evalua, pero no se extraen conclusiones) |
  | no viable | clases o grupos insuficientes para evaluar |

## 5. Patrones quimicos (M18)

- **Enriquecimiento.**
  - Contraste: Mann-Whitney sobre el CLR de cada categoria quimica, en cada nivel de un factor (clase, orden,
    familia, parte, tipo) frente al resto.
  - Unidad de contraste: articulo x nivel. Solo niveles con >= 2 articulos.
  - Correccion por comparaciones multiples: Benjamini-Hochberg.
- **Coocurrencia.**
  - Pares de clases quimicas presentes en las mismas unidades, comparados con un modelo nulo *curveball*.
  - El nulo conserva el numero de clases de cada unidad (profundidad de anotacion del laboratorio) y la frecuencia
    de cada clase. Se calculan z y p empiricos, con BH, y se exporta la red en GraphML.
- **Reglas de asociacion.**
  - FP-growth entre clases quimicas (sin items casi universales).
  - Reglas taxon -> clase quimica calculadas directamente, exigiendo >= 2 articulos de soporte.
- **Agrupamiento.**
  - PCA y UMAP; K-means con k elegido por silueta.
  - Estabilidad por bootstrap (ARI, 80 % de submuestra).
  - Concordancia (AMI) de los clusters con orden taxonomico, columna y articulo.
- **Particion de varianza (PERMANOVA euclidea sobre CLR = distancia de Aitchison).**
  - R2 marginal y ajustado de cada factor.
  - Los factores constantes dentro del articulo se contrastan permutando articulos completos.
  - Version intra-articulo: se centra el perfil por articulo y se permuta dentro de cada articulo, para parte,
    cultivo y especie.
- **Atipicos.** Isolation Forest sobre los perfiles.
- **Red quimica-actividad.** Fisher (superclase del metabolito x actividad citada) con BH, y heatmap de conteos.
- **Firma de Orchidaceae** (descriptiva):
  - metabolitos presentes en todos los estudios de orquideas y su frecuencia en el resto;
  - diferencia de composicion por superclase.

## 6. Reproducibilidad

- Semilla global 42, propagada a NumPy, scikit-learn, LightGBM, XGBoost, CatBoost, UMAP y los bootstraps. En GPU,
  XGBoost y CatBoost pueden diferir ligeramente de CPU en el ultimo decimal (sumas en coma flotante en paralelo).
- `manifiesto.json` por ejecucion: huellas SHA-256 de cada CSV de entrada, huella de la configuracion, versiones de
  Python y librerias, plataforma, commit de git, inicio, fin y duracion.
- Las ejecuciones nunca se sobrescriben (`overwrite: false`). La ultima de cada experimento alimenta
  `03_Resultados/Global/resumen_ejecutivo.md`.
