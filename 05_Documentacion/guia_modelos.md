# Guia de modelos

Generada por `python main.py resumen` a partir de `02_Script/config/modelos/*.yaml` y de la ultima ejecucion de cada experimento. Para cambiar un experimento edite su YAML (ver `02_Script/README.md`, seccion Configuracion) y reejecutelo con `python main.py ejecutar <ID>`.

## M01_modo_ionizacion - Modo de ionizacion (ESI+ / ESI-) a partir de la quimica del compuesto

**Pregunta.** ¿La composicion elemental y la superclase de un metabolito permiten anticipar si se detecta en ESI positivo o negativo, en articulos no vistos?

**Diseno.** Unidad = (articulo, metabolito) detectado en un solo modo, solo en articulos que adquirieron ambos modos. X = descriptores de la formula (C, H, N, O, P, S, DBE, H/C, O/C, indice de aromaticidad...) + superclase. Sin m/z, aducto ni RT (fuga). Grupos = articulo.

- Conjunto: `metabolito_modo` con parametros `{'incluir_superclase': True}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-122116_M01_modo_ionizacion_341e48ea` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.686 frente a 0.503 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.183); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.702.

**Como interpretarlo.** Los acidos (carboxilos, fenoles, fosfatos) tienden a ionizar en negativo y las bases nitrogenadas en positivo. Un rendimiento moderado es esperable: muchos compuestos ionizan en ambos modos y la eleccion depende del metodo.

## M02_filo - Filo a partir del perfil quimico

**Pregunta.** ¿El perfil quimico distingue angiospermas de gimnospermas y helechos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_FILO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-135252_M02_filo_53df305b` - estado **no_viable**, veredicto **no viable**
- Resultado: Tras exigir >= 2 grupos y >= 10 unidades por clase quedan 1 clases y 48 grupos; no es posible una evaluacion agrupada honesta.

**Como interpretarlo.** Solo Magnoliophyta tiene muestras en >= 2 articulos; se espera 'no viable'. El reino (Plantae) es constante y no se modela.

## M03_clase_taxonomica - Clase taxonomica a partir del perfil quimico

**Pregunta.** ¿El perfil quimico separa Magnoliopsida de Liliopsida (monocotiledoneas, incluidas las orquideas) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_CLASE_TAXONOMICA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-135253_M03_clase_taxonomica_37b8bb7d` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.486 frente a 0.521 del baseline y 0.389 del control solo-plataforma (ganancia sobre la mejor referencia -0.035); p de permutacion = 0.806; evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.514: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Liliopsida esta representada por pocos articulos; una prediccion correcta podria reflejar la plataforma de esos estudios.

## M04_orden - Orden taxonomico a partir del perfil quimico

**Pregunta.** ¿El perfil composicional permite reconocer el orden taxonomico de una planta de un estudio no visto?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_ORDEN', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-135501_M04_orden_cb32bf85` - estado **completado**, veredicto **senal debil**
- Resultado: balanced_accuracy = 0.253 frente a 0.116 del baseline y 0.189 del control solo-plataforma (ganancia sobre la mejor referencia +0.064); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.747: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Cada orden se representa por pocos articulos; los ordenes con un unico articulo se descartan.

## M05_familia - Familia botanica a partir del perfil quimico

**Pregunta.** ¿El perfil composicional permite reconocer la familia botanica (p. ej. Orchidaceae) de una planta de un estudio no visto?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_FAMILIA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-135823_M05_familia_7d7e0fbc` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.263 frente a 0.111 del baseline y 0.074 del control solo-plataforma (ganancia sobre la mejor referencia +0.151); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.737: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Orchidaceae tiene dos articulos (Gastrodia elata y Dendrobium officinale) con plataformas distintas.

## M06_genero - Genero a partir del perfil quimico

**Pregunta.** ¿El perfil quimico identifica el genero en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_GENERO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-135930_M06_genero_05674eb5` - estado **completado**, veredicto **evidencia insuficiente**
- Resultado: balanced_accuracy = 0.495 frente a 0.333 del baseline y 0.167 del control solo-plataforma (ganancia sobre la mejor referencia +0.161); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.505: la evaluacion ingenua sobrestimaria el rendimiento. Solo 8 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

**Como interpretarlo.** Pocos generos aparecen en mas de un articulo (Camellia, Ipomoea, Morus); es esperable poca o ninguna senal evaluable.

## M07_especie - Especie a partir del perfil quimico

