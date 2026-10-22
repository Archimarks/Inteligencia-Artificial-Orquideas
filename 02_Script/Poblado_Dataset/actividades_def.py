"""Actividades biologicas por articulo (revision de los 52 articulos).
Cada entrada: (actividad, especies (None = todas las del articulo), metabolito (None = extracto/especie), nota)"""

LIT = {
    1: [('Antioxidante', None, None, 'Compuestos fenolicos de guayusa'), ('Estimulante', None, 'Caffeine', 'Metilxantinas de guayusa'),
        ('Estimulante', None, 'Theobromine', 'Metilxantinas de guayusa'), ('Antifungico', None, 'Chlorogenic Acid', 'Atribuida a acidos clorogenicos'),
        ('Neuroprotector', None, 'Chlorogenic Acid', 'Atribuida a acidos clorogenicos'), ('Hipolipemiante', None, 'Chlorogenic Acid', 'Modulacion del metabolismo lipidico'),
        ('Antioxidante', None, 'Chlorogenic Acid', 'Atribuida a acidos clorogenicos'), ('Antiinflamatorio', None, None, 'Mencionado en la discusion')],
    5: [('Antifungico', None, None, 'Extractos de hoja como alternativa a fungicidas poscosecha'),
        ('Insecticida', None, None, 'Glicoalcaloides con efecto sobre insectos plaga')],
    6: [(a, None, None, 'Uso tradicional/literatura') for a in ('Antiinflamatorio', 'Hepatoprotector', 'Anticancerigeno', 'Desintoxicante')],
    7: [(a, None, None, 'Uso tradicional (etnias Li y Zhuang)') for a in ('Antiinflamatorio', 'Analgesico', 'Antimiatrofico', 'Antibacteriano', 'Anticancerigeno')] +
       [(a, None, None, 'Atribuida a xantonas') for a in ('Antiviral', 'Hepatoprotector', 'Antidiabetico', 'Inhibidor de xantina oxidasa')],
    8: [(a, None, None, 'Literatura sobre Qiancao') for a in ('Antiinflamatorio', 'Anticancerigeno', 'Antioxidante', 'Antimicrobiano', 'Antiplaquetario',
                                                              'Nefroprotector', 'Antiurolitiasico', 'Hepatoprotector', 'Neuroprotector')] +
       [('Antiviral', None, m, 'Efecto inhibitorio antiviral preclinico') for m in ('Citrusinine I', 'Hypoxanthine', 'Xanthopurpurin', 'Vanillic acid')],
    9: [(a, None, None, 'Literatura') for a in ('Antioxidante', 'Anticonvulsivo', 'Anticancerigeno', 'Antiarritmico')],
    10: [(a, None, None, 'Medicina tradicional china (aceite esencial)') for a in ('Antiinflamatorio', 'Antidepresivo', 'Antimicrobiano')] +
        [('Anticancerigeno', None, None, 'Compuestos no volatiles'), ('Antibacteriano', None, 'Alloaromadendrene', 'Literatura')],
    12: [(a, None, None, 'Literatura') for a in ('Antioxidante', 'Antihipoxico', 'Antihipertensivo', 'Hipolipemiante')] +
        [(a, None, 'Nodakenin', 'Literatura') for a in ('Antiinflamatorio', 'Antibacteriano', 'Antioxidante', 'Antiplaquetario')],
    13: [('Antioxidante', None, None, 'Literatura'), ('Antiinflamatorio', None, None, 'Literatura')],
    15: [('Antioxidante', None, None, 'Literatura'), ('Antiinflamatorio', None, None, 'Literatura')],
    17: [(a, None, None, 'Estudios farmacologicos in vivo e in vitro') for a in ('Antidiabetico', 'Anticancerigeno', 'Antiinflamatorio', 'Antioxidante',
                                                                                'Hepatoprotector', 'Antibacteriano')],
    18: [(a, None, None, 'Literatura') for a in ('Diuretico', 'Neuroprotector', 'Analgesico', 'Antiinflamatorio', 'Antiobesidad', 'Antienvejecimiento',
                                                  'Antibacteriano', 'Antioxidante', 'Anticancerigeno')] +
        [('Antihipertensivo', None, None, 'Oligopeptidos inhibidores de ACE predichos')],
    19: [('Antioxidante', None, None, 'Discutido para flavonoides y antocianinas')],
    20: [('Antidiabetico', None, None, 'Uso tradicional'), ('Modulador de la microbiota', None, None, 'Uso tradicional'),
         ('Inmunomodulador', None, None, 'Uso tradicional'), ('Anticancerigeno', None, None, 'Polisacaridos de Polygonatum')],
    23: [('Insecticida', None, None, 'Metabolitos con actividad insecticida/repelente segun literatura')],
    24: [(a, None, None, 'Farmacologia de Gastrodia elata') for a in ('Sedante', 'Anticonvulsivo', 'Analgesico', 'Neuroprotector', 'Antidepresivo',
                                                                      'Antiinflamatorio', 'Antioxidante')],
    25: [(a, None, None, 'Literatura') for a in ('Anticancerigeno', 'Antiviral', 'Antioxidante')],
    26: [(a, None, None, 'Hojas de morera') for a in ('Antioxidante', 'Antiinflamatorio', 'Antialergico')],
    27: [(a, None, None, 'Literatura') for a in ('Antioxidante', 'Antihipertensivo', 'Antidiabetico')] +
        [('Antiinflamatorio', None, m, 'Catequinas') for m in ('Catechin', 'Epicatechin')] +
        [(a, None, '1-Eicosanol', 'Literatura') for a in ('Antibacteriano', 'Antifungico', 'Anticancerigeno')] +
        [(a, None, None, 'Acidos fenolicos') for a in ('Hepatoprotector', 'Cardioprotector', 'Antiviral')],
    28: [(a, None, None, 'Acidos organicos') for a in ('Antibacteriano', 'Antidiabetico', 'Inmunomodulador')],
    29: [('Antioxidante', None, None, 'Flavonoides'), ('Antibacteriano', None, None, 'Flavonoides')],
    31: [(a, None, 'Chlorogenic acid', 'Literatura') for a in ('Antibacteriano', 'Antiviral', 'Desintoxicante')],
    32: [('Antioxidante', None, None, 'Metabolitos antioxidantes frente a estres por Mn')],
    33: [(a, None, None, 'Estudios in vitro e in vivo') for a in ('Antidiabetico', 'Antimicrobiano', 'Antiinflamatorio', 'Cicatrizante', 'Antioxidante',
                                                                  'Antihelmintico', 'Anticancerigeno', 'Cardioprotector')],
    34: [(a, None, None, 'Literatura') for a in ('Anticancerigeno', 'Antiinflamatorio', 'Antioxidante', 'Hepatoprotector', 'Inmunomodulador')] +
        [('Antibacteriano', None, None, 'Flavonoides'), ('Analgesico', None, None, 'Flavonoides')],
    35: [(a, None, None, 'Literatura') for a in ('Antimicrobiano', 'Antiinflamatorio', 'Hipolipemiante', 'Anticancerigeno', 'Antioxidante')],
    36: [('Antioxidante', None, None, 'Flavonoides')],
    38: [(a, None, None, 'Literatura') for a in ('Antioxidante', 'Antidiabetico', 'Antiproliferativo', 'Gastroprotector', 'Antimicrobiano')],
    39: [(a, None, None, 'Literatura') for a in ('Gastroprotector', 'Anticolitico', 'Anticancerigeno', 'Hepatoprotector', 'Antihipertensivo')],
    40: [(a, None, m, 'Literatura') for m in ('Piptamine', 'Resorcinol') for a in ('Antimicrobiano', 'Antifungico')],
    41: [(a, None, None, 'Literatura') for a in ('Anticancerigeno', 'Antibacteriano', 'Antifungico', 'Antiinflamatorio', 'Cardioprotector',
                                                  'Antioxidante', 'Antiviral')],
    42: [(a, None, None, 'Farmacologia del regaliz') for a in ('Antiinflamatorio', 'Antioxidante', 'Anticancerigeno', 'Gastroprotector', 'Antiviral',
                                                                'Antibacteriano', 'Hepatoprotector')],
    43: [(a, None, None, 'Alcaloides del loto') for a in ('Antioxidante', 'Anticancerigeno', 'Antibacteriano', 'Antiinflamatorio', 'Hipolipemiante',
                                                           'Antidiabetico')],
    45: [('Antioxidante', None, None, 'Literatura'), ('Antiinflamatorio', None, None, 'Literatura'), ('Cardioprotector', None, None, 'Literatura')],
    47: [(a, None, None, 'Flavonoides de Striga') for a in ('Hepatoprotector', 'Antioxidante', 'Antiinflamatorio', 'Antibacteriano', 'Anticancerigeno',
                                                             'Antiviral', 'Antiparasitario')],
    48: [(a, None, None, 'Flavonoides de H. citrina') for a in ('Cardioprotector', 'Antitusivo', 'Antibacteriano', 'Hepatoprotector', 'Antioxidante')] +
        [('Antiinflamatorio', None, 'Kaempferol-3-O-rhamnoside', 'Literatura'), ('Antiproliferativo', None, 'Kaempferol-3-O-rhamnoside', 'Literatura'),
         ('Antifungico', None, "3,5,7,2'-Tetrahydroxyflavone", 'Frente a Fusarium oxysporum'), ('Antioxidante', None, 'Taxifolin', 'Literatura')],
    49: [(a, None, None, 'Literatura sobre ashwagandha') for a in ('Ansiolitico', 'Inmunomodulador', 'Neuroprotector', 'Antidepresivo',
                                                                   'Hepatoprotector', 'Salud reproductiva', 'Antiinflamatorio')] +
        [('Neuroprotector', None, 'Gentianaine', 'Literatura'), ('Antibacteriano', None, 'Gentianaine', 'Literatura')],
    50: [(a, None, None, 'Literatura sobre Gouji') for a in ('Antioxidante', 'Antiinflamatorio', 'Osteogenico', 'Analgesico', 'Hemostatico')],
    51: [(a, None, None, 'Literatura') for a in ('Antimicrobiano', 'Antioxidante', 'Sedante', 'Antidepresivo', 'Antidiabetico')],
    52: [('Antibacteriano', None, None, 'Literatura'), ('Antioxidante', None, None, 'Literatura')],
}

