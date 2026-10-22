# Arquitectura del sistema

## 1. Principios

1. **Los datos originales no se modifican.** `01_Datos/Base` solo se lee; toda salida va a `03_Resultados`
   (`Global` y `Models/<Modelo>`). Dataset.csv se cachea en Parquet (`03_Resultados/_cache/dataset_<huella>.parquet`), con el nombre
   indexado por su SHA-256: si el CSV cambia, se regenera la cache.
2. **Configuracion, no codigo.** Cada experimento es un YAML en `02_Script/config/modelos/` y se valida antes de
   ejecutarse: claves obligatorias, modelos existentes, baseline obligatorio, validacion agrupada obligatoria y
   ausencia de variables con fuga.
3. **Evaluacion honesta por defecto.** La validacion cruzada se agrupa por articulo, o por formula cuando la unidad es
   el compuesto. Cada modelo se compara con baselines, con un control que solo usa variables de plataforma, con una
   validacion no agrupada (para medir la inflacion) y con una prueba de permutacion.
4. **Reproducibilidad y no sobrescritura.** Cada ejecucion tiene un identificador unico
   (`AAAAMMDD-HHMMSS_<id>_<huella-config>`) y guarda la configuracion resuelta, un manifiesto (huellas de datos,
   versiones, semilla, commit) y su registro.

## 2. Estructura de carpetas

```
Inteligencia Artificial Orquideas/
├── 01_Datos/Base/                 # entrada (solo lectura): 22 catalogos + Dataset.csv
├── 02_Script/
│   ├── main.py                    # interfaz (sin argumentos) o comandos; comprueba dependencias al arrancar
│   ├── requirements.txt           # lista unica de dependencias del proyecto
│   ├── config/
│   │   ├── rutas.yaml             # rutas relativas a la raiz (raiz_proyecto: auto)
│   │   ├── config_global.yaml     # semilla, niveles MSI aceptados, defaults de split/evaluacion/salidas
│   │   └── modelos/M01..M18.yaml  # un archivo por experimento
│   ├── src/orquideas/
│   │   ├── utils/                 # rutas, registro (logging), huellas SHA-256, E/S, deteccion de GPU
│   │   ├── data/                  # catalogos (PK/FK), dataset (cache, vista sin replicas), relaciones (integridad)
│   │   ├── audit/                 # auditoria completa e informe de diagnostico
│   │   ├── features/              # quimica (formula -> descriptores), perfiles (composicion CLR), conjuntos (unidades)
│   │   ├── models/                # registro de modelos y pipelines sin fuga
│   │   ├── evaluation/            # particiones agrupadas, filtrado de clases, metricas
│   │   ├── tasks/                 # supervisado (M01-M17b) y patrones (M18)
│   │   ├── config/                # esquema y validacion de YAML, deteccion de fuga
│   │   ├── pipeline/              # ejecutor (run id, manifiesto) e interpretacion (informes, resumen)
│   │   ├── interfaz/              # interfaz de consola (rich): maquina -> datos -> modelos -> opciones -> entrenamiento
│   │   └── visualization/         # graficas con titulo, ejes, leyenda y nota interpretativa
│   └── tests/                     # pytest: unitarias, flujo sintetico de extremo a extremo e integridad de datos
├── 03_Resultados/
│   ├── Global/                    # auditoria general, resumen ejecutivo, informe cientifico, comparacion global
│   └── Models/<Modelo>/           # p. ej. M01_Modo_Ionizacion: auditoria_datos/, ejecuciones/, metricas/,
│                                  #   graficas/, predicciones/, informes/, modelo_entrenado/  (una subcarpeta <run_id>)
└── 05_Documentacion/              # este documento y el resto de manuales
```

## 3. Flujo de datos

