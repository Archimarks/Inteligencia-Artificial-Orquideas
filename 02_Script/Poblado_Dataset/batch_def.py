"""Configuracion por batch: articulo, especie, parte, tipo de muestra, cultivo,
metodo de extraccion, columna y reglas por codigo de muestra."""
import re

FRESCO, SECO, CRUDO, SPE, ACUOSO, ETANOLICO, POLVO, COMERCIAL, QC, BLANCO, CURADO = (
    'Tejido fresco', 'Tejido seco', 'Extracto crudo enriquecido', 'Fraccion purificada (SPE C18)',
    'Extracto acuoso', 'Extracto etanolico', 'Polvo de extracto liofilizado', 'Extracto comercial (tabletas)',
    'Control de calidad (QC)', 'Blanco', 'Material curado o envejecido')
INVITRO, CAMPO, ORGANICO, CONTROLADO, SILVESTRE, ROCA, ARBOL, COMERCIAL_C, CHAKRA = (
    'In vitro', 'Cultivo convencional en campo', 'Cultivo organico', 'Invernadero o condiciones controladas',
    'Silvestre', 'Cultivo epifito en roca', 'Cultivo epifito en arbol', 'Material comercial',
    'Cultivo agroforestal (chakra)')


def qc_blank(code):
    c = code.lower()
    if 'blank' in c:
        return {'tipo': BLANCO, 'parte': None, 'grupo': 'Blanco'}
    if re.search(r'(^|_)(qc|pooled|mix)', c):
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (mezcla de muestras)'}
    return None


def rep(code):
    m = re.search(r'(\d+)$', code)
    return m.group(1) if m else ''


def by_prefix(table, sep=r'[-_]?\d+$'):
    """table: prefijo -> dict de overrides. Usa el prefijo del codigo sin numero final."""
    def f(code, g):
        pre = re.sub(sep, '', code)
        for k, v in table.items():
            if pre == k:
                return dict(v, replica=rep(code))
        return {}
    return f


def ilex(code, g):
    gg = g.get(code, {})
    tipo = gg.get('tipo', '')
    if tipo == 'QC' or 'POOLED' in code:
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (mezcla de muestras)'}
    if tipo == 'Sub_Quality_Control':
        return {'grupo': f"SubQC {gg.get('grupo', '')}", 'tipo': QC, 'parte': None,
                'desc': 'Mezcla parcial por factor experimental (subQC)'}
    return {'grupo': f"Ubicacion {gg.get('ubicacion', '')} | Luz {gg.get('luz', '')} | Edad {gg.get('edad', '')}"}


def caapi(code, g):
    grp = g.get(code, {}).get('grupo', '')
    parte = {'Non-organogenic meristems': 'Meristemo no organogenico', 'Organogenic meristem': 'Meristemo organogenico',
             'Stem explant': 'Explante de tallo', 'Leaf explant': 'Explante de hoja', 'Callus': 'Callo'}.get(grp)
    if grp == 'QC':
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (mezcla de muestras)'}
    if grp == 'Blank':
        return {'tipo': BLANCO, 'parte': None, 'grupo': 'Blanco de extraccion'}
    return {'parte': parte, 'grupo': grp, 'replica': (re.search(r'_R(\d)', code) or [None, ''])[1]}


def piper(code, g):
    m = re.search(r'_(S|F)(H|M)_PP_(\d)', code)
    if m:
        estado = 'Hoja seca' if m.group(1) == 'S' else 'Hoja fresca'
        ext = 'acuosa' if m.group(2) == 'H' else 'metanolica'
        return {'tipo': SECO if m.group(1) == 'S' else FRESCO, 'grupo': f'{estado}, extraccion {ext}',
                'replica': m.group(3), 'desc': 'Codigo interpretado: S/F = seca/fresca; H/M = extraccion acuosa/metanolica'}
    if 'QC' in code.upper():
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (' + code.split('_', 1)[1] + ')'}
    return {'tipo': BLANCO, 'parte': None, 'grupo': 'Blanco de proceso'}


