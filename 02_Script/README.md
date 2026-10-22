# 02_Script - Sistema de IA para el descubrimiento de patrones quimicos en orquideas

Sistema modular y reproducible que audita `01_Datos/Base` y entrena y evalua 18 experimentos de aprendizaje
supervisado y no supervisado. Todo resultado lleva su configuracion, sus huellas de datos y su informe.

## 1. Instalacion

Requisitos: Python 3.11-3.13 (probado con 3.13) y unos 4 GB de RAM libres.

**Windows (PowerShell):**
```powershell
cd "D:\Inteligencia Artificial Orquideas"
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd 02_Script
python -m pytest            # comprobacion de la instalacion
```

**Linux / macOS:**
```bash
cd "Inteligencia Artificial Orquideas"
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cd 02_Script && python -m pytest
```

Las rutas se resuelven solas a partir de la carpeta padre de `02_Script` (`raiz_proyecto: auto` en
`config/rutas.yaml`). Para fijarlas a mano: `raiz_proyecto: "D:/Inteligencia Artificial Orquideas"`.

## 2. Uso

Ejecutar desde `02_Script`:

| Comando | Que hace |
|---|---|
| `python main.py auditoria [--etiqueta X]` | Auditoria completa -> `04_Resultados/auditoria_datos/<X>/informe_auditoria.md` |
| `python main.py listar` | Lista los experimentos configurados |
| `python main.py validar [ID ...]` | Valida los YAML sin ejecutar (codigo de salida 1 si hay errores) |
| `python main.py ejecutar M05 [M13 ...] [--etiqueta X]` | Ejecuta experimentos (acepta `M05` o `M05_familia`) |
| `python main.py ejecutar-todos` | Ejecuta todos y genera el resumen (unas 2-3 h con 4 nucleos, sobre todo por las permutaciones) |
| `python main.py resumen` | Escribe `04_Resultados/informes/resumen_ejecutivo.md` y `05_Documentacion/guia_modelos.md` |
| `python main.py predecir RUN_ID datos.csv` | Aplica un modelo guardado a un CSV con las mismas columnas que X |

La primera lectura de Dataset.csv (~550 MB) tarda alrededor de 1 minuto y crea una cache Parquet en
`04_Resultados/cache`; las siguientes tardan segundos.

## 3. Salidas de cada ejecucion

`run_id = AAAAMMDD-HHMMSS_<ID>_<huella de la config>[_etiqueta]`. Nunca se sobrescribe una ejecucion previa.

| Carpeta | Contenido |
|---|---|
| `04_Resultados/ejecuciones/<run_id>/` | `informe.md`, `config_resuelta.yaml`, `manifiesto.json` (huellas SHA-256, versiones, semilla, commit), `resultado.json`, `ejecucion.log`, `tablas/` |
| `04_Resultados/metricas/<run_id>/` | metricas por modelo y por particion, reporte por clase o etiqueta, matriz de confusion, importancias, permutaciones |
| `04_Resultados/predicciones/<run_id>/` | predicciones fuera de particion con identificadores (articulo, muestra, metabolito...) |
| `04_Resultados/graficas/<run_id>/` | graficas con titulo, ejes, leyenda y nota interpretativa |
| `03_Modelos_Entrenados/<ID>/<run_id>/modelo.joblib` | pipeline final y metadatos (columnas, clases, codificador) |

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
```

Modelos disponibles: `baseline_mayoritaria`, `baseline_prior`, `baseline_estratificada`, `logistica`,
`random_forest`, `extra_trees`, `hist_gradient_boosting`, `lightgbm`, `knn`. Los hiperparametros se pasan tal cual
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