```
Dataset.csv ──► cargar_dataset (tipado + cache Parquet)
            └─► vista_quimica (quita la replicacion por medidas de actividad: 6 116 075 -> 5 798 278 filas)
                 ├─► identificados (ID_METABOLITO > 1 y nivel MSI I-III)
                 │     ├─► presencias (muestra biologica x metabolito, sin QC ni blancos)
                 │     │     ├─► perfiles: conteo por superclase/clase -> CLR      (M02-M07, M11-M15, M17, M18)
                 │     │     └─► matriz de presencia de metabolitos frecuentes    (M16)
                 │     └─► anotaciones por articulo (metabolito, modo, aducto)    (M01, M10)
                 └─► tabla_muestras (atributos + modos + n senales/identificados)
05_Metabolitos.csv ─► descriptores de la formula molecular                       (M08, M09, M17b)
Registo_Actividades_biologicas.csv ─► etiquetas de actividad                     (M17, M17b, M18)
```

## 4. Ciclo de un experimento (`python main.py ejecutar M05`)

1. `config/esquema.py`: lee el YAML, le aplica los `defaults` de `config_global.yaml` y lo valida. Si es invalido, se
   detiene con un mensaje que indica archivo y clave.
2. `pipeline/ejecutor.py`: crea el run id y las carpetas (falla si ya existen y `overwrite: false`), fija las semillas
   y escribe la configuracion resuelta y el manifiesto.
3. `features/conjuntos.py`: construye el `Conjunto` (X, y, grupos, metadatos, covariables instrumentales, pesos).
   `verificar_fuga` rechaza variables prohibidas: m/z, RT, intensidad, identificadores de lote, articulo o muestra,
   y el propio objetivo.
4. `tasks/supervisado.py`:
   1. filtra las clases evaluables (>= N grupos y >= M unidades) y genera las particiones agrupadas;
   2. audita los datos del modelo (`auditoria_datos/<run_id>`) y entrena cada modelo dentro de un `Pipeline`
      (imputacion, varianza, escalado y seleccion opcional se ajustan solo en entrenamiento). XGBoost reparte las
      particiones entre todas las GPU y CatBoost usa todas las GPU en cada ajuste;
   3. calcula predicciones OOF y metricas;
   4. elige el mejor modelo por la metrica principal y corre la evaluacion optimista, el control instrumental y las
      permutaciones;
   5. ajusta el modelo final con todos los datos y guarda modelo, predicciones, metricas y graficas.
5. `pipeline/interpretacion.py`: asigna un veredicto, derivado solo de las metricas, y escribe `informe.md`.

## 5. Decisiones de diseno

| Decision | Motivo |
|---|---|
| Grupo = articulo | Especie, laboratorio, plataforma y biblioteca de anotacion estan confundidos con el articulo. |
| Grupo = formula en modelos de compuesto | Los isomeros comparten descriptores; separarlos evita memorizar formulas. |
| Perfil por presencia, no por intensidad | ALTURA_PICO no es comparable entre lotes (detectores y normalizaciones distintos). |
| CLR | El perfil es composicional (fracciones); CLR lo lleva a un espacio euclideo. |
| Categorias en >= 3-5 articulos | Evita variables que solo existen en la biblioteca de un laboratorio. |
| Pesos 1/n por articulo | Un articulo con 200 muestras no domina el entrenamiento. |
| Unidad agregada en M16-M18 | Las replicas de un extracto no son evidencia independiente. |
| Reino | Constante (Plantae): no se modela; se usa solo como control de integridad. |
| Niveles MSI | I-III = identificado (entra en perfiles y modelos de compuesto); IV = senal sin identificar (excluida de todo analisis que requiere identidad). El nivel no se usa como predictor. |
| GPU | `utils/gpu.py` detecta todas las GPU NVIDIA con nvidia-smi. XGBoost (una GPU por particion, particiones en paralelo) y CatBoost (todas las GPU por modelo) las usan; sin GPU todo funciona en CPU. |
| Resultados por modelo | Cada modelo concentra en `03_Resultados/Models/<Modelo>` su auditoria de datos, ejecuciones, metricas, graficas, predicciones, informes y modelo entrenado. |
