# Informe de construccion del Dataset

Generado por `python main.py construir-dataset` en 175.5 s a partir de 01_Datos/Data (55 fuentes: 52 articulos + 1 articulo sin PDF + 2 conjuntos de datos sin articulo; 57 lotes).

## Tablas generadas

| Archivo | Filas |
|---|---|
| `01_Trazabilidad/01_Articulos.csv` | 56 |
| `01_Trazabilidad/02_Batches.csv` | 58 |
| `02_Taxonomia/01_Reinos.csv` | 2 |
| `02_Taxonomia/02_Filos.csv` | 4 |
| `02_Taxonomia/03_Clases_taxonomicas.csv` | 5 |
| `02_Taxonomia/04_Ordenes.csv` | 24 |
| `02_Taxonomia/05_Familias.csv` | 35 |
| `02_Taxonomia/06_Generos.csv` | 53 |
| `02_Taxonomia/07_Especies.csv` | 74 |
| `03_Geografia/01_Ubicaciones.csv` | 84 |
| `04_Muestra/01_Tipos_muestra.csv` | 6 |
| `04_Muestra/02_Partes_planta_estudiadas.csv` | 31 |
| `04_Muestra/03_Tipos_cultivo.csv` | 14 |
| `04_Muestra/04_Metodos_extraccion.csv` | 27 |
| `04_Muestra/05_Solventes.csv` | 8 |
| `05_Plataforma_analitica/01_Modos_ionizacion.csv` | 4 |
| `05_Plataforma_analitica/02_Tecnicas_separacion.csv` | 5 |
| `05_Plataforma_analitica/03_Columnas_cromatograficas.csv` | 19 |
| `05_Plataforma_analitica/04_Modos_adquisicion.csv` | 6 |
| `05_Plataforma_analitica/05_Analizadores.csv` | 6 |
| `05_Plataforma_analitica/06_Instrumentos.csv` | 24 |
| `05_Plataforma_analitica/07_Tipos_intensidad.csv` | 8 |
| `06_Quimica_Analitica/01_Niveles_identificacion.csv` | 5 |
| `06_Quimica_Analitica/02_Superclases_quimicas.csv` | 23 |
| `06_Quimica_Analitica/03_Clases_quimicas.csv` | 1,206 |
| `06_Quimica_Analitica/04_Aductos.csv` | 85 |
| `07_Metabolitos/01_Metabolitos.csv` | 45,943 |
| `07_Metabolitos/02_Sinonimos_metabolitos.csv` | 3,678 |
| `07_Metabolitos/03_Identificadores_externos.csv` | 96,996 |
| `08_Actividad_biologica/01_Categorias_actividad.csv` | 11 |
| `08_Actividad_biologica/02_Actividades_biologicas.csv` | 50 |
| `09_Hechos/01_Muestras.csv` | 1,773 |
| `09_Hechos/02_Senales.csv` | 272,749 |
| `09_Hechos/03_Intensidades.csv` | 5,802,308 |
| `09_Hechos/04_Registro_actividades.csv` | 613 |
| `10_Dataset_final/Dataset.csv` | 6,165,627 |

## Resumen por lote

