# Guia de modelos

Generada por `python main.py resumen` a partir de `02_Script/config/modelos/*.yaml` y de la ultima ejecucion de cada experimento. Para cambiar un experimento edite su YAML (ver `02_Script/README.md`, seccion Configuracion) y reejecutelo con `python main.py ejecutar <ID>`.

## M01_modo_ionizacion - Modo de ionizacion (ESI+ / ESI-) a partir de la quimica del compuesto

**Pregunta.** ¿La composicion elemental y la superclase de un metabolito permiten anticipar si se detecta en ESI positivo o negativo, en articulos no vistos?

**Diseno.** Unidad = (articulo, metabolito) detectado en un solo modo, solo en articulos que adquirieron ambos modos. X = descriptores de la formula (C, H, N, O, P, S, DBE, H/C, O/C, indice de aromaticidad...) + superclase. Sin m/z, aducto ni RT (fuga). Grupos = articulo.

- Conjunto: `metabolito_modo` con parametros `{'incluir_superclase': True}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-093736_M01_modo_ionizacion_f239609e` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.686 frente a 0.503 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.183); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.702.

**Como interpretarlo.** Los acidos (carboxilos, fenoles, fosfatos) tienden a ionizar en negativo y las bases nitrogenadas en positivo. Un rendimiento moderado es esperable: muchos compuestos ionizan en ambos modos y la eleccion depende del metodo.

## M02_filo - Filo a partir del perfil quimico

**Pregunta.** ¿El perfil quimico distingue angiospermas de gimnospermas y helechos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_FILO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-083940_M02_filo_95d4261c` - estado **no_viable**, veredicto **no viable**
- Resultado: Tras exigir >= 2 grupos y >= 10 unidades por clase quedan 1 clases y 48 grupos; no es posible una evaluacion agrupada honesta.

**Como interpretarlo.** Solo Magnoliophyta tiene muestras en >= 2 articulos; se espera 'no viable'. El reino (Plantae) es constante y no se modela.

## M03_clase_taxonomica - Clase taxonomica a partir del perfil quimico

**Pregunta.** ¿El perfil quimico separa Magnoliopsida de Liliopsida (monocotiledoneas) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_CLASE_TAXONOMICA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-083948_M03_clase_taxonomica_ef8707f2` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.486 frente a 0.521 del baseline y 0.389 del control solo-plataforma (ganancia sobre la mejor referencia -0.035); p de permutacion = 0.806; evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.514: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Liliopsida esta representada por pocos articulos; una prediccion correcta podria reflejar la plataforma de esos estudios.

## M04_orden - Orden taxonomico a partir del perfil quimico

**Pregunta.** ¿El perfil composicional permite reconocer el orden taxonomico de una planta de un estudio no visto?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_ORDEN', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-084009_M04_orden_26c7871e` - estado **completado**, veredicto **senal debil**
- Resultado: balanced_accuracy = 0.253 frente a 0.116 del baseline y 0.189 del control solo-plataforma (ganancia sobre la mejor referencia +0.064); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.747: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Cada orden se representa por pocos articulos; los ordenes con un unico articulo se descartan.

## M05_familia - Familia botanica a partir del perfil quimico

**Pregunta.** ¿El perfil composicional permite reconocer la familia botanica de una planta de un estudio no visto?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_FAMILIA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-084620_M05_familia_27a28475` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.263 frente a 0.111 del baseline y 0.074 del control solo-plataforma (ganancia sobre la mejor referencia +0.151); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.737: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** La mayoria de las familias tiene uno o dos articulos, cada uno con su propia plataforma; un acierto puede reflejar el protocolo del estudio y no la quimica de la familia.

## M06_genero - Genero a partir del perfil quimico

**Pregunta.** ¿El perfil quimico identifica el genero en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_GENERO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-084644_M06_genero_d8f1dc95` - estado **completado**, veredicto **evidencia insuficiente**
- Resultado: balanced_accuracy = 0.495 frente a 0.333 del baseline y 0.167 del control solo-plataforma (ganancia sobre la mejor referencia +0.161); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.505: la evaluacion ingenua sobrestimaria el rendimiento. Solo 8.0 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

