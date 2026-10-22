"""Parser de los 57 batches crudos a formato largo estandarizado.

Salida por batch: pickle con dos DataFrames
  feats: una fila por feature/metabolito (campos estandarizados)
  vals : (fid, muestra, valor) solo valores > 0
  samples: lista de codigos de muestra + metadatos crudos (grupo)
"""
import os, re, sys, pickle, math, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

D = '/home/user/Inteligencia-Artificial-Orquideas/01_Datos/Data/Batch/'
OUT = os.environ.get('PARSED_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed'))
os.makedirs(OUT, exist_ok=True)

FIELDS = ['name', 'formula', 'mass', 'mz', 'rt', 'adduct', 'mode', 'level',
          'superclass', 'clase', 'subclass', 'fuente_tabla', 'plataforma']


def read(f, sheet=0, header=0, **kw):
    return pd.read_excel(D + f, sheet_name=sheet, header=header, engine='calamine', **kw)


def num(v):
    """Convierte una celda de intensidad a float (NaN si no detectado)."""
    if v is None:
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v) if not (isinstance(v, float) and math.isnan(v)) else np.nan
    s = str(v).strip()
    if not s or s.upper() in {'ND', 'NA', 'N/A', '-', '--', 'NAN', 'NULL'}:
        return np.nan
    if '±' in s:
        s = s.split('±')[0]
    s = s.replace(',', '')
    try:
        return float(s)
    except ValueError:
        return np.nan


def clean_sample(c):
    c = str(c).strip()
    c = re.sub(r'\.(mzML|mzXML|CDF|d)\s*Peak (height|area)$', '', c)
    c = re.sub(r'\s*Peak (height|area)$', '', c)
    c = re.sub(r'^(Area_|Area: |all_)', '', c)
    return c.strip()


def s(v):
    if v is None:
        return ''
    if isinstance(v, float) and math.isnan(v):
        return ''
    t = str(v).strip()
    return '' if t.lower() in {'nan', '-', '--', '/', '\\', 'null', 'none', 'unknown', 'unclassified'} else t


def build(df, cmap, sample_cols, fixed=None, rt_unit='min', metware9=False, tiny=None,
          mode_fn=None, fuente=''):
    """cmap: campo estandar -> nombre de columna (o callable(row))."""
    fixed = fixed or {}
    df = df.reset_index(drop=True)
    feats = pd.DataFrame(index=df.index)
    for f in FIELDS:
        if f in cmap:
            src = cmap[f]
            if callable(src):
                feats[f] = df.apply(src, axis=1)
            else:
                feats[f] = df[src]
        elif f in fixed:
            feats[f] = fixed[f]
        else:
            feats[f] = ''
    for f in ['name', 'formula', 'adduct', 'mode', 'level', 'superclass', 'clase', 'subclass']:
        feats[f] = feats[f].map(s)
    for f in ['mass', 'mz', 'rt']:
        feats[f] = feats[f].map(num)
    if rt_unit == 's':
        feats['rt'] = feats['rt'] / 60.0
    if mode_fn is not None:
        feats['mode'] = df.apply(mode_fn, axis=1)
    feats['fuente_tabla'] = fuente
    feats['plataforma'] = fixed.get('plataforma', feats['plataforma'] if 'plataforma' in cmap else 'LC-MS')
    # intensidades
    mat = df[sample_cols].applymap(num) if hasattr(df, 'applymap') else df[sample_cols].map(num)
    if metware9:
        mat = mat.mask(mat == 9)
    if tiny is not None:
        mat = mat.mask(mat < tiny)
    mat.columns = [clean_sample(c) for c in sample_cols]
    return feats, mat


def finish(bid, parts, groups=None):
    """parts: lista de (feats, mat). Une, asigna fid y guarda."""
    allf, allv, samples = [], [], []
    fid = 0
    for feats, mat in parts:
        feats = feats.copy()
        feats['fid'] = range(fid, fid + len(feats))
        fid += len(feats)
        m = mat.copy()
        m.index = feats['fid'].values
        for c in m.columns:
            if c not in samples:
                samples.append(c)
        st = m.stack()
        st = st[st > 0]
        v = st.reset_index()
        v.columns = ['fid', 'muestra', 'valor']
        allf.append(feats)
        allv.append(v)
    feats = pd.concat(allf, ignore_index=True)
    vals = pd.concat(allv, ignore_index=True)
    with open(os.path.join(OUT, f'B{bid:02d}.pkl'), 'wb') as fh:
        pickle.dump({'feats': feats, 'vals': vals, 'samples': samples,
                     'groups': groups or {}}, fh)
    ident = (feats['name'] != '').sum()
    print(f'B{bid:02d}: feats={len(feats)} ident={ident} muestras={len(samples)} valores>0={len(vals)}',
          flush=True)


def adduct_mode(row_adduct):
    a = s(row_adduct)
    if a.endswith('+') or a.endswith('+1') or a.endswith('+2'):
        return 'POS'
    if a.endswith('-') or a.endswith('-1') or a.endswith('-2'):
        return 'NEG'
    return ''


