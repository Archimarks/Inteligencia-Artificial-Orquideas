# Diccionario de datos

Fuente: `01_Datos/Base` (separador `;`, codificacion UTF-8 con BOM). En todos los catalogos el ID 0 = "No especificado". 
Las claves foraneas se verifican en la auditoria (0 huerfanos).

## `01_Catalogo_Nucleo/01_Articulos.csv`
Catalogo `articulos` - 54 filas. Clave primaria: `ID_ARTICULO`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_ARTICULO | int64 | 0 | Identificador del articulo (0 = no especificado) |
| ARCHIVO_ARTICULO | str | 0 | Nombre del PDF en 01_Datos/Data/Articulos |
| TITULO | str | 0 | Titulo del articulo |
| DOI | str | 0 | DOI |

## `01_Catalogo_Nucleo/02_Batches.csv`
Catalogo `batches` - 58 filas. Clave primaria: `ID_BATCH`. Claves foraneas: `ID_ARTICULO` -> articulos.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_BATCH | int64 | 0 | Identificador del lote de datos (archivo BATxxxx) |
| ID_ARTICULO | int64 | 0 | Identificador del articulo (0 = no especificado) |
| ARCHIVO_BATCH | str | 0 | Nombre del archivo de lote |

## `01_Catalogo_Nucleo/03_Modo_ionizacion.csv`
Catalogo `modos` - 4 filas. Clave primaria: `ID_MODO_IONIZACION`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_MODO_IONIZACION | int64 | 0 | Modo de ionizacion (1 ESI+, 2 ESI-, 3 EI) |
| MODO_IONIZACION | str | 0 | Nombre del modo |
| DESCRIPCION | str | 0 | Descripcion textual |

## `01_Catalogo_Nucleo/04_Actividades_biologicas.csv`
Catalogo `actividades` - 45 filas. Clave primaria: `ID_ACTIVIDAD_BIOLOGICA`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_ACTIVIDAD_BIOLOGICA | int64 | 0 | Actividad biologica |
| ACTIVIDAD_BIOLOGICA | str | 0 | Nombre de la actividad |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/01_Reinos.csv`
Catalogo `reinos` - 2 filas. Clave primaria: `ID_REINO`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_REINO | int64 | 0 | Reino |
| REINO | str | 0 | Nombre del reino |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/02_Filos.csv`
Catalogo `filos` - 4 filas. Clave primaria: `ID_FILO`. Claves foraneas: `ID_REINO` -> reinos.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_FILO | int64 | 0 | Filo |
| ID_REINO | int64 | 0 | Reino |
| FILO | str | 0 | Nombre del filo |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/03_Clases_taxonomicas.csv`
Catalogo `clases_tax` - 5 filas. Clave primaria: `ID_CLASE_TAXONOMICA`. Claves foraneas: `ID_FILO` -> filos.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_CLASE_TAXONOMICA | int64 | 0 | Clase taxonomica |
| ID_FILO | int64 | 0 | Filo |
| CLASE_TAXONOMICA | str | 0 | Nombre de la clase |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/04_Ordenes.csv`
Catalogo `ordenes` - 24 filas. Clave primaria: `ID_ORDEN`. Claves foraneas: `ID_CLASE_TAXONOMICA` -> clases_tax.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_ORDEN | int64 | 0 | Orden |
| ID_CLASE_TAXONOMICA | int64 | 0 | Clase taxonomica |
| ORDEN | str | 0 | Nombre del orden |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/05_Familias.csv`
Catalogo `familias` - 35 filas. Clave primaria: `ID_FAMILIA`. Claves foraneas: `ID_ORDEN` -> ordenes.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_FAMILIA | int64 | 0 | Familia |
| ID_ORDEN | int64 | 0 | Orden |
| FAMILIA | str | 0 | Nombre de la familia |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/06_Generos.csv`
Catalogo `generos` - 52 filas. Clave primaria: `ID_GENERO`. Claves foraneas: `ID_FAMILIA` -> familias.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_GENERO | int64 | 0 | Genero |
| ID_FAMILIA | int64 | 0 | Familia |
| GENERO | str | 0 | Nombre del genero |
| DESCRIPCION | str | 0 | Descripcion textual |