**Pregunta.** ¿El perfil quimico identifica la especie en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_ESPECIE', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-140017_M07_especie_c206ea24` - estado **completado**, veredicto **evidencia insuficiente**
- Resultado: balanced_accuracy = 0.714 frente a 0.394 del baseline y 0.000 del control solo-plataforma (ganancia sobre la mejor referencia +0.320); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.286: la evaluacion ingenua sobrestimaria el rendimiento. Solo 4 grupos independientes (mediana 2.0 por clase): el resultado depende de muy pocos estudios y no permite conclusiones.

**Como interpretarlo.** Casi cada especie aparece en un solo articulo, por lo que la prediccion entre articulos no es evaluable; dentro de un articulo la especie se confunde con el lote. Se espera 'no viable' o sin senal.

## M08_superclase_quimica - Superclase quimica a partir de la formula molecular

**Pregunta.** ¿La composicion elemental de un metabolito (solo su formula) permite asignar su superclase quimica, incluso para formulas no vistas?

**Diseno.** Unidad = metabolito identificado con formula interpretable y clase conocida. X = 24 descriptores elementales. Grupos = formula molecular (los isomeros nunca se reparten entre entrenamiento y prueba).

- Conjunto: `metabolito_quimica` con parametros `{'objetivo': 'ID_SUPERCLASE_QUIMICA'}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 5 grupos y >= 30 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-122538_M08_superclase_quimica_b36a204e` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.575 frente a 0.078 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.497); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.589.

**Como interpretarlo.** La formula restringe la clase (p. ej. N para alcaloides, O/C alto para glicosidos), pero muchos isomeros pertenecen a clases distintas: hay un techo de rendimiento irreducible sin estructura.

## M09_clase_quimica - Clase quimica a partir de la formula molecular

**Pregunta.** ¿La formula molecular permite asignar la clase quimica (nivel fino de la ontologia) de un metabolito?

**Diseno.** Igual que M08 pero con las 40 clases quimicas mas frecuentes (>= 50 metabolitos y >= 5 formulas). Grupos = formula.

- Conjunto: `metabolito_quimica` con parametros `{'objetivo': 'ID_CLASE_QUIMICA'}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 5 grupos y >= 50 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-124343_M09_clase_quimica_30a1b4f5` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.426 frente a 0.025 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.401); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.447.

**Como interpretarlo.** Problema mas dificil que M08 por el numero de clases y los isomeros; comparar con top3_accuracy.

## M10_aducto - Tipo de aducto a partir de la quimica del compuesto y el modo

**Pregunta.** ¿La formula, la superclase y el modo de ionizacion permiten anticipar que aducto se informara para un metabolito en un estudio no visto?

**Diseno.** Unidad = (articulo, metabolito, aducto) con aducto informado (15 aductos mas frecuentes entre articulos). X = descriptores de formula + modo + superclase. m/z excluida (m/z - masa = masa del aducto). Grupos = articulo. Control instrumental = solo el modo.

- Conjunto: `metabolito_aducto` con parametros `{'max_clases': 15, 'incluir_superclase': True}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 20 unidades; 20 permutaciones
- Ultima ejecucion: `20261022-132211_M10_aducto_504ff3b8` - estado **completado**, veredicto **senal debil**
- Resultado: balanced_accuracy = 0.245 frente a 0.067 del baseline y 0.137 del control solo-plataforma (ganancia sobre la mejor referencia +0.108); p de permutacion = 0.048 (minimo alcanzable con 20 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.335.

**Como interpretarlo.** El modo determina la polaridad del aducto ([M+H]+ vs [M-H]-); el valor de la quimica se mide como la mejora sobre el control que solo usa el modo.

## M11_columna_cromatografica - Columna cromatografica a partir del perfil quimico

**Pregunta.** ¿El perfil de metabolitos identificados delata la columna cromatografica usada (efecto de plataforma)?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_COLUMNA_CROMATOGRAFICA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-140058_M11_columna_cromatografica_e9237dd2` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.510 frente a 0.200 del baseline y 0.136 del control solo-plataforma (ganancia sobre la mejor referencia +0.310); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.490: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Este modelo mide el efecto de plataforma: si la columna se predice bien, los perfiles reflejan el metodo analitico y no solo la planta.

## M12_tipo_muestra - Tipo de muestra a partir del perfil quimico