def norm_mode(v):
    t = s(v).lower()
    if not t:
        return ''
    if 'gc' in t:
        return 'EI'
    if 'pos' in t or t in {'+', 'p'}:
        return 'POS'
    if 'neg' in t or t in {'-', 'n'}:
        return 'NEG'
    return ''


# ---------------------------------------------------------------- metware ---
def metware_targeted(bid, f, sheet=0, header=0, samples_re=None, cols=None, extra=None):
    df = read(f, sheet, header)
    df = df[df[df.columns[0]].notna()]
    c = {k: k for k in df.columns}
    def pick(*names):
        for n in names:
            for col in df.columns:
                if str(col).strip().lower() == n.lower():
                    return col
        return None
    cmap = {}
    for fld, names in [('name', ['Compounds', 'compounds']), ('formula', ['Formula']),
                       ('mass', ['Molecular weight (Da)', 'Molecular Weight (Da)', 'Molecular Weight']),
                       ('mz', ['Q1 (Da)', 'Q1 (Th)']), ('adduct', ['Ionization model', 'Adduct']),
                       ('level', ['Level']), ('superclass', ['Class I', 'Class']),
                       ('clase', ['Class II', 'Sub-class']), ('rt', ['RT (min)'])]:
        col = pick(*names)
        if col is not None:
            cmap[fld] = col
    if extra:
        cmap.update(extra)
    if samples_re:
        sc = [col for col in df.columns if re.fullmatch(samples_re, str(col).strip())]
    else:
        sc = cols
    feats, mat = build(df, cmap, sc, metware9=True, fuente=str(sheet),
                       mode_fn=lambda r: adduct_mode(r[cmap['adduct']]) if 'adduct' in cmap else '')
    finish(bid, [(feats, mat)])


def metware_untargeted(bid, f, sheet=0, header=0, samples_re=None):
    df = read(f, sheet, header)
    df = df[df['Compounds'].notna()]
    sc = [col for col in df.columns if re.fullmatch(samples_re, str(col).strip())]
    cmap = {'name': 'Compounds', 'formula': 'Formula', 'mass': 'Molecular weight (Da)', 'mz': 'Q1 (Da)',
            'rt': 'RT (min)', 'adduct': 'Adduct', 'level': 'Level', 'superclass': 'Class I',
            'clase': 'Class II'}
    feats, mat = build(df, cmap, sc, metware9=False, fuente=str(sheet),
                       mode_fn=lambda r: norm_mode(r['Mode']) or adduct_mode(r['Adduct']))
    finish(bid, [(feats, mat)])


# ------------------------------------------------------------ por batch -----
def b01():
    raw = read('BAT0001_ilex_guayusa_NEG.xlsx', 0, None)
    meta = raw.iloc[0:10, 8:]
    df = read('BAT0001_ilex_guayusa_NEG.xlsx', 0, 10)
    sc = list(df.columns[9:])
    groups = {}
    for j, col in enumerate(sc):
        k = clean_sample(col)
        groups[k] = {'grupo': s(raw.iat[6, 9 + j]), 'tipo': s(raw.iat[4, 9 + j]),
                     'ubicacion': s(raw.iat[1, 9 + j]), 'luz': s(raw.iat[2, 9 + j]),
                     'edad': s(raw.iat[3, 9 + j])}
    cmap = {'mz': 'row_m_z', 'rt': 'row_retention_time', 'name': 'Metabolite',
            'level': 'Identification_level', 'clase': 'Class', 'superclass': 'Superclass', 'mode': 'Ion_Mode'}
    feats, mat = build(df, cmap, sc, fuente='Sheet 1')
    feats['mode'] = 'NEG'
    finish(1, [(feats, mat)], groups)


def b02():
    raw = read('BAT0002_ilex_guayusa_POS.xlsx', 'Hoja1', None)
    df = read('BAT0002_ilex_guayusa_POS.xlsx', 'Hoja1', 8)
    sc = list(df.columns[9:])
    groups = {}
    for j, col in enumerate(sc):
        k = clean_sample(col)
        groups[k] = {'grupo': s(raw.iat[5, 9 + j]), 'tipo': s(raw.iat[3, 9 + j]),
                     'ubicacion': s(raw.iat[0, 9 + j]), 'luz': s(raw.iat[1, 9 + j]),
                     'edad': s(raw.iat[2, 9 + j])}
    cmap = {'mz': 'row m/z', 'rt': 'row retention time', 'name': 'Metabolite',
            'level': 'Identification_level', 'clase': 'Class', 'superclass': 'Superclass'}
    feats, mat = build(df, cmap, sc, fixed={'mode': 'POS'}, fuente='Hoja1')
    finish(2, [(feats, mat)], groups)


