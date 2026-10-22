# Informe de auditoria de datos

Ejecucion: `oficial` (2026-10-22T08:31:49). Huellas SHA-256 de los archivos de entrada en `resumen.json`.

## 1. Inventario
| archivo | filas | columnas | pk | fks | bytes |
|---|---|---|---|---|---|
| 01_Catalogo_Nucleo/01_Articulos.csv | 54 | 4 | ID_ARTICULO | nan | 11779 |
| 01_Catalogo_Nucleo/02_Batches.csv | 58 | 3 | ID_BATCH | ID_ARTICULO->articulos | 2857 |
| 01_Catalogo_Nucleo/03_Modo_ionizacion.csv | 4 | 3 | ID_MODO_IONIZACION | nan | 316 |
| 01_Catalogo_Nucleo/04_Actividades_biologicas.csv | 45 | 3 | ID_ACTIVIDAD_BIOLOGICA | nan | 2941 |
| 02_Catalogo_Especie/01_Reinos.csv | 2 | 3 | ID_REINO | nan | 172 |
| 02_Catalogo_Especie/02_Filos.csv | 4 | 4 | ID_FILO | ID_REINO->reinos | 407 |
| 02_Catalogo_Especie/03_Clases_taxonomicas.csv | 5 | 4 | ID_CLASE_TAXONOMICA | ID_FILO->filos | 434 |
| 02_Catalogo_Especie/04_Ordenes.csv | 24 | 4 | ID_ORDEN | ID_CLASE_TAXONOMICA->clases_tax | 1852 |
| 02_Catalogo_Especie/05_Familias.csv | 35 | 4 | ID_FAMILIA | ID_ORDEN->ordenes | 2632 |
| 02_Catalogo_Especie/06_Generos.csv | 52 | 4 | ID_GENERO | ID_FAMILIA->familias | 2889 |
| 02_Catalogo_Especie/07_Especies.csv | 73 | 5 | ID_ESPECIE | ID_GENERO->generos | 8891 |
| 03_Catalogo_Metabolito/01_Niveles_identificacion.csv | 5 | 3 | ID_NIVEL_IDENTIFICACION | nan | 449 |
| 03_Catalogo_Metabolito/02_Superclases_quimicas.csv | 22 | 3 | ID_SUPERCLASE_QUIMICA | nan | 1919 |
| 03_Catalogo_Metabolito/03_Clases_quimicas.csv | 804 | 4 | ID_CLASE_QUIMICA | ID_SUPERCLASE_QUIMICA->superclases | 77261 |
| 03_Catalogo_Metabolito/04_Aductos.csv | 82 | 3 | ID_ADUCTO | nan | 7197 |
| 03_Catalogo_Metabolito/05_Metabolitos.csv | 45850 | 5 | ID_METABOLITO | ID_CLASE_QUIMICA->clases_quim | 5733331 |
| 04_Catalogo_Muestra/01_Columnas_cromatograficas.csv | 18 | 3 | ID_COLUMNA_CROMATOGRAFICA | nan | 3021 |
| 04_Catalogo_Muestra/02_Tipos_muestra.csv | 12 | 3 | ID_TIPO_MUESTRA | nan | 1080 |
| 04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv | 30 | 3 | ID_PARTE_ESTUDIADA | nan | 1777 |
| 04_Catalogo_Muestra/04_Tipos_cultivo.csv | 10 | 3 | ID_TIPO_CULTIVO | nan | 807 |
| 04_Catalogo_Muestra/05_Metodos_extraccion.csv | 32 | 3 | ID_METODO_EXTRACCION | nan | 2980 |
| 04_Catalogo_Muestra/06_Muestras_Batch.csv | 1774 | 11 | ID_MUESTRA | ID_BATCH->batches, ID_ESPECIE->especies, ID_PARTE_ESTUDIADA->partes, I | 194093 |
| 05_Pivotes/Registo_Actividades_biologicas.csv | 972 | 11 | ID_REGISTRO | ID_ARTICULO->articulos, ID_ESPECIE->especies, ID_MUESTRA->muestras, ID | 109427 |
| Dataset.csv | 6116075 | 29 | (sin clave unica; ver informe) | 22 columnas ID_* | 547657519 |

**Unidad de observacion de `Dataset.csv`.** Cada fila es una senal espectral (caracteristica LC/GC-MS o metabolito anotado)
medida en una muestra de un lote, con su intensidad `ALTURA_PICO`. No existe una clave unica: la combinacion natural
(muestra, senal) no tiene identificador de senal. Cuando una muestra tiene k medidas experimentales de actividad, cada
senal se repite k veces (columnas `ID_ACTIVIDAD_BIOLOGICA`, `VALOR_ACTIVIDAD`, `UNIDAD_ACTIVIDAD`): 317,797
filas replicadas. La vista quimica sin replicacion tiene 5,798,278 observaciones
(5,124,156 de muestras biologicas, sin QC ni blancos).