**Como interpretarlo.** Pocos generos aparecen en mas de un articulo (Camellia, Ipomoea, Morus); es esperable poca o ninguna senal evaluable.

## M07_especie - Especie a partir del perfil quimico

**Pregunta.** ¿El perfil quimico identifica la especie en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_ESPECIE', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-084710_M07_especie_3b75beb8` - estado **completado**, veredicto **evidencia insuficiente**
- Resultado: balanced_accuracy = 0.714 frente a 0.394 del baseline y 0.000 del control solo-plataforma (ganancia sobre la mejor referencia +0.320); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.286: la evaluacion ingenua sobrestimaria el rendimiento. Solo 4.0 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

**Como interpretarlo.** Casi cada especie aparece en un solo articulo, por lo que la prediccion entre articulos no es evaluable; dentro de un articulo la especie se confunde con el lote. Se espera 'no viable' o sin senal.

## M08_superclase_quimica - Superclase quimica a partir de la formula molecular

**Pregunta.** ¿La composicion elemental de un metabolito (solo su formula) permite asignar su superclase quimica, incluso para formulas no vistas?

**Diseno.** Unidad = metabolito identificado con formula interpretable y clase conocida. X = 24 descriptores elementales. Grupos = formula molecular (los isomeros nunca se reparten entre entrenamiento y prueba).

- Conjunto: `metabolito_quimica` con parametros `{'objetivo': 'ID_SUPERCLASE_QUIMICA'}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 5 grupos y >= 30 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-084722_M08_superclase_quimica_e65fb56d` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.537 frente a 0.078 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.459); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.561.

**Como interpretarlo.** La formula restringe la clase (p. ej. N para alcaloides, O/C alto para glicosidos), pero muchos isomeros pertenecen a clases distintas: hay un techo de rendimiento irreducible sin estructura.

## M09_clase_quimica - Clase quimica a partir de la formula molecular

**Pregunta.** ¿La formula molecular permite asignar la clase quimica (nivel fino de la ontologia) de un metabolito?

**Diseno.** Igual que M08 pero con las 40 clases quimicas mas frecuentes (>= 50 metabolitos y >= 5 formulas). Grupos = formula.

- Conjunto: `metabolito_quimica` con parametros `{'objetivo': 'ID_CLASE_QUIMICA'}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 5 grupos y >= 50 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-085306_M09_clase_quimica_433a0117` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.404 frente a 0.025 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.379); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.429.

**Como interpretarlo.** Problema mas dificil que M08 por el numero de clases y los isomeros; comparar con top3_accuracy.

## M10_aducto - Tipo de aducto a partir de la quimica del compuesto y el modo

**Pregunta.** ¿La formula, la superclase y el modo de ionizacion permiten anticipar que aducto se informara para un metabolito en un estudio no visto?

**Diseno.** Unidad = (articulo, metabolito, aducto) con aducto informado (15 aductos mas frecuentes entre articulos). X = descriptores de formula + modo + superclase. m/z excluida (m/z - masa = masa del aducto). Grupos = articulo. Control instrumental = solo el modo.

- Conjunto: `metabolito_aducto` con parametros `{'max_clases': 15, 'incluir_superclase': True}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 20 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-085949_M10_aducto_3e721902` - estado **completado**, veredicto **senal debil**
- Resultado: balanced_accuracy = 0.236 frente a 0.067 del baseline y 0.134 del control solo-plataforma (ganancia sobre la mejor referencia +0.102); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.329.

**Como interpretarlo.** El modo determina la polaridad del aducto ([M+H]+ vs [M-H]-); el valor de la quimica se mide como la mejora sobre el control que solo usa el modo.

## M11_columna_cromatografica - Columna cromatografica a partir del perfil quimico