def b03():
    raw = read('BAT0003_banisteriopsis_caapi_POS.xlsx', 'Hoja1', None)
    df = read('BAT0003_banisteriopsis_caapi_POS.xlsx', 'Hoja1', 4)
    sc = list(df.columns[13:])
    groups = {clean_sample(c): {'grupo': s(raw.iat[0, 13 + j])} for j, c in enumerate(sc)}
    cmap = {'mz': 'mass', 'rt': 'RT', 'name': 'Metabolite', 'level': 'IL',
            'superclass': 'classyfireR_Superclass', 'clase': 'classyfireR_class',
            'subclass': 'classyfireR_subclass'}
    feats, mat = build(df, cmap, sc, fixed={'mode': 'POS'}, fuente='Hoja1')
    finish(3, [(feats, mat)], groups)


def b04():
    raw = read('BAT0004_piper_peltatum_EI.xlsx', 'Sheet1', None)
    df = read('BAT0004_piper_peltatum_EI.xlsx', 'Sheet1', 4)
    sc = list(df.columns[28:56])
    groups = {clean_sample(c): {'grupo': s(raw.iat[1, 28 + j])} for j, c in enumerate(sc)}
    cmap = {'mz': 'Quant mass', 'rt': 'Average Rt(min)', 'name': 'Metabolite name', 'formula': 'Formula',
            'clase': 'Ontology'}
    feats, mat = build(df, cmap, sc, fixed={'mode': 'EI', 'plataforma': 'GC-MS'}, fuente='Sheet1')
    finish(4, [(feats, mat)], groups)


def b05_06(bid, f, mode):
    df = pd.read_csv(D + f, encoding='utf-8-sig')
    sc = list(df.columns[3:])
    feats, mat = build(df, {'mz': 'row m/z', 'rt': 'row retention time'}, sc,
                       fixed={'mode': mode}, fuente='csv')
    # quitar sufijo de corrida (_53310) para codigo de muestra estable
    finish(bid, [(feats, mat)])


def b07():
    f = 'BAT0007_pisum_sativum_POS.xlsx'
    df = read(f, 'Metaboscape')
    sir = read(f, 'SIRIUS')
    sir = sir[sir['formulaRank'] == 1].drop_duplicates('Feature_ID').set_index('Feature_ID')['molecularFormula']
    meta = read(f, 'Metadata')
    sc = list(df.columns[22:])
    df['formula2'] = [fo if s(fo) else sir.get(i, '') for fo, i in zip(df['Molecular Formula'], df['Feature_ID'])]
    def lvl(r):
        src = s(r['Annotation Source'])
        if not s(r['Name']):
            return ''
        return 'III' if 'in-silico' in src else 'II'
    cmap = {'name': 'Name', 'rt': 'RT [min]', 'mz': 'm/z meas.', 'mass': 'M meas.',
            'adduct': lambda r: s(r['Ions']).split(',')[0].strip(), 'formula': 'formula2', 'level': lvl}
    feats, mat = build(df, cmap, sc, fixed={'mode': 'POS'}, fuente='Metaboscape')
    groups = {}
    for _, r in meta.iterrows():
        k = re.sub(r'\.d$', '', str(r['filename']))
        groups[k] = {'grupo': f"{s(r['ATTRIBUTE_Cultivar'])} | {s(r['ATTRIBUTE_Location'])}",
                     'tipo': s(r['ATTRIBUTE_Sample_Type'])}
    finish(7, [(feats, mat)], groups)


def b09_10(bid, f, mode):
    df = read(f, 0)
    sc = [c for c in df.columns if re.match(r'^(OLD|OLC)_|^QC\d', str(c))]
    cmap = {'name': 'metabolite_identification', 'formula': 'chemical_formula', 'mz': 'mass_to_charge',
            'adduct': 'modifications', 'rt': 'retention_time'}
    feats, mat = build(df, cmap, sc, fixed={'mode': mode}, fuente='Metabolite profiling')
    finish(bid, [(feats, mat)])


def b11():
    df = read('BAT0011_garcinia_oblongifolia_POS_NEG.xlsx', 0, 1)
    sc = [c for c in df.columns if str(c).startswith('LS_GO')]
    cmap = {'name': 'MS2 name_x', 'superclass': 'Super.Class', 'clase': 'Class', 'subclass': 'Sub.Class',
            'rt': 'rt', 'mz': 'mz', 'mode': 'type'}
    feats, mat = build(df, cmap, sc, rt_unit='s', fuente='Table S1')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(11, [(feats, mat)])


def b12():
    df = read('BAT0012_rubia_spp_POS_NEG.xlsx', 'Table S1', 1)
    sc = [c for c in df.columns[15:]]
    cmap = {'name': 'Name', 'formula': 'Formula', 'superclass': 'Class', 'clase': 'Subclass',
            'mz': 'Measured mass (m/z)', 'rt': 'Retention time (s)', 'mode': 'Type', 'adduct': 'ms2Adduct',
            'level': 'level'}
    feats, mat = build(df, cmap, sc, rt_unit='s', fuente='Table S1')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(12, [(feats, mat)])


