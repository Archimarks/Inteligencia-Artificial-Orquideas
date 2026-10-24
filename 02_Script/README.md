# 02_Script - Sistema de IA para el descubrimiento de patrones quimicos

Sistema modular y reproducible que audita `01_Datos/Dataset` y entrena y evalua 18 experimentos de aprendizaje
supervisado y no supervisado. Todo resultado lleva su configuracion, sus huellas de datos y su informe.

## 1. Instalacion

Requisitos: Python 3.11-3.14 (probado con 3.13; ruedas verificadas para 3.14 en Windows) y unos 4 GB de RAM libres. Opcional: GPU NVIDIA con el controlador
instalado (XGBoost 2.1.4 admite GPU desde compute capability 6.0, p. ej. GTX 10xx).

**Windows (PowerShell), con el mismo Python con el que ejecutara main.py:**
```powershell
cd "D:\Inteligencia Artificial \02_Script"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py               # abre la interfaz
```
Si usa el boton "Ejecutar" de VS Code, instale las librerias con ese mismo interprete, por ejemplo
`& C:/Users/<usuario>/AppData/Local/Python/pythoncore-3.14-64/python.exe -m pip install -r requirements.txt`.
`main.py` comprueba al arrancar que esten todas las librerias; si falta alguna, muestra el comando exacto y
ofrece instalarlas.

Opcional (entorno virtual):
```powershell
cd "D:\Inteligencia Artificial "
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r 02_Script\requirements.txt
```

**Linux / macOS:**
```bash
cd "Inteligencia Artificial /02_Script"
python3 -m pip install -r requirements.txt
python3 main.py
```

Las rutas se resuelven solas a partir de la carpeta padre de `02_Script` (`raiz_proyecto: auto` en
`config/rutas.yaml`). Para fijarlas a mano: `raiz_proyecto: "D:/Inteligencia Artificial "`.

## 2. Interfaz (recomendada)

`python main.py` sin argumentos (o el boton Ejecutar de VS Code) abre la interfaz de consola:

1. **Entrenar modelos.** Es un asistente paso a paso:
   1. *Maquina:* muestra CPU, RAM, sistema y todas las GPU NVIDIA, y prueba cada una con un entrenamiento corto en
      CUDA (OK/FALLO). Despues se elige con que entrenar: todas las GPU que pasaron la prueba (recomendado),
      algunas, o solo CPU.
   2. *Datos:* comprueba que los CSV de `01_Datos/Dataset` existan y no sean punteros de Git LFS.
   3. *Modelos:* tabla de los 19 experimentos por categoria, con su ultimo resultado. Se eligen por numero
      (`1,3`), rango (`2-7`), categoria (`A B`), ID (`M05`) o `todos`.
   4. *Opciones:*
      - modo **completo** (con permutaciones y validacion sin agrupar) o **rapido** (para probar el flujo);
      - algoritmos a entrenar; los baselines siempre se entrenan.
   5. *Resumen y confirmacion;* luego el entrenamiento, con el progreso y el tiempo restante estimado, una linea
      de resultado por modelo y la tabla final. Al terminar se actualizan el resumen ejecutivo y la guia de modelos.
      Ctrl+C detiene la cola y conserva los modelos terminados.
2. **Ver resultados:** ultima ejecucion de cada modelo con su veredicto; puede abrir la carpeta de un modelo.
3. **Auditoria de datos.**
4. **Revisar el equipo.**
5. **Validar configuraciones.**

## 2.1 Comandos

Los mismos procesos sin interfaz (por ejemplo, para scripts), desde `02_Script`:

| Comando | Que hace |
|---|---|
| `python main.py auditoria [--etiqueta X]` | Auditoria general -> `03_Resultados/Global/auditoria_datos/<X>/informe_auditoria.md` |
| `python main.py hardware` | Muestra los nucleos CPU, todas las GPU NVIDIA detectadas y las que se usaran |
| `python main.py listar` | Lista los experimentos configurados |
| `python main.py validar [ID ...]` | Valida los YAML sin ejecutar (codigo de salida 1 si hay errores) |
| `python main.py datos [ID ...] [--variables]` | Archivos y columnas que usa cada experimento para entrenar; con `--variables` construye el conjunto y lista las variables finales de entrada |
| `python main.py ejecutar M05 [M13 ...] [--etiqueta X]` | Ejecuta experimentos (acepta `M05` o `M05_familia`) |
| `python main.py ejecutar-todos` | Ejecuta todos y genera el resumen (unas 2-3 h con 4 nucleos, sobre todo por las permutaciones) |
| `python main.py resumen` | Escribe `03_Resultados/Global/resumen_ejecutivo.md`, la grafica comparativa global y `05_Documentacion/guia_modelos.md` |
| `python main.py reinformar` | Regenera los informes de todas las ejecuciones sin reentrenar |
| `python main.py predecir RUN_ID datos.csv` | Aplica un modelo guardado a un CSV con las mismas columnas que X |

