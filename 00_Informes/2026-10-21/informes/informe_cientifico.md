# Informe cientifico: patrones quimicos en orquideas y plantas medicinales

Ejecuciones del 2026-10-22, semilla 42. Todas las cifras provienen de `04_Resultados/ejecuciones/*/resultado.json`;
la tabla completa esta en `04_Resultados/informes/resumen_ejecutivo.md`. La validacion se agrupa por articulo, o
por formula molecular en los modelos de compuesto. **Ganancia** = valor del modelo menos la mejor referencia que no
usa quimica: max(baseline, control solo-plataforma).

## 1. Datos
- 52 articulos, 57 lotes y 1 773 muestras (1 478 biologicas).
- 5 798 278 observaciones quimicas sin replicacion, de las cuales 25.6 % tienen un metabolito identificado (MSI I-III).
- 45 842 metabolitos distintos, 71 especies y 972 registros de actividad, de los cuales 81 % son literatura citada.
- Integridad: 0 claves foraneas huerfanas y jerarquia taxonomica coherente (ver `auditoria_datos/oficial`).

## 2. Resumen de resultados

| Experimento | Metrica | Modelo | Baseline | Control plataforma | Sin agrupar | p | Veredicto |
|---|---|---|---|---|---|---|---|
| M01 Modo ESI+/ESI- | exactitud balanceada | 0.686 | 0.503 | - | 0.702 | 0.048* | senal robusta |
| M02 Filo | - | - | - | - | - | - | no viable (1 filo con >= 2 articulos) |
| M03 Clase taxonomica | exactitud balanceada | 0.486 | 0.521 | 0.389 | 1.000 | 0.81 | sin senal |
| M04 Orden (9 clases) | exactitud balanceada | 0.253 | 0.116 | 0.189 | 1.000 | 0.032* | senal debil |
| M05 Familia (9 clases) | exactitud balanceada | 0.263 | 0.111 | 0.074 | 1.000 | 0.032* | senal robusta (ver 3.2) |
| M06 Genero (3 clases) | exactitud balanceada | 0.495 | 0.333 | 0.167 | 1.000 | 0.032* | evidencia insuficiente (8 articulos) |
| M07 Especie (2 clases) | exactitud balanceada | 0.714 | 0.394 | 0.000 | 1.000 | 0.032* | evidencia insuficiente (4 articulos) |
| M08 Superclase desde formula (13) | exactitud balanceada | 0.537 | 0.078 | - | 0.561 | 0.048* | senal robusta |
| M09 Clase desde formula (40) | exactitud balanceada | 0.404 | 0.025 | - | 0.429 | 0.048* | senal robusta |
| M10 Aducto (15) | exactitud balanceada | 0.236 | 0.067 | 0.134 | 0.329 | 0.048* | senal debil |
| M11 Columna cromatografica (5) | exactitud balanceada | 0.401 | 0.200 | 0.096 | 1.000 | 0.032* | senal robusta (efecto de plataforma) |
| M12 Tipo de muestra (3) | exactitud balanceada | 0.327 | 0.333 | 0.287 | 0.998 | 0.71 | sin senal |
| M13 Parte de la planta (9) | exactitud balanceada | 0.141 | 0.111 | 0.086 | 0.886 | 0.065 | sin senal |
| M14 Tipo de cultivo (5) | exactitud balanceada | 0.354 | 0.200 | 0.142 | 0.961 | 0.032* | senal robusta (ver 3.2) |
| M15 Metodo de extraccion (6) | exactitud balanceada | 0.515 | 0.167 | 0.543 | 1.000 | 0.032 | confundido con plataforma |
| M16 Presencia de 60 metabolitos | AP macro | 0.454 | 0.359 | 0.583 | 0.883 | 0.26 | confundido con plataforma |
| M17 Actividades de la especie (16) | AP macro | 0.416 | 0.300 | 0.437 | 0.700 | 0.020 | confundido con plataforma |
| M17b Actividades del metabolito (6) | AP macro | 0.436 | 0.292 | - | 0.496 | 0.039 | senal debil |
| M18 Patrones quimicos | - | - | - | - | - | - | descriptivo (seccion 4) |