| Lote | Articulo | Hojas | Muestras | Senales | Anotadas | Intensidades |
|---|---|---|---|---|---|---|
| BAT0001 | ART0001 | Sheet 1 | 100 | 636 | 11 | 63,396 |
| BAT0002 | ART0001 | Hoja1 | 100 | 675 | 3 | 52,490 |
| BAT0003 | ART0054 | Hoja1 | 59 | 4,435 | 29 | 127,229 |
| BAT0004 | ART0055 | Sheet_edited | 28 | 402 | 0 | 11,256 |
| BAT0005 | ART0002 | 0 | 201 | 23,253 | 0 | 585,704 |
| BAT0006 | ART0002 | 0 | 201 | 19,335 | 0 | 286,969 |
| BAT0007 | ART0003 | Metaboscape | 147 | 1,230 | 123 | 161,751 |
| BAT0008 | ART0005 | Sheet1 | 9 | 1,761 | 1,761 | 15,849 |
| BAT0009 | ART0006 | Metabolite profiling | 66 | 629 | 629 | 36,911 |
| BAT0010 | ART0006 | Metabolite profiling | 66 | 714 | 714 | 42,483 |
| BAT0011 | ART0007 | 0 | 12 | 402 | 402 | 4,824 |
| BAT0012 | ART0008 | Table S1 | 18 | 1,440 | 1,440 | 25,671 |
| BAT0013 | ART0009 | Table S1 | 18 | 641 | 640 | 6,738 |
| BAT0014 | ART0010 | Table S2; Table S3 | 15 | 24,264 | 5,793 | 363,960 |
| BAT0015 | ART0011 | Table S1 | 69 | 7,675 | 2,267 | 529,575 |
| BAT0016 | ART0012 | Sheet1 | 15 | 678 | 678 | 10,170 |
| BAT0017 | ART0013 | Table S1 | 21 | 98 | 98 | 2,058 |
| BAT0018 | ART0014 | Table S1 | 12 | 16,725 | 0 | 200,700 |
| BAT0019 | ART0015 | Sheet1 | 18 | 6,750 | 6,750 | 121,500 |
| BAT0020 | ART0016 | Table S4; Table S5 | 9 | 43,516 | 7,018 | 389,167 |
| BAT0021 | ART0017 | Supplementary Table 2 | 15 | 649 | 648 | 9,638 |
| BAT0022 | ART0018 | Table S1 | 12 | 1,595 | 1,594 | 19,140 |
| BAT0023 | ART0019 | Sheet1 | 12 | 3,415 | 3,415 | 40,925 |
| BAT0024 | ART0020 | PS_PO + PC_PO, PK_PO, PS_PK, PC_PK, PS_PC | 24 | 348 | 348 | 7,086 |
| BAT0025 | ART0021 | Raw Data | 12 | 163 | 163 | 1,956 |
| BAT0026 | ART0022 | sheet 1 | 41 | 23,534 | 2,519 | 964,894 |
| BAT0027 | ART0023 | E_N; Sheet1 | 6 | 623 | 621 | 3,738 |
| BAT0028 | ART0024 | Sheet1 | 18 | 11,132 | 990 | 200,376 |
| BAT0029 | ART0025 | Sheet1 | 7 | 430 | 429 | 2,917 |
| BAT0030 | ART0026 | all.exp.POS; all.exp.NEG | 15 | 1,753 | 1,751 | 26,295 |
| BAT0031 | ART0027 | Table S1 | 9 | 988 | 988 | 8,389 |
| BAT0032 | ART0028 | Sheet1 | 15 | 808 | 807 | 10,531 |
| BAT0033 | ART0029 | shee1 | 12 | 78 | 78 | 823 |
| BAT0034 | ART0030 | ST9. Oatwheat_complete_dataset | 36 | 702 | 702 | 24,910 |
| BAT0035 | ART0031 | Sheet1 | 20 | 398 | 398 | 7,960 |
| BAT0036 | ART0032 | POS ion mode ; NEG ion mode | 18 | 2,130 | 2,130 | 38,340 |
| BAT0037 | ART0033 | Table S2 | 9 | 541 | 541 | 4,824 |
| BAT0038 | ART0034 | Sheet1 | 12 | 1,237 | 1,237 | 14,186 |
| BAT0039 | ART0035 | Positive ion mode; Negative ion mode | 30 | 3,237 | 3,236 | 78,736 |
| BAT0040 | ART0036 | Sheet1 | 21 | 311 | 311 | 4,848 |
| BAT0041 | ART0037 | Sheet1 | 12 | 1,733 | 1,733 | 20,796 |
| BAT0042 | ART0038 | Table S1. | 6 | 776 | 776 | 4,656 |
| BAT0043 | ART0039 | Sheet1 | 12 | 1,929 | 1,927 | 23,097 |
| BAT0044 | ART0040 | Foglio1 | 9 | 1,752 | 1,750 | 10,735 |
| BAT0045 | ART0041 | All_sample_data | 18 | 1,362 | 1,362 | 23,929 |
| BAT0046 | ART0042 | Sheet1 | 15 | 1,909 | 1,909 | 28,635 |
| BAT0047 | ART0043 | Sheet1 | 18 | 1,094 | 1,093 | 19,692 |
| BAT0048 | ART0053 | Sheet1 | 15 | 3,705 | 3,702 | 55,575 |
| BAT0049 | ART0044 | Sheet1 | 9 | 1,344 | 1,343 | 12,087 |
| BAT0050 | ART0045 | Table S1 | 18 | 192 | 190 | 3,420 |
| BAT0051 | ART0046 | All metabolites | 15 | 1,341 | 1,340 | 20,115 |
| BAT0052 | ART0047 | Sheet1 | 24 | 911 | 911 | 21,864 |
| BAT0053 | ART0048 | Sheet1 | 12 | 364 | 364 | 4,149 |
| BAT0054 | ART0049 | Sheet1 | 3 | 993 | 992 | 2,979 |
| BAT0055 | ART0050 | tsv | 25 | 34,294 | 2,317 | 857,350 |
| BAT0056 | ART0051 | All data | 12 | 2,016 | 2,016 | 22,553 |
| BAT0057 | ART0052 | Data | 21 | 7,703 | 7,702 | 161,763 |