**Pregunta.** ¿El perfil de metabolitos identificados delata la columna cromatografica usada (efecto de plataforma)?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_COLUMNA_CROMATOGRAFICA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-090851_M11_columna_cromatografica_b5aeecbc` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.401 frente a 0.200 del baseline y 0.096 del control solo-plataforma (ganancia sobre la mejor referencia +0.201); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.599: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Este modelo mide el efecto de plataforma: si la columna se predice bien, los perfiles reflejan el metodo analitico y no solo la planta.

## M12_tipo_muestra - Tipo de muestra a partir del perfil quimico

**Pregunta.** ¿El perfil composicional de metabolitos identificados (conteo por clase quimica, CLR) permite reconocer el tipo de muestra (tejido fresco, tejido seco, extractos...) en articulos no vistos durante el entrenamiento?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_TIPO_MUESTRA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-090917_M12_tipo_muestra_59b87e4f` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.327 frente a 0.333 del baseline y 0.287 del control solo-plataforma (ganancia sobre la mejor referencia -0.006); p de permutacion = 0.710; evaluacion sin agrupar = 0.998. Sin agrupar por ID_ARTICULO la metrica sube +0.671: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** El tipo de muestra esta casi completamente confundido con el articulo (cada estudio usa un unico tipo). Un rendimiento alto solo es creible si supera tanto al baseline como al control con variables de plataforma.

## M13_parte_planta - Parte de la planta a partir del perfil quimico

**Pregunta.** ¿El perfil quimico permite reconocer el organo analizado (hoja, raiz, fruto, flor...) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_PARTE_ESTUDIADA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-091230_M13_parte_planta_9fd561d1` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.141 frente a 0.111 del baseline y 0.086 del control solo-plataforma (ganancia sobre la mejor referencia +0.030); p de permutacion = 0.065; evaluacion sin agrupar = 0.886. Sin agrupar por ID_ARTICULO la metrica sube +0.744: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Comparar con M18 (varianza intra-articulo por parte) para separar quimica del organo y efecto del estudio.

## M14_tipo_cultivo - Tipo de cultivo a partir del perfil quimico

**Pregunta.** ¿El perfil quimico distingue el tipo de cultivo (silvestre, campo, invernadero, in vitro...) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_TIPO_CULTIVO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-091302_M14_tipo_cultivo_d2e28473` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.354 frente a 0.200 del baseline y 0.142 del control solo-plataforma (ganancia sobre la mejor referencia +0.154); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.961. Sin agrupar por ID_ARTICULO la metrica sube +0.608: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** El tipo de cultivo suele ser constante dentro de un estudio; la senal puede deberse al estudio.

## M15_metodo_extraccion - Metodo de extraccion a partir del perfil quimico

**Pregunta.** ¿El perfil quimico delata el metodo de extraccion (solvente) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_METODO_EXTRACCION', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-091924_M15_metodo_extraccion_7e92a798` - estado **completado**, veredicto **confundido con plataforma**
- Resultado: balanced_accuracy = 0.515 frente a 0.167 del baseline y 0.543 del control solo-plataforma (ganancia sobre la mejor referencia -0.028); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.485: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

**Como interpretarlo.** Metodos frecuentes (p. ej. metanol 70 %) dominan; muchos metodos aparecen en un solo articulo y se descartan.

## M16_metabolitos - Presencia de metabolitos frecuentes a partir de taxonomia y tipo de muestra

**Pregunta.** Dado el taxon (clase, orden, familia), la parte de la planta, el tipo de muestra, el cultivo y la extraccion, ¿que metabolitos frecuentes cabe esperar en una planta de un estudio no visto?

**Diseno.** Unidad = grupo de muestras (lote x especie x parte x tipo x cultivo x metodo). Y = presencia (0/1) de los 60 metabolitos presentes en mas articulos (>= 5). X = one-hot de taxonomia y atributos de muestra. Multietiqueta, grupos = articulo. Control = solo plataforma (columna, modos, profundidad de identificacion).

