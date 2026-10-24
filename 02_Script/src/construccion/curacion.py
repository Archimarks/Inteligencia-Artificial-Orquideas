"""Metadatos curados articulo por articulo y lote por lote (01_Datos/Data/Articulos y 01_Datos/Data/Batch).

Para cada lote se indica que hoja(s) leer, que columna contiene cada atributo de la senal y como interpretar el
codigo de cada columna de muestra (especie, parte, grupo experimental, replica, QC o blanco). Las claves de
especie, parte, cultivo, ubicacion, metodo, instrumento, etc. se definen en `referencias.py`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ============================================================================================ articulos
# (archivo, titulo, autor principal, revista, anio, doi, enfoque, repositorio de datos, datos crudos, objetivo)
_A = "Articulo publicado"
ARTICULOS: dict[int, dict[str, Any]] = {}


def _art(i: int, archivo: str, titulo: str, autor: str, revista: str, anio: int | None, doi: str, enfoque: str,
         objetivo: str, repositorio: str = "", crudos: str = "", tipo: str = _A) -> None:
    ARTICULOS[i] = dict(CODIGO_ARTICULO=f"ART{i:04d}", ARCHIVO_ARTICULO=archivo, TITULO=titulo, AUTOR_PRINCIPAL=autor,
                        REVISTA=revista, ANIO_PUBLICACION=anio, DOI=doi, ENFOQUE_METABOLOMICO=enfoque,
                        OBJETIVO=objetivo, REPOSITORIO_DATOS=repositorio, DATOS_CRUDOS=crudos, TIPO_FUENTE=tipo)


ND, WT, QT = "No dirigido", "Ampliamente dirigido (widely targeted)", "Pseudo-dirigido (quasi-targeted)"
_art(1, "ART0001_ilex_guayusa.pdf", "Integrated HPLC-UV validation and LC-MS/MS optimization with molecular networking and chemometrics for advanced characterization of chlorogenic acids in Ilex guayusa", "Garzon T.", "Journal of Chromatography A", 2026, "10.1016/j.chroma.2026.466732", ND, "Validar HPLC-UV para 5-CQA y optimizar LC-MS/MS con redes moleculares para isomeros de acidos clorogenicos segun chakra, luz y edad de la planta.", "https://github.com/IKIAM-NPLab/I_guayusa_caffeoylquinic_acid_isomers", "GNPS/MassIVE MSV000098557")
_art(2, "ART0002_malpighiaceae_spp.pdf", "Untargeted Metabolomics Sheds Light on the Diversity of Major Classes of Secondary Metabolites in the Malpighiaceae Botanical Family", "Mannochio-Russo H.", "Frontiers in Plant Science", 2022, "10.3389/fpls.2022.854842", ND, "Quimiosistematica de 139 especies de Malpighiaceae combinando metabolomica no dirigida, clasificacion in silico y reconstruccion de caracteres ancestrales.", "", "MassIVE MSV000085119")
_art(3, "ART0003_pisum_sativum.pdf", "Untargeted LC-MS/MS metabolomics reveals farming practice- and cultivar-driven modulations of pea (Pisum sativum L.) seed metabolome across multiple biosynthetic pathways", "Kakhkhorov S.A.", "The Crop Journal", 2026, "10.1016/j.cj.2026.01.012", ND, "Efecto del cultivar y del sitio/practica agricola (convencional vs organica) sobre el metaboloma de semillas de arveja.")
_art(4, "ART0004_sophora_flavescens.pdf", "Dereplication of secondary metabolites from Sophora flavescens using an LC-MS/MS-based molecular networking strategy", "Wang H.", "Scientific Reports", 2025, "10.1038/s41598-025-94958", ND, "Estrategia de dereplicacion (DIA + DDA + redes moleculares) de metabolitos secundarios de la raiz.", "", "MassIVE MSV000096717")
_art(5, "ART0005_solanum_tuberosum.pdf", "Untargeted metabolomics reveals key steroidal glycoalkaloids and associated metabolites in crude and C18-purified extracts of potato leaves", "Lv Y.", "BMC Plant Biology", 2026, "10.1186/s12870-026-08606-7", ND, "Catalogar metabolitos de un extracto crudo y uno purificado (SPE C18) de hojas de papa e identificar glicoalcaloides esteroidales.")
_art(6, "ART0006_oldenlandia_spp.pdf", "Metabolomic and Transcriptomic Profiling of Two Closely Related Species within the Genus Oldenlandia", "Chen P.", "Scientific Data", 2026, "10.1038/s41597-026-06745-y", WT, "Comparar cinco tejidos de O. diffusa y O. corymbosa con metabolomica ampliamente dirigida y transcriptomica.", "https://www.ebi.ac.uk/metabolights/MTBLS13314")
_art(7, "ART0007_garcinia_oblongifolia.pdf", "Tissue-specific biosynthesis and spatial distribution of xanthones in Garcinia oblongifolia revealed by integrated metabolomic and full-length transcriptomic analyses", "Zhang Y.", "BMC Genomics", 2026, "10.1186/s12864-025-12391-2", ND, "Distribucion de xantonas en corteza, ramas, hojas y frutos y su ruta biosintetica.")
_art(8, "ART0008_rubia_spp.pdf", "Qiancao (Rubia spp.) - a comprehensive metabolomics analysis of the five core species", "Zhang M.", "Frontiers in Pharmacology", 2025, "10.3389/fphar.2025.1541994", ND, "Comparar el metaboloma de la droga cruda de cinco especies de Rubia.")
_art(9, "ART0009_pinellia_pedatisecta.pdf", "Integrative analyses of the transcriptome and metabolome of Huzhang (Pinellia pedatisecta Schott) uncover the molecular genetic basis of its medicinal properties", "Pan C.", "BMC Genomics", 2026, "10.1186/s12864-026-12616-y", ND, "Metaboloma y transcriptoma de hoja, tallo y tuberculo.")
_art(10, "ART0010_pogostemon_cablin.pdf", "Metabolomic Profiling of Pogostemon cablin Reveals Disruption of Secondary Metabolite Biosynthesis Induced by Corynespora cassiicola Infection", "Liao R.-X.", "International Journal of Molecular Sciences", 2025, "10.3390/ijms26083680", ND, "Efecto de la mancha foliar por Corynespora cassiicola sobre el perfil metabolico y el alcohol de pachuli.")
_art(11, "ART0011_nicotiana_tabacum.pdf", "Insights into tobacco leaf quality deterioration under long-term storage by investigating dynamic phytochemical and metabolite profile variations", "Xiao G.", "BMC Plant Biology", 2025, "10.1186/s12870-025-06375-3", ND, "Cambios del metaboloma de hojas de tabaco curadas en almacenamiento natural, mecanico y con aire acondicionado.")
_art(12, "ART0012_platostoma_chinense.pdf", "Quasi-Targeted Metabonomics Reveals Metabolites Associated with Antioxidant Activity of Mesona chinensis Benth Cultivar Xiaoye", "Niu Y.", "Plants", 2025, "10.3390/plants14111585", QT, "Relacionar el metaboloma de cuatro variedades con su actividad antioxidante (DPPH, ABTS).")
_art(13, "ART0013_eriobotrya_japonica.pdf", "Optimizing processing methods for maximum bioactive retention: comparative metabolomic analysis of dried loquat (Eriobotrya japonica) flowers and their powdered extracts", "Duan M.", "Frontiers in Nutrition", 2025, "10.3389/fnut.2025.1637247", WT, "Efecto del secado por calor y la liofilizacion sobre los flavonoides de flores de nispero y sus extractos en polvo.")
_art(14, "ART0014_codonopsis_pilosula.pdf", "Untargeted Metabolomics Reveals Multiple Phytometabolites in the Agricultural Waste Materials and Medicinal Materials of Codonopsis pilosula", "Zeng X.", "Frontiers in Plant Science", 2022, "10.3389/fpls.2021.814011", ND, "Comparar raices (material medicinal) con tallos y hojas (residuo agricola).")
_art(15, "ART0015_spatholobus_suberectus.pdf", "Seasonal Metabolic Profiling and Anti-Inflammatory Potential of Spatholobus suberectus Leaves Based on Metabolomics and Network Pharmacology", "Luo M.", "Plants", 2026, "10.3390/plants15101509", ND, "Perfil metabolico estacional de hojas y su potencial antiinflamatorio y antioxidante.")
_art(16, "ART0016_mosla_chinensis.pdf", "Non-targeted metabolomics reveals tissue-specific metabolic profiling and antioxidant-related markers in Mosla chinensis Maxim. cv. Jiangxiangru", "Wang Y.", "Frontiers in Plant Science", 2026, "10.3389/fpls.2026.1740266", ND, "Perfil por tejido (flor, hoja, tallo) y marcadores asociados a la actividad antioxidante.")
_art(17, "ART0017_fagopyrum_dibotrys.pdf", "Identification of Medicinal Compounds of Fagopyri Dibotryis Rhizome from Different Origins and Its Varieties Using UPLC-MS/MS-Based Metabolomics", "Zhang C.", "Metabolites", 2022, "10.3390/metabo12090790", WT, "Diferencias del rizoma entre cinco zonas de produccion.")
_art(18, "ART0018_akebia_trifoliata.pdf", "Widely Targeted Metabolomics Analysis Reveals Developmental Shifts in Antioxidants and Functional Peptides in Akebia trifoliata", "Jia T.", "Antioxidants", 2025, "10.3390/antiox14091039", WT, "Cambios quimicos y antioxidantes del fruto en cuatro estados de desarrollo.")
_art(19, "ART0019_ipomoea_batatas.pdf", "Exploring the metabolic characteristics of fresh-cut sweet potatoes at different storage times based on untargeted metabolomics", "Wan X.", "Food Chemistry: X", 2026, "10.1016/j.fochx.2026.104066", ND, "Respuesta metabolica de batata morada cortada durante 0-5 dias de almacenamiento.")
_art(20, "ART0020_polygonatum_spp.pdf", "Metabolic Signatures of Four Polygonatum Rhizoma Species Mapped Using Untargeted Metabolomics", "Jia N.", "Metabolites", 2025, "10.3390/metabo15110682", ND, "Diferencias metabolicas entre cuatro especies de Polygonatum.")
_art(21, "ART0021_fragaria_ananassa.pdf", "LC-MS/MS-based metabolomic study provides insights into altitude-dependent variations in flavonoid profiles of strawberries", "Rao M.J.", "Frontiers in Plant Science", 2025, "10.3389/fpls.2024.1527212", WT, "Efecto de la altitud sobre flavonoides, calidad y antioxidantes de la fresa.")
_art(22, "ART0022_medicago_sativa.pdf", "Metabolomic analyses reveal substances that contribute to the increased freezing tolerance of alfalfa (Medicago sativa L.) after continuous water deficit", "Xu H.", "BMC Plant Biology", 2020, "10.1186/s12870-019-2233-9", ND, "Metabolitos asociados a la tolerancia a congelamiento tras deficit hidrico.")
_art(23, "ART0023_camellia_tetracocca.pdf", "Untargeted Metabolite Profiling of Camellia tetracocca's Response to an Empoasca onukii Attack Using GC-MS and LC-MS", "Zhang N.", "Agronomy", 2023, "10.3390/agronomy13030791", ND, "Respuesta metabolica de hojas atacadas por el saltahojas del te.")
_art(24, "ART0024_gastrodia_elata.pdf", "Global metabolic profile and multiple phytometabolites in the different varieties of Gastrodia elata Blume", "Zeng X.", "Frontiers in Plant Science", 2023, "10.3389/fpls.2023.1249456", ND, "Perfil metabolico de tres variedades de tianma y sus fitometabolitos bioactivos.")
_art(25, "ART0025_camellia_sinensis.pdf", "Metabolite Profiling of External and Internal Petals in Three Different Colors of Tea Flowers (Camellia sinensis) Using Widely Targeted Metabolomics", "Zhang T.", "Metabolites", 2023, "10.3390/metabo13070784", WT, "Diferencias de metabolitos entre petalos externos e internos de flores de te de tres colores.")
_art(26, "ART0026_morus_alba.pdf", "Magnesium Nutrient Application Induces Metabolomics and Physiological Responses in Mulberry (Morus alba) Plants", "Jin X.", "International Journal of Molecular Sciences", 2023, "10.3390/ijms24119650", ND, "Respuesta metabolica de la morera a seis niveles de magnesio.")
_art(27, "ART0027_dioscorea_opposita.pdf", "Widely Targeted Metabolomics Reveals the Effects of Soil on the Metabolites in Dioscorea opposita Thunb.", "Yang L.", "Molecules", 2023, "10.3390/molecules28134925", WT, "Efecto del tipo de suelo (arenoso vs loess) sobre el tuberculo.")
_art(28, "ART0028_taxus_media.pdf", "Analysis of the utilization value of different tissues of Taxus x media based on metabolomics and antioxidant activity", "Li M.", "BMC Plant Biology", 2023, "10.1186/s12870-023-04308-6", WT, "Metabolitos y actividad antioxidante de corteza, hojas, semillas y arilo.")
_art(29, "ART0029_camellia_drupifera.pdf", "Metabolomic Study of Flavonoids in Camellia drupifera under Aluminum Stress by UPLC-MS/MS", "Wang Y.", "Plants", 2023, "10.3390/plants12071432", WT, "Flavonoides de hojas bajo estres por aluminio.")
_art(30, "ART0030_avena_sativa_triticum_aestivum.pdf", "Untargeted metabolomics profiling of oat (Avena sativa L.) and wheat (Triticum aestivum L.) infested with wheat stem sawfly (Cephus cinctus Norton) reveals differences associated with plant defense and insect nutrition", "Hager M.S.", "Frontiers in Plant Science", 2024, "10.3389/fpls.2024.1327390", ND, "Respuesta de tallos de avena y trigo a la infestacion por Cephus cinctus.")
_art(31, "ART0031_panax_quinquefolius.pdf", "Diversity and correlation analysis of endophytes and metabolites of Panax quinquefolius L. in various tissues", "Li R.", "BMC Plant Biology", 2023, "10.1186/s12870-023-04282-z", ND, "Metabolitos y endofitos de raiz, fibrilla, tallo y hoja.")
_art(32, "ART0032_morus_alba.pdf", "Metabolomics and physio-chemical analyses of mulberry plants leaves response to manganese deficiency and toxicity reveal key metabolites and their pathways in manganese tolerance", "Li J.", "Frontiers in Plant Science", 2024, "10.3389/fpls.2024.1349456", ND, "Respuesta de hojas de morera a deficiencia y toxicidad de manganeso.")
_art(33, "ART0033_neolamarckia_cadamba.pdf", "Comprehensive Secondary Metabolite Profiling and Antioxidant Activity of Aqueous and Ethanol Extracts of Neolamarckia cadamba (Roxb.) Bosser Fruits", "Yang L.", "Metabolites", 2024, "10.3390/metabo14090511", WT, "Comparar extractos acuoso y etanolico de frutos y su actividad antioxidante.")
_art(34, "ART0034_paeonia_lactiflora.pdf", "Widely targeted metabolomics reveals differences in metabolites of Paeonia lactiflora cultivars", "Li Y.", "PLOS ONE", 2024, "10.1371/journal.pone.0298194", WT, "Diferencias de metabolitos entre raices de tres cultivares.")
_art(35, "ART0035_chrysanthemum_morifolium.pdf", "Metabolomics and proteomics analyses of Chrysanthemi Flos: a mechanism study of changes in proteins and metabolites by processing methods", "Zhang W.", "Chinese Medicine", 2024, "10.1186/s13020-024-01013-w", ND, "Efecto del secado a la sombra y en horno sobre proteinas y metabolitos.")
_art(36, "ART0036_rosaceae_spp.pdf", "Analysis of flavonoid metabolism of compounds in succulent fruits and leaves of three different colors of Rosaceae", "Yang C.", "Scientific Reports", 2024, "10.1038/s41598-024-55541-4", WT, "Flavonoides de frutos y hojas de tres rosaceas ornamentales de distinto color.")
_art(37, "ART0037_ipomoea_batatas.pdf", "Comparative Metabolomic Analysis of the Nutrient Composition of Different Varieties of Sweet Potato", "Wan X.", "Molecules", 2024, "10.3390/molecules29225395", ND, "Aminoacidos, acidos organicos y lipidos de tres variedades de batata.")
_art(38, "ART0038_sesamum_indicum.pdf", "Comparative metabolomics analysis of different sesame (Sesamum indicum L.) tissues reveals a tissue-specific accumulation of metabolites", "Dossou S.S.K.", "BMC Plant Biology", 2021, "10.1186/s12870-021-03132-0", WT, "Distribucion de metabolitos en hojas, flores, carpelos y semillas.")
_art(39, "ART0039_dendrobium_officinale.pdf", "Multidimensional evaluation of quality differences for Dendrobium officinale stems grown under different cultivation environments based on widely targeted metabolomics, network pharmacology, molecular docking, and cell experiments", "Hou Y.", "Frontiers in Plant Science", 2025, "10.3389/fpls.2025.1501545", WT, "Calidad de tallos cultivados epifitos en arbol, en roca y en invernadero.")
_art(40, "ART0040_cormus_domestica.pdf", "Changes in the proteomics and metabolomics profiles of Cormus domestica (L.) fruits during the ripening process", "Tartaglia M.", "BMC Plant Biology", 2024, "10.1186/s12870-024-05677-2", ND, "Cambios poscosecha del fruto del serbal.")
_art(41, "ART0041_clematis_tangutica.pdf", "Potential Distribution Prediction and Metabolite Analysis of Clematis tangutica (Maxim.) Korsh. On the Qinghai Plateau", "Zhang H.", "Ecology and Evolution", 2025, "10.1002/ece3.72110", WT, "Distribucion potencial (MaxEnt) y metabolitos de hojas a lo largo de un gradiente altitudinal.")
_art(42, "ART0042_glycyrrhiza_spp.pdf", "Integrated Metabolomic and Transcriptomic Analysis Reveals the Pharmacological Effects and Differential Mechanisms of Isoflavone Biosynthesis in Four Species of Glycyrrhiza", "Lu Y.", "International Journal of Molecular Sciences", 2025, "10.3390/ijms26062539", WT, "Metabolitos e isoflavonas de cuatro especies de regaliz.")
_art(43, "ART0043_lonicera_japonica.pdf", "Integrated Metabolomic and Transcriptomic Analysis Reveals the Basis for the Difference in Flavonoid Accumulation in Six Medicinal Tissues of Lotus (Nelumbo nucifera Gaertn.)", "Yu Z.", "Applied Sciences", 2025, "10.3390/app15052319", ND, "Acumulacion de flavonoides en seis tejidos medicinales del loto (el nombre del archivo PDF no corresponde a la especie).")
_art(44, "ART0044_citrus_reticulata.pdf", "Integrated analysis of dynamic changes in volatile and non-volatile compounds in Chuan Chenpi (Citrus reticulata 'Dahongpao') during aging by GC-IMS and UPLC-MS/MS", "Zou J.", "Food Chemistry", 2026, "10.1016/j.foodchem.2026.149212", ND, "Cambios de compuestos volatiles y no volatiles de la cascara seca durante 1-8 anios de envejecimiento.")
_art(45, "ART0045_actinidia_chinensis.pdf", "Integrated widely targeted UPLC-MS/MS metabolomics and transcriptomics reveal MYB-linked variation in bioactive phenolics across five kiwifruit varieties", "Duan M.", "Food Chemistry: Molecular Sciences", 2026, "10.1016/j.fochms.2026.100410", WT, "Fenolicos de cinco variedades de kiwi y su capacidad captadora de radicales.")
_art(46, "ART0046_camellia_oleifera.pdf", "Widely targeted metabolomics analysis and antioxidant properties of Camellia oleifera seeds of different cultivars", "Zhu Z.", "Applied Food Research", 2026, "10.1016/j.afres.2026.101700", WT, "Metabolitos y propiedades antioxidantes de semillas de cuatro cultivares.")
_art(47, "ART0047_striga_asiatica.pdf", "Effect of soil factors on flavonoid metabolites in Striga asiatica using LC-MS based on untargeted metabolomics", "Tang S.", "Chemical and Biological Technologies in Agriculture", 2024, "10.1186/s40538-024-00614-9", ND, "Relacion entre flavonoides y propiedades del suelo en siete habitats.")
_art(48, "ART0048_hemerocallis_citrina.pdf", "Comparative analysis of flavonoid metabolites from different parts of Hemerocallis citrina", "Lv H.", "BMC Plant Biology", 2023, "10.1186/s12870-023-04510-6", WT, "Flavonoides de raiz, tallo, hoja y flor.")
_art(49, "ART0049_withania_somnifera.pdf", "Metabolomic profiling of Ashwagandha (Withania somnifera): linking bioactive compounds to functional therapeutic roles", "Tripathi G.", "Frontiers in Molecular Biosciences", 2026, "10.3389/fmolb.2026.1796983", ND, "Perfil de metabolitos secundarios de la raiz y su relacion con funciones terapeuticas.", "https://doi.org/10.6084/m9.figshare.33102755")
_art(50, "ART0050_cibotium_barometz.pdf", "Untargeted LC-MS/MS Metabolite Profiling of Wild, Field-Domesticated and Tissue-Cultured Rhizomes of the Endangered Medicinal Fern Cibotium barometz", "Su Y.", "Life", 2026, "10.3390/life16091435", ND, "Comparar rizomas silvestres, domesticados en campo y de cultivo de tejidos.", "https://doi.org/10.6084/m9.figshare.33295689")
_art(51, "ART0051_lagerstroemia_spp.pdf", "Comparative metabolomics, network analysis, and fraction-based in vitro evaluation of three Lagerstroemia species reveal bioactive compounds and potential for sustainable industrial applications", "Yue Z.", "Industrial Crops & Products", 2026, "10.1016/j.indcrop.2026.124377", WT, "Metabolitos de hojas de tres especies y actividad antioxidante y antidiabetica de sus fracciones.")
_art(52, "ART0052_capsicum_annuum.pdf", "Comparative Analysis of Chemical Constituents in Peppers from Different Regions by Integrated LC-MS and GC-MS Non-Targeted Metabolomics", "Gong X.", "Metabolites", 2026, "10.3390/metabo16010085", ND, "Metabolitos no volatiles de un mismo cultivar de aji en tres regiones.")
_art(53, "No disponible", "Metabolomics Based on UPLC-MS/MS Revealed the Metabolic Differences Among Four Species of Rhododendrons in Linzhi, Xizang", "", "Metabolites", 2026, "10.3390/metabo16040226", WT, "Atlas metabolicos de petalos de cuatro rododendros (PDF no incluido en 01_Datos/Data/Articulos; datos de BASE DE DATOS GLOBAL).")
_art(54, "No disponible", "Banisteriopsis caapi in vitro (conjunto de datos IKIAM sin articulo asociado)", "IKIAM-NPLab", "", None, "", ND, "Perfil de explantes y callos de B. caapi cultivados in vitro.", "https://github.com/IKIAM-NPLab/B_caapi_in_vitro", "", "Conjunto de datos sin articulo")
_art(55, "No disponible", "Piper peltatum metabolomics (conjunto de datos IKIAM sin articulo asociado)", "IKIAM-NPLab", "", None, "", ND, "Perfil GC-MS de hojas frescas y secas extraidas con agua o metanol.", "https://github.com/IKIAM-NPLab/Piper_peltatum_metabolomics", "", "Conjunto de datos sin articulo")

# Especies estudiadas por articulo (las de ART0004 no tienen lote; se registran para las actividades)
ESPECIES_ARTICULO = {4: ["sophora_flavescens"]}

# ============================================================================================ actividades
# Actividades atribuidas a la especie en el articulo (introduccion/discusion, literatura citada)
ACT_ESPECIE: dict[int, list[tuple[str, list[str]]]] = {
    1: [("ilex_guayusa", ["antioxidante"])],
    2: [("malpighiaceae_spp", [])],
    4: [("sophora_flavescens", ["antiinflamatorio", "anticancerigeno", "antimicrobiano"])],
    5: [("solanum_tuberosum", ["antifungico", "insecticida", "antibacteriano", "nematicida"])],
    6: [("oldenlandia_diffusa", ["antiinflamatorio", "anticancerigeno", "desintoxicante", "hepatoprotector"]),
        ("oldenlandia_corymbosa", ["antiinflamatorio", "anticancerigeno", "desintoxicante", "hepatoprotector"])],
    7: [("garcinia_oblongifolia", ["antiinflamatorio", "analgesico", "antibacteriano", "anticancerigeno"])],
    8: [(e, ["antiinflamatorio", "anticancerigeno", "antioxidante", "antimicrobiano", "antiplaquetario", "nefroprotector",
             "antiurolitiasico", "hepatoprotector", "neuroprotector", "antiviral"])
        for e in ("rubia_cordifolia", "rubia_yunnanensis", "rubia_wallichiana", "rubia_schumanniana", "rubia_magna")],
    9: [("pinellia_pedatisecta", ["antioxidante", "anticonvulsivo", "anticancerigeno", "antiarritmico", "antitusivo", "antiemetico"])],
    10: [("pogostemon_cablin", ["antiinflamatorio", "antidepresivo", "antimicrobiano", "anticancerigeno", "antioxidante"])],
    12: [("platostoma_palustre", ["antioxidante", "antihipoxia", "antihipertensivo", "hipolipemiante"])],
    13: [("eriobotrya_japonica", ["antioxidante", "antiinflamatorio", "antidiabetico"])],
    14: [("codonopsis_pilosula", ["antifatiga", "antihipoxia", "anticancerigeno", "antioxidante", "antiinflamatorio",
                                  "neuroprotector", "nefroprotector", "gastroprotector", "hepatoprotector"])],
    15: [("spatholobus_suberectus", ["circulatorio", "anticancerigeno", "antioxidante", "antiinflamatorio"])],
    16: [("mosla_chinensis", ["antiinflamatorio", "antioxidante", "analgesico", "antiemetico"])],
    17: [("fagopyrum_dibotrys", ["antidiabetico", "anticancerigeno", "antiinflamatorio", "antioxidante", "hepatoprotector", "antihipertensivo"])],
    18: [("akebia_trifoliata", ["diuretico", "neuroprotector", "analgesico", "antiinflamatorio", "antiobesidad",
                                "antienvejecimiento", "antibacteriano", "antioxidante", "anticancerigeno"])],
    20: [(e, ["antidiabetico", "inmunomodulador", "antiinflamatorio", "hipolipemiante", "anticancerigeno"])
         for e in ("polygonatum_sibiricum", "polygonatum_cyrtonema", "polygonatum_kingianum", "polygonatum_odoratum")],
    21: [("fragaria_ananassa", ["antioxidante", "antiinflamatorio", "anticancerigeno"])],
    24: [("gastrodia_elata", ["anticonvulsivo", "sedante", "neuroprotector", "antidepresivo", "antiinflamatorio", "antioxidante"])],
    25: [("camellia_sinensis", ["antiproliferativo", "antioxidante", "inmunomodulador", "anticancerigeno", "antiviral"])],
    26: [("morus_alba", ["antioxidante", "antiinflamatorio", "antialergico"])],
    27: [("dioscorea_opposita", ["antioxidante", "antihipertensivo", "antidiabetico"])],
    29: [("camellia_drupifera", ["antioxidante", "antibacteriano"])],
    31: [("panax_quinquefolius", ["antibacteriano", "antiviral"])],
    33: [("neolamarckia_cadamba", ["antidiabetico", "antimicrobiano", "antiinflamatorio", "cicatrizante", "antioxidante",
                                   "antihelmintico", "anticancerigeno", "cardioprotector"])],
    34: [("paeonia_lactiflora", ["anticancerigeno", "antiinflamatorio", "antioxidante", "hepatoprotector"])],
    35: [("chrysanthemum_morifolium", ["antimicrobiano", "antiinflamatorio", "hipolipemiante", "anticancerigeno", "antioxidante"])],
    36: [(e, ["antioxidante", "antienvejecimiento", "anticancerigeno"])
         for e in ("malus_pumila_medzwetzkyana", "prunus_cerasifera", "prunus_persica")],
    38: [("sesamum_indicum", ["antioxidante", "antidiabetico", "antiproliferativo", "gastroprotector", "antimicrobiano", "anticancerigeno"])],
    39: [("dendrobium_officinale", ["gastroprotector", "anticolitis", "anticancerigeno", "antidiabetico", "inmunomodulador",
                                    "hepatoprotector", "antihipertensivo", "antioxidante"])],
    40: [("cormus_domestica", ["antiinflamatorio", "antimicrobiano"])],
    41: [("clematis_tangutica", ["antioxidante", "antibacteriano", "anticancerigeno", "antifungico", "antiinflamatorio", "cardioprotector"])],
    42: [(e, ["antiinflamatorio", "antioxidante", "anticancerigeno", "gastroprotector", "antiviral", "antibacteriano",
              "hepatoprotector", "cardioprotector", "neuroprotector"])
         for e in ("glycyrrhiza_inflata", "glycyrrhiza_uralensis", "glycyrrhiza_pallidiflora", "glycyrrhiza_aspera")],
    43: [("nelumbo_nucifera", ["antidiabetico", "antiobesidad", "antioxidante", "anticancerigeno", "antibacteriano",
                               "antiinflamatorio", "hipolipemiante"])],
    44: [("citrus_reticulata", ["antioxidante"])],
    45: [(e, ["antioxidante", "antiinflamatorio", "cardioprotector"]) for e in ("actinidia_chinensis", "actinidia_arguta")],
    46: [("camellia_oleifera", ["antiobesidad", "antioxidante", "antiinflamatorio", "antimicrobiano", "hepatoprotector", "anticancerigeno"])],
    47: [("striga_asiatica", ["antihepatitis", "antioxidante", "antimalarico", "citotoxico", "antiinflamatorio", "anticancerigeno"])],
    48: [("hemerocallis_citrina", ["antidepresivo", "antioxidante", "antiinflamatorio", "anticancerigeno"])],
    49: [("withania_somnifera", ["neuroprotector", "hepatoprotector", "fertilidad", "antiinflamatorio", "inmunomodulador",
                                 "antioxidante", "adaptogeno", "ansiolitico", "antidepresivo"])],
    50: [("cibotium_barometz", ["antioxidante", "antiinflamatorio", "osteogenico"])],
    51: [(e, ["antimicrobiano", "antioxidante", "sedante", "antidepresivo", "antidiabetico"])
         for e in ("lagerstroemia_speciosa", "lagerstroemia_caudata", "lagerstroemia_indica")],
    52: [("capsicum_annuum", ["antibacteriano", "antioxidante"])],
}
# Actividades que el articulo atribuye a metabolitos concretos (nombre tal como aparece en el texto)
ACT_METABOLITO: dict[int, list[tuple[str, list[str]]]] = {
    1: [("Chlorogenic acid", ["antifungico", "antioxidante", "neuroprotector", "hipolipemiante", "antiinflamatorio"])],
    8: [("Rubiadin", ["hepatoprotector"]), ("Alizarin", ["anticancerigeno"]), ("Mollugin", ["anticancerigeno", "neuroprotector"]),
        ("Loganin", ["neuroprotector"]), ("Isorhamnetin 3-galactoside", ["antioxidante"]), ("Aschantin", ["antioxidante"]),
        ("Chalcomoracin", ["antioxidante"])],
    10: [("Alloaromadendrene", ["antibacteriano"]), ("L-Carnitine", ["antimicrobiano"]), ("Polygodial", ["antimicrobiano"])],
    12: [("Vitexin", ["antioxidante"]), ("Caffeic acid", ["antiviral"])],
    13: [("Violanthin", ["antioxidante"]), ("Cyanidin", ["antioxidante"]), ("Methyl hesperidin", ["antioxidante"])],
    14: [("Atractylenolide III", ["antiinflamatorio", "gastroprotector", "neuroprotector"]), ("Oleanolic acid", ["hepatoprotector"]),
         ("Echinocystic acid", ["antiinflamatorio", "antioxidante", "analgesico"])],
    17: [("Gallic acid", ["anticancerigeno"])],
    19: [("Forsythiaside", ["antioxidante"]), ("Leucodelphinidin", ["antioxidante"])],
    23: [("Momordicin I", ["antialimentario"])],
    24: [("Gastrodin", ["antidepresivo", "neuroprotector"]), ("Gastrodin B", ["neuroprotector"]), ("4-Hydroxybenzyl alcohol", ["antidepresivo"])],
    27: [("Ricinoleic acid", ["analgesico", "antiinflamatorio"]), ("Dihydrosphingosine", ["antiinflamatorio", "antimicrobiano"]),
         ("Luteolin", ["anticancerigeno", "antiinflamatorio", "antidiabetico", "antioxidante", "neuroprotector"]),
         ("Epigallocatechin", ["antiinflamatorio", "antioxidante"])],
    31: [("Dihydromyricetin", ["antiinflamatorio", "antihipertensivo", "hipolipemiante"])],
    37: [("Gambogic acid", ["anticancerigeno"]), ("1,5-Diferuloylquinic acid", ["antioxidante"])],
    40: [("Piptamine", ["antimicrobiano", "antifungico"]), ("Resorcinol", ["antimicrobiano", "antifungico"])],
    42: [("Glabridin", ["antiinflamatorio", "antioxidante", "anticancerigeno", "antimicrobiano", "osteogenico", "cardioprotector",
                        "neuroprotector", "hepatoprotector", "antiobesidad", "antidiabetico"])],
    48: [("Taxifolin", ["antioxidante"]), ("Tricetiflavan", ["antiviral"]), ("Rhoifolin", ["antiinflamatorio"]),
         ("Echinatin", ["hepatoprotector", "antioxidante", "antiinflamatorio"]), ("Quercetagetin-7-O-glucoside", ["antioxidante"]),
         ("Kaempferol-3-O-rhamnoside", ["antiinflamatorio"]), ("Quercetin 3-O-neohesperidoside", ["antimicrobiano"])],
}
# Mediciones experimentales del articulo: (lote, grupo de muestras, actividad, ensayo, valor, unidad, fuente)
MEDICIONES: list[tuple[int, str, str, str, float | None, str, str]] = []
for g, var, d50, a50, dp, ap in [("A", "TW", 0.36, 0.17, 67.6, 82.3), ("B", "XY", 0.25, 0.13, 72.3, 86.6),
                                 ("C", "MX", 1.02, 0.31, 51.9, 74.4), ("D", "ZC", 0.72, 0.23, 57.4, 80.1)]:
    f = f"Tabla 1 y Figura 2 (variedad {var}; asignacion de la letra {g} por el orden del articulo)"
    MEDICIONES += [(16, g, "antioxidante", "DPPH IC50", d50, "mg/mL", f), (16, g, "antioxidante", "ABTS IC50", a50, "mg/mL", f),
                   (16, g, "antioxidante", "DPPH captacion a 1 mg/mL", dp, "%", f), (16, g, "antioxidante", "ABTS captacion a 1 mg/mL", ap, "%", f)]
for g, v in [("FDP", 608.83), ("HDP", 552.89), ("FSP", 423.21), ("FD", 372.78), ("FS", 268.87), ("HD", 209.82)]:
    MEDICIONES.append((17, g, "antioxidante", "DPPH", v, "ug TE/g", "Figura 6"))
MEDICIONES += [(18, "JY", "antioxidante", "FRAP", 0.49, "mM", "Seccion de actividad antioxidante"),
               (18, "CK", "antioxidante", "FRAP", 0.42, "mM", "Seccion de actividad antioxidante"),
               (18, "JY", "antioxidante", "ABTS (TEAC)", 0.68, "mM Trolox", "Seccion de actividad antioxidante"),
               (18, "CK", "antioxidante", "ABTS (TEAC)", 0.42, "mM Trolox", "Seccion de actividad antioxidante"),
               (19, "January", "antioxidante", "DPPH IC50 (extracto etanolico)", 0.133, "mg/mL", "Seccion 2.3.2"),
               (19, "January", "antioxidante", "ABTS IC50 (extracto etanolico)", 0.062, "mg/mL", "Seccion 2.3.2"),
               (19, "January", "antiinflamatorio", "Inhibicion de COX-2 IC50", 16.41, "ug/mL", "Seccion 2.3.3")]
for g, ab, fr, dp, ic in [("S1", 90.09, 164.66, 97.88, 0.81), ("S2", 20.68, 44.90, 33.35, 2.82),
                          ("S3", 8.70, 11.58, 20.47, 10.89), ("S4", 5.56, 11.99, 15.34, 11.45)]:
    f = "Tabla 2 (asignacion ABTS/DPPH segun el orden de columnas)"
    MEDICIONES += [(22, g, "antioxidante", "ABTS captacion", ab, "%", f), (22, g, "antioxidante", "FRAP", fr, "umol Trolox/g DW", f),
                   (22, g, "antioxidante", "DPPH captacion", dp, "%", f),
                   (22, g, "inhibidor_glucosidasa", "Inhibicion de alfa-glucosidasa IC50", ic, "mg/mL DW", "Tabla 2")]
for g, fr, ab in [("TB", 0.23, 1.10), ("TS", 3.44, 0.08), ("TA", 0.33, 1.12), ("TFL", 1.85, 0.14)]:
    MEDICIONES += [(32, g, "antioxidante", "FRAP", fr, "mmol/g extracto", "Tabla 1"), (32, g, "antioxidante", "ABTS", ab, "mmol/g extracto", "Tabla 1")]
MEDICIONES.append((50, "DY", "antioxidante", "DPPH", 613.4, "ug TE/g FW", "Figura 1G (orden DY > WL > LC > SG > GC)"))
for g, ab, dp, fr in [("CL4", 18.01, 48.90, 36.94), ("CL18", 21.72, 55.15, 51.19), ("CL40", 18.51, 49.57, 36.85), ("CL53", 23.24, 66.13, 72.60)]:
    MEDICIONES += [(51, g, "antioxidante", "ABTS captacion", ab, "%", "Figura 6A"), (51, g, "antioxidante", "DPPH captacion", dp, "%", "Figura 6B"),
                   (51, g, "antioxidante", "FRAP", fr, "umol Trolox/g DW", "Figura 6D")]
for g, orden in [("F", "1 (mayor)"), ("L", "2"), ("S", "3 (menor)")]:
    MEDICIONES.append((20, g, "antioxidante", f"DPPH/FRAP/ABTS (rango {orden}: flor > hoja > tallo)", None, "", "Resumen y seccion 3"))
MEDICIONES += [(37, "ET", "antioxidante", "DPPH y ABTS (ET > WA)", None, "", "Resumen"),
               (37, "WA", "antioxidante", "DPPH y ABTS (ET > WA)", None, "", "Resumen"),
               (25, "ZT99", "antioxidante", "DPPH/FRAP/ABTS (Zhaotong > Dandong)", None, "", "Resumen"),
               (25, "DD99", "antioxidante", "DPPH/FRAP/ABTS (Zhaotong > Dandong)", None, "", "Resumen")]

# ============================================================================================ lotes


@dataclass
class Hoja:
    """Como leer una hoja (o archivo de texto) de un lote."""
    hoja: Any = 0                      # nombre o indice de la hoja
    cabecera: int = 0                  # fila (0-based) con los nombres de columna
    cols: dict[str, str] = field(default_factory=dict)  # atributo estandar -> columna del archivo
    muestras: str = ""                 # regex de las columnas de intensidad
    excluir: str = r"(?!x)x"           # regex de columnas a excluir aunque coincidan
    modo: str = ""                     # modo por defecto de la hoja (POS, NEG, EI)
    rt_segundos: bool = False          # el tiempo de retencion viene en segundos
    fila_muestras: int | None = None   # fila con los nombres de muestra si difieren de la cabecera
    filas_meta: dict[str, int] = field(default_factory=dict)  # atributo -> fila con metadatos por columna
    saltar_si: dict[str, str] = field(default_factory=dict)   # columna -> regex de filas a descartar
    tecnica: str = ""                  # sobreescribe la tecnica del lote (p. ej. GC)
    instrumento: str = ""
    columna_crom: str = ""
    intensidad: str = ""
    nivel_defecto: Any = None          # nivel MSI si la hoja no lo trae (anotado)
    combinar: list[Any] = field(default_factory=list)  # hojas adicionales con la misma estructura (se unen)
    anotar_desde: list[Any] = field(default_factory=list)  # hojas con anotacion por ID (mismo formato de cols)
    cols_anotacion: dict[str, str] = field(default_factory=dict)
    clave_anotacion_modo: bool = False  # unir la anotacion por (ID, modo)
    filtro: tuple[str, str] | None = None  # (columna, regex) filas que se conservan
    modo_por_valor: dict[str, str] = field(default_factory=dict)  # valor de la columna modo -> POS/NEG/EI
    mapa_nivel: dict[str, int] = field(default_factory=dict)  # nivel del laboratorio -> nivel MSI


@dataclass
class Regla:
    patron: str
    attrs: dict[str, Any]


def R(patron: str, **attrs: Any) -> Regla:
    return Regla(patron, attrs)


QC = R(r"(?i)(^|[_\-\s])(all_)?QC|pooled|mix0\d|^mix", tipo="qc", grupo="QC")
BLANCO = R(r"(?i)blank|^ES\d|_ES\d|^\d+_PB|_PB_", tipo="blanco", grupo="Blanco")


@dataclass
class Lote:
    id: int
    articulo: int
    archivo: str
    hojas: list[Hoja]
    reglas: list[Regla]
    especie: str = ""
    parte: str = ""
    cultivo: str = ""
    ubicacion: str = ""
    extraccion: str = ""
    tecnica: str = "uhplc_rp"
    columna: str = ""
    instrumento: str = ""
    adquisicion: str = "dda"
    intensidad: str = "area"
    modos: str = ""
    fase_movil: str = ""
    flujo: str = ""
    voltaje: str = ""
    temp_fuente: str = ""
    cero_si_igual: float | None = None   # placeholder de no detectado (Metware usa 9)
    umbral_cero: float | None = None     # valores imputados minimos que se tratan como 0
    notas: str = ""
    metadatos_hoja: tuple[Any, str] | None = None  # (hoja, columna clave) con metadatos de muestra (Pisum)


LOTES: dict[int, Lote] = {}


def _lote(**kw: Any) -> None:
    lt = Lote(**kw)
    LOTES[lt.id] = lt


FA = "A: agua 0.1% acido formico; B: acetonitrilo 0.1% acido formico"
# Columnas estandar de las tablas Metware de MRM ampliamente dirigido
MW_MRM = dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular weight (Da)", formula="Formula", aducto="Ionization model",
              nombre="Compounds", superclase="Class I", clase="Class II", cas="CAS", nivel="Level", kegg="cpd_ID")
# Columnas estandar de las tablas Metware no dirigidas (TripleTOF, columna T3)
MW_T3 = dict(id="Index", modo="Mode", nombre="Compounds", superclase="Class I", clase="Class II", formula="Formula", mz="Q1 (Da)",
             masa="Molecular weight (Da)", rt="RT (min)", aducto="Adduct", error_ppm="Mass error", nivel="Level", puntaje="score",
             cas="CAS", pubchem="PubChem CID", hmdb="HMDB", metlin="Metlin", kegg="cpd_ID")
MZMINE = dict(id="row ID", mz="row m/z", rt="row retention time")

# ---- 1-2 Ilex guayusa
_ILEX_LOC = {"A": "ec_talag", "B": "ec_alto_pano", "C": "ec_alto_tena"}
_ILEX_NOM = {"A": "Talag", "B": "Alto Pano", "C": "Alto Tena", "+": "luz", "-": "sombra", "0": "temprana (4-6 anios)",
             "1": "media (6-8 anios)", "2": "tardia (8-10 anios)"}
_ILEX = [R(r"_MB_\d+_(?P<loc>[ABC])(?P<luz>[+\-])(?P<edad>[012])_(?P<rep>\d+)_", tipo="biologica",
           ubicacion=("loc", _ILEX_LOC), grupo="{loc}{luz}{edad}", replica="{rep}",
           tratamiento=lambda g: f"Chakra {_ILEX_NOM[g['loc']]}; exposicion a {_ILEX_NOM[g['luz']]}; edad {_ILEX_NOM[g['edad']]}"),
         R(r"_GC_\d+_(?P<f>[ABC012+\-])_", tipo="subqc", grupo="SubQC {f}",
           tratamiento=lambda g: f"Mezcla por factor: {_ILEX_NOM[g['f']]}"),
         R(r"POOLED_QC", tipo="qc", grupo="QC"), R(r"(^|_)PB_", tipo="blanco", grupo="Blanco de proceso")]
_comun_ilex = dict(articulo=1, especie="ilex_guayusa", parte="hoja", cultivo="agroforestal", ubicacion="", extraccion="ilex_acido",
                   columna="csh_c18_50x3", instrumento="xevo_g2xs", adquisicion="dda", intensidad="altura", fase_movil=FA,
                   flujo="0.5 mL/min", temp_fuente="100 C")
_ILEX_COLS = dict(nombre="Metabolite", nivel="Identification_level", clase="Class", superclase="Superclass")
_lote(id=1, archivo="BAT0001_ilex_guayusa_NEG.xlsx", modos="NEG", voltaje="2.5 kV", reglas=_ILEX, **_comun_ilex,
      hojas=[Hoja("Sheet 1", 10, dict(id="row_ID", mz="row_m_z", rt="row_retention_time", modo="Ion_Mode", **_ILEX_COLS),
                  muestras=r"^\d+_.*THOM", modo="NEG")])
_lote(id=2, archivo="BAT0002_ilex_guayusa_POS.xlsx", modos="POS", voltaje="0.5 kV", reglas=_ILEX, **_comun_ilex,
      notas="Se usa la hoja 'Hoja1' (tabla anotada con nivel de identificacion); las hojas Export_mzmine/Pos_1/Pos_2 son "
            "procesamientos alternativos de las mismas inyecciones.",
      hojas=[Hoja("Hoja1", 8, dict(id="row ID", mz="row m/z", rt="row retention time", modo="Ion Mode", **_ILEX_COLS),
                  muestras=r"^\d+_.*THOM", modo="POS")])
# ---- 3 Banisteriopsis caapi (in vitro, IKIAM)
_CAAPI = {"Non-organogenic meristems": ("meristemo", "Meristemo no organogenico"), "Organogenic meristem": ("meristemo", "Meristemo organogenico"),
          "Stem explant": ("explante_tallo", "Explante de tallo"), "Leaf explant": ("explante_hoja", "Explante de hoja"),
          "Callus": ("callo", "Callo")}
_lote(id=3, articulo=54, archivo="BAT0003_banisteriopsis_caapi_POS.xlsx", especie="banisteriopsis_caapi", cultivo="in_vitro",
      ubicacion="ec_ikiam", columna="rp_ne", instrumento="lcms_ne", intensidad="altura", modos="POS",
      reglas=[R(r"\|QC$", tipo="qc", grupo="QC"), R(r"\|Blank$", tipo="blanco", grupo="Blanco"),
              R(r"_R(?P<rep>\d)[A-Z]+\d*_pos.*\|(?P<g>.+)$", tipo="biologica", parte=lambda g: _CAAPI[g["g"]][0],
                grupo=lambda g: _CAAPI[g["g"]][1], replica="{rep}")],
      hojas=[Hoja("Hoja1", 4, dict(id="Mzmine_ID", mz="mass", rt="RT", nivel="IL", nombre="Metabolite", inchikey="InChIKey",
                                   nist="NIST_Number", superclase="classyfireR_Superclass", clase="classyfireR_class",
                                   subclase="classyfireR_subclass", clase2="Manual_class", modo="Ion Mode"),
                  muestras=r"_pos$", modo="POS", filas_meta={"grupo": 0}, nivel_defecto=2)])
# ---- 4 Piper peltatum (GC-MS, IKIAM)
_lote(id=4, articulo=55, archivo="BAT0004_piper_peltatum_EI.xlsx", especie="piper_peltatum", parte="hoja", ubicacion="ec_ikiam",
      tecnica="gc", columna="gc_ne", instrumento="gcms_ne", adquisicion="gc_scan", intensidad="altura", modos="EI",
      reglas=[R(r"_(?P<e>[FS])(?P<s>[HM])_PP_(?P<rep>\d)$", tipo="biologica", grupo="{e}{s}", replica="{rep}",
                extraccion=("s", {"H": "agua_piper", "M": "metanol_100"}),
                tratamiento=lambda g: ("Hoja fresca" if g["e"] == "F" else "Hoja seca") + (", extracto acuoso" if g["s"] == "H" else ", extracto metanolico")),
              R(r"(?i)QC_(MetOH|H2?0|H2O)", tipo="subqc", grupo="QC por solvente"), R(r"(?i)QC_pooled", tipo="qc", grupo="QC"),
              R(r"(?i)Blank", tipo="blanco", grupo="Blanco de proceso")],
      hojas=[Hoja("Sheet_edited", 0, dict(id="Alignment ID", rt="Average Rt(min)", ri="Average RI", mz="Quant mass",
                                          nombre="Metabolite name", formula="Formula", clase="Ontology", inchikey="INCHIKEY",
                                          smiles="SMILES", puntaje="Total score"), muestras=r"^\d+_", modo="EI", nivel_defecto=2)])
# ---- 5-6 Malpighiaceae
_MALP = [R(r"(?i)^Blank", tipo="blanco", grupo="Blanco con estandar interno"), R(r"(?i)^QC", tipo="qc", grupo="QC"),
         R(r"^P(?P<p>\d)_(?P<w>[A-H]\d+)_(?P<g>[GB])(?P<c>[A-H]\d+)_", tipo="biologica", grupo="Serie {g}",
           replica="placa {p}, pozo {w}", tratamiento="Codigo de extracto {g}{c}")]
_comun_malp = dict(articulo=2, especie="malpighiaceae_spp", cultivo="silvestre", ubicacion="br", extraccion="etoh80_o_etoac",
                   columna="kinetex_c18_50", instrumento="maxis_impact", intensidad="area", fase_movil=FA, flujo="0.5 mL/min",
                   reglas=_MALP)
_lote(id=5, archivo="BAT0005_malpighiaceae_spp_POS.csv", modos="POS", **_comun_malp,
      hojas=[Hoja(0, 0, dict(MZMINE), muestras=r"^(Blank|QC|P\d_)", modo="POS")])
_lote(id=6, archivo="BAT0006_malpighiaceae_spp_NEG.csv", modos="NEG", **_comun_malp,
      hojas=[Hoja(0, 0, dict(MZMINE), muestras=r"^(Blank|QC|P\d_)", modo="NEG")])
# ---- 7 Pisum sativum (metadatos en hoja 'Metadata')
_lote(id=7, articulo=3, archivo="BAT0007_pisum_sativum_POS.xlsx", especie="pisum_sativum", parte="semilla", extraccion="metanol_80",
      columna="intensity_solo_c18", instrumento="impact_ii", intensidad="area", modos="POS", metadatos_hoja=("Metadata", "filename"),
      reglas=[R(r"^QC", tipo="qc", grupo="QC"), R(r"ES\d", tipo="blanco", grupo="Blanco de extraccion"),
              R(r"\|Sample\|(?P<cv>[^|]+)\|(?P<loc>[^|]+)\|(?P<rep>[\d.]+)$", tipo="biologica", grupo="{cv} - {loc}",
                replica=lambda g: str(int(float(g["rep"]))), ubicacion=("loc", {"Sejet": "dk_sejet", "Gamborg": "dk_gamborg", "Hammel": "dk_hammel"}),
                cultivo=("loc", {"Sejet": "campo", "Gamborg": "campo", "Hammel": "organico"}), tratamiento="Cultivar {cv}; sitio {loc}")],
      hojas=[Hoja("Metaboscape", 0, dict(id="Feature_ID", nombre="Name", rt="RT [min]", mz="m/z meas.", masa="M meas.", aducto="Ions",
                                         formula="Molecular Formula", puntaje="MS/MS score", fuente_anot="Annotation Source"),
                  muestras=r"_\d+_1_\d{4}$", modo="POS", nivel_defecto=2,
                  anotar_desde=["SIRIUS"], cols_anotacion=dict(id="Feature_ID", superclase="ClassyFire#superclass",
                                                                clase="ClassyFire#class", subclase="ClassyFire#most specific class",
                                                                inchikey2d="InChIkey2D", smiles="smiles"))])
# ---- 8 Solanum tuberosum
_lote(id=8, articulo=5, archivo="BAT0008_solanum_tuberosum_POS_NEG.xlsx", especie="solanum_tuberosum", parte="hoja", cultivo="campo",
      ubicacion="cn_ulanqab", columna="premier_hss_t3", instrumento="tripletof_6600_exion", modos="POS/NEG", fase_movil=FA,
      flujo="0.4 mL/min", temp_fuente="500 C",
      reglas=[QC, R(r"^TQW-(?P<rep>\d)", tipo="biologica", grupo="TQW", replica="{rep}", extraccion="solanum_crudo", tratamiento="Extracto crudo"),
              R(r"^CHW-(?P<rep>\d)", tipo="biologica", grupo="CHW", replica="{rep}", extraccion="solanum_spe", tratamiento="Extracto purificado en SPE C18")],
      hojas=[Hoja("Sheet1", 0, dict(MW_T3), muestras=r"^(TQW|CHW)-\d|^QC\d")])
# ---- 9-10 Oldenlandia
_OLD_T = {"R": "raiz", "S": "tallo", "L": "hoja", "Fl": "flor", "Fr": "fruto"}
_OLD = [QC, R(r"^(?P<sp>OLD|OLC)_(?P<t>Fl|Fr|R|S|L)(?P<rep>\d)$", tipo="biologica",
              especie=("sp", {"OLD": "oldenlandia_diffusa", "OLC": "oldenlandia_corymbosa"}), parte=("t", _OLD_T),
              grupo="{sp}_{t}", replica="{rep}")]
_MAF = dict(mwdb="database_identifier", formula="chemical_formula", smiles="smiles", inchi="inchi", nombre="metabolite_identification",
            mz="mass_to_charge", aducto="modifications")
_comun_old = dict(articulo=6, cultivo="campo", ubicacion="cn_xinzhou_hubei", extraccion="metanol_70", columna="sb_c18",
                  instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", fase_movil=FA, flujo="0.35 mL/min",
                  temp_fuente="500 C", reglas=_OLD, cero_si_igual=9)
_lote(id=9, archivo="BAT0009_oldenlandia_spp_NEG.xlsx", modos="NEG", **_comun_old,
      hojas=[Hoja("Metabolite profiling", 0, dict(_MAF), muestras=r"^(OLD|OLC)_|^QC\d", modo="NEG", nivel_defecto=2)])
_lote(id=10, archivo="BAT0010_oldenlandia_spp_POS.xlsx", modos="POS", **_comun_old,
      hojas=[Hoja("Metabolite profiling", 0, dict(_MAF), muestras=r"^(OLD|OLC)_|^QC\d", modo="POS", nivel_defecto=2)])
# ---- 11 Garcinia oblongifolia
_lote(id=11, articulo=7, archivo="BAT0011_garcinia_oblongifolia_POS_NEG.xlsx", especie="garcinia_oblongifolia", cultivo="silvestre",
      ubicacion="cn_lingshui", extraccion="metanol_agua_3_1", columna="hss_t3", instrumento="exploris_120", intensidad="normalizada",
      modos="POS/NEG", fase_movil="A: acetato de amonio 5 mM y acido acetico 5 mM en agua; B: acetonitrilo",
      reglas=[R(r"^LS_GO_3_(?P<arbol>\d+)_(?P<t>L|S|B|FR)$", tipo="biologica", parte=("t", {"L": "hoja", "S": "rama", "B": "corteza", "FR": "fruto"}),
                grupo="{t}", replica="arbol {arbol}")],
      hojas=[Hoja(0, 1, dict(nombre="MS2 name_x", puntaje="MS2 score", kegg="KEGG COMPOUND ID", superclase="Super.Class", clase="Class",
                             subclase="Sub.Class", rt="rt", mz="mz", modo="type"), muestras=r"^LS_GO_", rt_segundos=True, nivel_defecto=2)])
# ---- 12 Rubia spp.
_RUB_SP = {"Q": "rubia_cordifolia", "X": "rubia_yunnanensis", "Z": "rubia_wallichiana", "DY": "rubia_schumanniana", "D": "rubia_magna"}
_RUB_UB = {"Q": "cn_anguo", "X": "cn_kunming", "DY": "cn_sichuan_herbal", "D": "cn_hekang"}
_lote(id=12, articulo=8, archivo="BAT0012_rubia_spp_POS_NEG.xlsx", parte="raiz_rizoma", cultivo="comercial", extraccion="metanol_acn_agua",
      columna="kinetex_c18_100_26", instrumento="exploris_120", modos="POS/NEG",
      fase_movil="A: acido acetico 0.01% en agua; B: 2-propanol:acetonitrilo 1:1",
      reglas=[QC, R(r"^(?P<sp>DY|D|Q|X|Z)_(?P<rep>\d)$", tipo="biologica", especie=("sp", _RUB_SP), grupo="{sp}", replica="{rep}",
                    ubicacion=lambda g: _RUB_UB.get(g["sp"]) or {"1": "cn_ningxia", "2": "cn_tibet", "3": "cn_tibet"}[g["rep"]])],
      hojas=[Hoja("Table S1", 1, dict(nombre="Name", formula="Formula", cas="CAS", inchikey="InChIKey", kegg="KEGG id", hmdb="HMDB id",
                                      superclase="Class", clase="Subclass", puntaje="Score", mz="Measured mass (m/z)",
                                      rt="Retention time (s)", error_ppm="ppm", modo="Type", aducto="ms2Adduct", nivel="level"),
                  muestras=r"^(DY|D|Q|X|Z)_\d$|^QC\d", rt_segundos=True)])
# ---- 13 Pinellia pedatisecta
_lote(id=13, articulo=9, archivo="BAT0013_pinellia_pedatisecta_POS_NEG.xlsx", especie="pinellia_pedatisecta", cultivo="invernadero",
      ubicacion="cn_wuhan_bg", extraccion="metanol_80_frio", columna="rp_ne", instrumento="orbitrap_ne", modos="POS/NEG",
      reglas=[R(r"^(?P<t>[LST])0?(?P<rep>\d)$", tipo="biologica", parte=("t", {"L": "hoja", "S": "tallo", "T": "tuberculo"}), grupo="{t}", replica="{rep}")],
      hojas=[Hoja("Table S1", 1, dict(id="Compound_ID", nombre="Name", formula="Formula", masa="Molecular Weight", rt="RT [min]", mz="m/z",
                                      superclase="HMDB_Superclass", clase="HMDB_Class", subclase="HMDB_Subclass"),
                  muestras=r"^[LST]\d\d$", nivel_defecto=2)])
# ---- 14 Pogostemon cablin
_POGO = dict(nombre="MS2_name", rt="RT", mz="m/z", superclase="SuperClass", clase="Class", subclase="SubClass", cas="CAS", hmdb="HMDB", kegg="C_ID")
_lote(id=14, articulo=10, archivo="BAT0014_pogostemon_cablin_POS_NEG.xlsx", especie="pogostemon_cablin", parte="hoja", cultivo="controlado",
      ubicacion="cn_guangzhou", extraccion="metanol_acn_agua", tecnica="uhplc_hilic", columna="beh_hilic", instrumento="tripletof_6600_agilent",
      modos="POS/NEG", fase_movil="A: acetato de amonio 25 mM e hidroxido de amonio 25 mM en agua; B: acetonitrilo", temp_fuente="600 C",
      reglas=[QC, R(r"^CK-(?P<rep>\d)$", tipo="biologica", grupo="CK", replica="{rep}", tratamiento="Hojas sanas (control con agua esteril)"),
              R(r"^LD-TJ-(?P<rep>\d)$", tipo="biologica", grupo="LD-TJ", replica="{rep}", tratamiento="Hojas inoculadas con Corynespora cassiicola")],
      hojas=[Hoja("Table S2", 1, dict(_POGO), muestras=r"^(CK|LD-TJ|QC)-\d$", modo="POS", nivel_defecto=2),
             Hoja("Table S3", 1, dict(_POGO), muestras=r"^(CK|LD-TJ|QC)-\d$", modo="NEG", nivel_defecto=2)])
# ---- 15 Nicotiana tabacum
_TAB = {"NT": "natural", "MC": "mecanico", "AC": "aire acondicionado"}
_lote(id=15, articulo=11, archivo="BAT0015_nicotiana_tabacum_POS_NEG.xlsx", especie="nicotiana_tabacum", parte="hoja", cultivo="almacen",
      ubicacion="cn_wuhan", extraccion="metanol_80_frio", columna="hypersil_gold", instrumento="exploris_120", modos="POS/NEG",
      flujo="0.2 mL/min", fase_movil="POS: A acido formico 0.1%, B metanol; NEG: A acetato de amonio 5 mM pH 9, B metanol",
      reglas=[QC, R(r"^CK-(?P<rep>\d)$", tipo="biologica", grupo="CK (T0)", replica="{rep}", tratamiento="Inicio del almacenamiento (T0)"),
              R(r"^(?P<c>NT|MC|AC)-(?P<t>T\d)-(?P<rep>\d)$", tipo="biologica", grupo="{c}-{t}", replica="{rep}",
                tratamiento=lambda g: f"Almacenamiento {_TAB[g['c']]}, tiempo {g['t']} (T3 = 9 meses)")],
      hojas=[Hoja("Table S1", 2, dict(id="ID", nombre="Name", puntaje="Score", nivel="Level", superclase="Class_I", clase="Class_II",
                                      formula="Formula", mz="m/z", rt="RT [min]", cas="CAS", kegg="Kegg_ID", modo="Type"),
                  muestras=r"^(NT|MC|AC)-T\d-\d$|^CK-\d$|^QC\d", rt_segundos=True)])
# ---- 16 Platostoma palustre (Mesona chinensis)
_PLAT = {"A": "TW", "B": "XY", "C": "MX", "D": "ZC"}
_PLAT_N = {"TW": "Taiwan", "XY": "Xiaoye", "MX": "Minxuan", "ZC": "Zengcheng"}
_lote(id=16, articulo=12, archivo="BAT0016_platostoma_chinense_POS.xlsx", especie="platostoma_palustre", parte="parte_aerea", cultivo="campo",
      ubicacion="cn_wuping", extraccion="metanol_80_frio", columna="xselect_hss_t3", instrumento="qtrap_6500_plus", adquisicion="mrm_quasi",
      intensidad="area_mrm", modos="POS", fase_movil=FA, flujo="0.4 mL/min",
      reglas=[QC, R(r"^all_(?P<g>[A-D])_(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}",
                    tratamiento=lambda g: f"Variedad {g['g']} (por el orden del articulo: {_PLAT_N[_PLAT[g['g']]]} {_PLAT[g['g']]})")],
      hojas=[Hoja("Sheet1", 0, dict(id="ID", nombre="Name", sinonimo="Chinese name", formula="Formula", masa="Molecular Weight", rt="RT [min]",
                                    superclase="Class I(English)", clase="Class II(English)", cas="CAS", hmdb="HMDB ID", kegg="KEGG ID",
                                    lipidmaps="Lipidmaps ID"), muestras=r"^all_", nivel_defecto=2)])
# ---- 17 Eriobotrya japonica
_ERIO = {"FS": ("metanol_80", "Flor fresca refrigerada (4 C)"), "HD": ("metanol_80", "Flor secada con calor (60 C, 6 h)"),
         "FD": ("metanol_80", "Flor liofilizada"), "FSP": ("eriobotrya_polvo", "Polvo de extracto acuoso de flor fresca"),
         "HDP": ("eriobotrya_polvo", "Polvo de extracto acuoso de flor secada con calor"), "FDP": ("eriobotrya_polvo", "Polvo de extracto acuoso de flor liofilizada")}
_lote(id=17, articulo=13, archivo="BAT0017_eriobotrya_japonica_POS.xlsx", especie="eriobotrya_japonica", parte="flor", cultivo="campo",
      ubicacion="cn_yongshan", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil=FA, flujo="0.35 mL/min", temp_fuente="500 C", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<g>FSP|HDP|FDP|FS|HD|FD)(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}",
                    extraccion=lambda g: _ERIO[g["g"]][0], tratamiento=lambda g: _ERIO[g["g"]][1])],
      hojas=[Hoja("Table S1", 0, dict(MW_MRM), muestras=r"^(FSP|HDP|FDP|FS|HD|FD)\d$|^QC\d", excluir=r"_vs_")])
# ---- 18 Codonopsis pilosula
_lote(id=18, articulo=14, archivo="BAT0018_codonopsis_pilosula_POS.xlsx", especie="codonopsis_pilosula", cultivo="campo",
      ubicacion="cn_changzhi", extraccion="metanol_80_is", columna="beh_c18", instrumento="qe_hfx_waters", intensidad="log10",
      modos="POS/NEG", fase_movil=FA, flujo="0.40 mL/min",
      reglas=[R(r"^JY(?P<rep>\d)$", tipo="biologica", parte="parte_aerea", grupo="JY", replica="{rep}", tratamiento="Tallos y hojas (residuo agricola)"),
              R(r"^CK(?P<rep>\d)$", tipo="biologica", parte="raiz", grupo="CK", replica="{rep}", tratamiento="Raices (material medicinal)")],
      hojas=[Hoja("Table S1", 1, dict(id="Metab ID", modo="Mode", mz="M/Z"), muestras=r"^(JY|CK)\d$")])
# ---- 19 Spatholobus suberectus
_lote(id=19, articulo=15, archivo="BAT0019_spatholobus_suberectus_POS_NEG.xlsx", especie="spatholobus_suberectus", parte="hoja",
      cultivo="campo", ubicacion="cn_nanning", extraccion="metanol_70", columna="premier_hss_t3", instrumento="tripletof_6600_exion",
      modos="POS/NEG", flujo="0.4 mL/min", temp_fuente="550 C",
      reglas=[R(r"^(?P<m>January|March|May|July|September|November)_(?P<rep>\d)$", tipo="biologica", grupo="{m}", replica="{rep}",
                tratamiento="Cosecha de {m}")],
      hojas=[Hoja("Sheet1", 0, dict(MW_T3), muestras=r"^(January|March|May|July|September|November)_\d$")])
# BioDeep (BAT0020, BAT0047) llama nivel 1 a la coincidencia de MS/MS con bibliotecas (= MSI II) y nivel 2 a MetaDNA
_BIODEEP = {"1": 2, "2": 3, "3": 3}
# ---- 20 Mosla chinensis (features en S4/S5, anotacion en S6-S8 por ID)
_MOSLA_ANOT = dict(id="ID", nombre="name", masa="exact_mass", error_ppm="ppm", formula="formula", aducto="precursor_type",
                   superclase="class", clase="sub_class", kegg="KEGG", cas="CAS", hmdb="hmdb", nivel="level", modo="posneg")
_lote(id=20, articulo=16, archivo="BAT0020_mosla_chinensis_POS.xlsx", especie="mosla_chinensis", cultivo="invernadero",
      ubicacion="cn_fenyi", extraccion="etanol_70_mosla", columna="hss_t3", instrumento="exploris_120", modos="POS/NEG", flujo="0.3 mL/min",
      reglas=[R(r"^MCJXR-(?P<t>[SLF])(?P<rep>\d)$", tipo="biologica", parte=("t", {"S": "tallo", "L": "hoja", "F": "flor"}), grupo="{t}", replica="{rep}")],
      hojas=[Hoja("Table S4", 1, dict(id="ID", mz="mz", rt="rtmin"), muestras=r"^MCJXR-", modo="POS",
                  anotar_desde=["Table S6", "Table S7", "Table S8"], cols_anotacion=_MOSLA_ANOT, clave_anotacion_modo=True,
                  mapa_nivel=_BIODEEP),
             Hoja("Table S5", 1, dict(id="ID", mz="mz", rt="rtmin"), muestras=r"^MCJXR-", modo="NEG",
                  anotar_desde=["Table S6", "Table S7", "Table S8"], cols_anotacion=_MOSLA_ANOT, clave_anotacion_modo=True,
                  mapa_nivel=_BIODEEP)])
# ---- 21 Fagopyrum dibotrys
_FAG = {"CS": "cn_shizhu", "CF": "cn_fuling", "YQ": "cn_qujing", "YK": "cn_kunming_campo", "GB": "cn_bijie"}
_lote(id=21, articulo=17, archivo="BAT0021_fagopyrum_dibotrys_POS_NEG.xls", especie="fagopyrum_dibotrys", parte="rizoma", cultivo="campo",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil=FA, cero_si_igual=9,
      reglas=[R(r"^(?P<o>CS|CF|YQ|YK|GB)-(?P<rep>\d)$", tipo="biologica", ubicacion=("o", _FAG), grupo="{o}", replica="{rep}",
                tratamiento="Zona de produccion {o}")],
      hojas=[Hoja("Supplementary Table 2", 1, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight (Da)", formula="Formula",
                                                    aducto="Ionization model", nombre="Compounds", superclase="Class"),
                  muestras=r"^(CS|CF|YQ|YK|GB)-\d$", nivel_defecto=2)])
# ---- 22 Akebia trifoliata
_lote(id=22, articulo=18, archivo="BAT0022_akebia_trifoliata_POS_NEG.xlsx", especie="akebia_trifoliata", parte="fruto", cultivo="germoplasma",
      ubicacion="cn_jiujiang", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely",
      intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[R(r"^S(?P<s>[1-4])-(?P<rep>\d)$", tipo="biologica", grupo="S{s}", replica="{rep}",
                tratamiento=lambda g: f"Estado S{g['s']} ({30 + 30 * int(g['s'])} dias tras plena floracion)")],
      hojas=[Hoja("Table S1", 1, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular weight (Da)", aducto="Ionization model",
                                      nombre="Compounds", superclase="Class", nivel="Level", kegg="cpd_ID"), muestras=r"^S[1-4]-\d$")])
# ---- 23 Ipomoea batatas (almacenamiento)
_lote(id=23, articulo=19, archivo="BAT0023_ipomoea_batatas_POS.xlsx", especie="ipomoea_batatas", parte="raiz_tuberosa", cultivo="campo",
      ubicacion="cn_enshi", extraccion="metanol_70_frio", columna="hss_t3", instrumento="tripletof_6600_exion", adquisicion="dia",
      modos="POS", fase_movil=FA, flujo="0.40 mL/min", temp_fuente="550 C",
      reglas=[R(r"^(?P<d>\d)d-(?P<rep>\d)$", tipo="biologica", grupo="{d} d", replica="{rep}", tratamiento="Batata 'Zifei' cortada, {d} dias de almacenamiento")],
      hojas=[Hoja("Sheet1", 1, dict(id="Index", nombre="Compounds", superclase="Class I", rt="RT (min)", aducto="Adduct"),
                  muestras=r"^\dd-\d$", modo="POS", nivel_defecto=2)])
# ---- 24 Polygonatum (solo tablas diferenciales por pares: se unen y se deduplican)
_POLY_SP = {"PS": "polygonatum_sibiricum", "PC": "polygonatum_cyrtonema", "PK": "polygonatum_kingianum", "PO": "polygonatum_odoratum"}
_POLY_UB = {"PS": "cn_hanzhong", "PC": "cn_taining", "PK": "cn_maguan", "PO": "cn_anhua"}
_POLY_COLS = dict(id="ID", mz="m/z", rt="Retention time (min)", modo="Ion mode", nombre="Metabolites", hmdb="Compound ID",
                  superclase="Super Class", clase="Class", subclase="Sub Class", nivel="level", kegg="kegg", puntaje="Score",
                  aducto="Adducts", formula="Formula", error_ppm="Mass Error (ppm)")
_lote(id=24, articulo=20, archivo="BAT0024_polygonatum_spp_POS.xlsx", parte="rizoma", cultivo="campo", extraccion="metanol_70",
      columna="hss_t3", instrumento="qe_ultimate", modos="POS/NEG", fase_movil="A: agua; B: acetonitrilo 0.1% acido formico", flujo="0.35 mL/min",
      notas="El archivo solo trae metabolitos diferenciales por pares de especies; se unen las seis tablas y se deduplica por ID.",
      reglas=[R(r"^(?P<sp>PS|PC|PK|PO)-(?P<rep>\d)$", tipo="biologica", especie=("sp", _POLY_SP), ubicacion=("sp", _POLY_UB),
                grupo="{sp}", replica="{rep}")],
      hojas=[Hoja("PS_PO", 1, dict(_POLY_COLS), muestras=r"^P[SCKO]-\d$", combinar=["PC_PO", "PK_PO", "PS_PK", "PC_PK", "PS_PC"])])
# ---- 25 Fragaria x ananassa
_FRA = {"ZT": ("cn_zhaotong_fresa", "'Akihime' cultivada en Zhaotong (1900 m)"), "ZT99": ("cn_zhaotong_fresa", "'Red Face' cultivada en Zhaotong (1900 m)"),
        "DD99": ("cn_dandong", "'Red Face' cultivada en Dandong (20 m)")}
_lote(id=25, articulo=21, archivo="BAT0025_fragaria_ananassa_POS_NEG.xlsx", especie="fragaria_ananassa", parte="fruto", cultivo="invernadero",
      extraccion="metanol_50_hcl", tecnica="hplc_rp", columna="vp_ods", instrumento="qtrap_4000", adquisicion="mrm_widely", intensidad="area_mrm",
      modos="POS/NEG", fase_movil="A: agua 0.04% acido acetico; B: acetonitrilo 0.04% acido acetico", flujo="0.25 mL/min", temp_fuente="500 C",
      cero_si_igual=9,
      reglas=[QC, R(r"^(?P<g>ZT99|DD99|ZT)-(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}",
                    ubicacion=lambda g: _FRA[g["g"]][0], tratamiento=lambda g: _FRA[g["g"]][1])],
      hojas=[Hoja("Raw Data", 0, dict(MW_MRM), muestras=r"^(ZT99|DD99|ZT)-\d$|^QC\d")])
# ---- 26 Medicago sativa
_lote(id=26, articulo=22, archivo="BAT0026_medicago_sativa_POS_NEG.xlsx", especie="medicago_sativa", parte="corona_raiz", cultivo="controlado",
      ubicacion="cn_incubadora_alfalfa", extraccion="metanol_agua_7_3_frio", columna="beh_c18", instrumento="waters_qtof", modos="POS/NEG",
      fase_movil=FA, flujo="0.40 mL/min",
      reglas=[QC, R(r"^(?P<w>WD|WW)_(?P<f>\d)_(?P<rep>\d)$", tipo="biologica", grupo="{w}_{f}", replica="{rep}",
                    tratamiento=lambda g: ("Deficit hidrico (25% de la capacidad de retencion)" if g["w"] == "WD" else "Riego adecuado (80%)") + f"; fase de frio {g['f']}")],
      hojas=[Hoja("sheet 1", 0, dict(id="ID", nombre="Metabolites", etiqueta="Compound", mz="m/z", rt="Retention time (min)", modo="Ion mode",
                                     hmdb="Compound ID", aducto="Adducts", formula="Formula", puntaje="Score", error_ppm="Mass Error (ppm)"),
                  muestras=r"^(WD|WW)_\d_\d$|^QC", excluir=r"RSD", saltar_si={"ID": r"^label$"}, nivel_defecto=2)])
# ---- 27 Camellia tetracocca (LC-MS y GC-MS; solo metabolitos diferenciales)
_CT = [R(r"^E(?P<rep>\d)$", tipo="biologica", grupo="E", replica="{rep}", tratamiento="Hojas atacadas por Empoasca onukii"),
       R(r"^N(?P<rep>\d)$", tipo="biologica", grupo="N", replica="{rep}", tratamiento="Hojas no atacadas")]
_lote(id=27, articulo=23, archivo="BAT0027_camellia_tetracocca_POS.xlsx", especie="camellia_tetracocca", parte="hoja", cultivo="campo",
      ubicacion="cn_puan", extraccion="metanol_agua_7_3_cloroformo", columna="beh_c18", instrumento="vion_imsqtof", modos="POS/NEG/EI",
      fase_movil=FA, flujo="0.35 mL/min", voltaje="2.5 kV", temp_fuente="115 C", reglas=_CT,
      notas="Las dos hojas contienen solo metabolitos diferenciales (VIP) entre hojas atacadas y no atacadas.",
      hojas=[Hoja("E_N", 0, dict(id="ID", mz="m/z", rt="Retention time (min)", modo="Ion mode", nombre="Metabolites", hmdb="HMDB",
                                 metlin="METLIN", lipidmaps="Lipidmaps", kegg="kegg", pubchem="PubChem", cas="CAS", superclase="Super Class",
                                 sinonimo="中文名称", clase="Class", subclase="Sub Class", nivel="level", puntaje="Score", aducto="Adducts",
                                 formula="Formula", error_ppm="Mass Error (ppm)"), muestras=r"^[EN]\d$"),
             Hoja("Sheet1", 0, dict(id="Alignment ID", rt="Average Rt(min)", ri="Average RI", mz="Quant mass", nombre="Metabolites",
                                    puntaje="Total score", hmdb="HMDB", superclase="Super Class", clase="Class", subclase="Sub Class",
                                    kegg="KEGG"), muestras=r"^[EN]\d$", modo="EI", tecnica="gc", instrumento="gcms_ne",
                  columna_crom="gc_ne", nivel_defecto=2)])
# ---- 28 Gastrodia elata
_GAS = {"GB": "Tianma negro (G. elata f. glauca)", "GR": "Tianma rojo (G. elata f. elata)", "GG": "Tianma verde (G. elata f. viridis)"}
_lote(id=28, articulo=24, archivo="BAT0028_gastrodia_elata_POS_NEG.xlsx", especie="gastrodia_elata", parte="tuberculo", cultivo="campo",
      ubicacion="cn_yiliang", extraccion="metanol_70_is", columna="hypersil_gold_aq", instrumento="orbitrap_ne", modos="POS/NEG",
      fase_movil=FA, flujo="0.35 mL/min",
      reglas=[R(r"^Area_(?P<g>GB|GR|GG)(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}", tratamiento=lambda g: _GAS[g["g"]])],
      hojas=[Hoja("Sheet1", 0, dict(id="Mode_ID", rt="RT [min]", masa="Molecular Weight", formula="Formula", nombre="Metabolite",
                                    hmdb="HMDB.ID", kegg="KEGG.ID", chemspider="ChemSpiderID", superclase="Super.class", clase="Class",
                                    subclase="Sub_class", clase2="Family"), muestras=r"^Area_", nivel_defecto=2)])
# ---- 29 Camellia sinensis (medias +/- DE por grupo)
_TEA = {"W": "blanca", "WP": "blanco-rosada", "P": "rosada", "E": "petalos externos", "I": "petalos internos"}
_lote(id=29, articulo=25, archivo="BAT0029_camellia_sinensis_POS_NEG.xlsx", especie="camellia_sinensis", parte="petalo", cultivo="silvestre",
      ubicacion="cn_wangmo", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="media_de",
      modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", temp_fuente="550 C",
      reglas=[R(r"^QC$", tipo="qc", grupo="QC"),
              R(r"^(?P<c>WP|W|P)(?P<p>[EI])$", tipo="media", grupo="{c}{p}", replica="media (n=3)",
                tratamiento=lambda g: f"Flor {_TEA[g['c']]}, {_TEA[g['p']]}")],
      hojas=[Hoja("Sheet1", 1, dict(id="NO.", masa="Molecular weight (Da)", formula="Formula", aducto="Ionization model", nombre="Compounds",
                                    superclase="Classfication", cas="CAS"), muestras=r"^(WE|WI|WPE|WPI|PE|PI|QC)$", nivel_defecto=2)])
# ---- 30 Morus alba (Mg)
_MG = {"CK": "3 mmol/L (optimo)", "T1": "0 mmol/L (deficiencia)", "T2": "1 mmol/L (bajo)", "T3": "2 mmol/L (bajo)", "T4": "6 mmol/L (alto)", "T5": "9 mmol/L (exceso)"}
_MORUS_MG = dict(id="index", nombre="MS2_name", nombre_ms1="MS1_name", formula="formula", rt="rtmin", mz="mz", superclase="Class", cas="CAS",
                 hmdb="HMDB", kegg="C_ID")
_lote(id=30, articulo=26, archivo="BAT0030_morus_alba_POS_NEG.xlsx", especie="morus_alba", parte="hoja", cultivo="controlado",
      ubicacion="cn_zhenjiang", extraccion="metanol_80_frio", columna="hypersil_gold", instrumento="qe_hfx_vanquish", modos="POS/NEG",
      fase_movil="A: agua 0.1% acido formico; B: metanol", flujo="0.2 mL/min",
      reglas=[QC, R(r"^(?P<t>CK|T\d)-(?P<rep>\d)$", tipo="biologica", grupo="{t}", replica="{rep}", tratamiento=lambda g: f"MgSO4 {_MG[g['t']]}")],
      hojas=[Hoja("all.exp.POS", 1, dict(_MORUS_MG), muestras=r"^(CK|T\d)-\d$|^QC\d", modo="POS", nivel_defecto=2),
             Hoja("all.exp.NEG", 1, dict(_MORUS_MG), muestras=r"^(CK|T\d)-\d$|^QC\d", modo="NEG", nivel_defecto=2)])
# ---- 31 Dioscorea opposita
_lote(id=31, articulo=27, archivo="BAT0031_dioscorea_opposita_POS_NEG.xlsx", especie="dioscorea_opposita", parte="tuberculo", cultivo="campo",
      ubicacion="cn_wen_county", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="area_mrm",
      modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", temp_fuente="550 C", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<s>SCY|LCY)(?P<rep>\d)$", tipo="biologica", grupo="{s}", replica="{rep}",
                    tratamiento=lambda g: "Suelo arenoso" if g["s"] == "SCY" else "Suelo de loess")],
      hojas=[Hoja("Table S1", 1, dict(MW_MRM), muestras=r"^(SCY|LCY|QC)\d$")])
# ---- 32 Taxus x media
_lote(id=32, articulo=28, archivo="BAT0032_taxus_media_POS_NEG.xlsx", especie="taxus_media", cultivo="campo", ubicacion="cn_zibo",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil="A: acido formico 0.1%; B: acetonitrilo 0.1% acido formico", flujo="0.35 mL/min", temp_fuente="550 C", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<t>TB|TFL|TS|TA)-(?P<rep>\d)$", tipo="biologica", parte=("t", {"TB": "corteza", "TFL": "hoja", "TS": "semilla", "TA": "arilo"}),
                    grupo="{t}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 1, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight (Da)", formula="Formula", aducto="Ionization model",
                                    nombre="Compounds", superclase="Class I", cas="CAS", nivel="Level"), muestras=r"^(TB|TFL|TS|TA)-\d$|^mix")])
# ---- 33 Camellia drupifera
_lote(id=33, articulo=29, archivo="BAT0033_camellia_drupifera_POS_NEG.xlsx", especie="camellia_drupifera", parte="hoja", cultivo="controlado",
      ubicacion="cn_guangzhou_zhongkai", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely",
      intensidad="normalizada", modos="POS/NEG", fase_movil="A: agua 0.1% acido formico; B: acetonitrilo 0.05% acido formico", flujo="0.35 mL/min",
      reglas=[R(r"^MWXS", tipo="qc", grupo="QC"), R(r"^(?P<t>CK|GZ2|GZ4)-(?P<rep>\d)$", tipo="biologica", grupo="{t}", replica="{rep}",
                                                     tratamiento=lambda g: {"CK": "Control sin aluminio", "GZ2": "AlCl3 2 mmol/L", "GZ4": "AlCl3 4 mmol/L"}[g["t"]])],
      hojas=[Hoja("shee1", 0, dict(id="Index", nombre="Compounds", superclase="Class", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight",
                                   modo="Ion mode", aducto="Ionization model", formula="Formula", kegg="cpd_ID", cas="CAS"),
                  muestras=r"^(CK|GZ2|GZ4)-\d$|^MWXS", nivel_defecto=2)])
# ---- 34 Avena sativa y Triticum aestivum
_AVT = {"dane": "avena_sativa", "otana": "avena_sativa", "choteau": "triticum_aestivum", "scholar": "triticum_aestivum",
        "conan": "triticum_aestivum", "reeder": "triticum_aestivum"}
_lote(id=34, articulo=30, archivo="BAT0034_avena_sativa_triticum_aestivum_NA.xlsx", parte="tallo", cultivo="invernadero",
      ubicacion="us_montana", extraccion="metanol_100", columna="kinetex_c18_150", instrumento="agilent_6538", modos="NA",
      fase_movil=FA, flujo="0.6 mL/min",
      notas="La tabla no indica el modo de ionizacion de cada senal.",
      reglas=[R(r"(?i)^(?P<cv>dane|otana|choteau|scholar|conan|reeder)(?P<s>[ic])(?P<rep>\d)$", tipo="biologica",
                especie=lambda g: _AVT[g["cv"].lower()], grupo=lambda g: f"{g['cv'].capitalize()} {'infestado' if g['s'].lower() == 'i' else 'control'}",
                replica="{rep}", tratamiento=lambda g: f"Cultivar {g['cv'].capitalize()}; " + ("infestado por Cephus cinctus" if g["s"].lower() == "i" else "control sin infestar"))],
      hojas=[Hoja("ST9. Oatwheat_complete_dataset", 0, dict(nombre="sample", mz="m/z", rt="retention time", formula="formula"),
                  muestras=r"(?i)^(dane|otana|choteau|scholar|conan|reeder)[ic]\d$", saltar_si={"sample": r"^status$"}, nivel_defecto=3)])
# ---- 35 Panax quinquefolius
_lote(id=35, articulo=31, archivo="BAT0035_panax_quinquefolius_POS_NEG.xlsx", especie="panax_quinquefolius", cultivo="campo",
      ubicacion="cn_wendeng", extraccion="metanol_formico", columna="rp_ne", instrumento="waters_qtof", modos="POS/NEG",
      fase_movil="A: agua 0.1% acido formico; B: acetonitrilo", flujo="0.2 mL/min",
      reglas=[R(r"^all_(?P<t>Root|Fibril|Stem1|Leaf)_(?P<rep>\d)$", tipo="biologica",
                parte=("t", {"Root": "raiz", "Fibril": "raiz_fina", "Stem1": "tallo", "Leaf": "hoja"}), grupo="{t}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 1, dict(id="Compound_ID", nombre="Name", formula="Formula", masa="Molecular Weight", rt="RT [min]", mz="m/z"),
                  muestras=r"^all_", nivel_defecto=2)])
# ---- 36 Morus alba (Mn)
_MN = {"CK": "0.15 mM (suficiencia)", "T0": "0 mM (deficiencia)", "T1": "0.03 mM (deficiencia)", "T2": "1.5 mM (toxicidad)", "T3": "3 mM (toxicidad)"}
_MORUS_MN = dict(id="index", nombre="MS2_name", rt="RT", mz="m/z", superclase="Class", cas="CAS", hmdb="HMDB", kegg="C_ID")
_lote(id=36, articulo=32, archivo="BAT0036_morus_alba_POS_NEG.xlsx", especie="morus_alba", parte="hoja", cultivo="invernadero",
      ubicacion="cn_zhenjiang", extraccion="metanol_acn_agua", columna="hss_t3", instrumento="tripletof_6600_agilent", modos="POS/NEG",
      fase_movil="POS: agua y acetonitrilo con 0.1% acido formico; NEG: A fluoruro de amonio 0.5 mM, B acetonitrilo", flujo="0.3 mL/min",
      temp_fuente="600 C",
      reglas=[QC, R(r"^(?P<t>CK|T\d)-(?P<rep>\d)$", tipo="biologica", grupo="{t}", replica="{rep}", tratamiento=lambda g: f"MnSO4 {_MN[g['t']]}")],
      hojas=[Hoja("POS ion mode ", 2, dict(_MORUS_MN), muestras=r"^(CK|T\d|QC)-\d$", modo="POS", rt_segundos=True, nivel_defecto=2),
             Hoja("NEG ion mode", 2, dict(_MORUS_MN), muestras=r"^(CK|T\d|QC)-\d$", modo="NEG", rt_segundos=True, nivel_defecto=2)])
# ---- 37 Neolamarckia cadamba (nombres de muestra en la fila bajo la cabecera)
_lote(id=37, articulo=33, archivo="BAT0037_neolamarckia_cadamba_POS_NEG.xlsx", especie="neolamarckia_cadamba", parte="fruto", cultivo="campo",
      ubicacion="cn_guangzhou_scau", columna="sb_c18", instrumento="qtrap_shimadzu", adquisicion="mrm_widely", intensidad="area_mrm",
      modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[QC, R(r"^WA(?P<rep>\d)$", tipo="biologica", grupo="WA", replica="{rep}", extraccion="agua_hirviendo", tratamiento="Extracto acuoso"),
              R(r"^ET(?P<rep>\d)$", tipo="biologica", grupo="ET", replica="{rep}", extraccion="etanol_70_cadamba", tratamiento="Extracto etanolico")],
      hojas=[Hoja("Table S2", 2, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight (Da)", formula="Formula",
                                      aducto="Ionization model", nombre="Compounds", superclase="Class", clase="Sub-class", cas="CAS", kegg="cpd_ID"),
                  muestras=r"^(WA|ET)\d$|^mix", fila_muestras=3, nivel_defecto=2)])
# ---- 38 Paeonia lactiflora
_PAE = {"CK": "'Fenyunu'", "DFG": "'Dafugui'", "HSML": "'Red Charm'"}
_lote(id=38, articulo=34, archivo="BAT0038_paeonia_lactiflora_POS_NEG.xlsx", especie="paeonia_lactiflora", parte="raiz_tuberosa",
      cultivo="germoplasma", ubicacion="cn_luoyang", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500",
      adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<c>CK|DFG|HSML)(?P<rep>\d)$", tipo="biologica", grupo="{c}", replica="{rep}", tratamiento=lambda g: f"Cultivar {_PAE[g['c']]}")],
      hojas=[Hoja("Sheet1", 0, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight (Da)", formula="Formula", aducto="Ionization model",
                                    nombre="Compounds", sinonimo="物质", superclase="Class I", clase="Class II", cas="CAS", nivel="Level", kegg="cpd_ID"),
                  muestras=r"^(CK|DFG|HSML)\d$|^mix")])
# ---- 39 Chrysanthemum x morifolium
_CHRY = {"FCF": "Capitulo fresco", "SCF": "Secado a la sombra", "DCF": "Secado en horno"}
_CHRY_COLS = dict(id="NO.", nombre="Metabolites", hmdb="Library ID", kegg="KEGG ID", modo="Ion mode", formula="Formula", mz="m/z",
                  rt="Retention time (min)", aducto="Adducts", error_ppm="Mass Error (ppm)", puntaje="Score")
_lote(id=39, articulo=35, archivo="BAT0039_chrysanthemum_morifolium_POS_NEG.xlsx", especie="chrysanthemum_morifolium", parte="capitulo",
      cultivo="campo", ubicacion="cn_bozhou", extraccion="metanol_70", columna="accucore_c18", instrumento="qe_plus_exion", modos="POS/NEG",
      fase_movil="Acetonitrilo y agua con 0.1% acido formico", flujo="0.20 mL/min", umbral_cero=1e-6,
      reglas=[QC, R(r"^(?P<g>FCF|SCF|DCF)(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="lote {rep}", tratamiento=lambda g: _CHRY[g["g"]])],
      hojas=[Hoja("Positive ion mode", 1, dict(_CHRY_COLS), muestras=r"^(FCF|SCF|DCF|QC)\d$", modo="POS", nivel_defecto=2),
             Hoja("Negative ion mode", 1, dict(_CHRY_COLS), muestras=r"^(FCF|SCF|DCF|QC)\d$", modo="NEG", nivel_defecto=2)])
# ---- 40 Rosaceae
_ROS_SP = {"H": "malus_pumila_medzwetzkyana", "T": "prunus_persica", "L": "prunus_cerasifera"}
_lote(id=40, articulo=36, archivo="BAT0040_rosaceae_spp_POS_NEG.xlsx", cultivo="campo", ubicacion="cn_taian", extraccion="metanol_70",
      columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG", fase_movil=FA,
      flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<sp>[HTL])(?P<t>[YF])-(?P<rep>\d)$", tipo="biologica", especie=("sp", _ROS_SP), parte=("t", {"Y": "hoja", "F": "fruto"}),
                    grupo="{sp}{t}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 0, dict(MW_MRM), muestras=r"^[HTL][YF]-\d$|^mix")])
# ---- 41 Ipomoea batatas (variedades)
_BAT41 = {"BS": "'Chestnut Potato' (pulpa blanca)", "CS": "'Watermelon Red No. 1' (pulpa naranja)", "ZS": "'Purple Potato' (pulpa morada)"}
_lote(id=41, articulo=37, archivo="BAT0041_ipomoea_batatas_POS_NEG.xlsx", especie="ipomoea_batatas", parte="raiz_tuberosa", cultivo="controlado",
      ubicacion="cn_enshi", extraccion="metanol_70_is", columna="hss_t3", instrumento="tripletof_6600_exion", modos="POS/NEG", fase_movil=FA,
      flujo="0.40 mL/min",
      reglas=[QC, R(r"^(?P<v>BS|CS|ZS)-(?P<rep>\d)$", tipo="biologica", grupo="{v}", replica="{rep}", tratamiento=lambda g: f"Variedad {_BAT41[g['v']]}")],
      hojas=[Hoja("Sheet1", 1, dict(MW_T3, pubchem="PubChem"), muestras=r"^(BS|CS|ZS)-\d$|^QC\d")])
# ---- 42 Sesamum indicum (contenido relativo medio por grupo)
_lote(id=42, articulo=38, archivo="BAT0042_sesamum_indicum_NA.xlsx", especie="sesamum_indicum", cultivo="campo", ubicacion="cn_zhumadian",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely", intensidad="contenido_relativo",
      modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min",
      reglas=[R(r"^QC$", tipo="qc", grupo="QC"),
              R(r"^(?P<t>FC|FS|ML|PF|WF)$", tipo="media", parte=("t", {"FC": "carpelo", "FS": "semilla", "ML": "hoja", "PF": "flor", "WF": "flor"}),
                grupo="{t}", replica="media",
                tratamiento=lambda g: {"FC": "Carpelos frescos", "FS": "Semillas frescas", "ML": "Hojas medias", "PF": "Flores purpuras", "WF": "Flores blancas"}[g["t"]])],
      hojas=[Hoja("Table S1.", 1, dict(id="Index", mz="Q1 (Da)", q3="Q3 (Da)", masa="Molecular Weight (Da)", formula="Formula",
                                       aducto="Ionization model", nombre="Compounds", superclase="Class", kegg="KEGG_ID"),
                  muestras=r"^(QC|FC|FS|ML|PF|WF)$", fila_muestras=2, nivel_defecto=2)])
# ---- 43 Dendrobium officinale
_DEN = {"SEC": ("epifito_roca", "Cultivo epifito sobre roca caliza (1152 m)"), "TEC": ("epifito_arbol", "Cultivo epifito sobre Schima superba (1136 m)"),
        "GC": ("invernadero", "Invernadero sobre corteza de pino (1120 m)")}
_lote(id=43, articulo=39, archivo="BAT0043_dendrobium_officinale_POS_NEG.xlsx", especie="dendrobium_officinale", parte="tallo",
      ubicacion="cn_anlong", extraccion="metanol_70_frio", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely",
      intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", temp_fuente="500 C", cero_si_igual=9,
      reglas=[R(r"^QC\d", tipo="qc", grupo="QC"),
              R(r"^(?P<c>SEC|TEC|GC)-(?P<rep>\d)$", tipo="biologica", grupo="{c}", replica="{rep}", cultivo=lambda g: _DEN[g["c"]][0],
                tratamiento=lambda g: _DEN[g["c"]][1])],
      hojas=[Hoja("Sheet1", 0, dict(MW_MRM), muestras=r"^(SEC|TEC|GC)-\d$|^QC\d")])
# ---- 44 Cormus domestica
_lote(id=44, articulo=40, archivo="BAT0044_cormus_domestica_POS_NEG.xlsx", especie="cormus_domestica", parte="fruto", cultivo="silvestre",
      ubicacion="it_campania", extraccion="etanol_agua_4_1_frio", columna="beh_c18", instrumento="qe_ultimate", modos="POS/NEG",
      fase_movil="A: agua 0.1% acido formico; B: metanol 0.1% acido formico", flujo="0.5 mL/min",
      notas="La tabla no trae m/z ni modo por senal (solo masa calculada).",
      reglas=[R(r"^T(?P<t>[012])_(?P<rep>\d)$", tipo="biologica", grupo="T{t}", replica="{rep}",
                tratamiento=lambda g: {"0": "Recien cosechado", "1": "Dos semanas poscosecha", "2": "Cuatro semanas poscosecha"}[g["t"]])],
      hojas=[Hoja("Foglio1", 1, dict(nombre="Compound", sinonimo="IUPAC", superclase="SUPERCLASS", clase="CLASS/SUBCLASS", formula="Formula",
                                     masa="Calc. MW", rt="RT [min]"), muestras=r"^T[012]_\d$", nivel_defecto=2)])
# ---- 45 Clematis tangutica
_CLE = {"JZ": "cn_jianzha", "MY": "cn_menyuan", "GH": "cn_gonghe", "DQ": "cn_da_qaidam", "ZD": "cn_zaduo"}
_CLE_ALT = {"JZ": 2060, "MY": 2641, "GH": 3191, "DQ": 3590, "ZD": 4252}
_lote(id=45, articulo=41, archivo="BAT0045_clematis_tangutica_POS_NEG.xlsx", especie="clematis_tangutica", parte="hoja", cultivo="silvestre",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil=FA, flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[QC, R(r"^(?P<s>JZ|MY|GH|DQ|ZD)-(?P<rep>\d)$", tipo="biologica", ubicacion=("s", _CLE), grupo="{s}", replica="{rep}",
                    tratamiento=lambda g: f"Poblacion a {_CLE_ALT[g['s']]} m")],
      hojas=[Hoja("All_sample_data", 0, dict(MW_MRM), muestras=r"^(JZ|MY|GH|DQ|ZD)-\d$|^QC\d")])
# ---- 46 Glycyrrhiza spp.
_GLY = {"Ginf": "glycyrrhiza_inflata", "Gura": "glycyrrhiza_uralensis", "Gpal": "glycyrrhiza_pallidiflora", "Gasp": "glycyrrhiza_aspera"}
_lote(id=46, articulo=42, archivo="BAT0046_glycyrrhiza_spp_POS_NEG.xlsx", parte="raiz", cultivo="germoplasma", ubicacion="cn_turpan",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      cero_si_igual=9,
      reglas=[QC, R(r"^(?P<sp>Ginf|Gura|Gpal|Gasp)_(?P<rep>\d)$", tipo="biologica", especie=("sp", _GLY), grupo="{sp}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 1, dict(MW_MRM, plataforma="Platform"), muestras=r"^(Ginf|Gura|Gpal|Gasp)_\d$|^QC\d")])
# ---- 47 Nelumbo nucifera (archivo nombrado lonicera_japonica)
_NEL = {"Flo": "flor", "Pet": "peciolo", "Rec": "receptaculo", "Sta": "estambre", "Sem": "semilla", "Plu": "plumula"}
_lote(id=47, articulo=43, archivo="BAT0047_lonicera_japonica_POS_NEG.xlsx", especie="nelumbo_nucifera", cultivo="campo", ubicacion="cn_nanchang",
      extraccion="metanol_is", columna="hss_t3", instrumento="qe_focus", modos="POS/NEG",
      fase_movil="POS: A agua 0.1% acido formico, B acetonitrilo 0.1% acido formico; NEG: A formiato de amonio 5 mM, B acetonitrilo", flujo="0.3 mL/min",
      notas="El archivo se llama lonicera_japonica pero contiene los seis tejidos del loto (ART0043).",
      reglas=[R(r"^(?P<t>Flo|Pet|Rec|Sta|Sem|Plu)(?P<rep>\d)$", tipo="biologica", parte=("t", _NEL), grupo="{t}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 0, dict(id="ID", nombre="name", mz="mz", rt="rt", masa="exact_mass", error_ppm="ppm", formula="formula",
                                    aducto="precursor_type", superclase="class", clase="sub_class", kegg="KEGG", cas="CAS", hmdb="hmdb",
                                    nivel="level", modo="posneg"), muestras=r"^(Flo|Pet|Rec|Sta|Sem|Plu)\d$", rt_segundos=True,
                  mapa_nivel=_BIODEEP)])
# ---- 48 Rhododendron (archivo nombrado lonicera_japonica; articulo sin PDF)
_RHO = {"Rtri": "rhododendron_triflorum", "Rfau": "rhododendron_faucium", "Rniv": "rhododendron_nivale", "Rstr": "rhododendron_strigillosum"}
_lote(id=48, articulo=53, archivo="BAT0048_lonicera_japonica_POS_NEG.xlsx", parte="petalo", cultivo="silvestre", ubicacion="cn_linzhi",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil=FA, flujo="0.35 mL/min", temp_fuente="500 C", cero_si_igual=9,
      notas="El archivo se llama lonicera_japonica pero contiene cuatro especies de Rhododendron (BASE DE DATOS GLOBAL, batch 48).",
      reglas=[QC, R(r"^(?P<sp>Rtri|Rfau|Rniv|Rstr)_(?P<rep>\d)$", tipo="biologica", especie=("sp", _RHO), grupo="{sp}", replica="{rep}")],
      hojas=[Hoja("Sheet1", 0, dict(nombre="Compounds", superclase="Class I", clase="Class II", formula="Formula", mz="Q1 (Th)", q3="Q3 (Th)",
                                    masa="Molecular weight (Da)", aducto="Ionization model", nivel="Level", cas="CAS", kegg="cpd_ID"),
                  muestras=r"^(Rtri|Rfau|Rniv|Rstr)_\d$|^QC\d")])
# ---- 49 Citrus reticulata (medias +/- DE por anio de envejecimiento)
_lote(id=49, articulo=44, archivo="BAT0049_citrus_reticulata_POS_NEG.xlsx", especie="citrus_reticulata", parte="pericarpio", cultivo="comercial",
      ubicacion="cn_neijiang", extraccion="metanol_70", columna="hss_t3", instrumento="tripletof_6600_exion", intensidad="media_de",
      modos="POS/NEG", fase_movil=FA, flujo="0.4 mL/min", temp_fuente="550 C",
      reglas=[R(r"^QC$", tipo="qc", grupo="QC"), R(r"^CCPY(?P<y>\d)$", tipo="media", grupo="CCPY{y}", replica="media (n=3)",
                                                  tratamiento="Cascara envejecida {y} anios")],
      hojas=[Hoja("Sheet1", 1, dict(MW_T3), muestras=r"^CCPY\d$|^QC$")])
# ---- 50 Actinidia
_KIW = {"LC": ("actinidia_arguta", "cn_dandong_kiwi", "'Maolvfeng'"), "DY": ("actinidia_arguta", "cn_dandong_kiwi", "'Danyang flat'"),
        "GC": ("actinidia_chinensis", "cn_weixin", "'Guichang'"), "WL": ("actinidia_chinensis", "cn_weixin", "silvestre"),
        "SG": ("actinidia_chinensis", "nz", "'SunGold'")}
_lote(id=50, articulo=45, archivo="BAT0050_actinidia_chinensis_POS_NEG.xlsx", parte="pulpa_fruto", extraccion="metanol_80", columna="sb_c18",
      instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min",
      temp_fuente="500 C", cero_si_igual=9,
      reglas=[R(r"^QC\d", tipo="qc", grupo="QC"),
              R(r"^(?P<v>LC|DY|GC|SG|WL)(?P<rep>\d)$", tipo="biologica", especie=lambda g: _KIW[g["v"]][0], ubicacion=lambda g: _KIW[g["v"]][1],
                cultivo=lambda g: "silvestre" if g["v"] == "WL" else "campo", grupo="{v}", replica="{rep}",
                tratamiento=lambda g: f"Variedad {_KIW[g['v']][2]}")],
      hojas=[Hoja("Table S1", 1, dict(MW_MRM), muestras=r"^(LC|DY|GC|SG|WL)\d$|^QC\d")])
# ---- 51 Camellia oleifera
_lote(id=51, articulo=46, archivo="BAT0051_camellia_oleifera_POS_NEG.xlsx", especie="camellia_oleifera", parte="semilla", cultivo="campo",
      ubicacion="cn_changshan", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_4500", adquisicion="mrm_widely",
      intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, cero_si_igual=9,
      reglas=[QC, R(r"^(?P<c>CL\d+)-(?P<rep>\d)$", tipo="biologica", grupo="{c}", replica="{rep}", tratamiento="Cultivar 'Changlin {c}'")],
      hojas=[Hoja("All metabolites", 0, {k: v for k, v in MW_MRM.items() if k not in ("nivel", "kegg")},
                  muestras=r"^CL\d+-\d$|^QC\d", nivel_defecto=2)])
# ---- 52 Striga asiatica
_STR = {"XB": "cn_xb", "BH": "cn_bh", "HLA": "cn_hla", "LH": "cn_lh", "ZQ": "cn_zq", "YQ": "cn_yq", "FS": "cn_fs"}
_lote(id=52, articulo=47, archivo="BAT0052_striga_asiatica_POS_NEG.xlsx", especie="striga_asiatica", parte="planta_entera", cultivo="silvestre",
      extraccion="metanol_agua_4_1_is", columna="hss_t3", instrumento="qe_hfx_waters", intensidad="log10", modos="POS/NEG",
      fase_movil="A: agua:acetonitrilo 95:5 con 0.1% acido formico; B: acetonitrilo:isopropanol:agua 47.5:47.5:5 con 0.1% acido formico",
      flujo="0.4 mL/min",
      reglas=[QC, R(r"^(?P<h>XB|BH|HLA|LH|ZQ|YQ|FS)(?P<rep>\d)$", tipo="biologica", ubicacion=("h", _STR), grupo="{h}", replica="{rep}",
                    tratamiento="Habitat {h}")],
      hojas=[Hoja("Sheet1", 1, dict(id="ID", nombre="Metabolite", kegg="KEGG Compound  ID", lipidmaps="Library ID", modo="Mode", mz="M/Z",
                                    aducto="Adducts", formula="Formula", rt="Retention time", puntaje="Fragmentation Score",
                                    error_ppm="Mass Error", cas="CAS ID", superclase="HMDB Superclass", clase="HMDB Class",
                                    subclase="HMDB Subclass"), muestras=r"^(XB|BH|HLA|LH|ZQ|YQ|FS)\d$|^QC\d", nivel_defecto=2)])
# ---- 53 Hemerocallis citrina
_lote(id=53, articulo=48, archivo="BAT0053_hemerocallis_citrina_POS_NEG.xlsx", especie="hemerocallis_citrina", cultivo="campo",
      ubicacion="cn_datong", extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely",
      intensidad="area_mrm", modos="POS/NEG", fase_movil=FA, flujo="0.35 mL/min", cero_si_igual=9,
      reglas=[R(r"^(?P<t>[FLSR])h(?P<rep>\d)$", tipo="biologica", parte=("t", {"F": "flor", "L": "hoja", "S": "tallo", "R": "raiz"}),
                grupo="{t}h", replica="{rep}")],
      hojas=[Hoja("Sheet1", 1, dict(id="#ID", formula="Formula", nombre="compounds", mz="Q1 (Da)", q3="Q3 (Da)", aducto="Ionization model",
                                    superclase="Class I", clase="Class II"), muestras=r"^[FLSR]h\d$", nivel_defecto=2)])
# ---- 54 Withania somnifera
_lote(id=54, articulo=49, archivo="BAT0054_withania_somnifera_POS_NEG.xlsx", especie="withania_somnifera", parte="raiz", cultivo="producto",
      ubicacion="in_aiia", extraccion="ripa_metanol", columna="thermo_c18_3um", instrumento="orbitrap_ne", modos="POS/NEG",
      fase_movil="A: acido formico 0.1%; B: acetonitrilo",
      reglas=[R(r"^Area: BR(?P<rep>\d)$", tipo="biologica", grupo="BR", replica="{rep}", tratamiento="Extracto comercial de raiz (tabletas)")],
      hojas=[Hoja("Sheet1", 0, dict(id="S.no", superclase="Major Class_Class_Subclass_PMDB ID_Metabolite", nombre="Metabolite", rt="RT [min]", kegg="KEGG ID",
                                    pmdb="PMDB ID", masa="Calc. MW", aducto="Reference Ion", mz="m/z", formula="Formula"),
                  muestras=r"^Area: BR\d$", nivel_defecto=3)])
# ---- 55 Cibotium barometz (archivo de texto separado por tabuladores)
_CIB = {"WP": ("silvestre", "Rizoma silvestre (bosque de reserva)"), "DM": ("campo", "Rizoma domesticado en campo"),
        "ZP": ("in_vitro", "Rizoma de cultivo de tejidos")}
_lote(id=55, articulo=50, archivo="BAT0055_cibotium_barometz_NA.xls", especie="cibotium_barometz", parte="rizoma", ubicacion="cn_fangchenggang",
      extraccion="metanol_acn_agua", columna="hss_t3", instrumento="exploris_120", intensidad="log10", modos="POS/NEG",
      fase_movil="POS: agua y acetonitrilo con 0.1% acido formico; NEG: A acetato de amonio 5 mM, B acetonitrilo", flujo="0.3 mL/min",
      notas="Los grupos WR, WS, WL y WN no se describen en el articulo (que solo compara WP, DM y ZP).",
      reglas=[R(r"^QC\d", tipo="qc", grupo="QC"),
              R(r"^(?P<g>WP|DM|ZP)_(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}", cultivo=lambda g: _CIB[g["g"]][0],
                tratamiento=lambda g: _CIB[g["g"]][1]),
              R(r"^(?P<g>WR|WS|WL|WN)_(?P<rep>\d)$", tipo="biologica", grupo="{g}", replica="{rep}", parte="", cultivo="",
                tratamiento="Grupo {g} (no descrito en el articulo)")],
      hojas=[Hoja("tsv", 0, dict(id="ID", nombre="Name", formula="Formula", aducto="Reference_Ion", rt="RT_min", mz="m/z", modo="Mode",
                                 puntaje="Total_score", hmdb="HMDBID", kegg="KEGGID", superclase="SuperClass", clase="Class",
                                 subclase="SubClass", cas="CASNo", inchikey="InChIKey"), muestras=r"^(WR|WS|WL|WN|WP|DM|ZP)_\d$|^QC\d",
                  nivel_defecto=2)])
# ---- 56 Lagerstroemia
_LAG = {"LS": "lagerstroemia_speciosa", "LC": "lagerstroemia_caudata", "LI": "lagerstroemia_indica"}
_lote(id=56, articulo=51, archivo="BAT0056_lagerstroemia_spp_POS_NEG.xlsx", parte="hoja", cultivo="campo", ubicacion="cn",
      extraccion="metanol_70", columna="sb_c18", instrumento="qtrap_exion", adquisicion="mrm_widely", intensidad="area_mrm", modos="POS/NEG",
      fase_movil=FA, flujo="0.35 mL/min", temp_fuente="500 C", cero_si_igual=9,
      reglas=[R(r"^QC\d", tipo="qc", grupo="QC"), R(r"^(?P<sp>LS|LC|LI)(?P<rep>\d)$", tipo="biologica", especie=("sp", _LAG), grupo="{sp}", replica="{rep}")],
      hojas=[Hoja("All data", 1, dict(MW_MRM), muestras=r"^(LS|LC|LI)\d$|^QC\d")])
# ---- 57 Capsicum annuum (LC-MS y GC-MS en la misma tabla)
_CAP = {"XX": "cn_xiangcheng", "PZ": "cn_pengzhou", "AY": "cn_anyue"}
_lote(id=57, articulo=52, archivo="BAT0057_capsicum_annuum_POS_NEG.xlsx", especie="capsicum_annuum", parte="fruto", cultivo="campo",
      extraccion="metanol_agua_7_3_frio", columna="hss_t3", instrumento="qe_plus_acquity", modos="POS/NEG/EI",
      fase_movil="A: agua 0.1% acido formico; B: acetonitrilo", flujo="0.35 mL/min",
      reglas=[QC, R(r"^(?P<s>XX|PZ|AY)-(?P<rep>\d)$", tipo="biologica", ubicacion=("s", _CAP), grupo="{s}", replica="{rep}", tratamiento="Region {s}")],
      hojas=[Hoja("Data", 0, dict(id="ID", mz="m/z", rt="Retention time (min)", modo="Ion mode", nombre="Metabolites", pubchem="cid",
                                  hmdb="HMDB", metlin="METLIN", lipidmaps="Lipidmaps", chebi="ChEBI", kegg="KEGG", cas="CAS", smiles="smiles",
                                  inchikey="InChIKey", superclase="Super Class", clase="Class", subclase="Sub Class", nivel="level",
                                  puntaje="Score", aducto="Adducts", formula="Formula", error_ppm="Mass Error (ppm)", ri="Average RI"),
                  muestras=r"^(XX|PZ|AY)-\d$|^QC\d", modo_por_valor={"LCMS-pos": "POS", "LCMS-neg": "NEG", "GCMS": "EI"})])


def rellenar(valor: Any, grupos: dict[str, str]) -> Any:
    """Resuelve el valor de un atributo de regla: literal con {grupo}, (grupo, mapa) o funcion."""
    if callable(valor):
        return valor(grupos)
    if isinstance(valor, tuple):
        g, mapa = valor
        return mapa.get(grupos.get(g, ""), "")
    if isinstance(valor, str):
        return valor.format(**{k: (v or "") for k, v in grupos.items()})
    return valor


def interpretar_muestra(lote: Lote, codigo: str) -> dict[str, Any] | None:
    """Aplica las reglas del lote al texto de la muestra; devuelve los atributos o None si ninguna regla aplica."""
    for regla in lote.reglas:
        m = re.search(regla.patron, codigo)
        if m:
            g = m.groupdict()
            return {k: rellenar(v, g) for k, v in regla.attrs.items()}
    return None