# Ensayos experimentales sin valor por muestra (solo figura) o sobre fracciones
EXP_SIN_VALOR = [
    # (articulo, especies, actividad, ensayo, valor, unidad, nota)
    (16, None, 'Antioxidante', 'DPPH, ABTS y FRAP por tejido', None, '', 'Valores solo en figura'),
    (29, None, 'Antioxidante', 'DPPH (% inhibicion)', None, '', 'Valores solo en figura'),
    (33, None, 'Antioxidante', 'DPPH y ABTS', None, '', 'Extracto etanolico (ET) mayor que acuoso (WA); valores en figura'),
    (39, None, 'Anticancerigeno', 'Inhibicion de celulas HepG2', None, '', 'Dependiente de la concentracion; SEC mayor a 100 ug/mL'),
    (39, None, 'Gastroprotector', 'Proteccion en modelo celular de gastritis atrofica cronica', None, '', 'SEC superior a TEC y GC'),
    (44, None, 'Antioxidante', 'ABTS/DPPH IC50 y FRAP', None, '', 'Patron fluctuante con el envejecimiento; valores en figura'),
    (46, None, 'Antioxidante', 'ABTS, DPPH, radical hidroxilo y FRAP', None, '', 'CL53 con la mayor capacidad; valores en figura'),
    (51, ['l_speciosa'], 'Antioxidante', 'DPPH (fraccion acuosa)', 22.41, 'mmol TE/100 g DW', 'Fraccion acuosa de hojas, no vinculada a muestras del metaboloma'),
    (51, ['l_speciosa'], 'Antioxidante', 'ABTS (fraccion acuosa)', 4.43, 'mmol TE/100 g DW', 'Fraccion acuosa de hojas, no vinculada a muestras del metaboloma'),
    (51, None, 'Antidiabetico', 'Inhibicion de alfa-glucosidasa y alfa-amilasa por fracciones', None, '', 'Tabla 2 del articulo (IC50 por fraccion)'),
]