## `02_Catalogo_Especie/07_Especies.csv`
Catalogo `especies` - 73 filas. Clave primaria: `ID_ESPECIE`. Claves foraneas: `ID_GENERO` -> generos.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_ESPECIE | int64 | 0 | Especie |
| ID_GENERO | int64 | 0 | Genero |
| NOMBRE_CIENTIFICO | str | 0 | Nombre cientifico con autor |
| NOMBRE_COMUN | str | 0 | Nombre comun |
| DESCRIPCION | str | 0 | Descripcion textual |

## `03_Catalogo_Metabolito/01_Niveles_identificacion.csv`
Catalogo `niveles` - 5 filas. Clave primaria: `ID_NIVEL_IDENTIFICACION`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_NIVEL_IDENTIFICACION | int64 | 0 | Nivel MSI de identificacion (1-4) |
| NIVEL_IDENTIFICACION | str | 0 | I, II, III o IV |
| DESCRIPCION | str | 0 | Descripcion textual |

## `03_Catalogo_Metabolito/02_Superclases_quimicas.csv`
Catalogo `superclases` - 22 filas. Clave primaria: `ID_SUPERCLASE_QUIMICA`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_SUPERCLASE_QUIMICA | int64 | 0 | Superclase quimica (ontologia tipo ClassyFire) |
| SUPERCLASE_QUIMICA | str | 0 | Nombre de la superclase |
| DESCRIPCION | str | 0 | Descripcion textual |

## `03_Catalogo_Metabolito/03_Clases_quimicas.csv`
Catalogo `clases_quim` - 804 filas. Clave primaria: `ID_CLASE_QUIMICA`. Claves foraneas: `ID_SUPERCLASE_QUIMICA` -> superclases.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_CLASE_QUIMICA | int64 | 0 | Clase quimica |
| ID_SUPERCLASE_QUIMICA | int64 | 0 | Superclase quimica (ontologia tipo ClassyFire) |
| CLASE_QUIMICA | str | 0 | Nombre de la clase quimica |
| DESCRIPCION | str | 0 | Descripcion textual |

## `03_Catalogo_Metabolito/04_Aductos.csv`
Catalogo `aductos` - 82 filas. Clave primaria: `ID_ADUCTO`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_ADUCTO | int64 | 0 | Tipo de aducto/ion |
| ADUCTO | str | 0 | Notacion del aducto |
| DESCRIPCION | str | 0 | Descripcion textual |