def malp(code, g):
    if code.startswith('Blank'):
        return {'tipo': BLANCO, 'parte': None, 'grupo': 'Blanco con estandar interno'}
    if code.startswith('QC'):
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (mezcla de muestras)'}
    m = re.match(r'(P\d)_([A-H]\d+)_', code)
    return {'grupo': f'Placa {m.group(1)} pozo {m.group(2)}' if m else code,
            'desc': 'Especie no identificable: el mapeo pozo-especie esta en la Tabla Suplementaria 1 (no disponible)'}


def pisum(code, g):
    gg = g.get(code, {})
    t = gg.get('tipo', '')
    if t == 'QC' or code.startswith('QC'):
        return {'tipo': QC, 'parte': None, 'grupo': 'QC (mezcla de muestras)'}
    if t == 'Blank' or code.startswith('ES') or code.startswith('2_ES'):
        return {'tipo': BLANCO, 'parte': None, 'grupo': 'Blanco/estandar de extraccion (ES)'}
    grp = gg.get('grupo', '')
    cult = ORGANICO if 'Hammel' in grp else CAMPO
    return {'grupo': grp, 'cultivo': cult, 'replica': (re.match(r'\d+([ABC])', code) or [None, ''])[1]}


def potato(code, g):
    if code.startswith('TQW'):
        return {'tipo': CRUDO, 'metodo': 'POT_CRUDO', 'grupo': 'Extracto crudo enriquecido en SGA (TQW)', 'replica': rep(code)}
    if code.startswith('CHW'):
        return {'tipo': SPE, 'metodo': 'POT_SPE', 'grupo': 'Fraccion purificada C18 (CHW)', 'replica': rep(code)}
    return {}


def olden(code, g):
    m = re.match(r'(OLD|OLC)_(R|S|L|Fl|Fr)(\d)', code)
    if not m:
        return {}
    sp = 'o_diffusa' if m.group(1) == 'OLD' else 'o_corymbosa'
    parte = {'R': 'Raiz', 'S': 'Tallo', 'L': 'Hoja', 'Fl': 'Flor', 'Fr': 'Fruto'}[m.group(2)]
    return {'especie': sp, 'parte': parte, 'grupo': f'{m.group(1)} {parte}', 'replica': m.group(3)}


def garcinia(code, g):
    m = re.match(r'LS_GO_3_(\d)_(L|S|B|FR)', code)
    parte = {'L': 'Hoja', 'S': 'Rama', 'B': 'Corteza', 'FR': 'Fruto'}[m.group(2)]
    return {'parte': parte, 'grupo': parte, 'replica': m.group(1)}


RUBIA = {'D': 'r_magna', 'DY': 'r_schumanniana', 'Q': 'r_cordifolia', 'X': 'r_yunnanensis', 'Z': 'r_wallichiana'}


def rubia(code, g):
    pre = code.split('_')[0]
    if pre in RUBIA:
        return {'especie': RUBIA[pre], 'grupo': pre, 'replica': rep(code)}
    return {}


def gastrodia(code, g):
    pre = code[:2]
    forma = {'GB': 'f. glauca (tallo negro, GB)', 'GR': 'f. elata (tallo rojo, GR)', 'GG': 'f. viridis (tallo verde, GG)'}[pre]
    return {'grupo': forma, 'replica': rep(code)}


def morus_mg(code, g):
    t = {'CK': 'Mg 3 mM (optimo, CK)', 'T1': 'Mg 0 mM (deficiencia)', 'T2': 'Mg 1 mM (bajo)', 'T3': 'Mg 2 mM (bajo)',
         'T4': 'Mg 6 mM (alto)', 'T5': 'Mg 9 mM (alto)'}
    return {'grupo': t.get(code.split('-')[0], code), 'replica': rep(code)}


