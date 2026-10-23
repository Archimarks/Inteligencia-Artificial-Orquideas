# Limitaciones cientificas

Estas limitaciones condicionan la interpretacion de todos los resultados. Se derivan de la auditoria y de los
experimentos, no de supuestos.

## 1. Confusion articulo-especie-plataforma
- Cada articulo (52 con datos) estudia, en general, una especie, con una plataforma y una biblioteca de anotacion
  propias.
- Casi cada especie aparece en un solo articulo (71 especies con datos; solo 2 especies y 3 generos en >= 2
  articulos).
- No es posible separar "quimica de la especie" de "metodo del laboratorio" con estos datos. La prediccion de
  especie o genero entre articulos no es evaluable, y la de familia u orden descansa en muy pocos articulos por
  clase.
- La validacion no agrupada alcanza valores cercanos a 1 en casi todos los modelos de muestra. Esa cifra mide el
  reconocimiento del estudio y no debe reportarse como rendimiento.

## 2. Pocos articulos por familia
- La mayoria de las familias botanicas tiene uno o dos articulos. Por ejemplo, Orchidaceae esta representada por dos articulos: *Gastrodia elata* (articulo 24, Hypersil GOLD aQ) y *Dendrobium
  officinale* (articulo 39, Agilent SB-C18), con plataformas distintas.
- Cualquier "firma de familia" es descriptiva y debe confirmarse con mas especies analizadas con un mismo protocolo.

## 3. Intensidades no comparables
- ALTURA_PICO proviene de detectores, normalizaciones y escalas distintas (areas, alturas, intensidades
  normalizadas).
- Los modelos usan presencia y composicion, no abundancia.
- Las comparaciones cuantitativas entre muestras solo son validas dentro de un lote.

## 4. Bibliotecas de anotacion
- La presencia de un metabolito depende de que este en la biblioteca del laboratorio.
- Los estudios con MRM amplio (p. ej. Metware) comparten biblioteca y producen perfiles muy parecidos, lo que puede
  generar coocurrencias y agrupamientos artificiales. M18 usa un nulo que conserva la profundidad de anotacion, pero
  no puede eliminar el efecto de una biblioteca compartida.
- El 74 % de las observaciones biologicas no tienen metabolito identificado (nivel IV) y no entran en los perfiles.
- Los lotes sin identificaciones (BAT0004-0006, BAT0018) no aportan a los modelos de perfil.

## 5. Actividades biologicas
- 786 de 972 registros son actividades citadas en la literatura del articulo, no medidas en las muestras.
- Son etiquetas positivas sin negativos verificados (aprendizaje PU): la ausencia no implica inactividad.
- Los compuestos y especies muy estudiados acumulan mas citas (sesgo de publicacion).
- Las 174 medidas experimentales usan ensayos, unidades y escalas distintas, lo que impide una regresion de
  potencia.

## 6. Tamano efectivo de muestra
- Los modelos de muestra tienen cientos de muestras pero solo ~50 grupos independientes.
- Los intervalos de confianza reales son amplios. La desviacion estandar entre particiones de las tablas de
  metricas es una referencia minima.

## 7. Variables no modelables
- **Reino:** constante (Plantae).
- **Filo:** solo Magnoliophyta con >= 2 articulos.
- **Especie y genero entre articulos:** ver punto 1.
- **Identificacion de metabolitos desconocidos:** no hay espectros MS/MS.
- **Prediccion de RT entre lotes:** columnas y gradientes distintos.

## 8. Que haria falta
- Espectros MS/MS y RT estandarizados (indices de retencion).
- Mas especies por familia analizadas con un protocolo comun.
- Muestras puente compartidas entre laboratorios.
- Ensayos de actividad con controles negativos y valores homogeneos.
- El mapeo pozo-especie de BAT0005/BAT0006.