La primera lectura de Dataset.csv (~550 MB) tarda alrededor de 1 minuto y crea una cache Parquet en
`03_Resultados/_cache`; las siguientes tardan segundos.

## 3. Salidas: `03_Resultados`

`run_id = AAAAMMDD-HHMMSS_<ID>_<huella de la config>[_etiqueta]`. Nunca se sobrescribe una ejecucion previa.

```
03_Resultados/
├── Global/
│   ├── auditoria_datos/<run>/          auditoria general de 01_Datos/Dataset (informe_auditoria.md, tablas, graficas)
│   ├── resumen_ejecutivo.md / .csv     ultima ejecucion de cada modelo con su veredicto
│   ├── informe_cientifico.md
│   └── graficas/comparacion_global_modelos.png
└── Models/
    ├── M01_Modo_Ionizacion/
    │   ├── auditoria_datos/<run_id>/   datos del modelo: unidades, grupos, clases evaluables y descartadas,
    │   │                               descripcion de variables, unidades por grupo (auditoria_datos.md)
    │   ├── ejecuciones/<run_id>/       config_resuelta.yaml, manifiesto.json (huellas, versiones, CPU/GPU, commit),
    │   │                               resultado.json, informe.md, ejecucion.log,
    │   │                               datos_entrenamiento.md/.json (archivos, columnas y variables usadas)
    │   ├── metricas/<run_id>/          metricas por modelo y particion (con la GPU usada), por clase, importancias,
    │   │                               permutaciones
    │   ├── graficas/<run_id>/          graficas con titulo, ejes, leyenda y nota interpretativa
    │   ├── predicciones/<run_id>/      predicciones fuera de particion con identificadores
    │   ├── informes/                   INFORME.md (ultima ejecucion) + informe_<run_id>.md de cada ejecucion
    │   └── modelo_entrenado/<run_id>/  modelo.joblib (pipeline final, columnas, clases, codificador)
    ├── M03_Clase_Taxonomica/  (misma estructura)
    └── ...
```

## 3.1 GPU

El sistema detecta todas las GPU NVIDIA con `nvidia-smi` (incluido en el controlador) y las usa segun
`hardware` en `config/config_global.yaml`. Por defecto (`usar_gpu: auto`, `gpus: todas`) usa todas las GPU
detectadas:
- **XGBoost:** cada modelo usa una GPU, y las particiones de la validacion cruzada y de las permutaciones se reparten
  entre todas las GPU y se entrenan en paralelo. Con dos GPU, dos particiones a la vez.
- **CatBoost:** cada modelo se entrena con todas las GPU a la vez (`devices="0:1"`).
- **LightGBM, Random Forest, regresion logistica y KNN:** CPU con todos los nucleos. LightGBM de pip es solo CPU.

Sin GPU, el mismo codigo entrena en CPU. Con `usar_gpu: si`, el sistema se detiene si no hay GPU, y `gpus: [0]`
limita las GPU usadas. `CUDA_VISIBLE_DEVICES` se respeta. Compruebe la deteccion con `python main.py hardware`.
Cada `manifiesto.json` registra las GPU detectadas y usadas, y `metricas_por_particion.csv` la GPU de cada
particion.

## 4. Configuracion

### 4.1 `config/config_global.yaml`
- `semilla`, `n_jobs`.
- `datos.niveles_identificados`: niveles MSI que cuentan como metabolito identificado; por defecto `[1, 2, 3]`.
- `datos.tipos_muestra_excluidos`: QC y blancos, `[9, 10]`.
- `defaults`: valores que hereda cada experimento si no los redefine:
  - `split`: `strategy`, `n_splits`, `min_groups_per_class`, `min_samples_per_class`;
  - `evaluation`: `permutation_test`, `n_permutations`, `confounding_control`, `evaluacion_optimista`;
  - `outputs`: `save_model`, `save_predictions`, `save_plots`, `overwrite`.

### 4.2 Un experimento (`config/modelos/<ID>.yaml`)
```yaml
id: M05_familia                 # debe coincidir con el nombre del archivo
nombre: "Familia botanica a partir del perfil quimico"
tarea: supervisado              # supervisado | patrones
pregunta_cientifica: "..."      # obligatoria; aparece en el informe
descripcion: "..."
conjunto:
  nombre: perfil_muestra        # metabolito_quimica | metabolito_modo | metabolito_aducto | actividad_metabolito |
                                # perfil_muestra | presencia_metabolitos | actividad_especie
  parametros:
    objetivo: ID_FAMILIA        # cualquier atributo de muestra: ID_FILO..ID_ESPECIE, ID_PARTE_ESTUDIADA, ...
    nivel: clase                # superclase | clase
    transformacion: clr         # clr | fraccion | conteo
    min_metabolitos: 20
    min_articulos_categoria: 5
    max_categorias: 60
    agregar_por: null           # p. ej. [ID_ARTICULO, ID_ESPECIE] para agregar muestras
    ponderar_por_grupo: true
split:                          # sobreescribe defaults
  n_splits: 5
  min_groups_per_class: 2       # >= 2 obligatorio
  min_samples_per_class: 10
max_clases: null                # limita a las N clases mas frecuentes
seleccion_variables: {metodo: ninguna}    # ninguna | anova | informacion_mutua (con k)
modelos:                        # al menos un baseline y un modelo real
  - nombre: baseline_mayoritaria
  - nombre: logistica
    hiperparametros: {C: 0.5}
  - nombre: random_forest
  - nombre: lightgbm
evaluation:
  n_permutations: 30
variables_prohibidas: []        # prefijos adicionales a excluir de X
interpretacion: "..."
datos_entrenamiento:            # archivos y columnas usados para entrenar (ver 4.2.1)
  archivos:
    dataset: Dataset.csv
  variables:
    incluir: []
    excluir: []
```

