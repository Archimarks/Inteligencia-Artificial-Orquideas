# M02_filo - Filo a partir del perfil quimico

- Ejecucion: `20261022-083940_M02_filo_95d4261c` (2026-10-22T08:39:40, 7.8 s)
- Configuracion: `M02_filo.yaml` (huella `95d4261c9086`), semilla 42
- Estado: **no_viable** - Veredicto: **no viable**

## Pregunta cientifica
¿El perfil quimico distingue angiospermas de gimnospermas y helechos?

## Diseno
Unidad = muestra biologica (sin QC ni blancos) con >= 20 metabolitos clasificados. X = CLR de los conteos de metabolitos por clase quimica (60 clases presentes en >= 5 articulos + 'otras'). Validacion agrupada por articulo (StratifiedGroupKFold, 5 particiones); solo clases presentes en >= 2 articulos. Pesos 1/n por articulo. Se compara con baselines, con un control que usa solo variables de plataforma (columna, modos, n de senales/identificados), con una validacion no agrupada (optimista) y con una prueba de permutacion.

## Unidad de analisis y precauciones
- Perfil = numero de metabolitos identificados por clase quimica (categorias presentes en >= 5 articulos + 'otras'), transformado con clr. Se excluyen muestras con < 20 metabolitos clasificados, QC, blancos y objetivo 'No especificado'.

## Datos evaluados
- Unidades: 909 de 942 (grupos: 48 de 50; columna de grupo `ID_ARTICULO`)
- Clases/etiquetas evaluables: 1 (descartadas: 2; ver `tablas/clases_descartadas.csv`)
- Variables predictoras: 61

## Resultado
No viable: Tras exigir >= 2 grupos y >= 10 unidades por clase quedan 1 clases y 48 grupos; no es posible una evaluacion agrupada honesta.

## Como interpretar
Solo Magnoliophyta tiene muestras en >= 2 articulos; se espera 'no viable'. El reino (Plantae) es constante y no se modela.

## Reproducibilidad
Manifiesto con huellas SHA-256 de los datos y versiones de librerias: `20261022-083940_M02_filo_95d4261c/manifiesto.json`. Reejecutar: `python main.py ejecutar M02_filo`.
