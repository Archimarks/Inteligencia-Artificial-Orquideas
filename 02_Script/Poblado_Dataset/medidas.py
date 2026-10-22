# (batch, regex_codigo_muestra, actividad, ensayo, valor, unidad, fuente)
MEDIDAS = [
 (16,r'all_A_\d|A_\d','Antioxidante','DPPH IC50',0.36,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_B_\d|B_\d','Antioxidante','DPPH IC50',0.25,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_C_\d|C_\d','Antioxidante','DPPH IC50',1.02,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_D_\d|D_\d','Antioxidante','DPPH IC50',0.72,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_A_\d|A_\d','Antioxidante','ABTS IC50',0.17,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_B_\d|B_\d','Antioxidante','ABTS IC50',0.13,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_C_\d|C_\d','Antioxidante','ABTS IC50',0.31,'mg/mL','ART0012 Tabla 1'),
 (16,r'all_D_\d|D_\d','Antioxidante','ABTS IC50',0.23,'mg/mL','ART0012 Tabla 1'),
 (17,r'FS\d','Antioxidante','DPPH (equivalentes Trolox)',268.87,'ug TE/g','ART0013 Fig. 6'),
 (17,r'HD\d','Antioxidante','DPPH (equivalentes Trolox)',209.82,'ug TE/g','ART0013 Fig. 6'),
 (17,r'FD\d','Antioxidante','DPPH (equivalentes Trolox)',372.78,'ug TE/g','ART0013 Fig. 6'),
 (17,r'FSP\d','Antioxidante','DPPH (equivalentes Trolox)',423.21,'ug TE/g','ART0013 Fig. 6'),
 (17,r'HDP\d','Antioxidante','DPPH (equivalentes Trolox)',552.89,'ug TE/g','ART0013 Fig. 6'),
 (17,r'FDP\d','Antioxidante','DPPH (equivalentes Trolox)',608.83,'ug TE/g','ART0013 Fig. 6'),
 (18,r'JY\d','Antioxidante','FRAP',0.49,'mM Fe2+','ART0014 Sec. resultados'),
 (18,r'CK\d','Antioxidante','FRAP',0.42,'mM Fe2+','ART0014 Sec. resultados'),
 (18,r'JY\d','Antioxidante','ABTS (TEAC)',0.68,'mM Trolox','ART0014 Sec. resultados'),
 (18,r'CK\d','Antioxidante','ABTS (TEAC)',0.42,'mM Trolox','ART0014 Sec. resultados'),
]
MEDIDAS += [
 (19,r'January_\d','Antioxidante','DPPH IC50',0.133,'mg/mL','ART0015 Sec. 2.3'),
 (19,r'January_\d','Antioxidante','ABTS IC50',0.062,'mg/mL','ART0015 Sec. 2.3'),
 (19,r'January_\d','Antiinflamatorio','Inhibicion COX-2 IC50',16.41,'ug/mL','ART0015 Sec. 2.3'),
]
for g,(ab,dp,fr,ic) in {'S1':(97.88,90.09,164.66,0.81),'S2':(33.35,20.68,44.90,2.82),'S3':(20.47,8.70,11.58,10.89),'S4':(15.34,5.56,11.99,11.45)}.items():
    MEDIDAS += [(22,g+r'-\d','Antioxidante','ABTS (% captacion)',ab,'%','ART0018 Tabla 2'),
                (22,g+r'-\d','Antioxidante','DPPH (% captacion)',dp,'%','ART0018 Tabla 2'),
                (22,g+r'-\d','Antioxidante','FRAP',fr,'umol Trolox/g DW','ART0018 Tabla 2'),
                (22,g+r'-\d','Antidiabetico','Inhibicion alfa-glucosidasa IC50',ic,'mg/mL','ART0018 Tabla 2')]
MEDIDAS += [
 (25,r'ZT99-\d','Antioxidante','DPPH (% captacion)',65.34,'%','ART0021 Fig. 6'),
 (25,r'ZT99-\d','Antioxidante','Capacidad antioxidante (equivalentes Trolox)',91.39,'mM TE/100 mg','ART0021 Fig. 6'),
 (25,r'ZT99-\d','Antioxidante','FRAP',27.76,'mmol Fe2+/g','ART0021 Fig. 6'),
 (25,r'ZT99-\d','Antioxidante','ABTS (% captacion)',79.92,'%','ART0021 Fig. 6'),
 (25,r'DD99-\d','Antioxidante','DPPH (% captacion)',35.47,'%','ART0021 Fig. 6'),
 (25,r'DD99-\d','Antioxidante','Capacidad antioxidante (equivalentes Trolox)',49.46,'mM TE/100 mg','ART0021 Fig. 6'),
 (25,r'DD99-\d','Antioxidante','FRAP',11.45,'mmol Fe2+/g','ART0021 Fig. 6'),
 (25,r'DD99-\d','Antioxidante','ABTS (% captacion)',48.28,'%','ART0021 Fig. 6'),
]
for g,(fr,ab) in {'TB':(0.23,1.10),'TS':(3.44,0.08),'TA':(0.33,1.12),'TFL':(1.85,0.14)}.items():
    MEDIDAS += [(32,g+r'-\d','Antioxidante','FRAP',fr,'mmol/g','ART0028 Tabla 1'),
                (32,g+r'-\d','Antioxidante','ABTS',ab,'mmol/g','ART0028 Tabla 1')]
MEDIDAS += [(50,r'DY\d','Antioxidante','DPPH (equivalentes Trolox)',613.4,'ug TE/g FW','ART0045 Fig. 1G / texto')]