#### 4.2.1 Archivos y columnas de entrenamiento (`datos_entrenamiento`)
Cada YAML de `config/modelos` indica que archivos lee el experimento y, en comentarios debajo de cada archivo, que
columnas toma de el y para que (variables de entrada, objetivo, grupos de validacion, control instrumental, filtros).
- `archivos`: nombre logico -> ruta. Las rutas relativas se resuelven contra `datos.catalogos` de `config/rutas.yaml`;
  tambien se admiten rutas absolutas. Nombres validos: `dataset` y los catalogos (`metabolitos`, `clases_quim`,
  `registro_actividades`, `familias`, ...). Cambiar una ruta hace que ese experimento lea otro archivo; antes de
  entrenar se comprueba que exista y que tenga las columnas que necesita.
- `variables.incluir` / `variables.excluir`: seleccionan las variables de entrada (X) ya construidas. Vacio = todas.
  Admiten comodines (`*`, `?`) y se comparan con el nombre de la variable (`ID_FAMILIA_6`, `clase_240`, `dbe`) y con la
  columna de origen (`ID_SUPERCLASE_QUIMICA`, `FORMULA_MOLECULAR`). Ejemplo: `excluir: [ID_SUPERCLASE_QUIMICA]` en M10
  entrena con la formula y el modo de ionizacion, sin la superclase.

Al entrenar, la consola y `ejecucion.log` muestran los archivos, las columnas y la lista de variables; se guardan en
`ejecuciones/<run_id>/datos_entrenamiento.md` y `.json`, y el informe incluye la seccion "Archivos y columnas de
entrenamiento". `python main.py datos M05` lo muestra sin entrenar.

Modelos disponibles: `baseline_mayoritaria`, `baseline_prior`, `baseline_estratificada`, `logistica`,
`random_forest`, `extra_trees`, `hist_gradient_boosting`, `lightgbm`, `xgboost` (GPU), `catboost` (GPU), `knn`. Los hiperparametros se pasan tal cual
al estimador de scikit-learn o LightGBM.

### 4.3 Validacion automatica
`python main.py validar` comprueba:
- claves obligatorias y que el `id` coincida con el archivo;
- que existan la tarea, el conjunto y los modelos;
- que haya al menos un baseline;
- que la estrategia de particion sea agrupada (`stratified_kfold` se rechaza por fuga);
- que `n_splits` y `min_groups_per_class` sean >= 2, y que el metodo de seleccion sea valido.

En ejecucion, `verificar_fuga` rechaza variables predictoras con m/z, RT, intensidad, identificadores de lote,
articulo o muestra, o el propio objetivo.

### 4.4 Crear un experimento nuevo
Copie un YAML parecido, cambie `id` y el nombre del archivo, ajuste `conjunto.parametros` y ejecute
`python main.py validar <ID>` y luego `python main.py ejecutar <ID>`.

## 5. Pruebas

`python -m pytest` incluye:
- unitarias: formula, validacion, configuracion, CLR;
- flujo supervisado de extremo a extremo con datos sinteticos;
- integridad de los datos reales (se omiten si falta Dataset.csv).

## 6. Documentacion

En `../05_Documentacion`: `arquitectura.md`, `diccionario_datos.md`, `metodologia.md`, `guia_modelos.md`,
`limitaciones_cientificas.md` e `informe_cientifico.md`.

## Construccion de 01_Datos/Dataset

`python main.py construir-dataset` lee los 57 lotes de `01_Datos/Data/Batch` y la curacion de los 52 articulos
(`src/construccion/curacion.py` y `referencias.py`) y escribe las 40 tablas normalizadas de `01_Datos/Dataset`
(trazabilidad, taxonomia, geografia, muestra, plataforma analitica, quimica, metabolitos, actividad biologica,
hechos y `10_Dataset_final/Dataset.csv`) junto con `INFORME_CONSTRUCCION.md`. Si los CSV ya existen con cabecera,
se respeta el orden de sus columnas y las columnas nuevas se agregan al final (`--ignorar-plantillas` lo desactiva).
Opciones: `--salida`, `--lotes 1 2 3`, `--sin-dataset`.