\* p minimo alcanzable con el numero de permutaciones usado (20 o 30): ninguna permutacion igualo el valor observado.

## 3. Interpretacion

### 3.1 La quimica del compuesto si es aprendible
- **Superclase y clase desde la formula (M08, M09).** Usando solo la composicion elemental, la superclase se asigna
  con exactitud balanceada 0.54 entre 13 clases (azar 0.08) y la clase con 0.40 entre 40 (azar 0.025). La
  evaluacion es sobre formulas nunca vistas.
  - Variables dominantes: O/C, numero de heteroatomos, DBE/C y H/C, coherentes con el diagrama de Van Krevelen.
  - La diferencia agrupada vs no agrupada es pequena (0.54 vs 0.56): el modelo no memoriza formulas.
  - El techo se debe a los isomeros: una misma formula pertenece a clases distintas.
- **Modo de ionizacion (M01).** La formula anticipa si un compuesto se informa en ESI+ o ESI- (0.69 frente a 0.50),
  y O/C es la variable principal. Es coherente con la quimica: los compuestos oxigenados acidos ionizan en
  negativo.
- **Aducto (M10).** La quimica mejora en 0.10 al modelo que solo conoce el modo (0.24 vs 0.13). Senal real pero
  modesta: la eleccion del aducto depende sobre todo del software de cada laboratorio.
- **Actividad de un metabolito (M17b).** Hay senal debil (AP 0.44 vs 0.29 de prevalencia, p = 0.039), concentrada
  en "antimicrobiano" (ROC-AUC 0.79) y "antioxidante" (AP 0.74 con prevalencia 0.66). Son solo 93 metabolitos con
  sesgo de publicacion: es una hipotesis, no un predictor.

### 3.2 El perfil de una planta refleja sobre todo el estudio
- **El efecto de estudio es dominante.** La validacion no agrupada da cerca de 1.0 en casi todos los modelos de
  muestra (M03-M07, M11, M12, M14, M15). Con validacion agrupada, el rendimiento cae a 0.14-0.40. Cualquier cifra
  de "exactitud" publicada sobre estos datos sin agrupar por articulo mide el reconocimiento del estudio.
- **Familia (M05).** Supera al baseline y al control, pero el acierto procede casi por completo de una familia:
  Rubiaceae (recall 0.89, 3 articulos). Lamiaceae y Rosaceae se aciertan parcialmente y las otras seis familias,
  incluida **Orchidaceae (recall 0)**, no se reconocen en articulos no vistos. No hay evidencia de una firma
  quimica de familia transferible entre laboratorios, salvo quiza Rubiaceae.
- **Orden (M04).** Ganancia de solo 0.06 sobre el control de plataforma: senal debil.
- **Clase taxonomica (M03).** Ningun modelo separa Liliopsida (monocotiledoneas, incluidas las orquideas) de
  Magnoliopsida.
- **Columna (M11).** Se predice desde el perfil (0.40 vs 0.20). Es una medida directa del efecto de plataforma: el
  perfil de metabolitos identificados delata el metodo analitico.
- **Tipo de cultivo (M14).** Supera a las referencias (0.35 vs 0.20). El cultivo es casi constante dentro de cada
  articulo, por lo que puede reflejar otros rasgos del estudio; se considera hipotesis.
- **Sin senal.** Parte de la planta (M13), tipo de muestra (M12) y clase taxonomica (M03) no superan a las
  referencias.
- **Confundidos con plataforma.** En el metodo de extraccion (M15), la presencia de metabolitos (M16) y las
  actividades de especie (M17), el control con solo plataforma rinde igual o mejor que el modelo quimico. En M16 la
  presencia de un metabolito se predice mejor con la plataforma (AP 0.58) que con la taxonomia (0.45): lo que se
  detecta depende de la biblioteca del laboratorio.

## 4. Patrones quimicos (M18)

Unidad: especie x articulo x parte (111 unidades, 51 articulos).
- **Particion de varianza.**
  - El articulo explica practicamente toda la variacion del perfil (R2 ajustado 0.99).
  - Familia: R2 0.79 frente a un nulo de 0.67 al permutar articulos completos (p = 0.026). Es la unica senal
    taxonomica significativa.
  - Orden, columna y metodo no superan su nulo.
  - Dentro de un mismo articulo, la parte de la planta, el cultivo y la especie explican <= 2 % de la variacion, sin
    significancia.