## `03_Catalogo_Metabolito/05_Metabolitos.csv`
Catalogo `metabolitos` - 45850 filas. Clave primaria: `ID_METABOLITO`. Claves foraneas: `ID_CLASE_QUIMICA` -> clases_quim.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_METABOLITO | int64 | 0 | Metabolito (0 no especificado, 1 = senal no identificada) |
| NOMBRE_METABOLITO | str | 0 | Nombre del metabolito |
| FORMULA_MOLECULAR | str | 5547 | Formula molecular neutra |
| ID_CLASE_QUIMICA | int64 | 0 | Clase quimica |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/01_Columnas_cromatograficas.csv`
Catalogo `columnas` - 18 filas. Clave primaria: `ID_COLUMNA_CROMATOGRAFICA`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_COLUMNA_CROMATOGRAFICA | int64 | 0 | Columna cromatografica |
| COLUMNA_CROMATOGRAFICA | str | 0 | Descripcion de la columna |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/02_Tipos_muestra.csv`
Catalogo `tipos_muestra` - 12 filas. Clave primaria: `ID_TIPO_MUESTRA`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_TIPO_MUESTRA | int64 | 0 | Tipo de muestra (9 QC, 10 blanco) |
| TIPO_MUESTRA | str | 0 | Nombre del tipo |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv`
Catalogo `partes` - 30 filas. Clave primaria: `ID_PARTE_ESTUDIADA`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_PARTE_ESTUDIADA | int64 | 0 | Parte de la planta |
| PARTE_PLANTA_ESTUDIADA | str | 0 | Nombre de la parte |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/04_Tipos_cultivo.csv`
Catalogo `cultivos` - 10 filas. Clave primaria: `ID_TIPO_CULTIVO`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_TIPO_CULTIVO | int64 | 0 | Tipo de cultivo/procedencia |
| TIPO_CULTIVO | str | 0 | Nombre del tipo de cultivo |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/05_Metodos_extraccion.csv`
Catalogo `metodos` - 32 filas. Clave primaria: `ID_METODO_EXTRACCION`.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_METODO_EXTRACCION | int64 | 0 | Metodo de extraccion |
| METODO_EXTRACCION | str | 0 | Descripcion del metodo |
| DESCRIPCION | str | 0 | Descripcion textual |

## `04_Catalogo_Muestra/06_Muestras_Batch.csv`
Catalogo `muestras` - 1774 filas. Clave primaria: `ID_MUESTRA`. Claves foraneas: `ID_BATCH` -> batches, `ID_ESPECIE` -> especies, `ID_PARTE_ESTUDIADA` -> partes, `ID_TIPO_MUESTRA` -> tipos_muestra, `ID_TIPO_CULTIVO` -> cultivos, `ID_METODO_EXTRACCION` -> metodos.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_MUESTRA | int64 | 0 | Muestra (inyeccion) dentro de un lote |
| ID_BATCH | int64 | 0 | Identificador del lote de datos (archivo BATxxxx) |
| CODIGO_MUESTRA | str | 0 | Codigo original de la muestra en el lote |
| ID_ESPECIE | int64 | 0 | Especie |
| ID_PARTE_ESTUDIADA | int64 | 0 | Parte de la planta |
| ID_TIPO_MUESTRA | int64 | 0 | Tipo de muestra (9 QC, 10 blanco) |
| ID_TIPO_CULTIVO | int64 | 0 | Tipo de cultivo/procedencia |
| ID_METODO_EXTRACCION | int64 | 0 | Metodo de extraccion |
| GRUPO_EXPERIMENTAL | str | 0 | Tratamiento/grupo descrito en el articulo |
| REPLICA | str | 812 | Numero de replica |
| DESCRIPCION | str | 0 | Descripcion textual |

## `05_Pivotes/Registo_Actividades_biologicas.csv`
Catalogo `registro_actividades` - 972 filas. Clave primaria: `ID_REGISTRO`. Claves foraneas: `ID_ARTICULO` -> articulos, `ID_ESPECIE` -> especies, `ID_MUESTRA` -> muestras, `ID_METABOLITO` -> metabolitos, `ID_ACTIVIDAD_BIOLOGICA` -> actividades.

| columna | tipo | nulos/vacios | descripcion |
|---|---|---|---|
| ID_REGISTRO | int64 | 0 | Identificador del registro de actividad |
| ID_ARTICULO | int64 | 0 | Identificador del articulo (0 = no especificado) |
| ID_ESPECIE | int64 | 0 | Especie |
| ID_MUESTRA | int64 | 0 | Muestra (inyeccion) dentro de un lote |
| ID_METABOLITO | int64 | 0 | Metabolito (0 no especificado, 1 = senal no identificada) |
| ID_ACTIVIDAD_BIOLOGICA | int64 | 0 | Actividad biologica |
| TIPO_EVIDENCIA | str | 0 | Literatura citada / ensayo experimental |
| ENSAYO | str | 786 | Ensayo (DPPH, ABTS, ...) |
| VALOR_ACTIVIDAD | float64 | 796 | Valor medido |
| UNIDAD_ACTIVIDAD | str | 796 | Unidad del valor |
| FUENTE | str | 0 | Fragmento o tabla de origen en el articulo |

## `Dataset.csv`
6 116 075 filas x 29 columnas. Unidad: una senal espectral (caracteristica o metabolito anotado) medida en una muestra de un lote. 
Las columnas `ID_*` repiten los atributos de articulo, lote, muestra, taxonomia y quimica (desnormalizado). Cuando una muestra tiene k 
medidas experimentales de actividad, cada senal aparece k veces con `ID_ACTIVIDAD_BIOLOGICA`, `VALOR_ACTIVIDAD` y `UNIDAD_ACTIVIDAD`; 
`vista_quimica()` elimina esa replicacion (5 798 278 filas).

| columna | descripcion |
|---|---|
| ID_ARTICULO | Identificador del articulo (0 = no especificado) |
| ID_BATCH | Identificador del lote de datos (archivo BATxxxx) |
| ID_MUESTRA | Muestra (inyeccion) dentro de un lote |
| ID_REINO | Reino |
| ID_FILO | Filo |
| ID_CLASE_TAXONOMICA | Clase taxonomica |
| ID_ORDEN | Orden |
| ID_FAMILIA | Familia |
| ID_GENERO | Genero |
| ID_ESPECIE | Especie |
| ID_TIPO_MUESTRA | Tipo de muestra (9 QC, 10 blanco) |
| ID_PARTE_ESTUDIADA | Parte de la planta |
| ID_TIPO_CULTIVO | Tipo de cultivo/procedencia |
| ID_METODO_EXTRACCION | Metodo de extraccion |
| ID_COLUMNA_CROMATOGRAFICA | Columna cromatografica |
| ID_MODO_IONIZACION | Modo de ionizacion (1 ESI+, 2 ESI-, 3 EI) |
| ID_NIVEL_IDENTIFICACION | Nivel MSI de identificacion (1-4) |
| ID_SUPERCLASE_QUIMICA | Superclase quimica (ontologia tipo ClassyFire) |
| ID_CLASE_QUIMICA | Clase quimica |
| ID_ADUCTO | Tipo de aducto/ion |
| ID_METABOLITO | Metabolito (0 no especificado, 1 = senal no identificada) |
| ID_ACTIVIDAD_BIOLOGICA | Actividad biologica |
| FORMULA_MOLECULAR | Formula molecular neutra |
| MASA_MONOISOTOPICA | Masa monoisotopica neutra (Da) |
| RELACION_MASA_CARGA | m/z observada |
| TIEMPO_RETENCION_MINUTOS | Tiempo de retencion (min) |
| ALTURA_PICO | Intensidad/area de la senal en la muestra (escala propia de cada lote) |
| VALOR_ACTIVIDAD | Valor medido |
| UNIDAD_ACTIVIDAD | Unidad del valor |

## Variables derivadas (02_Script/src/orquideas/features)

| variable | origen | uso |
|---|---|---|
| n_C, n_H, n_N, n_O, n_P, n_S, n_F, n_Cl, n_Br, n_I, n_otros | conteo de atomos de la formula | M01, M08-M10, M17b |
| dbe | dobles enlaces equivalentes = 1 + C - (H+X)/2 + N/2 | idem |
| masa_formula | masa monoisotopica calculada de la formula | idem |
| H_C, O_C, N_C, S_C, P_C, dbe_C | cocientes elementales (diagrama de Van Krevelen) | idem |
| ai_mod | indice de aromaticidad modificado (Koch y Dittmar) | idem |
| heteroatomos, halogenado, n_atomos_pesados, regla_nitrogeno_par | derivados de la formula | idem |
| superclase_k / clase_k | CLR del numero de metabolitos identificados de la categoria k en la muestra/unidad | M02-M07, M11-M15, M17, M18 |
| ID_*_v (one-hot) | indicadoras de atributos categoricos | M01, M10, M16, controles instrumentales |
| log_n_identificados, log_n_senales, MODOS, columna | profundidad de anotacion y plataforma | control de confusion |