def b13():
    df = read('BAT0013_pinellia_pedatisecta_POS_NEG.xlsx', 'Table S1', 1)
    sc = list(df.columns[11:29])
    cmap = {'name': 'Name', 'formula': lambda r: s(r['Formula']).replace(' ', ''), 'mass': 'Molecular Weight',
            'rt': 'RT [min]', 'mz': 'm/z', 'superclass': 'HMDB_Superclass', 'clase': 'HMDB_Class',
            'subclass': 'HMDB_Subclass'}
    feats, mat = build(df, cmap, sc, fuente='Table S1',
                       mode_fn=lambda r: norm_mode(str(r['Compound_ID']).split('_')[-1]))
    finish(13, [(feats, mat)])


def b14():
    parts = []
    for sh, mode in [('Table S2', 'POS'), ('Table S3', 'NEG')]:
        df = read('BAT0014_pogostemon_cablin_POS_NEG.xlsx', sh, 1)
        sc = list(df.columns[3:18])
        cmap = {'name': 'MS2_name', 'rt': 'RT', 'mz': 'm/z', 'superclass': 'SuperClass', 'clase': 'Class',
                'subclass': 'SubClass'}
        parts.append(build(df, cmap, sc, fixed={'mode': mode}, fuente=sh))
    finish(14, parts)


def b15():
    df = read('BAT0015_nicotiana_tabacum_POS_NEG.xlsx', 'Table S1', 2)
    df = df[df['ID'].notna()]
    sc = [c for c in df.columns if re.fullmatch(r'(MC|NT|AC)-T\d-\d|CK-\d|QC\d+', str(c))]
    cmap = {'name': 'Name', 'level': 'Level', 'superclass': 'Class_I', 'clase': 'Class_II', 'formula': 'Formula',
            'mz': 'm/z', 'rt': 'RT [min]', 'mode': 'Type'}
    feats, mat = build(df, cmap, sc, rt_unit='s', fuente='Table S1')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(15, [(feats, mat)])


def b16():
    df = read('BAT0016_platostoma_chinense_POS.xlsx', 0)
    sc = list(df.columns[14:29])
    cmap = {'name': 'Name', 'formula': 'Formula', 'mass': 'Molecular Weight', 'rt': 'RT [min]',
            'superclass': 'Class I(English)', 'clase': 'Class II(English)'}
    feats, mat = build(df, cmap, sc, fuente='Sheet1',
                       mode_fn=lambda r: norm_mode(str(r['ID']).split('_')[-1]))
    finish(16, [(feats, mat)])


def b18():
    df = read('BAT0018_codonopsis_pilosula_POS.xlsx', 0, 1)
    sc = list(df.columns[7:19])
    feats, mat = build(df, {'mz': 'M/Z'}, sc, fuente='Table S1',
                       mode_fn=lambda r: norm_mode(str(r['Mode']).split('_')[0]))
    finish(18, [(feats, mat)])


def b20():
    f = 'BAT0020_mosla_chinensis_POS.xlsx'
    ann = []
    for sh in ['Table S6', 'Table S7', 'Table S8']:
        a = read(f, sh, 1)
        ann.append(a.iloc[:, :17])
    ann = pd.concat(ann).drop_duplicates(['ID', 'posneg'])
    ann['ID0'] = ann['ID'].astype(str).str.replace(r'_\d+$', '', regex=True)
    parts = []
    for sh, mode in [('Table S4', 'POS'), ('Table S5', 'NEG')]:
        df = read(f, sh, 1)
        a = ann[ann['posneg'].str.lower() == mode.lower()].drop_duplicates('ID0').set_index('ID0')
        for col_src, col_dst in [('name', 'name'), ('formula', 'formula'), ('exact_mass', 'exact_mass'),
                                 ('precursor_type', 'precursor_type'), ('class', 'class'),
                                 ('sub_class', 'sub_class'), ('level', 'level')]:
            df['A_' + col_dst] = df['ID'].map(a[col_src])
        sc = list(df.columns[4:13])
        cmap = {'mz': 'mz', 'rt': 'rt', 'name': 'A_name', 'formula': 'A_formula', 'mass': 'A_exact_mass',
                'adduct': 'A_precursor_type', 'clase': 'A_class', 'subclass': 'A_sub_class', 'level': 'A_level'}
        parts.append(build(df, cmap, sc, fixed={'mode': mode}, rt_unit='s', fuente=sh))
    finish(20, parts)


def b23():
    df = read('BAT0023_ipomoea_batatas_POS.xlsx', 0, 1)
    sc = list(df.columns[5:17])
    cmap = {'name': 'Compounds', 'superclass': 'Class I', 'rt': 'RT (min)', 'adduct': 'Adduct'}
    feats, mat = build(df, cmap, sc, fixed={'mode': 'POS'}, fuente='Table S1')
    finish(23, [(feats, mat)])