- **Enriquecimiento.**
  - Con el articulo como unidad de contraste y correccion BH, solo 2 de 660 contrastes son significativos, ambos en
    categorias minoritarias de Rosaceae.
  - Los "enriquecimientos" aparentes por orden o familia que aparecen si se cuentan las muestras como independientes
    desaparecen cuando el articulo es la unidad de contraste.
- **Coocurrencia.**
  - Con un nulo que conserva la riqueza de cada unidad, 160 de 1 770 pares de clases coaparecen mas de lo esperado
    (con Fisher sin controlar la riqueza casi todos los pares resultan significativos, porque los laboratorios con
    bibliotecas grandes detectan todas las clases a la vez).
  - Los mas fuertes son quimicamente coherentes: acidos organicos + acilos grasos (z = 6.1), glicerofosfolipidos +
    esteroides (5.4), flavonas + flavanonas (5.2), glicerofosfolipidos + acidos grasos (5.1).
  - Esto apunta a modulos biosinteticos (lipidos de membrana; ruta de flavonoides), aunque las bibliotecas
    compartidas pueden contribuir.
- **Reglas taxon -> quimica** (sostenidas por >= 2 articulos):
  - Moraceae -> fenilpropanoides C6-C3 (lift 4.8, 2 articulos);
  - Lamiaceae -> aminas y alcaloides de triptofano (3 articulos);
  - Solanaceae -> aminas (lift 4.6, 4 articulos), coherente con la quimica nitrogenada conocida de las solanaceas.
- **Agrupamiento.** Tres grupos estables (silueta 0.50, ARI bootstrap 0.81) con concordancia baja y similar con
  orden (AMI 0.13), columna (0.12) y articulo (0.16): los grupos no son taxonomicos.
- **Quimica-actividad.** Ninguna superclase esta enriquecida en una actividad tras BH.
- **Orquideas.** Dos estudios: *Gastrodia elata* y *Dendrobium officinale*.
  - 73 metabolitos aparecen en ambos.
  - 5 de ellos estan en <= 10 % de los otros 49 articulos: dihidroresveratrol, isorhapontigenina, pterostilbeno
    (estilbenos), equol y grosamida.
  - Composicion relativa: algo menos fenilpropanoides/policetidos (-8 puntos) y algo mas lipidos, acidos organicos
    y bencenoides.
  - Son **candidatos descriptivos**: con dos estudios y plataformas distintas no puede separarse la planta del
    metodo.

## 5. Conclusiones
1. **Lo que funciona.** Los modelos centrados en el compuesto (formula -> superclase, clase, modo, aducto) aprenden
   relaciones quimicas reales y generalizan a formulas y articulos no vistos. Son las herramientas mas utiles de
   este sistema, por ejemplo para anotar la clase de formulas sin clasificar o anticipar el modo de deteccion.
2. **Lo que no se puede afirmar.** Con estos datos no puede afirmarse que el perfil quimico identifique la
   taxonomia, el organo o el tipo de muestra entre estudios. La variacion esta dominada por el estudio y su
   plataforma. La unica senal taxonomica consistente es a nivel de familia, concentrada en Rubiaceae.
3. **Patrones con respaldo.** Los patrones quimicos con respaldo independiente del estudio son coocurrencias de
   clases biosinteticamente relacionadas y unas pocas reglas taxon -> quimica (Solanaceae y Lamiaceae -> aminas;
   Moraceae -> fenilpropanoides).
4. **Orquideas.** No se distinguen quimicamente en validacion entre estudios (recall 0 en M05). Los estilbenos
   compartidos por *Gastrodia* y *Dendrobium* son la pista mas especifica y deben verificarse con un protocolo
   comun.
5. **Para avanzar** (ver `limitaciones_cientificas.md`): mas especies de Orchidaceae medidas con el mismo metodo,
   muestras puente entre laboratorios, espectros MS/MS y ensayos de actividad con controles negativos.