**Pregunta.** ¿El perfil composicional de metabolitos identificados (conteo por clase quimica, CLR) permite reconocer el tipo de muestra (tejido fresco, tejido seco, extractos...) en articulos no vistos durante el entrenamiento?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_TIPO_MUESTRA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-141555_M12_tipo_muestra_73ef39de` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.327 frente a 0.333 del baseline y 0.287 del control solo-plataforma (ganancia sobre la mejor referencia -0.006); p de permutacion = 0.710; evaluacion sin agrupar = 0.998. Sin agrupar por ID_ARTICULO la metrica sube +0.671: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** El tipo de muestra esta casi completamente confundido con el articulo (cada estudio usa un unico tipo). Un rendimiento alto solo es creible si supera tanto al baseline como al control con variables de plataforma.

## M13_parte_planta - Parte de la planta a partir del perfil quimico

**Pregunta.** ¿El perfil quimico permite reconocer el organo analizado (hoja, raiz, fruto, flor...) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_PARTE_ESTUDIADA', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-141838_M13_parte_planta_b6fb0605` - estado **completado**, veredicto **sin senal**
- Resultado: balanced_accuracy = 0.141 frente a 0.111 del baseline y 0.086 del control solo-plataforma (ganancia sobre la mejor referencia +0.030); p de permutacion = 0.065; evaluacion sin agrupar = 0.886. Sin agrupar por ID_ARTICULO la metrica sube +0.744: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** Comparar con M18 (varianza intra-articulo por parte) para separar quimica del organo y efecto del estudio.

## M14_tipo_cultivo - Tipo de cultivo a partir del perfil quimico

**Pregunta.** ¿El perfil quimico distingue el tipo de cultivo (silvestre, campo, invernadero, in vitro...) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_TIPO_CULTIVO', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-141957_M14_tipo_cultivo_8986cb39` - estado **completado**, veredicto **senal robusta**
- Resultado: balanced_accuracy = 0.354 frente a 0.200 del baseline y 0.142 del control solo-plataforma (ganancia sobre la mejor referencia +0.154); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.961. Sin agrupar por ID_ARTICULO la metrica sube +0.608: la evaluacion ingenua sobrestimaria el rendimiento.

**Como interpretarlo.** El tipo de cultivo suele ser constante dentro de un estudio; la senal puede deberse al estudio.

## M15_metodo_extraccion - Metodo de extraccion a partir del perfil quimico

**Pregunta.** ¿El perfil quimico delata el metodo de extraccion (solvente) en articulos no vistos?

**Diseno.** Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