def morus_mn(code, g):
    t = {'CK': 'Mn suficiente (CK)', 'T0': 'Mn 0 mM (deficiencia)', 'T1': 'Mn 0.03 mM (deficiencia)',
         'T2': 'Mn 1.5 mM (toxicidad)', 'T3': 'Mn 3 mM (toxicidad)'}
    return {'grupo': t.get(code.split('-')[0], code), 'replica': rep(code)}


def avena(code, g):
    c = code.lower()
    m = re.match(r'(dane|otana|choteau|scholar|conan|reeder)([ic])(\d)', c)
    if not m:
        return {}
    sp = 'a_sativa' if m.group(1) in ('dane', 'otana') else 't_aestivum'
    trat = 'infestado por Cephus cinctus' if m.group(2) == 'i' else 'control'
    return {'especie': sp, 'grupo': f'cv. {m.group(1).capitalize()} {trat}', 'replica': m.group(3)}


def rosaceae(code, g):
    m = re.match(r'([HTL])([YF])-(\d)', code)
    if not m:
        return {}
    sp = {'H': 'm_pumila', 'T': 'p_persica', 'L': 'p_cerasifera'}[m.group(1)]
    parte = 'Hoja' if m.group(2) == 'Y' else 'Fruto'
    return {'especie': sp, 'parte': parte, 'grupo': code[:2], 'replica': m.group(3)}


def actinidia(code, g):
    pre = re.sub(r'\d$', '', code)
    if pre in ('LC', 'DY'):
        sp = 'a_arguta'
    elif pre in ('GC', 'SG', 'WL'):
        sp = 'a_chinensis'
    else:
        return {}
    nom = {'LC': "'Maolvfeng'", 'DY': "'Danyang flat'", 'GC': "'Guichang'", 'SG': "'SunGold'", 'WL': 'silvestre'}[pre]
    return {'especie': sp, 'grupo': f'{pre} {nom}', 'replica': rep(code),
            'cultivo': 'Silvestre' if pre == 'WL' else CAMPO}


def cibotium(code, g):
    pre = code.split('_')[0]
    if pre == 'WP':
        return {'cultivo': SILVESTRE, 'grupo': 'WP silvestre', 'replica': rep(code)}
    if pre == 'DM':
        return {'cultivo': CONTROLADO, 'grupo': 'DM domesticado en campo con malla de sombra', 'replica': rep(code)}
    if pre == 'ZP':
        return {'cultivo': INVITRO, 'grupo': 'ZP cultivo de tejidos', 'replica': rep(code)}
    if pre in ('WR', 'WS', 'WL', 'WN'):
        return {'cultivo': SILVESTRE, 'parte': None, 'grupo': f'{pre} (codigo no descrito en el articulo)', 'replica': rep(code),
                'desc': 'Muestra adicional de material silvestre no descrita en el articulo'}
    return {}


LAGER = {'LS': 'l_speciosa', 'LC': 'l_caudata', 'LI': 'l_indica'}
GLY = {'Ginf': 'g_inflata', 'Gura': 'g_uralensis', 'Gpal': 'g_pallidiflora', 'Gasp': 'g_aspera'}
RHODO = {'Rtri': 'r_triflorum', 'Rfau': 'r_faucium', 'Rniv': 'r_nivale', 'Rstr': 'r_strigillosum'}
POLY = {'PS': 'p_sibiricum', 'PC': 'p_cyrtonema', 'PK': 'p_kingianum', 'PO': 'p_odoratum'}


def mapsp(table, sep):
    def f(code, g):
        pre = re.split(sep, code)[0]
        if pre in table:
            return {'especie': table[pre], 'grupo': pre, 'replica': rep(code)}
        return {}
    return f


def P(parte, grupo):
    return {'parte': parte, 'grupo': grupo}