def b24():
    f = 'BAT0024_polygonatum_spp_POS.xlsx'
    xl = pd.ExcelFile(D + f, engine='calamine')
    feat_rows = {}
    vals = {}
    for sh in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sh, header=1)
        sc = [c for c in df.columns if re.fullmatch(r'P[SOCK]-\d', str(c))]
        for _, r in df.iterrows():
            k = r['ID']
            if k not in feat_rows:
                feat_rows[k] = r
                vals[k] = {}
            for c in sc:
                vals[k][c] = r[c]
    df = pd.DataFrame(list(feat_rows.values()))
    mat_df = pd.DataFrame([vals[k] for k in feat_rows])
    sc = sorted(mat_df.columns)
    df = pd.concat([df.reset_index(drop=True)[['ID', 'm/z', 'Retention time (min)', 'Ion mode', 'Metabolites',
                                               'Super Class', 'Class', 'Sub Class', 'level', 'Adducts',
                                               'Formula']],
                    mat_df[sc].reset_index(drop=True)], axis=1)
    cmap = {'name': 'Metabolites', 'mz': 'm/z', 'rt': 'Retention time (min)', 'mode': 'Ion mode',
            'superclass': 'Super Class', 'clase': 'Class', 'subclass': 'Sub Class', 'level': 'level',
            'adduct': lambda r: s(r['Adducts']).split(',')[0].strip(), 'formula': 'Formula'}
    feats, mat = build(df, cmap, sc, fuente='Tablas 2-1 a 2-6 (union)')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(24, [(feats, mat)])


def b26():
    df = read('BAT0026_medicago_sativa_POS_NEG.xlsx', 0)
    df = df[df['ID'].astype(str) != 'label']
    sc = [c for c in df.columns if re.fullmatch(r'(WD|WW)_\d_\d|QC.*', str(c).strip())]
    cmap = {'name': 'Metabolites', 'mz': 'm/z', 'rt': 'Retention time (min)', 'mode': 'Ion mode',
            'adduct': 'Adducts', 'formula': 'Formula'}
    feats, mat = build(df, cmap, sc, fuente='sheet 1')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(26, [(feats, mat)])


def b27():
    f = 'BAT0027_camellia_tetracocca_POS.xlsx'
    df = read(f, 'E_N')
    sc = ['E1', 'E2', 'E3', 'N1', 'N2', 'N3']
    cmap = {'name': 'Metabolites', 'mz': 'm/z', 'rt': 'Retention time (min)', 'mode': 'Ion mode',
            'superclass': 'Super Class', 'clase': 'Class', 'subclass': 'Sub Class', 'level': 'level',
            'adduct': lambda r: s(r['Adducts']).split(',')[0].strip(), 'formula': 'Formula'}
    p1 = build(df, cmap, sc, fuente='E_N')
    p1[0]['mode'] = p1[0]['mode'].map(norm_mode)
    g = read(f, 'Sheet1')
    cmap2 = {'name': 'Metabolites', 'mz': 'Quant mass', 'rt': 'Average Rt(min)', 'superclass': 'Super Class',
             'clase': 'Class', 'subclass': 'Sub Class'}
    p2 = build(g, cmap2, sc, fixed={'mode': 'EI', 'plataforma': 'GC-MS'}, fuente='Sheet1 (GC-MS)')
    finish(27, [p1, p2])


def b28():
    df = read('BAT0028_gastrodia_elata_POS_NEG.xlsx', 0)
    sc = list(df.columns[14:32])
    cmap = {'name': 'Metabolite', 'formula': lambda r: s(r['Formula']).replace(' ', ''),
            'mass': 'Molecular Weight', 'rt': 'RT [min]', 'superclass': 'Super.class', 'clase': 'Class',
            'subclass': 'Sub_class'}
    feats, mat = build(df, cmap, sc, fuente='Sheet1',
                       mode_fn=lambda r: norm_mode(str(r['Mode_ID']).split('_')[0]))
    finish(28, [(feats, mat)])


def b29():
    df = read('BAT0029_camellia_sinensis_POS_NEG.xlsx', 0, 1)
    sc = ['WE', 'WI', 'WPE', 'WPI', 'PE', 'PI', 'QC']
    cmap = {'name': 'Compounds', 'formula': 'Formula', 'mass': 'Molecular weight (Da)',
            'adduct': 'Ionization model', 'superclass': 'Classfication'}
    feats, mat = build(df, cmap, sc, fuente='Sheet1',
                       mode_fn=lambda r: adduct_mode(r['Ionization model']))
    finish(29, [(feats, mat)])


def b30():
    parts = []
    for sh, mode in [('all.exp.POS', 'POS'), ('all.exp.NEG', 'NEG')]:
        df = read('BAT0030_morus_alba_POS_NEG.xlsx', sh, 1)
        sc = list(df.columns[6:21])
        cmap = {'name': lambda r: s(r['MS2_name']) or s(r['MS1_name']),
                'formula': lambda r: s(r['formula']).replace(' ', ''), 'rt': 'rtmin', 'mz': 'mz', 'clase': 'Class'}
        parts.append(build(df, cmap, sc, fixed={'mode': mode}, fuente=sh))
    finish(30, parts)