- Conjunto: `presencia_metabolitos` con parametros `{'min_articulos': 5, 'max_metabolitos': 60}`
- Modelos: baseline_prior, logistica, random_forest, knn
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-091946_M16_metabolitos_4306ef20` - estado **completado**, veredicto **confundido con plataforma**
- Resultado: average_precision_macro = 0.454 frente a 0.359 del baseline y 0.583 del control solo-plataforma (ganancia sobre la mejor referencia -0.129); p de permutacion = 0.258; evaluacion sin agrupar = 0.883. Sin agrupar por ID_ARTICULO la metrica sube +0.429: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

**Como interpretarlo.** La presencia depende de la biblioteca del laboratorio tanto como de la planta: si el control solo-plataforma iguala al modelo, lo que se predice es la cobertura de la biblioteca, no la quimica del taxon. La precision promedio debe compararse con la prevalencia de cada metabolito.

## M17_actividades_especie - Actividades biologicas de una especie a partir de su perfil quimico

**Pregunta.** ¿El perfil composicional de una especie (superclases quimicas) permite anticipar que actividades biologicas se le atribuyen?

**Diseno.** Unidad = especie x articulo con actividad registrada y perfil (>= 20 metabolitos). Y = actividades (multietiqueta) con >= 8 unidades positivas. X = CLR por superclase. Grupos = articulo.

- Conjunto: `actividad_especie` con parametros `{'nivel': 'superclase', 'min_positivos': 8}`
- Modelos: baseline_prior, logistica, random_forest, knn
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 50 permutaciones
- Ultima ejecucion: `20261022-092041_M17_actividades_especie_c5142b20` - estado **completado**, veredicto **confundido con plataforma**
- Resultado: average_precision_macro = 0.416 frente a 0.300 del baseline y 0.437 del control solo-plataforma (ganancia sobre la mejor referencia -0.022); p de permutacion = 0.020 (minimo alcanzable con 50 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.700. Sin agrupar por ID_ARTICULO la metrica sube +0.285: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

**Como interpretarlo.** Etiquetas positivas-no etiquetadas: una actividad ausente puede no haberse estudiado. Con ~60 unidades la incertidumbre es grande; solo una mejora clara sobre la prevalencia y p < 0.05 sugiere senal.

## M17b_actividades_metabolito - Actividades biologicas de un metabolito a partir de su formula y superclase

**Pregunta.** ¿La composicion elemental y la superclase de un metabolito con actividad citada permiten anticipar que tipo de actividad se le atribuye?

**Diseno.** Unidad = metabolito con actividad registrada en la literatura citada por los articulos. Y = actividades con >= 10 metabolitos. X = descriptores de formula + superclase. Grupos = formula.

- Conjunto: `actividad_metabolito` con parametros `{'min_positivos': 10}`
- Modelos: baseline_prior, logistica, random_forest, knn
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 50 permutaciones
- Ultima ejecucion: `20261022-092508_M17b_actividades_metabolito_0aedd318` - estado **completado**, veredicto **senal debil**
- Resultado: average_precision_macro = 0.436 frente a 0.292 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.144); p de permutacion = 0.039; evaluacion sin agrupar = 0.496.

**Como interpretarlo.** Muy pocos metabolitos (~90) y sesgo de publicacion: compuestos famosos acumulan muchas actividades citadas.

## M18_patrones_quimicos - Patrones quimicos: enriquecimiento, coocurrencia, reglas, agrupamiento y particion de varianza

**Pregunta.** ¿Que patrones quimicos (categorias enriquecidas por taxon u organo, categorias que coaparecen, reglas taxon -> quimica, grupos de especies con perfil similar, perfiles atipicos y asociaciones quimica-actividad) se sostienen cuando se controla que cada articulo aporta su propia plataforma y biblioteca de anotacion?

**Diseno.** Unidad = especie x articulo x parte de la planta (suma de muestras biologicas). Perfil = numero de metabolitos identificados por superclase (o clase) quimica, transformado con CLR. Contrastes Mann-Whitney con correccion BH, coocurrencias con Fisher exacto + BH, FP-growth, K-means con estabilidad bootstrap, PERMANOVA (R2 marginal con permutaciones; version intra-articulo centrando por estudio), Isolation Forest, enriquecimiento superclase-actividad y firma descriptiva de cada familia botanica con >= 2 articulos.

- Ultima ejecucion: `20261022-092519_M18_patrones_quimicos_2e13e5d1` - estado **completado**, veredicto **descriptivo**
- Resultado: Analisis no supervisado / de asociacion; ver hallazgos.
- Hallazgos:
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

**Como interpretarlo.** Un patron es candidato a hallazgo solo si (1) aparece en varios articulos independientes, (2) sobrevive a la correccion por comparaciones multiples y (3) no se explica mejor por columna/plataforma (comparar R2 de articulo y columna con el de orden/familia). Las coocurrencias pueden deberse a bibliotecas compartidas (p. ej. MRM de Metware). Las firmas por familia son descriptivas: cada familia tiene pocos estudios.