# batch: dict
B = {
    1: dict(art=1, especie='ilex_guayusa', parte='Hoja', tipo=FRESCO, cultivo=CHAKRA, metodo='ILEX', columna='CSH_C18', fn=ilex),
    2: dict(art=1, especie='ilex_guayusa', parte='Hoja', tipo=FRESCO, cultivo=CHAKRA, metodo='ILEX', columna='CSH_C18', fn=ilex),
    3: dict(art=0, especie='b_caapi', parte=None, tipo=FRESCO, cultivo=INVITRO, metodo=None, columna=None, fn=caapi),
    4: dict(art=0, especie='p_peltatum', parte='Hoja', tipo=SECO, cultivo=None, metodo='PIPER', columna='GC', fn=piper),
    5: dict(art=2, especie=None, familia='Malpighiaceae', parte=None, tipo=SECO, cultivo=SILVESTRE, metodo='MALP', columna='KINETEX_17_50', fn=malp),
    6: dict(art=2, especie=None, familia='Malpighiaceae', parte=None, tipo=SECO, cultivo=SILVESTRE, metodo='MALP', columna='KINETEX_17_50', fn=malp),
    7: dict(art=3, especie='p_sativum', parte='Semilla', tipo=SECO, cultivo=CAMPO, metodo='PISUM', columna='INTENSITY_SOLO', fn=pisum),
    8: dict(art=5, especie='s_tuberosum', parte='Hoja', tipo=CRUDO, cultivo=CAMPO, metodo='POT_CRUDO', columna='PREMIER_HSS_T3', fn=potato),
    9: dict(art=6, especie=None, parte=None, tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH70_IS', columna='SB_C18', fn=olden),
    10: dict(art=6, especie=None, parte=None, tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH70_IS', columna='SB_C18', fn=olden),
    11: dict(art=7, especie='g_oblongifolia', parte=None, tipo=FRESCO, cultivo=SILVESTRE, metodo='MEOH_W_31', columna='HSS_T3', fn=garcinia),
    12: dict(art=8, especie=None, parte='Raiz', tipo=SECO, cultivo=COMERCIAL_C, metodo='MAW221', columna='KINETEX_26_100', fn=rubia,
             parte_desc='Raices y rizomas (pieza comercial)'),
    13: dict(art=9, especie='p_pedatisecta', parte=None, tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH80', columna=None,
             fn=by_prefix({'L': P('Hoja', 'Hoja'), 'S': P('Tallo', 'Tallo'), 'T': P('Tuberculo', 'Tuberculo')}, r'\d+$')),
    14: dict(art=10, especie='p_cablin', parte='Hoja', tipo=FRESCO, cultivo=CAMPO, metodo='MAW221', columna='BEH_HILIC',
             fn=by_prefix({'CK': {'grupo': 'Hojas sanas (CK)'}, 'LD-TJ': {'grupo': 'Hojas con mancha foliar por Corynespora (LD-TJ)'}})),
    15: dict(art=11, especie='n_tabacum', parte='Hoja', tipo=CURADO, cultivo=COMERCIAL_C, metodo='MEOH80', columna='HYPERSIL_GOLD',
             fn=lambda c, g: ({'grupo': 'T0 inicio del almacenamiento (CK)', 'replica': rep(c)} if c.startswith('CK') else
                              {'grupo': {'NT': 'Almacenamiento natural', 'MC': 'Almacenamiento mecanico', 'AC': 'Aire acondicionado'}.get(c[:2], '') +
                               ' ' + {'T1': '3 meses (T1)', 'T2': '5 meses (T2)', 'T3': '9 meses (T3)'}.get(c[3:5], ''), 'replica': rep(c)}
                              if re.match(r'(NT|MC|AC)-T\d', c) else {})),
    16: dict(art=12, especie='p_chinense', parte='Hoja', tipo=SECO, cultivo=CAMPO, metodo='MEOH80', columna='XSELECT_HSS_T3',
             fn=by_prefix({'A': {'grupo': 'Variedad Taiwan (TW)'}, 'B': {'grupo': 'Variedad Xiaoye (XY)'},
                           'C': {'grupo': 'Variedad Minxuan (MX)'}, 'D': {'grupo': 'Variedad Zengcheng (ZC)'}}, r'_\d+$')),
    17: dict(art=13, especie='e_japonica', parte='Flor', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'FS': {'grupo': 'Flor fresca (FS)', 'tipo': FRESCO},
                           'HD': {'grupo': 'Flor secada al calor (HD)', 'tipo': SECO},
                           'FD': {'grupo': 'Flor liofilizada (FD)', 'tipo': SECO},
                           'FSP': {'grupo': 'Polvo de extracto acuoso de flor fresca (FSP)', 'tipo': POLVO, 'metodo': 'AGUA90'},
                           'HDP': {'grupo': 'Polvo de extracto acuoso de flor secada al calor (HDP)', 'tipo': POLVO, 'metodo': 'AGUA90'},
                           'FDP': {'grupo': 'Polvo de extracto acuoso de flor liofilizada (FDP)', 'tipo': POLVO, 'metodo': 'AGUA90'}}, r'\d+$')),
    18: dict(art=14, especie='c_pilosula', parte=None, tipo=SECO, cultivo=CAMPO, metodo='MEOH80_US_IS', columna='BEH_C18',
             fn=by_prefix({'JY': {'parte': 'Partes aereas (tallos y hojas)', 'grupo': 'Partes aereas marchitas (JY)'},
                           'CK': {'parte': 'Raiz', 'grupo': 'Raices secas (material medicinal, CK)'}}, r'\d+$')),
    19: dict(art=15, especie='s_suberectus', parte='Hoja', tipo=FRESCO, cultivo=CAMPO, metodo=None, columna='PREMIER_HSS_T3',
             fn=lambda c, g: {'grupo': {'January': 'Enero', 'March': 'Marzo', 'May': 'Mayo', 'July': 'Julio',
                                        'September': 'Septiembre', 'November': 'Noviembre'}[c.split('_')[0]], 'replica': rep(c)}),
    20: dict(art=16, especie='m_chinensis', parte=None, tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH80_IS', columna='HSS_T3',
             fn=lambda c, g: {'parte': {'S': 'Tallo', 'L': 'Hoja', 'F': 'Flor'}[c[-2]], 'grupo': {'S': 'Tallo', 'L': 'Hoja', 'F': 'Flor'}[c[-2]], 'replica': c[-1]}),
    21: dict(art=17, especie='f_dibotrys', parte='Rizoma', tipo=SECO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'CS': {'grupo': 'Shizhu, Chongqing (CS)'}, 'CF': {'grupo': 'Fuling, Chongqing (CF)'},
                           'YQ': {'grupo': 'Qujing, Yunnan (YQ)'}, 'YK': {'grupo': 'Kunming, Yunnan (YK)'},
                           'GB': {'grupo': 'Bijie, Guizhou (GB)'}})),
    22: dict(art=18, especie='a_trifoliata', parte='Fruto', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_4C', columna='SB_C18',
             fn=by_prefix({'S1': {'grupo': 'S1 60 DAFB'}, 'S2': {'grupo': 'S2 90 DAFB'}, 'S3': {'grupo': 'S3 120 DAFB'},
                           'S4': {'grupo': 'S4 150 DAFB'}})),
    23: dict(art=19, especie='i_batatas', parte='Tuberculo', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_IS', columna='HSS_T3',
             fn=lambda c, g: {'grupo': f"Corte fresco almacenado {c.split('d')[0]} d a 4 C (cv. Zifei)", 'replica': rep(c)}),
    24: dict(art=20, especie=None, parte='Rizoma', tipo=FRESCO, cultivo=None, metodo='MW73', columna='HSS_T3', fn=mapsp(POLY, '-')),
    25: dict(art=21, especie='f_ananassa', parte='Fruto', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH50_HCL', columna='VP_ODS',
             fn=by_prefix({'ZT': {'grupo': 'Zhaotong (alta altitud, ZT)'}, 'ZT99': {'grupo': "Zhaotong 'Red Face' (alta altitud, ZT99)"},
                           'DD99': {'grupo': "Dandong 'Red Face' (baja altitud, DD99)"}})),
    26: dict(art=22, especie='m_sativa', parte='Corona radicular', tipo=FRESCO, cultivo=CONTROLADO, metodo='MW73_IS', columna='BEH_C18',
             fn=lambda c, g: ({'grupo': ('Deficit hidrico 25% CC' if c.startswith('WD') else 'Riego 80% CC') + f" fase {c.split('_')[1]}",
                               'replica': rep(c)} if c[:2] in ('WD', 'WW') else {})),
    27: dict(art=23, especie='c_tetracocca', parte='Hoja', tipo=FRESCO, cultivo=CAMPO, metodo='MW73', columna='BEH_C18',
             fn=by_prefix({'E': {'grupo': 'Atacada por Empoasca onukii (E)'}, 'N': {'grupo': 'Sana (N)'}}, r'\d+$')),
    28: dict(art=24, especie='g_elata', parte='Tuberculo', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_IS_US', columna='HYPERSIL_GOLD_AQ', fn=gastrodia),
    29: dict(art=25, especie='c_sinensis', parte='Petalo', tipo=FRESCO, cultivo=SILVESTRE, metodo='MEOH70', columna='SB_C18',
             fn=lambda c, g: {'WE': {'grupo': 'Flor blanca, petalo externo (WE)'}, 'WI': {'grupo': 'Flor blanca, petalo interno (WI)'},
                              'WPE': {'grupo': 'Flor blanca-rosa, petalo externo (WPE)'}, 'WPI': {'grupo': 'Flor blanca-rosa, petalo interno (WPI)'},
                              'PE': {'grupo': 'Flor rosa, petalo externo (PE)'}, 'PI': {'grupo': 'Flor rosa, petalo interno (PI)'}}.get(c, {})),
    30: dict(art=26, especie='m_alba', parte='Hoja', tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH80', columna='HYPERSIL_GOLD', fn=morus_mg),
    31: dict(art=27, especie='d_opposita', parte='Tuberculo', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'SCY': {'grupo': 'Suelo arenoso (SCY)'}, 'LCY': {'grupo': 'Suelo loess (LCY)'}}, r'\d+$')),
    32: dict(art=28, especie='t_media', parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'TB': P('Corteza', 'Corteza (TB)'), 'TFL': P('Hoja', 'Hoja fresca (TFL)'),
                           'TS': P('Semilla', 'Semilla (TS)'), 'TA': P('Arilo', 'Arilo (TA)')})),
    33: dict(art=29, especie='c_drupifera', parte='Hoja', tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'CK': {'grupo': 'Control, agua (CK)'}, 'GZ2': {'grupo': 'AlCl3 2 mM (GZ2)'}, 'GZ4': {'grupo': 'AlCl3 4 mM (GZ4)'},
                           'MWXS22575a': {'grupo': 'MWXS22575a (no descrita en el articulo)', 'tipo': None,
                                          'desc': 'Muestra presente en la tabla pero no descrita en el articulo'}}, r'_R\d$|-\d$')),
    34: dict(art=30, especie=None, parte='Tallo', tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH100', columna='KINETEX_17_150', fn=avena),
    35: dict(art=31, especie='p_quinquefolius', parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH_FA', columna=None,
             fn=by_prefix({'Root': P('Raiz', 'Raiz'), 'Fibril': P('Raicilla', 'Fibrilla'), 'Stem1': P('Tallo', 'Tallo'),
                           'Leaf': P('Hoja', 'Hoja')}, r'_\d+$')),
    36: dict(art=32, especie='m_alba', parte='Hoja', tipo=FRESCO, cultivo=CONTROLADO, metodo='MAW221', columna='HSS_T3', fn=morus_mn),
    37: dict(art=33, especie='n_cadamba', parte='Fruto', tipo=SECO, cultivo=CAMPO, metodo=None, columna='SB_C18',
             fn=by_prefix({'WA': {'grupo': 'Extracto acuoso (WA)', 'tipo': ACUOSO, 'metodo': 'AGUA_EBULL'},
                           'ET': {'grupo': 'Extracto etanolico (ET)', 'tipo': ETANOLICO, 'metodo': 'ETOH70'}}, r'\d+$')),
    38: dict(art=34, especie='p_lactiflora', parte='Raiz', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_4C', columna='SB_C18',
             fn=by_prefix({'CK': {'grupo': "cv. 'Fenyunu' (CK)"}, 'DFG': {'grupo': "cv. 'Dafugui' (DFG)"},
                           'HSML': {'grupo': "cv. 'Red Charm' (HSML)"}}, r'\d+$')),
    39: dict(art=35, especie='c_morifolium', parte='Flor', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_US1H', columna='ACCUCORE_C18',
             fn=by_prefix({'FCF': {'grupo': 'Capitulo fresco (FCF)', 'tipo': FRESCO},
                           'SCF': {'grupo': 'Secado a la sombra (SCF)', 'tipo': SECO},
                           'DCF': {'grupo': 'Secado en horno 50 C (DCF)', 'tipo': SECO}}, r'\d+$')),
    40: dict(art=36, especie=None, parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18', fn=rosaceae),
    41: dict(art=37, especie='i_batatas', parte='Tuberculo', tipo=FRESCO, cultivo=CONTROLADO, metodo='MEOH70_IS', columna='HSS_T3',
             fn=by_prefix({'BS': {'grupo': "Pulpa blanca 'Chestnut Potato' (BS)"}, 'CS': {'grupo': "Pulpa naranja 'Watermelon Red No. 1' (CS)"},
                           'ZS': {'grupo': "Pulpa morada 'Purple Potato' (ZS)"}})),
    42: dict(art=38, especie='s_indicum', parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=lambda c, g: {'FC': P('Carpelo', 'Carpelos frescos (FC)'), 'FS': P('Semilla', 'Semillas frescas (FS)'),
                              'ML': P('Hoja', 'Hojas medias (ML)'), 'PF': P('Flor', 'Flores purpuras (PF)'),
                              'WF': P('Flor', 'Flores blancas (WF)')}.get(c, {})),
    43: dict(art=39, especie='d_officinale', parte='Tallo', tipo=FRESCO, cultivo=None, metodo='MEOH70_IS', columna='SB_C18',
             fn=by_prefix({'SEC': {'cultivo': ROCA, 'grupo': 'Epifito en roca (SEC)'}, 'TEC': {'cultivo': ARBOL, 'grupo': 'Epifito en arbol (TEC)'},
                           'GC': {'cultivo': CONTROLADO, 'grupo': 'Invernadero (GC)'}})),
    44: dict(art=40, especie='c_domestica', parte='Fruto', tipo=FRESCO, cultivo=SILVESTRE, metodo='ETOH_W41', columna='BEH_C18',
             fn=by_prefix({'T0': {'grupo': 'Postcosecha T0'}, 'T1': {'grupo': 'Postcosecha T1'}, 'T2': {'grupo': 'Postcosecha T2'}}, r'_\d$')),
    45: dict(art=41, especie='c_tangutica', parte='Hoja', tipo=FRESCO, cultivo=SILVESTRE, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'JZ': {'grupo': 'Jianzha 2060 m (JZ)'}, 'MY': {'grupo': 'Menyuan 2641 m (MY)'}, 'GH': {'grupo': 'Gonghe 3191 m (GH)'},
                           'DQ': {'grupo': 'Da Qaidam 3590 m (DQ)'}, 'ZD': {'grupo': 'Zaduo 4252 m (ZD)'}})),
    46: dict(art=42, especie=None, parte='Raiz', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_IS', columna='SB_C18', fn=mapsp(GLY, '_')),
    47: dict(art=43, especie='n_nucifera', parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH_IS', columna='HSS_T3',
             fn=by_prefix({'Flo': P('Flor', 'Flor (Flo)'), 'Pet': P('Peciolo', 'Peciolo (Pet)'), 'Sem': P('Semilla', 'Semilla (Sem)'),
                           'Plu': P('Plumula', 'Plumula (Plu)'), 'Sta': P('Estambre', 'Estambre (Sta)'),
                           'Rec': P('Receptaculo floral', 'Receptaculo/vaina (Rec)')}, r'\d+$')),
    48: dict(art=53, especie=None, parte='Petalo', tipo=FRESCO, cultivo=SILVESTRE, metodo='MEOH70', columna='SB_C18', fn=mapsp(RHODO, '_')),
    49: dict(art=44, especie='c_reticulata', parte='Pericarpio (cascara)', tipo=CURADO, cultivo=CAMPO, metodo='MEOH70_IS', columna='HSS_T3',
             fn=lambda c, g: {'grupo': f'Cascara envejecida {c[4:]} anio(s) (CCPY{c[4:]})'} if c.startswith('CCPY') else {}),
    50: dict(art=45, especie=None, parte='Pulpa del fruto', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_IS', columna='SB_C18', fn=actinidia),
    51: dict(art=46, especie='c_oleifera', parte='Almendra (semilla descascarada)', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=lambda c, g: {'grupo': f"cv. changlin {c.split('-')[0][2:]} ({c.split('-')[0]})", 'replica': rep(c)} if c.startswith('CL') else {}),
    52: dict(art=47, especie='s_asiatica', parte='Planta entera', tipo=SECO, cultivo=SILVESTRE, metodo='MW41_IS', columna='HSS_T3',
             fn=by_prefix({'XB': {'grupo': 'Daling, Huizhou (XB)'}, 'BH': {'grupo': 'Baihua, Huizhou (BH)'}, 'HLA': {'grupo': 'Hengli, Huizhou (HLA)'},
                           'LH': {'grupo': 'Lianghua, Huizhou (LH)'}, 'ZQ': {'grupo': 'Guanxu, Zhaoqing (ZQ)'},
                           'YQ': {'grupo': 'Yanqian, Longyan (YQ)'}, 'FS': {'grupo': 'Shashi, Ganzhou (FS)'}}, r'\d+$')),
    53: dict(art=48, especie='h_citrina', parte=None, tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70', columna='SB_C18',
             fn=by_prefix({'Fh': P('Flor', 'Flor'), 'Lh': P('Hoja', 'Hoja'), 'Sh': P('Tallo', 'Tallo'), 'Rh': P('Raiz', 'Raiz')}, r'\d+$')),
    54: dict(art=49, especie='w_somnifera', parte='Raiz', tipo=COMERCIAL, cultivo=COMERCIAL_C, metodo='RIPA', columna='THERMO_C18_3',
             fn=lambda c, g: {'grupo': 'Extracto comercial de raiz (replica biologica)', 'replica': rep(c)}),
    55: dict(art=50, especie='c_barometz', parte='Rizoma', tipo=FRESCO, cultivo=None, metodo='MAW221_20', columna='HSS_T3', fn=cibotium),
    56: dict(art=51, especie=None, parte='Hoja', tipo=FRESCO, cultivo=CAMPO, metodo='MEOH70_IS', columna='SB_C18', fn=mapsp(LAGER, r'\d')),
    57: dict(art=52, especie='c_annuum', parte='Fruto', tipo=SECO, cultivo=CAMPO, metodo='MW73_HIELO', columna='HSS_T3',
             fn=by_prefix({'AY': {'grupo': 'Anyue, Sichuan (AY)'}, 'PZ': {'grupo': 'Pengzhou, Sichuan (PZ)'},
                           'XX': {'grupo': 'Xiangcheng, Henan (XX)'}})),
}

# escalas logaritmicas a revertir a intensidad lineal (base)
LOG_BASE = {18: 10, 52: 10, 55: 10, 57: 2}

# batch -> especie unica para muestras QC/blanco