def b33():
    df = read('BAT0033_camellia_drupifera_POS_NEG.xlsx', 0)
    sc = list(df.columns[9:21])
    cmap = {'name': 'Compounds', 'clase': 'Class', 'mz': 'Q1 (Da)', 'mass': 'Molecular Weight',
            'adduct': 'Ionization model', 'formula': 'Formula'}
    feats, mat = build(df, cmap, sc, fixed={'superclass': 'Flavonoids'}, fuente='shee1',
                       mode_fn=lambda r: norm_mode(r['Ion mode']))
    finish(33, [(feats, mat)])


def b34():
    df = read('BAT0034_avena_sativa_triticum_aestivum_NA.xlsx', 0)
    df = df[df['sample'] != 'status']
    sc = list(df.columns[4:40])
    cmap = {'name': 'sample', 'mz': 'm/z', 'rt': 'retention time', 'formula': lambda r: re.sub(r'([A-Z][a-z]?)1(?![0-9])', r'\1', s(r['formula']))}
    feats, mat = build(df, cmap, sc, fuente='ST9')
    finish(34, [(feats, mat)])


def b35():
    df = read('BAT0035_panax_quinquefolius_POS_NEG.xlsx', 0, 1)
    sc = list(df.columns[9:29])
    cmap = {'name': 'Name', 'formula': lambda r: s(r['Formula']).replace(' ', ''), 'mass': 'Molecular Weight',
            'rt': 'RT [min]', 'mz': 'm/z'}
    feats, mat = build(df, cmap, sc, fuente='Sheet1',
                       mode_fn=lambda r: norm_mode(str(r['Compound_ID']).split('_')[-1]))
    finish(35, [(feats, mat)])


def b36():
    parts = []
    for sh, mode in [('POS ion mode ', 'POS'), ('NEG ion mode', 'NEG')]:
        df = read('BAT0036_morus_alba_POS_NEG.xlsx', sh, 2)
        sc = list(df.columns[4:22])
        cmap = {'name': 'MS2_name', 'rt': 'RT', 'mz': 'm/z', 'clase': 'Class'}
        parts.append(build(df, cmap, sc, fixed={'mode': mode}, rt_unit='s', fuente=sh.strip()))
    finish(36, parts)


def b37():
    df = read('BAT0037_neolamarckia_cadamba_POS_NEG.xlsx', 0, 2)
    df = df.iloc[1:]
    names = list(df.columns[:11]) + ['WA1', 'WA2', 'WA3', 'ET1', 'ET2', 'ET3', 'mix01', 'mix02', 'mix03']
    df.columns = names
    sc = names[11:]
    cmap = {'name': 'Compounds', 'formula': 'Formula', 'mass': 'Molecular Weight (Da)', 'mz': 'Q1 (Da)',
            'adduct': 'Ionization model', 'superclass': 'Class ', 'clase': 'Sub-class'}
    feats, mat = build(df, cmap, sc, metware9=True, fuente='Table S2',
                       mode_fn=lambda r: adduct_mode(r['Ionization model']))
    finish(37, [(feats, mat)])


def b39():
    parts = []
    for sh in ['Positive ion mode', 'Negative ion mode']:
        df = read('BAT0039_chrysanthemum_morifolium_POS_NEG.xlsx', sh, 1)
        sc = list(df.columns[12:42])
        cmap = {'name': 'Metabolites', 'mode': 'Ion mode', 'formula': 'Formula', 'mz': 'm/z',
                'rt': 'Retention time (min)', 'adduct': lambda r: s(r['Adducts']).split(',')[0].strip()}
        p = build(df, cmap, sc, tiny=1e-6, fuente=sh)
        p[0]['mode'] = p[0]['mode'].map(norm_mode)
        parts.append(p)
    finish(39, parts)


def b42():
    df = read('BAT0042_sesamum_indicum_NA.xlsx', 0, 1)
    df = df.iloc[1:]
    names = list(df.columns[:9]) + ['QC', 'FC', 'FS', 'ML', 'PF', 'WF']
    df.columns = names
    cmap = {'name': 'Compounds', 'formula': 'Formula', 'mass': 'Molecular Weight (Da)', 'mz': 'Q1 (Da)',
            'adduct': 'Ionization model', 'superclass': 'Class '}
    feats, mat = build(df, cmap, names[9:], metware9=True, fuente='Table S1.',
                       mode_fn=lambda r: adduct_mode(r['Ionization model']))
    finish(42, [(feats, mat)])


def b44():
    df = read('BAT0044_cormus_domestica_POS_NEG.xlsx', 0, 1)
    sc = list(df.columns[7:16])
    cmap = {'name': 'Compound', 'superclass': 'SUPERCLASS', 'clase': 'CLASS/SUBCLASS', 'formula': 'Formula',
            'mass': 'Calc. MW', 'rt': 'RT [min]'}
    feats, mat = build(df, cmap, sc, fuente='Foglio1')
    finish(44, [(feats, mat)])


