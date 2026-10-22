#
# Archivo: interpretacion_graficos.py
# Autor: @Marcos Alejandro Collazos Marmolejo
#
# Junto a cada grafico PNG se escribe un <nombre>.txt que explica: para que
# sirve esa grafica, como se lee, y como saber si el resultado esta bien o mal.
#
from __future__ import annotations

from pathlib import Path

_SEP = "-" * 66

# nombre_de_grafico -> texto de ayuda (sin la seccion "TU CASO", que se agrega
# aparte con los valores reales del entrenamiento).
_AYUDA: dict[str, str] = {
    # ---------------- clasificacion ----------------
    "matriz_confusion": """MATRIZ DE CONFUSION (normalizada por fila)

QUE MUESTRA
  Cada fila es la clase real, cada columna la clase predicha. El numero de la
  celda (i, j) es la fraccion de muestras de la clase i que el modelo predijo
  como clase j. Los valores de cada fila suman 1.

COMO SE LEE
  - La diagonal (arriba-izq a abajo-der) = aciertos. Cuanto mas oscura, mejor.
  - Una celda oscura FUERA de la diagonal = el modelo confunde esas dos clases
    de forma sistematica (mira que tienen en comun).

ESTA BIEN SI
  - La diagonal esta claramente marcada y el resto casi vacio.

ESTA MAL SI
  - Hay columnas enteras oscuras: el modelo predice casi siempre esa clase
    (clase mayoritaria o colapso).
  - La diagonal es tenue y el color esta repartido: el modelo no aprendio.""",

    "metricas_por_clase": """METRICAS POR CLASE (precision, recall, F1)

QUE MUESTRA
  Para cada clase: precision (de lo que predije como esta clase, cuanto acerte),
  recall (de las muestras reales de esta clase, cuantas encontre) y F1 (media
  armonica de las dos). Con muchas clases se muestran solo las 25 con mas datos.

COMO SE LEE
  - Barras largas y parejas (las 3 juntas) = clase bien modelada.
  - Recall alto y precision baja = el modelo "sobre-predice" esa clase.
  - Precision alta y recall bajo = cuando la predice acierta, pero se le escapan
    muchas.

ESTA BIEN SI
  - La mayoria de las clases tiene F1 > 0.6 y no hay clases en 0.

ESTA MAL SI
  - Varias clases con las 3 metricas cerca de 0 (el modelo las ignora, casi
    siempre por falta de muestras de esa clase).""",

    "curva_roc": """CURVA ROC / AUC

QUE MUESTRA
  Que tan bien el modelo SEPARA las clases variando el umbral de decision.
  Eje X = falsos positivos, eje Y = verdaderos positivos. El AUC es el area bajo
  la curva (0.5 = azar, 1.0 = perfecto). En multiclase se dibuja una curva por
  clase (uno-vs-resto) mas el promedio.

COMO SE LEE
  - Curva pegada a la esquina superior izquierda = bueno.
  - Curva sobre la diagonal punteada = el modelo no distingue nada (azar).

ESTA BIEN SI
  - AUC (macro o micro) > 0.8.

ESTA MAL SI
  - AUC <= 0.6, o alguna clase con su curva por debajo de la diagonal.""",

    "curva_precision_recall": """CURVA PRECISION-RECALL / AP

QUE MUESTRA
  Como cambian precision y recall al mover el umbral de decision. Complementa
  a la ROC: con clases desbalanceadas (todos los objetivos de este proyecto lo
  estan) la ROC puede verse bien aunque el modelo acierte poco en la clase rara,
  mientras que precision-recall no se infla asi. AP = area bajo la curva.
  En multiclase se dibuja una curva por clase (uno-vs-resto) mas el promedio.

COMO SE LEE
  - Curva pegada a la esquina superior derecha = bueno.
  - La linea punteada "azar" es lo que daria un modelo que predijera al azar
    respetando la proporcion real de la clase positiva; por debajo de eso el
    modelo no aporta nada.

ESTA BIEN SI
  - AP claramente por encima de la prevalencia de la clase (la linea de azar).

ESTA MAL SI
  - La curva esta pegada a la linea de azar o por debajo: el modelo no separa
    mejor que adivinar segun que tan comun es la clase.""",

    "distribucion_clases": """DISTRIBUCION DE CLASES

QUE MUESTRA
  Cuantas muestras hay de cada clase en el conjunto evaluado.

COMO SE LEE
  - Barras muy desparejas = dataset desbalanceado.

ESTA BIEN SI
  - Las clases estan mas o menos parejas, o al menos ninguna con 1-2 muestras.

ESTA MAL SI
  - Hay clases con muy pocas muestras: no se pueden aprender ni validar bien
    (mira el aviso de validacion en el log). Ahi conviene juntar clases raras o
    conseguir mas datos.""",

    # ---------------- regresion ----------------
    "prediccion_vs_real": """PREDICCION vs. VALOR REAL

QUE MUESTRA
  Cada punto es una muestra: eje X su valor real, eje Y el que predijo el
  modelo. La linea punteada es el ideal (prediccion = real).

COMO SE LEE
  - Puntos pegados a la linea = buenas predicciones.
  - Puntos formando una nube horizontal = el modelo predice casi siempre lo
    mismo (no uso las features).
  - Curvatura sistematica respecto a la linea = falta un termino no lineal.

ESTA BIEN SI
  - Los puntos siguen la diagonal y R2 > 0.5.

ESTA MAL SI
  - R2 <= 0 (peor que predecir el promedio) o la nube no tiene relacion con la
    diagonal.""",

    "residuos_vs_prediccion": """RESIDUOS vs. PREDICCION

QUE MUESTRA
  El residuo (real - prediccion) contra el valor predicho. Deberia ser ruido
  centrado en 0 sin patron.

COMO SE LEE
  - Nube pareja alrededor de la linea 0 = bien.
  - Forma de embudo (residuos crecen con la prediccion) = varianza no constante,
    conviene modelar en log.
  - Curva o tendencia = el modelo tiene un sesgo sistematico.

ESTA BIEN SI
  - Puntos repartidos simetricamente arriba y abajo de 0, sin forma.

ESTA MAL SI
  - Patron claro (curva, embudo, escalon).""",

    "histograma_residuos": """HISTOGRAMA DE RESIDUOS

QUE MUESTRA
  La distribucion de los errores (real - prediccion). mu = media, sigma =
  desviacion.

COMO SE LEE
  - Campana centrada en 0 = errores sin sesgo.
  - Centrada lejos de 0 = el modelo sub- o sobre-estima en promedio.
  - Muy ancha = errores grandes.
  - Colas largas o segundo pico = hay un grupo de muestras que el modelo falla
    distinto (posible subpoblacion).

ESTA BIEN SI
  - mu cerca de 0 y la campana es angosta comparada con el rango de Y.

ESTA MAL SI
  - mu lejos de 0, o distribucion bimodal / muy sesgada.""",

    # ---------------- comun ----------------
    "distribucion_features": """DISTRIBUCION DE COLUMNAS (histograma + densidad)

QUE MUESTRA
  Como se distribuyen los valores de las features con mas varianza (las mas
  informativas de mirar; con muchas columnas no entrarian todas). Barras =
  histograma, linea = densidad estimada (KDE) de la misma columna.

COMO SE LEE
  - Campana simetrica = distribucion normal, sin sorpresas.
  - Cola larga hacia un lado = distribucion sesgada (comun en abundancias,
    conteos, tiempos): un modelo lineal/distancia puede necesitar transformarla
    (log, etc.) para rendir bien.
  - Varios picos separados (multimodal) = probablemente hay subgrupos distintos
    mezclados en esa columna.
  - Una sola barra dominante = columna casi constante, aporta poca informacion.

ESTA BIEN SI
  - Las formas son coherentes con lo que se espera del dato (una feature de
    conteo/abundancia sesgada a la derecha es normal, no un error).

ESTA MAL SI
  - Una columna que deberia variar aparece perfectamente constante (posible
    error de carga/ETL) o con valores extremos aislados muy lejos del resto
    (outliers que conviene revisar antes de confiar en el modelo).""",

    "importancia_features": """IMPORTANCIA DE LAS FEATURES (top 20)

QUE MUESTRA
  Que columnas (metabolitos / picos) pesan mas en las predicciones del modelo.
  El titulo dice de donde sale el numero: ganancia del arbol, magnitud del
  coeficiente, o permutacion.

COMO SE LEE
  - Barras que caen rapido = el modelo se apoya en pocas features (bien, es
    interpretable; ojo si son solo 1-2, puede ser fuga de datos).
  - Barras casi iguales = ninguna feature manda; el modelo reparte.

ESTA BIEN SI
  - Las features de arriba tienen sentido quimico/biologico para el objetivo.

ESTA MAL SI
  - Arriba aparece una feature "sospechosa" (un ID, un artefacto, algo que no
    deberia predecir la etiqueta) -> revisar el dataset.""",

    "curva_aprendizaje": """CURVA DE APRENDIZAJE

QUE MUESTRA
  El puntaje (accuracy o R2) de entrenamiento y de validacion a medida que
  crece la cantidad de filas usadas para entrenar (sobre una muestra chica del
  dataset, reentrenando el modelo varias veces -- es un diagnostico, no la
  metrica final que se reporta en la ficha).

COMO SE LEE
  - Las dos curvas convergen arriba = el modelo aprovecha bien los datos.
  - Mucha distancia entre las dos, entrenamiento muy por arriba de validacion =
    sobreajuste (el modelo memoriza); conviene mas regularizacion o menos
    complejidad.
  - Las dos curvas bajas y juntas, sin subir = el modelo no da para mas con
    estas features (mas datos no van a ayudar mucho); hace falta otra
    representacion o otro algoritmo.
  - La curva de validacion todavia sube al final = mas datos probablemente
    sigan ayudando.

ESTA BIEN SI
  - Ambas curvas suben y terminan cerca una de otra.

ESTA MAL SI
  - Separacion grande y estable entre las dos (sobreajuste), o ambas
    estancadas muy bajo (el modelo/las features no alcanzan).""",

    "ficha": """FICHA DEL ENTRENAMIENTO

QUE MUESTRA
  Resumen en texto: modelo, tarea, objetivo, tamano del dataset, tipo de
  validacion y las metricas finales. Es lo primero que hay que mirar.

COMO SE LEE
  - "Validacion: holdout ..." o "validacion cruzada ..." = las metricas son
    confiables.
  - "Validacion: sin validacion (metricas de entrenamiento)" = OJO, esas
    metricas son optimistas, hay muy pocos datos.""",

    # ---------------- no supervisado ----------------
    "proyeccion_2d": """PROYECCION PCA A 2D

QUE MUESTRA
  Las muestras aplastadas a 2 dimensiones (las 2 de mayor varianza), coloreadas
  por el grupo que asigno el modelo (o normal/anomalia).

COMO SE LEE
  - Colores que forman islas separadas = el modelo encontro estructura real.
  - Colores mezclados sin separacion = los grupos son arbitrarios (o la
    estructura no se ve en 2D, que tambien pasa).
  - "ruido" (gris) = muestras que DBSCAN no asigno a ningun cluster.

ESTA BIEN SI
  - Los grupos se ven como nubes distinguibles.

ESTA MAL SI
  - Un solo color se come casi todo, o los colores estan completamente
    entreverados.""",

    "tamano_clusters": """TAMANO DE CADA CLUSTER

QUE MUESTRA
  Cuantas muestras cayeron en cada grupo.

COMO SE LEE
  - Un cluster gigante + varios diminutos = el modelo no separo bien (o hay un
    grupo dominante real).
  - Barra "ruido" grande (DBSCAN) = el eps es muy chico.

ESTA BIEN SI
  - Los tamanos son razonables para lo que esperas del problema.

ESTA MAL SI
  - 1 cluster con casi todo, o muchos clusters con 1-2 muestras.""",

    "perfiles_quimicos_grupos": """FIRMAS QUIMICAS MEDIAS POR GRUPO

QUE MUESTRA
  La media Hellinger de las clases quimicas mas diferentes entre grupos.
  Cada fila es un cluster (o normal/anomalia) y cada columna una clase.

COMO SE LEE
  - Celdas claras: abundancia relativa transformada mas alta en el grupo.
  - Celdas oscuras: abundancia relativa transformada mas baja en el grupo.
  - Patrones de color distintos entre filas = los grupos tienen perfiles
    quimicos diferentes; columnas parecidas en todas las filas separan poco.
  - Si hay mas de 20 grupos, solo se dibujan los 20 mas numerosos.

ESTA BIEN SI
  - Se observan perfiles de abundancia distintos entre los grupos.

ESTA MAL SI
  - Todas las filas muestran el mismo patron: la asignacion no separa firmas
    quimicas claras.""",

    "varianza_explicada": """VARIANZA EXPLICADA (PCA)

QUE MUESTRA
  Cuanta informacion (varianza) conserva cada componente y el acumulado.

COMO SE LEE
  - La curva acumulada sube rapido y se aplana = pocas componentes bastan para
    resumir los datos.
  - Sube despacio y lineal = los datos no se dejan comprimir (mucha info
    repartida).

ESTA BIEN SI
  - Con 10 componentes ya tenes > 0.7-0.8 de varianza acumulada.

ESTA MAL SI
  - Con 10 componentes seguis por debajo de 0.4: PCA no ayuda mucho aca.""",

    "puntajes_anomalia": """PUNTAJES DE ANOMALIA

QUE MUESTRA
  El puntaje del modelo para cada muestra, separado en "normal" y "anomalia"
  segun el corte. El titulo dice el % marcado.

COMO SE LEE
  - Las dos distribuciones bien separadas = el modelo distingue claro lo raro.
  - Muy encimadas = el corte es casi arbitrario, las "anomalias" no son tan
    distintas.

ESTA BIEN SI
  - Se ve un grupito de muestras con puntaje muy distinto al resto.
  - El % marcado es chico (1-10%).

ESTA MAL SI
  - El % marcado es alto (>20%) o las dos distribuciones son la misma.""",

    "dispersion_componentes": """DISPERSION DE LAS 2 PRIMERAS COMPONENTES

QUE MUESTRA
  Las muestras proyectadas sobre las 2 primeras componentes/ejes que aprendio
  el metodo de reduccion.

COMO SE LEE
  - Si ves agrupamientos o gradientes = la reduccion capturo estructura.
  - Una bola sin forma = o no hay estructura, o hace falta mirar mas ejes.

ESTA BIEN SI
  - Aparece algun patron (grupos, ejes, curva).

ESTA MAL SI
  - Todo es una mancha uniforme y ademas la varianza explicada es baja.""",

    "matriz_transicion": """MATRIZ DE TRANSICION (Cadena de Markov)

QUE MUESTRA
  Cada fila es una clase quimica "actual" (el ultimo metabolito que eluyo),
  cada columna la clase "siguiente". El color de la celda (i, j) es la
  probabilidad de que, despues de ver la clase i, la proxima sea la clase j.
  No tiene etiquetas (son 300+ clases, no entrarian): sirve para ver el
  patron general -- cuan dispersa o concentrada es la matriz.

COMO SE LEE
  - Manchas oscuras sueltas = algunas clases predicen casi con certeza cual
    viene despues (ver transiciones_top para cuales son).
  - Todo parejo y tenue = las clases eluyen casi al azar una despues de otra.

ESTA BIEN SI
  - Hay estructura visible (no todo uniforme): el orden de elucion no es azar.

ESTA MAL SI
  - precision_siguiente_estado esta cerca de 1/n_estados (equivalente a
    adivinar al azar entre todas las clases).""",

    "transiciones_top": """TRANSICIONES MAS PROBABLES

QUE MUESTRA
  Las 15 transiciones clase_actual -> clase_siguiente con mayor probabilidad
  segun la cadena, sin contar A -> A (una clase seguida de si misma, que casi
  siempre es la mas alta por co-elucion y no es interesante repetir).

COMO SE LEE
  - Una barra alta = esa secuencia (una clase eluye justo despues de la otra)
    es consistente entre muestras, no casualidad de una corrida puntual.

ESTA BIEN SI
  - Las transiciones top tienen sentido quimico (familias biosinteticamente
    relacionadas que suelen coeluir o salir en secuencia).

ESTA MAL SI
  - Ninguna transicion supera demasiado al resto (P cercana a 1/n_estados):
    la cadena no encontro nada mas fuerte que el azar.""",

    "reglas_top": """TOP REGLAS DE ASOCIACION POR LIFT

QUE MUESTRA
  Las reglas "si aparece A entonces aparece B" con mayor LIFT. Lift = cuantas
  veces mas probable es B cuando esta A, comparado con B solo.

COMO SE LEE
  - Lift = 1: A y B son independientes (regla inutil).
  - Lift > 1: aparecen juntos mas de lo esperado (co-ocurrencia real).
  - Lift < 1: se excluyen.

ESTA BIEN SI
  - Hay reglas con lift claramente > 1 y confianza alta, y los metabolitos
    involucrados tienen relacion biosintetica esperable.

ESTA MAL SI
  - Todas las reglas con lift ~1, o 0 reglas (subi/baja el soporte minimo).""",
}


# Escribe <nombre>.txt junto al PNG. `valores` (opcional) es un dict
# metrica -> numero que se agrega como "TU CASO".
def escribir(destino: str | Path, nombre: str, valores: dict | None = None) -> None:
    ayuda = _AYUDA.get(nombre)
    if not ayuda:
        return
    partes = [ayuda]
    if valores:
        lineas = "\n".join(
            f"  {k} = {v:.4f}" if isinstance(v, float) else f"  {k} = {v}"
            for k, v in valores.items())
        partes.append(f"{_SEP}\nTU CASO\n{lineas}")
    (Path(destino) / f"{nombre}.txt").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