- Conjunto: `perfil_muestra` con parametros `{'objetivo': 'ID_METODO_EXTRACCION', 'nivel': 'clase', 'transformacion': 'clr', 'min_metabolitos': 20, 'min_articulos_categoria': 5, 'max_categorias': 60}`
- Modelos: baseline_mayoritaria, baseline_estratificada, logistica, random_forest, lightgbm, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 2 grupos y >= 10 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-142305_M15_metodo_extraccion_bc93b9e3` - estado **completado**, veredicto **confundido con plataforma**
- Resultado: balanced_accuracy = 0.515 frente a 0.167 del baseline y 0.543 del control solo-plataforma (ganancia sobre la mejor referencia -0.028); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 1.000. Sin agrupar por ID_ARTICULO la metrica sube +0.485: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

**Como interpretarlo.** Metodos frecuentes (p. ej. metanol 70 %) dominan; muchos metodos aparecen en un solo articulo y se descartan.

## M16_metabolitos - Presencia de metabolitos frecuentes a partir de taxonomia y tipo de muestra

**Pregunta.** Dado el taxon (clase, orden, familia), la parte de la planta, el tipo de muestra, el cultivo y la extraccion, ¿que metabolitos frecuentes cabe esperar en una planta de un estudio no visto?

**Diseno.** Unidad = grupo de muestras (lote x especie x parte x tipo x cultivo x metodo). Y = presencia (0/1) de los 60 metabolitos presentes en mas articulos (>= 5). X = one-hot de taxonomia y atributos de muestra. Multietiqueta, grupos = articulo. Control = solo plataforma (columna, modos, profundidad de identificacion).

- Conjunto: `presencia_metabolitos` con parametros `{'min_articulos': 5, 'max_metabolitos': 60}`
- Modelos: baseline_prior, logistica, random_forest, knn, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 30 permutaciones
- Ultima ejecucion: `20261022-142403_M16_metabolitos_27840f44` - estado **completado**, veredicto **confundido con plataforma**
- Resultado: average_precision_macro = 0.499 frente a 0.364 del baseline y 0.591 del control solo-plataforma (ganancia sobre la mejor referencia -0.091); p de permutacion = 0.032 (minimo alcanzable con 30 permutaciones: ninguna permutacion igualo el valor observado); evaluacion sin agrupar = 0.881. Sin agrupar por ID_ARTICULO la metrica sube +0.382: la evaluacion ingenua sobrestimaria el rendimiento. El modelo con solo variables de plataforma rinde igual o mejor: no se puede atribuir la prediccion a la quimica.

**Como interpretarlo.** La presencia depende de la biblioteca del laboratorio tanto como de la planta: si el control solo-plataforma iguala al modelo, lo que se predice es la cobertura de la biblioteca, no la quimica del taxon. La precision promedio debe compararse con la prevalencia de cada metabolito.

## M17_actividades_especie - Actividades biologicas de una especie a partir de su perfil quimico

**Pregunta.** ¿El perfil composicional de una especie (superclases quimicas) permite anticipar que actividades biologicas se le atribuyen?

**Diseno.** Unidad = especie x articulo con actividad registrada y perfil (>= 20 metabolitos). Y = actividades (multietiqueta) con >= 8 unidades positivas. X = CLR por superclase. Grupos = articulo.

- Conjunto: `actividad_especie` con parametros `{'nivel': 'superclase', 'min_positivos': 8}`
- Modelos: baseline_prior, logistica, random_forest, knn, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 50 permutaciones
- Sin ejecuciones registradas.

**Como interpretarlo.** Etiquetas positivas-no etiquetadas: una actividad ausente puede no haberse estudiado. Con ~60 unidades la incertidumbre es grande; solo una mejora clara sobre la prevalencia y p < 0.05 sugiere senal.

## M17b_actividades_metabolito - Actividades biologicas de un metabolito a partir de su formula y superclase

**Pregunta.** ¿La composicion elemental y la superclase de un metabolito con actividad citada permiten anticipar que tipo de actividad se le atribuye?

**Diseno.** Unidad = metabolito con actividad registrada en la literatura citada por los articulos. Y = actividades con >= 10 metabolitos. X = descriptores de formula + superclase. Grupos = formula.

- Conjunto: `actividad_metabolito` con parametros `{'min_positivos': 10}`
- Modelos: baseline_prior, logistica, random_forest, knn, xgboost, catboost
- Validacion: group_kfold (5 particiones), clases con >= 3 grupos y >= 5 unidades; 50 permutaciones
- Ultima ejecucion: `20261022-134608_M17b_actividades_metabolito_e835e018` - estado **completado**, veredicto **senal debil**
- Resultado: average_precision_macro = 0.436 frente a 0.292 del baseline y nan del control solo-plataforma (ganancia sobre la mejor referencia +0.144); p de permutacion = 0.039; evaluacion sin agrupar = 0.499.

**Como interpretarlo.** Muy pocos metabolitos (~90) y sesgo de publicacion: compuestos famosos acumulan muchas actividades citadas.

## M18_patrones_quimicos - Patrones quimicos: enriquecimiento, coocurrencia, reglas, agrupamiento y particion de varianza

**Pregunta.** ¿Que patrones quimicos (categorias enriquecidas por taxon u organo, categorias que coaparecen, reglas taxon -> quimica, grupos de especies con perfil similar, perfiles atipicos y asociaciones quimica-actividad) se sostienen cuando se controla que cada articulo aporta su propia plataforma y biblioteca de anotacion?

**Diseno.** Unidad = especie x articulo x parte de la planta (suma de muestras biologicas). Perfil = numero de metabolitos identificados por superclase (o clase) quimica, transformado con CLR. Contrastes Mann-Whitney con correccion BH, coocurrencias con Fisher exacto + BH, FP-growth, K-means con estabilidad bootstrap, PERMANOVA (R2 marginal con permutaciones; version intra-articulo centrando por estudio), Isolation Forest, enriquecimiento superclase-actividad y firma descriptiva de Orchidaceae.

- Sin ejecuciones registradas.

**Como interpretarlo.** Un patron es candidato a hallazgo solo si (1) aparece en varios articulos independientes, (2) sobrevive a la correccion por comparaciones multiples y (3) no se explica mejor por columna/plataforma (comparar R2 de articulo y columna con el de orden/familia). Las coocurrencias pueden deberse a bibliotecas compartidas (p. ej. MRM de Metware). La firma de orquideas es descriptiva: solo hay dos estudios de Orchidaceae.