def b46():
    df = read('BAT0046_glycyrrhiza_spp_POS_NEG.xlsx', 0, 1)
    sc = [c for c in df.columns if re.fullmatch(r'G(inf|ura|pal|asp)_\d|QC\d+', str(c))]
    cmap = {'name': 'Compounds', 'formula': 'Formula', 'mass': 'Molecular weight (Da)', 'mz': 'Q1 (Da)',
            'adduct': 'Ionization model', 'superclass': 'Class I', 'clase': 'Class II', 'level': 'Level',
            'plataforma': lambda r: 'GC-MS' if 'GC' in str(r['Platform']) else 'LC-MS'}
    def mode(r):
        if 'GC' in str(r['Platform']):
            return 'EI'
        return adduct_mode(r['Ionization model'])
    feats, mat = build(df, cmap, sc, metware9=True, fuente='Sheet1', mode_fn=mode)
    feats['plataforma'] = df.reset_index(drop=True).apply(cmap['plataforma'], axis=1)
    finish(46, [(feats, mat)])


def b47():
    df = read('BAT0047_lonicera_japonica_POS_NEG.xlsx', 0)
    sc = list(df.columns[17:35])
    cmap = {'name': 'name', 'mz': 'mz', 'rt': 'rt', 'mass': 'exact_mass', 'formula': 'formula',
            'adduct': 'precursor_type', 'clase': 'class', 'subclass': 'sub_class', 'level': 'level',
            'mode': 'posneg'}
    feats, mat = build(df, cmap, sc, rt_unit='s', fuente='Sheet1')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(47, [(feats, mat)])


def b52():
    df = read('BAT0052_striga_asiatica_POS_NEG.xlsx', 0, 1)
    sc = list(df.columns[24:48])
    cmap = {'name': 'Metabolite', 'mode': 'Mode', 'mz': 'M/Z',
            'adduct': lambda r: s(r['Adducts']).split(',')[0].strip(), 'formula': 'Formula',
            'rt': 'Retention time', 'superclass': 'HMDB Superclass', 'clase': 'HMDB Class',
            'subclass': 'HMDB Subclass'}
    feats, mat = build(df, cmap, sc, fuente='Table S2')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(52, [(feats, mat)])


def b54():
    df = read('BAT0054_withania_somnifera_POS_NEG.xlsx', 0)
    df = df[df['Metabolite'].notna()]
    sc = ['Area: BR1', 'Area: BR2', 'Area: BR3']
    def cls(i):
        def f(r):
            parts = [p.strip() for p in re.split(r'_', str(r['Major Class_Class_Subclass_PMDB ID_Metabolite']).replace('\n', ''))]
            return parts[i] if len(parts) > i else ''
        return f
    def ion(r):
        a = s(r['Reference Ion'])
        return re.sub(r'([+-])1$', r'\1', a)
    cmap = {'name': lambda r: ' '.join(str(r['Metabolite']).split()), 'rt': 'RT [min]', 'mass': 'Calc. MW',
            'mz': 'm/z', 'adduct': ion, 'formula': lambda r: s(r['Formula']).replace(' ', ''),
            'superclass': cls(1), 'clase': cls(2)}
    feats, mat = build(df, cmap, sc, fuente='Sheet1', mode_fn=lambda r: adduct_mode(ion(r)))
    finish(54, [(feats, mat)])


def b55():
    df = pd.read_csv(D + 'BAT0055_cibotium_barometz_NA.xls', sep='\t')
    sc = [c for c in df.columns if re.fullmatch(r'(W[RSLNP]|DM|ZP)_\d|QC\d', c)]
    cmap = {'name': 'Name', 'formula': 'Formula', 'adduct': 'Reference_Ion', 'rt': 'RT_min', 'mz': 'm/z',
            'mode': 'Mode', 'superclass': 'SuperClass', 'clase': 'Class', 'subclass': 'SubClass'}
    feats, mat = build(df, cmap, sc, fuente='tsv')
    feats['mode'] = feats['mode'].map(norm_mode)
    finish(55, [(feats, mat)])


def b57():
    df = read('BAT0057_capsicum_annuum_POS_NEG.xlsx', 0)
    sc = list(df.columns[33:54])
    cmap = {'name': 'Metabolites', 'mz': 'm/z', 'rt': 'Retention time (min)', 'mode': 'Ion mode',
            'superclass': 'Super Class', 'clase': 'Class', 'subclass': 'Sub Class', 'level': 'level',
            'adduct': lambda r: s(r['Adducts']).split(',')[0].strip(), 'formula': 'Formula',
            'plataforma': lambda r: 'GC-MS' if 'GC' in str(r['Ion mode']) else 'LC-MS'}
    feats, mat = build(df, cmap, sc, fuente='Data')
    feats['mode'] = feats['mode'].map(norm_mode)
    feats['plataforma'] = df.reset_index(drop=True).apply(cmap['plataforma'], axis=1)
    finish(57, [(feats, mat)])