## Cifras clave

- Especies con datos: 72 (orquideas: 2)
- Muestras: 1,772 (QC: 192, blancos: 35, medias de grupo: 19, sub-QC: 71)
- Senales: 272,749; anotadas con metabolito: 82,689; niveles MSI: 1=6,691, 2=49,866, 3=21,707, 4=194,485
- Metabolitos distintos: 45,941; sinonimos: 3,678; identificadores externos: 96,996
- Intensidades (valores > 0): 5,802,308
- Registros de actividad biologica: 613 (experimentales: 231)

## Decisiones de curacion

- ART0043 (`ART0043_lonicera_japonica.pdf`) trata del loto (*Nelumbo nucifera*); BAT0047 (`lonicera_japonica`) contiene sus seis tejidos.
- BAT0048 (`lonicera_japonica`) contiene cuatro *Rhododendron* de Linzhi; su articulo (doi 10.3390/metabo16040226) no esta en 01_Datos/Data/Articulos y se registra como ART0053 con los datos de BASE DE DATOS GLOBAL.
- BAT0003 (*Banisteriopsis caapi*) y BAT0004 (*Piper peltatum*) no tienen articulo: se registran como ART0054 y ART0055 (repositorios IKIAM) para no mezclarlos en un mismo grupo.
- ART0004 (*Sophora flavescens*) no tiene lote; se conserva en 01_Articulos y en el registro de actividades.
- BAT0002 usa la hoja `Hoja1` (tabla anotada); las demas hojas son reprocesamientos de las mismas inyecciones.
- BAT0020: las senales de las tablas S4 (positivo) y S5 (negativo) se anotan con los nombres de las tablas S6-S8 por ID y modo.
- BAT0024 solo trae metabolitos diferenciales por pares de especies: se unen las seis hojas y se deduplica por ID.
- BAT0029, BAT0042 y BAT0049 solo reportan medias por grupo: se guardan como muestras de tipo 'Media de grupo'.
- BAT0016: la asignacion de las variedades A-D a TW, XY, MX y ZC sigue el orden del articulo (no esta explicita en la tabla).
- Metware usa el valor 9 como marcador de no detectado en tablas MRM; se trata como 0 (no se guarda).
- Las tablas en log10 (BAT0018, BAT0052, BAT0055) se conservan en esa escala (ver ID_TIPO_INTENSIDAD).
- Las clases quimicas de cada laboratorio (Metware, ClassyFire, HMDB) se unifican en 21 superclases; la clase original se guarda en 02_Senales.CLASE_ORIGINAL.