| Entidad | Cantidad |
|---|---|
| Articulos con datos / en catalogo | 52 / 53 |
| Lotes (batches) | 57 |
| Muestras (biologicas / QC+blanco) | 1773 (1478 / 295) |
| Especies con datos | 71 |
| Metabolitos identificados distintos (nivel I-III) | 45,842 |
| Observaciones con metabolito identificado | 1,311,831 (25.6 %) |
| Registros de actividad biologica | 972 |

Jerarquia: articulo (1) -> lote (1..3) -> muestra (n) -> observacion (senal x muestra). Especie, parte, tipo de muestra,
cultivo y metodo de extraccion son atributos de la muestra; columna cromatografica es atributo del lote; modo, aducto,
nivel y metabolito son atributos de la observacion; las actividades biologicas se registran por articulo/especie,
por metabolito (literatura) o por muestra (ensayo experimental) en `05_Pivotes/Registo_Actividades_biologicas.csv`.

## 2. Integridad referencial
Claves foraneas huerfanas (catalogos + Dataset): **0**.

| columna | referencia | valores_distintos | huerfanos | pct_cero |
|---|---|---|---|---|
| ID_ARTICULO | articulos | 53 | 0 | 2.26 |
| ID_BATCH | batches | 57 | 0 | 0.0 |
| ID_MUESTRA | muestras | 1773 | 0 | 0.0 |
| ID_REINO | reinos | 2 | 0 | 0.4 |
| ID_FILO | filos | 4 | 0 | 0.4 |
| ID_CLASE_TAXONOMICA | clases_tax | 5 | 0 | 0.4 |
| ID_ORDEN | ordenes | 24 | 0 | 0.4 |
| ID_FAMILIA | familias | 35 | 0 | 0.4 |
| ID_GENERO | generos | 51 | 0 | 14.68 |
| ID_ESPECIE | especies | 72 | 0 | 15.26 |
| ID_TIPO_MUESTRA | tipos_muestra | 12 | 0 | 0.0 |
| ID_PARTE_ESTUDIADA | partes | 30 | 0 | 31.99 |
| ID_TIPO_CULTIVO | cultivos | 10 | 0 | 3.03 |
| ID_METODO_EXTRACCION | metodos | 31 | 0 | 2.11 |
| ID_COLUMNA_CROMATOGRAFICA | columnas | 18 | 0 | 2.32 |
| ID_MODO_IONIZACION | modos | 4 | 0 | 0.58 |
| ID_NIVEL_IDENTIFICACION | niveles | 4 | 0 | 0.0 |
| ID_SUPERCLASE_QUIMICA | superclases | 22 | 0 | 78.52 |
| ID_CLASE_QUIMICA | clases_quim | 740 | 0 | 78.08 |
| ID_ADUCTO | aductos | 82 | 0 | 64.88 |
| ID_METABOLITO | metabolitos | 45849 | 0 | 0.0 |
| ID_ACTIVIDAD_BIOLOGICA | actividades | 4 | 0 | 90.56 |

Consistencia jerarquica:

| chequeo | inconsistencias |
|---|---|
| especie->genero coherente con catalogo | 0 |
| genero->familia coherente con catalogo | 0 |
| muestra con atributos unicos | 0 |
| atributos de muestra iguales en Dataset y 06_Muestras_Batch (ID_MUESTR | 0 |
| filas con ID_MUESTRA=0 (senal sin valores por muestra; atributos a niv | 1 |
| lote->articulo coherente con 02_Batches | 0 |

## 3. Variables categoricas, cobertura y desbalance
La unidad independiente para evaluar generalizacion es el **articulo** (cada articulo usa su propia plataforma, laboratorio
y especie). `categorias_con_>=2_articulos` indica cuantas categorias pueden evaluarse con validacion por grupos.

| variable | categorias_no_vacias | categorias_con_>=2_articulos | categorias_con_>=3_articulos | razon_desbalance_max_min | pct_registros_categoria_0 |
|---|---|---|---|---|---|
| familia | 34 | 10 | 6 | 87.8 | 0.0 |
| orden | 23 | 10 | 8 | 75.2 | 0.0 |
| clase_taxonomica | 4 | 2 | 2 | 110.2 | 0.0 |
| filo | 3 | 1 | 1 | 120.4 | 0.0 |
| genero | 50 | 3 | 1 | 40.0 | 26.66 |
| especie | 71 | 2 | 0 | 36.0 | 26.66 |
| parte | 29 | 10 | 8 | 354.0 | 27.47 |
| tipo_muestra | 9 | 3 | 2 | 259.0 | 0.27 |
| cultivo | 9 | 5 | 4 | 162.3 | 2.44 |
| metodo | 30 | 6 | 4 | 131.3 | 3.04 |
| columna | 17 | 5 | 3 | 131.3 | 5.62 |
| modo | 3 | 3 | 3 | 327.4 | 0.7 |
| nivel | 4 | 4 | 4 | 21.8 | 0.0 |
| superclase | 21 | 19 | 19 | 21811.8 | 20.1 |
| aducto | 81 | 40 | 37 | 185269.3 | 66.29 |

## 4. Cobertura por lote
| ID_BATCH | articulo | especie | columna | muestras | filas | metabolitos | pct_identificadas |
|---|---|---|---|---|---|---|---|
| 1 | 1 | Ilex guayusa Loes. | ACQUITY UPLC CSH C18 (1.7 um, 3.0 x 50 mm) con precolumna VanGuard CSH | 100 | 63396 | 11 | 1.73 |
| 2 | 1 | Ilex guayusa Loes. | ACQUITY UPLC CSH C18 (1.7 um, 3.0 x 50 mm) con precolumna VanGuard CSH | 100 | 52490 | 3 | 0.4 |
| 3 | 0 | Banisteriopsis caapi (Spruce ex Griseb.) C.V.Morton | No especificado | 59 | 127229 | 28 | 1.14 |
| 4 | 0 | Piper peltatum L. | Columna capilar de GC-MS (no especificada en los datos) | 28 | 11256 | 0 | 0.0 |
| 5 | 2 | No especificado | Kinetex C18 (1.7 um, 50 x 2.1 mm; Phenomenex) | 201 | 585704 | 0 | 0.0 |
| 6 | 2 | No especificado | Kinetex C18 (1.7 um, 50 x 2.1 mm; Phenomenex) | 201 | 286969 | 0 | 0.0 |
| 7 | 3 | Pisum sativum L. | Intensity Solo 2 C18 (2 um, 100 x 2.1 mm; Bruker) con precolumna ACQUI | 147 | 161751 | 123 | 10.02 |
| 8 | 5 | Solanum tuberosum L. | Waters ACQUITY Premier HSS T3 (1.8 um, 2.1 x 100 mm) | 9 | 15849 | 1761 | 100.0 |
| 9 | 6 | Oldenlandia diffusa (Willd.) Roxb. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 66 | 36911 | 629 | 100.0 |
| 10 | 6 | Oldenlandia diffusa (Willd.) Roxb. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 66 | 42483 | 714 | 100.0 |
| 11 | 7 | Garcinia oblongifolia Champ. ex Benth. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 12 | 4824 | 402 | 100.0 |
| 12 | 8 | Rubia magna P.G.Xiao | Phenomenex Kinetex C18 (2.6 um, 2.1 x 100 mm) | 18 | 25671 | 1440 | 100.0 |
| 13 | 9 | Pinellia pedatisecta Schott | No especificado | 18 | 6738 | 640 | 100.0 |
| 14 | 10 | Pogostemon cablin (Blanco) Benth. | Waters ACQUITY UPLC BEH HILIC (1.7 um, 2.1 x 100 mm) | 15 | 363960 | 5793 | 23.87 |
| 15 | 11 | Nicotiana tabacum L. | Hypersil GOLD (1.9 um, 100 x 2.1 mm) | 69 | 529575 | 2267 | 29.54 |
| 16 | 12 | Platostoma chinense (Benth.) A.J.Paton | Waters XSelect HSS T3 (2.5 um, 2.1 x 150 mm) | 15 | 10170 | 678 | 100.0 |
| 17 | 13 | Eriobotrya japonica (Thunb.) Lindl. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 21 | 2058 | 98 | 100.0 |
| 18 | 14 | Codonopsis pilosula (Franch.) Nannf. | Waters ACQUITY UPLC BEH C18 (1.7 um, 2.1 x 100 mm) | 12 | 200700 | 0 | 0.0 |
| 19 | 15 | Spatholobus suberectus Dunn | Waters ACQUITY Premier HSS T3 (1.8 um, 2.1 x 100 mm) | 18 | 121500 | 6750 | 100.0 |
| 20 | 16 | Mosla chinensis Maxim. cv. Jiangxiangru | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 9 | 389167 | 5156 | 13.76 |
| 21 | 17 | Fagopyrum dibotrys (D.Don) H.Hara | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 15 | 9638 | 648 | 100.0 |
| 22 | 18 | Akebia trifoliata (Thunb.) Koidz. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 19140 | 1595 | 100.0 |
| 23 | 19 | Ipomoea batatas (L.) Lam. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 13 | 40926 | 3415 | 100.0 |
| 24 | 20 | Polygonatum cyrtonema Hua | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 24 | 7086 | 348 | 100.0 |
| 25 | 21 | Fragaria x ananassa (Weston) Duchesne | Shim-pack VP-ODS C18 (5.0 um, 2 x 150 mm) | 12 | 1956 | 163 | 100.0 |
| 26 | 22 | Medicago sativa L. | Waters ACQUITY UPLC BEH C18 (1.7 um, 2.1 x 100 mm) | 41 | 964894 | 2519 | 10.7 |
| 27 | 23 | Camellia tetracocca Hung T.Chang | Waters ACQUITY UPLC BEH C18 (1.7 um, 2.1 x 100 mm) | 6 | 3738 | 620 | 100.0 |
| 28 | 24 | Gastrodia elata Blume | Hypersil GOLD aQ (1.9 um, 100 x 2.1 mm; Thermo) | 18 | 200376 | 927 | 8.89 |
| 29 | 25 | Camellia sinensis (L.) Kuntze | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 7 | 2917 | 429 | 100.0 |
| 30 | 26 | Morus alba L. | Hypersil GOLD (1.9 um, 100 x 2.1 mm) | 15 | 26295 | 1753 | 100.0 |
| 31 | 27 | Dioscorea opposita Thunb. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 9 | 8389 | 988 | 100.0 |
| 32 | 28 | Taxus x media Rehder | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 15 | 10531 | 807 | 100.0 |
| 33 | 29 | Camellia drupifera Lour. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 823 | 78 | 100.0 |
| 34 | 30 | Avena sativa L. | Kinetex C18 (1.7 um, 150 x 2.1 mm; Phenomenex) | 36 | 24910 | 702 | 100.0 |
| 35 | 31 | Panax quinquefolius L. | No especificado | 20 | 7960 | 398 | 100.0 |
| 36 | 32 | Morus alba L. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 18 | 38340 | 2130 | 100.0 |
| 37 | 33 | Neolamarckia cadamba (Roxb.) Bosser | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 9 | 4824 | 541 | 100.0 |
| 38 | 34 | Paeonia lactiflora Pall. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 14186 | 1237 | 100.0 |
| 39 | 35 | Chrysanthemum morifolium Ramat. | Accucore C18 (2.6 um, 2.1 x 100 mm; Thermo) | 30 | 78736 | 3237 | 100.0 |
| 40 | 36 | Malus pumila var. medzwetzkyana Dieck | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 21 | 4848 | 311 | 100.0 |
| 41 | 37 | Ipomoea batatas (L.) Lam. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 12 | 20796 | 1733 | 100.0 |
| 42 | 38 | Sesamum indicum L. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 6 | 4395 | 776 | 100.0 |
| 43 | 39 | Dendrobium officinale Kimura & Migo | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 23097 | 1929 | 100.0 |
| 44 | 40 | Cormus domestica (L.) Spach | Waters ACQUITY UPLC BEH C18 (1.7 um, 2.1 x 100 mm) | 9 | 10735 | 1176 | 99.94 |
| 45 | 41 | Clematis tangutica (Maxim.) Korsh. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 18 | 23929 | 1362 | 100.0 |
| 46 | 42 | Glycyrrhiza inflata Batalin | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 15 | 28635 | 1909 | 100.0 |
| 47 | 43 | Nelumbo nucifera Gaertn. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 18 | 19692 | 1094 | 100.0 |
| 48 | 53 | Rhododendron triflorum Hook.f. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 15 | 55575 | 3705 | 100.0 |
| 49 | 44 | Citrus reticulata Blanco 'Dahongpao' | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 9 | 12087 | 1343 | 100.0 |
| 50 | 45 | Actinidia arguta (Siebold & Zucc.) Planch. ex Miq. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 18 | 3420 | 190 | 100.0 |
| 51 | 46 | Camellia oleifera C.Abel | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 15 | 20115 | 1341 | 100.0 |
| 52 | 47 | Striga asiatica (L.) Kuntze | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 24 | 21864 | 911 | 100.0 |
| 53 | 48 | Hemerocallis citrina Baroni | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 4149 | 364 | 100.0 |
| 54 | 49 | Withania somnifera (L.) Dunal | Thermo Scientific C18 (3 um, 2.1 x 100 mm) | 3 | 2976 | 990 | 100.0 |
| 55 | 50 | Cibotium barometz (L.) J.Sm. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 25 | 857350 | 2317 | 6.76 |
| 56 | 51 | Lagerstroemia speciosa (L.) Pers. | Agilent SB-C18 (1.8 um, 2.1 x 100 mm) | 12 | 22553 | 2016 | 100.0 |
| 57 | 52 | Capsicum annuum L. | Waters ACQUITY UPLC HSS T3 (1.8 um, 2.1 x 100 mm) | 21 | 157996 | 7702 | 99.99 |

## 5. Respuestas a las preguntas del diagnostico
1. **Informacion disponible.** Intensidades por senal y muestra, identidades quimicas (para 25.6 % de las
   observaciones biologicas), clase/superclase quimica, aducto, modo, masa, m/z y RT (cobertura parcial por lote), atributos
   de muestra (especie, parte, tipo, cultivo, extraccion), columna cromatografica y actividades biologicas por especie,
   metabolito o muestra.
2. **Variables utiles para ML.** Composicion quimica relativa por muestra (fraccion de metabolitos por superclase/clase), presencia
   de metabolitos, composicion elemental derivada de la formula (C, H, N, O, P, S, insaturaciones, cocientes H/C y O/C), masa
   monoisotopica. Las intensidades absolutas y el RT no son comparables entre lotes.
3. **Objetivos de prediccion posibles.** Superclase/clase quimica de un metabolito a partir de su formula; modo de ionizacion y
   tipo de aducto a partir de la quimica del compuesto; categorias de muestra (clase taxonomica, familia, orden, parte, tipo de
   muestra, metodo, columna) a partir del perfil quimico; actividades biologicas por especie (multietiqueta).
4. **Requieren supervision.** Los anteriores, con validacion agrupada por articulo para no mezclar datos del mismo estudio.
5. **Se benefician de tecnicas no supervisadas.** Similitud y agrupamiento de especies por perfil quimico, coocurrencia de
   metabolitos y clases, reglas de asociacion, deteccion de perfiles atipicos y redes metabolito-especie-actividad.
6. **No modelables de forma fiable hoy.** Variables con <2 categorias evaluables entre articulos: filo.
   Prediccion de especie entre articulos (casi cada especie aparece en un solo articulo) y de filo/reino (1-2 lotes fuera de
   Magnoliophyta). Regresion de valores de actividad (muy pocos grupos con valor medido y escalas/ensayos distintos).
   Identificacion de un metabolito desconocido: no hay espectros MS/MS en el conjunto.
7. **Limitaciones para generalizar.** Confusion total entre especie, articulo, plataforma analitica y laboratorio; cobertura
   desigual de familias (muy pocas orquideas: Gastrodia y Dendrobium); bibliotecas de anotacion distintas entre plataformas
   (los MRM de Metware comparten biblioteca y eso induce coocurrencias artificiales); intensidades no comparables; actividades
   mayoritariamente bibliograficas (etiquetas positivas sin negativos verificados).
8. **Informacion adicional necesaria.** Espectros MS/MS y RT estandarizados (indices de retencion), mas especies de orquideas,
   varias especies analizadas con un mismo protocolo, muestras compartidas entre laboratorios (puente de lotes), ensayos de
   actividad con controles negativos y valores cuantitativos homogeneos, y el mapeo pozo-especie de BAT0005/0006.

Variables con >=2 categorias evaluables entre articulos: familia, orden, clase_taxonomica, genero, especie, parte, tipo_muestra, cultivo, metodo, columna, modo, nivel, superclase, aducto.

## 6. Graficas
- `graficas/actividades_por_especies.png`
- `graficas/cobertura_numericas_por_lote.png`
- `graficas/dist_columna_articulos.png`
- `graficas/dist_cultivo_articulos.png`
- `graficas/dist_especie_articulos.png`
- `graficas/dist_familia_articulos.png`
- `graficas/dist_genero_articulos.png`
- `graficas/dist_metodo_articulos.png`
- `graficas/dist_orden_articulos.png`
- `graficas/dist_parte_articulos.png`
- `graficas/dist_tipo_muestra_articulos.png`
- `graficas/intensidad_por_lote.png`
- `graficas/metabolitos_por_superclase.png`
- `graficas/niveles_identificacion.png`
- `graficas/pct_identificadas_por_lote.png`