JOBS = {
    1: b01, 2: b02, 3: b03, 4: b04,
    5: lambda: b05_06(5, 'BAT0005_malpighiaceae_spp_POS.csv', 'POS'),
    6: lambda: b05_06(6, 'BAT0006_malpighiaceae_spp_NEG.csv', 'NEG'),
    7: b07,
    8: lambda: metware_untargeted(8, 'BAT0008_solanum_tuberosum_POS_NEG.xlsx', samples_re=r'TQW-\d|CHW-\d|QC\d+'),
    9: lambda: b09_10(9, 'BAT0009_oldenlandia_spp_NEG.xlsx', 'NEG'),
    10: lambda: b09_10(10, 'BAT0010_oldenlandia_spp_POS.xlsx', 'POS'),
    11: b11, 12: b12, 13: b13, 14: b14, 15: b15, 16: b16,
    17: lambda: metware_targeted(17, 'BAT0017_eriobotrya_japonica_POS.xlsx', samples_re=r'(FS|HD|FD|FSP|HDP|FDP)\d|QC\d+'),
    18: b18,
    19: lambda: metware_untargeted(19, 'BAT0019_spatholobus_suberectus_POS_NEG.xlsx', samples_re=r'[A-Z][a-z]+_\d'),
    20: b20,
    21: lambda: metware_targeted(21, 'BAT0021_fagopyrum_dibotrys_POS_NEG.xls', header=1, samples_re=r'(CS|CF|YQ|YK|GB)-\d'),
    22: lambda: metware_targeted(22, 'BAT0022_akebia_trifoliata_POS_NEG.xlsx', 'Table S1', 1, samples_re=r'S\d-\d'),
    23: b23, 24: b24,
    25: lambda: metware_targeted(25, 'BAT0025_fragaria_ananassa_POS_NEG.xlsx', samples_re=r'(ZT|ZT99|DD99)-\d|QC\d+'),
    26: b26, 27: b27, 28: b28, 29: b29, 30: b30,
    31: lambda: metware_targeted(31, 'BAT0031_dioscorea_opposita_POS_NEG.xlsx', 'Table S1', 1, samples_re=r'(SCY|LCY|QC)\d'),
    32: lambda: metware_targeted(32, 'BAT0032_taxus_media_POS_NEG.xlsx', 0, 1, samples_re=r'(TB|TFL|TS|TA)-\d|mix\d+'),
    33: b33, 34: b34, 35: b35, 36: b36, 37: b37,
    38: lambda: metware_targeted(38, 'BAT0038_paeonia_lactiflora_POS_NEG.xlsx', samples_re=r'(CK|DFG|HSML)\d|mix\d+',
                                 extra={'mz': 'Q1 (Da)更新'}),
    39: b39,
    40: lambda: metware_targeted(40, 'BAT0040_rosaceae_spp_POS_NEG.xlsx', samples_re=r'[HTL][YF]-\d|mix\d+'),
    41: lambda: metware_untargeted(41, 'BAT0041_ipomoea_batatas_POS_NEG.xlsx', 0, 1, samples_re=r'(BS|CS|ZS)-\d|QC\d+'),
    42: b42,
    43: lambda: metware_targeted(43, 'BAT0043_dendrobium_officinale_POS_NEG.xlsx', samples_re=r'(SEC|TEC|GC)-\d|QC\d+'),
    44: b44,
    45: lambda: metware_targeted(45, 'BAT0045_clematis_tangutica_POS_NEG.xlsx', samples_re=r'(JZ|MY|GH|DQ|ZD)-\d|QC\d+'),
    46: b46, 47: b47,
    48: lambda: metware_targeted(48, 'BAT0048_lonicera_japonica_POS_NEG.xlsx', samples_re=r'R(tri|fau|niv|str)_\d|QC\d+'),
    49: lambda: metware_untargeted(49, 'BAT0049_citrus_reticulata_POS_NEG.xlsx', 0, 1, samples_re=r'CCPY\d|QC'),
    50: lambda: metware_targeted(50, 'BAT0050_actinidia_chinensis_POS_NEG.xlsx', 0, 1, samples_re=r'(LC|DY|GC|SG|WL)\d|QC\d+'),
    51: lambda: metware_targeted(51, 'BAT0051_camellia_oleifera_POS_NEG.xlsx', samples_re=r'CL\d+-\d|QC\d+'),
    52: b52,
    53: lambda: metware_targeted(53, 'BAT0053_hemerocallis_citrina_POS_NEG.xlsx', 0, 1, samples_re=r'[FLSR]h\d'),
    54: b54, 55: b55,
    56: lambda: metware_targeted(56, 'BAT0056_lagerstroemia_spp_POS_NEG.xlsx', 0, 1, samples_re=r'(LS|LC|LI)\d|QC\d+'),
    57: b57,
}

if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or sorted(JOBS)
    for i in ids:
        try:
            JOBS[i]()
        except Exception as e:
            import traceback
            print(f'B{i:02d}: ERROR {e!r}')
            traceback.print_exc(limit=3)
