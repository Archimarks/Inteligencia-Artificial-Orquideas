"""Construye los catalogos, la tabla pivote y Dataset.csv a partir de los
batches parseados (parse.py) y de las definiciones curadas."""
import csv, glob, math, os, pickle, re, sys
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalogos_def import *          # noqa
from batch_def import B, LOG_BASE, qc_blank, QC, BLANCO
from actividades_def import LIT, EXP_SIN_VALOR
from medidas import MEDIDAS

ROOT = '/home/user/Inteligencia-Artificial-Orquideas'
OUT = os.environ.get('OUT_DIR', ROOT + '/01_Datos/Dataset')
PARSED = os.environ.get('PARSED_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed'))
ND = 'No disponible'
NE = 'No especificado'


def write_cat(rel, header, rows):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(['' if v is None else v for v in r])
    print(f'  {rel}: {len(rows)} filas')


# ============================================================ articulos ====
def articulos():
    g = pd.read_csv(ROOT + '/01_Datos/Data/BASE DE DATOS GLOBAL.csv', dtype=str)
    g.columns = [c.strip() for c in g.columns]
    def norm(t):
        return ' '.join(str(t).split()) if isinstance(t, str) else ''
    def doi(d):
        d = norm(d)
        if not d or d.lower().startswith('no info'):
            return ND
        d = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', d)
        return 'https://doi.org/' + d
    bymap = {}
    for _, r in g.iterrows():
        bymap[norm(r['ID'])] = (norm(r['PAPER name']), doi(r['DOI-PAPER']))
    files = sorted(os.listdir(ROOT + '/01_Datos/Data/Articulos'))
    # articulo -> batch representativo en la base global
    art_batch = {}
    for b, cfg in B.items():
        art_batch.setdefault(cfg['art'], b)
    rows = [(0, ND, ND, ND)]
    for f in files:
        aid = int(f[3:7])
        if aid == 4:
            t, d = bymap['SIN BATCH TABLE']
            d = 'https://doi.org/10.1038/s41598-025-94958-3'
        else:
            t, d = bymap[f'BATCH {art_batch[aid]}']
        if aid == 3:
            d = 'https://doi.org/10.1016/j.cj.2026.01.012'
        rows.append((aid, f, t, d))
    t, d = bymap['BATCH 48']
    rows.append((53, ND + ' (articulo no incluido en la carpeta Articulos; datos de BASE DE DATOS GLOBAL)', t, d))
    return rows


# ============================================================ taxonomia ====
def taxonomia():
    T = {}
    T['reino'] = [(0, NE, ND)] + [(1, n, d) for n, d in REINOS]
    rid = {n: i + 1 for i, (n, _) in enumerate(REINOS)}
    T['filo'] = [(0, 0, NE, ND)] + [(i + 1, rid[r], n, d) for i, (n, r, d) in enumerate(FILOS)]
    fid = {n: i + 1 for i, (n, _, _) in enumerate(FILOS)}
    filo_reino = {n: rid[r] for n, r, _ in FILOS}
    T['clase'] = [(0, 0, NE, ND)] + [(i + 1, fid[f], n, d) for i, (n, f, d) in enumerate(CLASES)]
    cid = {n: i + 1 for i, (n, _, _) in enumerate(CLASES)}
    clase_filo = {n: f for n, f, _ in CLASES}
    ords = sorted(ORDENES)
    T['orden'] = [(0, 0, NE, ND)] + [(i + 1, cid[ORDENES[o][0]], o, ORDENES[o][1]) for i, o in enumerate(ords)]
    oid = {o: i + 1 for i, o in enumerate(ords)}
    fams = sorted(FAMILIAS)
    T['familia'] = [(0, 0, NE, ND)] + [(i + 1, oid[FAMILIAS[f][0]], f, FAMILIAS[f][1]) for i, f in enumerate(fams)]
    famid = {f: i + 1 for i, f in enumerate(fams)}
    gens = sorted(GENEROS)
    T['genero'] = [(0, 0, NE, ND)] + [(i + 1, famid[GENEROS[g]], g, f'Genero de la familia {GENEROS[g]}') for i, g in enumerate(gens)]
    gid = {g: i + 1 for i, g in enumerate(gens)}
    T['especie'] = [(0, 0, NE, NE, ND)] + [(i + 1, gid[g], n, c, d) for i, (k, g, n, c, d) in enumerate(ESPECIES)]
    spid = {k: i + 1 for i, (k, *_r) in enumerate(ESPECIES)}
    # cadena completa por especie
    chain = {}
    for k, g, *_r in ESPECIES:
        fam = GENEROS[g]; o = FAMILIAS[fam][0]; c = ORDENES[o][0]; fi = clase_filo[c]
        chain[k] = dict(ID_REINO=filo_reino[fi], ID_FILO=fid[fi], ID_CLASE_TAXONOMICA=cid[c], ID_ORDEN=oid[o],
                        ID_FAMILIA=famid[fam], ID_GENERO=gid[g], ID_ESPECIE=spid[k])
    def fam_chain(fam):
        o = FAMILIAS[fam][0]; c = ORDENES[o][0]; fi = clase_filo[c]
        return dict(ID_REINO=filo_reino[fi], ID_FILO=fid[fi], ID_CLASE_TAXONOMICA=cid[c], ID_ORDEN=oid[o],
                    ID_FAMILIA=famid[fam], ID_GENERO=0, ID_ESPECIE=0)
    return T, chain, fam_chain, spid


TAXK = ['ID_REINO', 'ID_FILO', 'ID_CLASE_TAXONOMICA', 'ID_ORDEN', 'ID_FAMILIA', 'ID_GENERO', 'ID_ESPECIE']


def common_chain(chains):
    out = {}
    for k in TAXK:
        vals = {c[k] for c in chains}
        out[k] = vals.pop() if len(vals) == 1 else 0
    # si un nivel superior difiere, los inferiores tampoco son comunes
    zero = False
    for k in TAXK:
        if zero:
            out[k] = 0
        elif out[k] == 0:
            zero = True
    return out


# ====================================================== quimica / clases ===
SUPER_MAP = {
    'alkaloids': 'Alkaloids and derivatives', 'alkaloids and derivatives': 'Alkaloids and derivatives',
    'alcohol and amines': 'Organic nitrogen compounds', 'amines': 'Organic nitrogen compounds', 'polyamine': 'Organic nitrogen compounds',
    'tryptamines,cholines,pigments': 'Organic nitrogen compounds',
    'alcohols and polyols': 'Organic oxygen compounds', 'organooxygen compounds': 'Organic oxygen compounds',
    'carbohydrates': 'Organic oxygen compounds', 'carbohydrates and its derivatives': 'Organic oxygen compounds',
    'abscisic acid': 'Lipids and lipid-like molecules', 'gibberellins': 'Lipids and lipid-like molecules',
    'brassinosteroids': 'Lipids and lipid-like molecules', 'jasmonates': 'Lipids and lipid-like molecules',
    'auxins': 'Organoheterocyclic compounds', 'cytokinins': 'Organoheterocyclic compounds',
    'amino acid and its derivatives': 'Organic acids and derivatives', 'amino acid and its metabolites': 'Organic acids and derivatives',
    'amino acids and peptides': 'Organic acids and derivatives', 'amino acids and derivatives': 'Organic acids and derivatives',
    'amino acids and their derivatives': 'Organic acids and derivatives', 'organic acids': 'Organic acids and derivatives',
    'organic acid and its derivatives': 'Organic acids and derivatives', 'organic acids and derivative': 'Organic acids and derivatives',
    'benzene and substituted derivatives': 'Benzenoids', 'phenols and its derivatives': 'Benzenoids', 'quinones': 'Benzenoids',
    'fa': 'Lipids and lipid-like molecules', 'fa fatty acyls': 'Lipids and lipid-like molecules', 'fatty acids': 'Lipids and lipid-like molecules',
    'gl': 'Lipids and lipid-like molecules', 'gp': 'Lipids and lipid-like molecules', 'sl': 'Lipids and lipid-like molecules',
    'lipids': 'Lipids and lipid-like molecules', 'steroids': 'Lipids and lipid-like molecules', 'terpenoids': 'Lipids and lipid-like molecules',
    'flavonoids': 'Phenylpropanoids and polyketides', 'flavonoids and their derivatives': 'Phenylpropanoids and polyketides',
    'phenolic acids': 'Phenylpropanoids and polyketides', 'phenolics': 'Phenylpropanoids and polyketides', 'tannins': 'Phenylpropanoids and polyketides',
    'polyketides': 'Phenylpropanoids and polyketides', 'pk polyketides': 'Phenylpropanoids and polyketides',
    'phenylpropanoids': 'Phenylpropanoids and polyketides', 'shikimates and phenylpropanoids': 'Phenylpropanoids and polyketides',
    'heterocyclic compounds': 'Organoheterocyclic compounds', 'organoheterocyclic metabolites': 'Organoheterocyclic compounds',
    'nucleotide and its derivates': 'Nucleosides, nucleotides, and analogues', 'nucleotides and derivatives': 'Nucleosides, nucleotides, and analogues',
    'nucleotides and their derivatives': 'Nucleosides, nucleotides, and analogues',
    'organic nitrogen metabolites': 'Organic nitrogen compounds', 'organic oxygen metabolites': 'Organic oxygen compounds',
    'organosulfur metabolites': 'Organosulfur compounds', 'organic 1,3-dipolar metabolites': 'Organic 1,3-dipolar compounds',
    'lignans, neolignans and related metabolites': 'Lignans, neolignans and related compounds',
}
CLASSYFIRE_SUPER = ['Alkaloids and derivatives', 'Benzenoids', 'Homogeneous metal compounds', 'Homogeneous non-metal compounds',
                    'Hydrocarbon derivatives', 'Hydrocarbons', 'Lignans, neolignans and related compounds', 'Lipids and lipid-like molecules',
                    'Mixed metal/non-metal compounds', 'Nucleosides, nucleotides, and analogues', 'Organic 1,3-dipolar compounds',
                    'Organic acids and derivatives', 'Organic nitrogen compounds', 'Organic oxygen compounds', 'Organic Polymers',
                    'Organohalogen compounds', 'Organoheterocyclic compounds', 'Organometallic compounds', 'Organophosphorus compounds',
                    'Organosulfur compounds', 'Phenylpropanoids and polyketides']
for sc in CLASSYFIRE_SUPER:
    SUPER_MAP[sc.lower()] = sc
SUPER_DESC = {
    'Alkaloids and derivatives': 'Compuestos nitrogenados basicos de origen natural (alcaloides) y derivados',
    'Benzenoids': 'Compuestos aromaticos con anillo bencenico (fenoles, benzoatos, quinonas)',
    'Homogeneous metal compounds': 'Compuestos formados solo por atomos metalicos',
    'Homogeneous non-metal compounds': 'Compuestos inorganicos formados solo por no metales',
    'Hydrocarbon derivatives': 'Derivados de hidrocarburos con heteroatomos simples',
    'Hydrocarbons': 'Compuestos formados solo por carbono e hidrogeno',
    'Lignans, neolignans and related compounds': 'Dimeros de fenilpropanoides (lignanos y neolignanos)',
    'Lipids and lipid-like molecules': 'Acidos grasos, glicerolipidos, fosfolipidos, esteroides, terpenoides (prenol lipidos)',
    'Mixed metal/non-metal compounds': 'Compuestos con atomos metalicos y no metalicos',
    'Nucleosides, nucleotides, and analogues': 'Nucleosidos, nucleotidos y analogos',
    'Organic 1,3-dipolar compounds': 'Compuestos organicos 1,3-dipolares',
    'Organic acids and derivatives': 'Acidos carboxilicos, aminoacidos, peptidos y derivados',
    'Organic nitrogen compounds': 'Compuestos organicos nitrogenados (aminas, colinas)',
    'Organic oxygen compounds': 'Compuestos organicos oxigenados (carbohidratos, alcoholes, carbonilos)',
    'Organic Polymers': 'Polimeros organicos',
    'Organohalogen compounds': 'Compuestos organicos halogenados',
    'Organoheterocyclic compounds': 'Compuestos heterociclicos (indoles, piridinas, purinas, cumarinas simples)',
    'Organometallic compounds': 'Compuestos organometalicos',
    'Organophosphorus compounds': 'Compuestos organofosforados',
    'Organosulfur compounds': 'Compuestos organoazufrados',
    'Phenylpropanoids and polyketides': 'Flavonoides, acidos fenolicos, cumarinas, taninos, estilbenos y policetidos',
}
CLASS_SUPER_MANUAL = {
    'carboxylic acids and derivatives': 'Organic acids and derivatives', 'organooxygen compounds': 'Organic oxygen compounds',
    'fatty acyls': 'Lipids and lipid-like molecules', 'benzene and substituted derivatives': 'Benzenoids',
    'prenol lipids': 'Lipids and lipid-like molecules', 'flavonoids': 'Phenylpropanoids and polyketides',
    'steroids and steroid derivatives': 'Lipids and lipid-like molecules', 'phenols': 'Benzenoids',
    'organonitrogen compounds': 'Organic nitrogen compounds', 'indoles and derivatives': 'Organoheterocyclic compounds',
    'imidazopyrimidines': 'Organoheterocyclic compounds', 'pyridines and derivatives': 'Organoheterocyclic compounds',
    'coumarins and derivatives': 'Phenylpropanoids and polyketides', 'isoflavonoids': 'Phenylpropanoids and polyketides',
    'cinnamic acids and derivatives': 'Phenylpropanoids and polyketides', 'quinolines and derivatives': 'Organoheterocyclic compounds',
    'terpenoids': 'Lipids and lipid-like molecules', 'diazines': 'Organoheterocyclic compounds', 'alkaloids': 'Alkaloids and derivatives',
    'benzopyrans': 'Organoheterocyclic compounds', 'purine nucleosides': 'Nucleosides, nucleotides, and analogues',
    'pteridines and derivatives': 'Organoheterocyclic compounds', 'hydroxy acids and derivatives': 'Organic acids and derivatives',
    'keto acids and derivatives': 'Organic acids and derivatives', 'purine nucleotides': 'Nucleosides, nucleotides, and analogues',
    'glycerophospholipids': 'Lipids and lipid-like molecules', 'azoles': 'Organoheterocyclic compounds', 'lactones': 'Organoheterocyclic compounds',
    'organic phosphoric acids and derivatives': 'Organic acids and derivatives', 'naphthalenes': 'Benzenoids',
    'pyrimidine nucleosides': 'Nucleosides, nucleotides, and analogues', 'phenol ethers': 'Benzenoids',
    'pyrimidine nucleotides': 'Nucleosides, nucleotides, and analogues', 'phenylpropanoids': 'Phenylpropanoids and polyketides',
    'linear 1,3-diarylpropanoids': 'Phenylpropanoids and polyketides', 'phenylpropanoic acids': 'Phenylpropanoids and polyketides',
    'stilbenes': 'Phenylpropanoids and polyketides', 'morphinans': 'Alkaloids and derivatives', 'lactams': 'Organoheterocyclic compounds',
    'phenanthrenes and derivatives': 'Benzenoids', 'anthracenes': 'Benzenoids', 'piperidines': 'Organoheterocyclic compounds',
    'isoquinolines and derivatives': 'Organoheterocyclic compounds', "5'-deoxyribonucleosides": 'Nucleosides, nucleotides, and analogues',
    'diazanaphthalenes': 'Organoheterocyclic compounds', 'carbohydrates and carbohydrate conjugates': 'Organic oxygen compounds',
    'carboximidic acids and derivatives': 'Organic acids and derivatives', 'glycerolipids': 'Lipids and lipid-like molecules',
    'triazines': 'Organoheterocyclic compounds', 'furanoid lignans': 'Lignans, neolignans and related compounds',
    'macrolides and analogues': 'Phenylpropanoids and polyketides', 'diarylheptanoids': 'Phenylpropanoids and polyketides',
    'pyrans': 'Organoheterocyclic compounds', 'tropane alkaloids': 'Alkaloids and derivatives', 'tannins': 'Phenylpropanoids and polyketides',
    'carbonyl compounds': 'Organic oxygen compounds', 'sphingolipids': 'Lipids and lipid-like molecules', 'saccharides': 'Organic oxygen compounds',
    'steroids': 'Lipids and lipid-like molecules', 'quinones': 'Benzenoids', 'amino acids': 'Organic acids and derivatives',
    'polyketides': 'Phenylpropanoids and polyketides', 'fatty acids': 'Lipids and lipid-like molecules',
    'lignan glycosides': 'Lignans, neolignans and related compounds', 'lignan lactones': 'Lignans, neolignans and related compounds',
    'dibenzylbutane lignans': 'Lignans, neolignans and related compounds', 'tetrapyrroles and derivatives': 'Organoheterocyclic compounds',
    'furans': 'Organoheterocyclic compounds', 'pyrroles': 'Organoheterocyclic compounds', 'cinnamaldehydes': 'Phenylpropanoids and polyketides',
    'organic sulfonic acids and derivatives': 'Organic acids and derivatives', 'flavin nucleotides': 'Nucleosides, nucleotides, and analogues',
    '2-arylbenzofuran flavonoids': 'Phenylpropanoids and polyketides', 'cinnamyl alcohols': 'Phenylpropanoids and polyketides',
    'flavonolignans': 'Phenylpropanoids and polyketides', 'pyridine nucleotides': 'Nucleosides, nucleotides, and analogues',
    'organic oxides': 'Organic oxygen compounds', 'alcohols and polyols': 'Organic oxygen compounds', 'amines': 'Organic nitrogen compounds',
    'azacyclic compounds': 'Organoheterocyclic compounds', 'aromatic hydrocarbons': 'Hydrocarbons', 'saturated hydrocarbons': 'Hydrocarbons',
    'thiols': 'Organosulfur compounds', 'thioethers': 'Organosulfur compounds', 'organic disulfides': 'Organosulfur compounds',
    'benzofurans': 'Organoheterocyclic compounds', 'tetrahydrofurans': 'Organoheterocyclic compounds', 'naphthopyrans': 'Organoheterocyclic compounds',
    'endocannabinoids': 'Lipids and lipid-like molecules', 'organic carbonic acids and derivatives': 'Organic acids and derivatives',
}
NO_CHEM = re.compile(r'(drug|endogenous|chemical|natural products|toxin|pesticide|additive|cosmetic|counterfeit|extractable|'
                     r'excipient|textile|leachable|medicine|doping|hormones)', re.I)


def cap(s):
    s = ' '.join(str(s).split()).strip(' |_')
    return s[:1].upper() + s[1:] if s else ''


def harmonize(sc_raw, cl_raw):
    sc_raw = cap(re.sub(r'\|.*$', '', sc_raw or ''))
    cl_raw = cap(re.sub(r'\|.*$', '', cl_raw or ''))
    if NO_CHEM.search(cl_raw) or ';' in cl_raw:
        cl_raw = ''
    if cl_raw.lower() in ('others', 'other', 'unclassified', '-', '--', 'not available', 'nan', 'none', 'hash(0x34b1ff8)'):
        cl_raw = ''
    if cl_raw.startswith('HASH('):
        cl_raw = ''
    low = sc_raw.lower()
    sup = SUPER_MAP.get(low, '')
    if low == 'lignans and coumarins':
        sup = 'Lignans, neolignans and related compounds' if 'lignan' in cl_raw.lower() else 'Phenylpropanoids and polyketides'
    clase = cl_raw
    # superclases Metware/NPClassifier: conservar su nombre como clase si no hay una mas fina
    if sup and low not in {s.lower() for s in CLASSYFIRE_SUPER} and not clase:
        clase = sc_raw
    if sup and clase.lower() == sup.lower():
        clase = ''
    return sup, clase


# ================================================================ formula ===
MASS = {'C': 12.0, 'H': 1.00782503207, 'N': 14.0030740048, 'O': 15.99491461956, 'P': 30.97376163, 'S': 31.97207100,
        'Cl': 34.96885268, 'Br': 78.9183371, 'F': 18.99840322, 'I': 126.904473, 'Na': 22.9897692809, 'K': 38.96370668,
        'Se': 79.9165213, 'B': 11.0093054, 'Si': 27.9769265325, 'Fe': 55.9349375, 'Mg': 23.9850417, 'Ca': 39.96259098,
        'Cu': 62.9295975, 'Zn': 63.9291422, 'Co': 58.933195, 'Mn': 54.9380451, 'As': 74.9215965, 'Hg': 201.970643,
        'Al': 26.98153863, 'Li': 7.01600455, 'Ni': 57.9353429, 'Pt': 194.9647911, 'Gd': 157.9241039, 'Sn': 119.9021947}


def clean_formula(f):
    f = re.sub(r'\s+', '', str(f or ''))
    f = re.sub(r'[\[\]]', '', f)
    if not re.fullmatch(r'([A-Z][a-z]?\d*)+[+-]?\d*', f):
        return ''
    return f


def mono_mass(f):
    f = re.sub(r'[+-]\d*$', '', f)
    tot = 0.0
    for el, n in re.findall(r'([A-Z][a-z]?)(\d*)', f):
        if el not in MASS:
            return None
        tot += MASS[el] * (int(n) if n else 1)
    return round(tot, 5) if tot else None


# ================================================================= aducto ===
def norm_adduct(a, mode):
    a = str(a or '').strip()
    if not a:
        return ''
    a = a.replace(' ', '').replace('[M+]+', '[M]+').replace('[M-]-', '[M]-')
    m = re.fullmatch(r'\[(\d*M[^\]]*)\](\d*)([+-]?)(\d*)', a)
    if m:
        core, sign, n = m.group(1), m.group(3), m.group(2) or m.group(4) or ''
    elif re.fullmatch(r'\d*M([+-][A-Za-z0-9]+)*[+-]?', a):
        core, sign, n = a, '', ''
        if core.endswith(('+', '-')):
            sign, core = core[-1], core[:-1]
    else:
        return ''
    if core.endswith(('+', '-')):
        sign, core = core[-1], core[:-1]
    core = {'M-H2O+H': 'M+H-H2O', 'M+H+H': 'M+2H', 'M+HCOO': 'M+FA-H', 'M+CH3CN+H': 'M+ACN+H',
            'M+CH3CN+Na': 'M+ACN+Na', 'M-H+H2O': 'M+H2O-H'}.get(core, core)
    if not sign:
        sign = '+' if mode == 'POS' else '-' if mode == 'NEG' else ''
        if not sign:
            return ''
    if n == '1':
        n = ''
    return f'[{core}]{n}{sign}'


def adduct_desc(a):
    core = a[1:a.index(']')]
    charge = a[a.index(']') + 1:]
    sign = 'positivo' if charge.endswith('+') else 'negativo'
    z = charge[:-1] or '1'
    parts = []
    mult = re.match(r'(\d*)M', core).group(1)
    if mult:
        parts.append(f'{mult} moleculas (dimero/multimero)')
    names = {'H': 'proton', 'Na': 'sodio', 'K': 'potasio', 'NH4': 'amonio', 'H2O': 'agua', 'FA': 'formiato', 'HCOO': 'formiato',
             'HCOOH': 'acido formico', 'CH3COO': 'acetato', 'Cl': 'cloruro', 'ACN': 'acetonitrilo', 'CH3OH': 'metanol',
             'NH3': 'amoniaco', 'CO2': 'dioxido de carbono', 'Hac': 'acido acetico', 'DMSO': 'DMSO'}
    for sgn, cnt, grp in re.findall(r'([+-])(\d*)([A-Za-z][A-Za-z0-9]*)', core):
        nm = names.get(grp, grp)
        parts.append(('ganancia' if sgn == '+' else 'perdida') + f' de {cnt + " " if cnt else ""}{nm}')
    return f'Ion en modo {sign} (carga {z}): ' + (', '.join(parts) if parts else 'ion molecular')


# ================================================================== nivel ===
def nivel(raw, named):
    r = str(raw or '').strip().lower().replace('level', '').replace(' ', '')
    if not named:
        return 4
    m = {'i': 1, '1': 1, '1.0': 1, 'a': 1, 'ii': 2, '2': 2, '2.0': 2, 'b': 2, '***': 2,
         'iii': 3, '3': 3, '3.0': 3, '3.1': 3, '3.2': 3, '**': 3, '*': 3, '4': 3, 'iv': 3}
    return m.get(r, 2)


def norm_name(n):
    n = ' '.join(str(n).split()).strip().strip('"').strip()
    n = re.sub(r'\*+$', '', n).strip()
    return n


def key_name(n):
    return norm_name(n).casefold()


# ================================================================== main ===
def main():
    os.makedirs(OUT, exist_ok=True)
    T, chain, fam_chain, spid = taxonomia()
    print('Cargando batches parseados...')
    data = {}
    for p in sorted(glob.glob(PARSED + '/B*.pkl')):
        b = int(os.path.basename(p)[1:3])
        d = pickle.load(open(p, 'rb'))
        f = d['feats']
        f['name'] = f['name'].map(norm_name)
        f.loc[f['name'].str.lower().isin({'nan', 'compounds', 'metabolites', 'name'}), 'name'] = ''
        # identificadores de caracteristica usados como nombre (sin anotacion real)
        f.loc[f['name'].str.fullmatch(r'(M\d+(\.\d+)?T\d+(\.\d+)?(_\d+)?|Com_\d+_(pos|neg)|metab_\d+|\d+(\.\d+)?)', case=False), 'name'] = ''
        f['formula'] = f['formula'].map(clean_formula)
        if b == 34:
            f.loc[(f['rt'] > 100) | (f['mz'] > 5000), ['mz', 'rt']] = np.nan
        v = d['vals']
        if b in LOG_BASE:
            base = LOG_BASE[b]
            if b == 57:
                v = v[v['valor'] > v['valor'].min() + 1e-9]
            v = v.assign(valor=np.power(float(base), v['valor']))
        # quitar filas vacias (sin nombre, sin m/z, sin masa, sin RT y sin valores)
        con_val = set(v['fid'])
        vacia = (f['name'] == '') & f['mz'].isna() & f['mass'].isna() & f['rt'].isna() & ~f['fid'].isin(con_val)
        f = f[~vacia]
        v = v[v['fid'].isin(set(f['fid']))]
        d['feats'], d['vals'] = f, v
        data[b] = d

    # ---- clases quimicas
    print('Armonizando clases quimicas...')
    learned = defaultdict(Counter)
    for b, d in data.items():
        f = d['feats']
        h = [harmonize(a, c) for a, c in zip(f['superclass'], f['clase'])]
        f['sup_h'] = [x[0] for x in h]
        f['cl_h'] = [x[1] for x in h]
        for s_, c_ in h:
            if s_ and c_:
                learned[c_.lower()][s_] += 1
    for b, d in data.items():
        f = d['feats']
        fix = []
        for s_, c_ in zip(f['sup_h'], f['cl_h']):
            if not s_ and c_:
                s_ = CLASS_SUPER_MANUAL.get(c_.lower()) or (learned[c_.lower()].most_common(1)[0][0] if learned[c_.lower()] else '')
            fix.append(s_)
        f['sup_h'] = fix

    # ---- metabolitos
    print('Construyendo catalogo de metabolitos...')
    met_name, met_form, met_cls, met_batches, met_n = {}, defaultdict(Counter), defaultdict(Counter), defaultdict(set), Counter()
    for b, d in data.items():
        f = d['feats']
        for n, fo, s_, c_ in zip(f['name'], f['formula'], f['sup_h'], f['cl_h']):
            if not n:
                continue
            k = key_name(n)
            met_name.setdefault(k, n)
            if fo and b != 54:
                met_form[k][re.sub(r'[+-]\d*$', '', fo)] += 1
            if s_ or c_:
                met_cls[k][(s_, c_)] += 1
            met_batches[k].add(b)
            met_n[k] += 1
    keys = sorted(met_name, key=lambda k: met_name[k].casefold())
    met_id = {k: i + 2 for i, k in enumerate(keys)}

    # superclases / clases
    sup_set, cls_set = set(), set()
    met_class = {}
    for k in keys:
        if met_cls[k]:
            (s_, c_), _ = met_cls[k].most_common(1)[0]
            met_class[k] = (s_, c_)
    for d in data.values():
        f = d['feats']
        for s_, c_ in zip(f['sup_h'], f['cl_h']):
            if s_:
                sup_set.add(s_)
            if c_:
                cls_set.add((s_, c_))
    sups = sorted(sup_set)
    sup_id = {s_: i + 1 for i, s_ in enumerate(sups)}
    # una clase puede aparecer con distintas superclases: se conserva la mas frecuente
    cls_sup = defaultdict(Counter)
    for d in data.values():
        f = d['feats']
        for s_, c_ in zip(f['sup_h'], f['cl_h']):
            if c_:
                cls_sup[c_][s_] += 1
    clss = sorted(cls_sup, key=str.casefold)
    cls_best_sup = {c_: next((s_ for s_, _ in cls_sup[c_].most_common() if s_), '') for c_ in clss}
    cls_id = {c_: i + 1 for i, c_ in enumerate(clss)}
    cls_nb = defaultdict(set)
    for b, d in data.items():
        for c_ in set(d['feats']['cl_h']):
            if c_:
                cls_nb[c_].add(b)

    def class_ids(s_, c_):
        cid_ = cls_id.get(c_, 0)
        if cid_:
            s2 = cls_best_sup[c_] or s_
            return sup_id.get(s2, 0), cid_
        return sup_id.get(s_, 0), 0

    met_rows = [(0, NE, '', 0, ND), (1, 'No identificado', '', 0,
                 'Marcador para senales/caracteristicas espectrales sin metabolito asignado')]
    met_info = {}
    for k in keys:
        fo = met_form[k].most_common(1)[0][0] if met_form[k] else ''
        s_, c_ = met_class.get(k, ('', ''))
        sid, cid_ = class_ids(s_, c_)
        bl = sorted(met_batches[k])
        desc = f"Reportado en {len(bl)} batch(es): " + ', '.join(f'BAT{x:04d}' for x in bl)
        met_rows.append((met_id[k], met_name[k], fo, cid_, desc))
        met_info[k] = (met_id[k], fo, sid, cid_)

    # ---- aductos
    add_set = Counter()
    for d in data.values():
        f = d['feats']
        f['add_n'] = [norm_adduct(a, m) for a, m in zip(f['adduct'], f['mode'])]
        add_set.update(x for x in f['add_n'] if x)
    adds = sorted(add_set, key=lambda a: (-add_set[a], a))
    add_id = {a: i + 1 for i, a in enumerate(adds)}

    # ---- catalogos simples
    def simple(lst):
        return [(0, NE, ND)] + [(i + 1, n, d_) for i, (n, d_) in enumerate(lst)]
    parte_id = {n: i + 1 for i, (n, _) in enumerate(PARTES)}
    tipo_id = {n: i + 1 for i, (n, _) in enumerate(TIPOS_MUESTRA)}
    cult_id = {n: i + 1 for i, (n, _) in enumerate(TIPOS_CULTIVO)}
    met_keys = sorted(METODOS)
    metodo_id = {k: i + 1 for i, k in enumerate(met_keys)}
    col_keys = list(COLUMNAS)
    col_id = {k: i + 1 for i, k in enumerate(col_keys)}
    act_id = {n: i + 1 for i, (n, _) in enumerate(ACTIVIDADES)}
    modo_id = {'POS': 1, 'NEG': 2, 'EI': 3}

    # ---- muestras
    print('Construyendo catalogo de muestras...')
    muestras = [(0, 0, NE, 0, 0, 0, 0, 0, NE, '', ND)]
    samp_info = {}   # (b, code) -> dict
    mid = 1
    for b in sorted(data):
        cfg = B[b]
        d = data[b]
        batch_species = set()
        for code in d['samples']:
            o = cfg['fn'](code, d['groups']) or {}
            if o.get('especie') or cfg.get('especie'):
                batch_species.add(o.get('especie') or cfg.get('especie'))
        if batch_species:
            common = common_chain([chain[s_] for s_ in batch_species])
        elif cfg.get('familia'):
            common = fam_chain(cfg['familia'])
        else:
            common = {k: 0 for k in TAXK}
        for code in d['samples']:
            o = dict(cfg['fn'](code, d['groups']) or {})
            qb = qc_blank(code) if not o.get('tipo') in (QC, BLANCO) else None
            if qb and not o.get('grupo', '').startswith(('Placa',)):
                o.update(qb)
            sp = o.get('especie', cfg.get('especie'))
            tipo = o['tipo'] if 'tipo' in o else cfg['tipo']
            if tipo in (QC, BLANCO):
                tax = common if tipo == QC else {k: 0 for k in TAXK}
                sp_id = tax['ID_ESPECIE']
            elif sp:
                tax = chain[sp]; sp_id = spid[sp]
            else:
                tax = common; sp_id = tax['ID_ESPECIE']
            parte = o['parte'] if 'parte' in o else cfg['parte']
            cult = o['cultivo'] if 'cultivo' in o else cfg['cultivo']
            metodo = o.get('metodo', cfg['metodo'])
            if tipo == BLANCO:
                cult = None
            info = dict(tax, ID_ESPECIE=sp_id, ID_MUESTRA=mid,
                        ID_PARTE_ESTUDIADA=parte_id.get(parte, 0) if parte else 0,
                        ID_TIPO_MUESTRA=tipo_id.get(tipo, 0) if tipo else 0,
                        ID_TIPO_CULTIVO=cult_id.get(cult, 0) if cult else 0,
                        ID_METODO_EXTRACCION=metodo_id.get(metodo, 0) if metodo else 0)
            desc = o.get('desc', '')
            muestras.append((mid, b, code, sp_id, info['ID_PARTE_ESTUDIADA'], info['ID_TIPO_MUESTRA'], info['ID_TIPO_CULTIVO'],
                             info['ID_METODO_EXTRACCION'], o.get('grupo', '') or NE, o.get('replica', ''), desc or ND))
            samp_info[(b, code)] = info
            mid += 1
        # muestra generica del batch para caracteristicas sin valores por muestra
        samp_info[(b, None)] = dict(common, ID_MUESTRA=0, ID_PARTE_ESTUDIADA=parte_id.get(cfg['parte'], 0) if cfg['parte'] else 0,
                                    ID_TIPO_MUESTRA=0, ID_TIPO_CULTIVO=cult_id.get(cfg['cultivo'], 0) if cfg['cultivo'] else 0,
                                    ID_METODO_EXTRACCION=metodo_id.get(cfg['metodo'], 0) if cfg['metodo'] else 0)

    # ---- medidas experimentales por muestra
    med_by_sample = defaultdict(list)
    for (b, rx, act, ens, val, uni, fuente) in MEDIDAS:
        for code in data[b]['samples']:
            if re.fullmatch(rx, code):
                med_by_sample[(b, code)].append((act_id[act], val, uni, ens, fuente))

    # ---- pivote de actividades
    print('Construyendo registro de actividades...')
    art_species = defaultdict(set)
    for (b, code), info in samp_info.items():
        if code is not None and info['ID_ESPECIE']:
            art_species[B[b]['art']].add(info['ID_ESPECIE'])
    art_species[4].add(spid['s_flavescens'])
    piv = []
    rid = 1
    def met_lookup(name):
        if not name:
            return 0
        k = key_name(name)
        return met_id.get(k, 0)
    for art in sorted(LIT):
        for act, sps, metab, nota in LIT[art]:
            sp_ids = [spid[x] for x in sps] if sps else sorted(art_species[art]) or [0]
            mt = met_lookup(metab)
            nota2 = nota + (f' (compuesto: {metab})' if metab and not mt else '')
            for s_ in sp_ids:
                piv.append((rid, art, s_, 0, mt, act_id[act], 'Literatura citada en el articulo', '', '', '', nota2)); rid += 1
    for art, sps, act, ens, val, uni, nota in EXP_SIN_VALOR:
        sp_ids = [spid[x] for x in sps] if sps else sorted(art_species[art]) or [0]
        for s_ in sp_ids:
            piv.append((rid, art, s_, 0, 0, act_id[act], 'Ensayo experimental (no vinculado a muestras del batch)', ens,
                        '' if val is None else val, uni, nota)); rid += 1
    code_by_mid = {}
    for (b, code), info in samp_info.items():
        if code is not None:
            code_by_mid[(b, code)] = info['ID_MUESTRA']
    for (b, code), lst in sorted(med_by_sample.items(), key=lambda x: code_by_mid[x[0]]):
        info = samp_info[(b, code)]
        for aid, val, uni, ens, fuente in lst:
            piv.append((rid, B[b]['art'], info['ID_ESPECIE'], info['ID_MUESTRA'], 0, aid,
                        'Ensayo experimental (valor por grupo de muestra)', ens, val, uni, fuente)); rid += 1

    # ================================================= escritura catalogos
    print('Escribiendo catalogos...')
    write_cat('01_Catalogo_Nucleo/01_Articulos.csv', ['ID_ARTICULO', 'ARCHIVO_ARTICULO', 'TITULO', 'DOI'], articulos())
    bat_files = {int(f[3:7]): f for f in os.listdir(ROOT + '/01_Datos/Data/Batch')}
    write_cat('01_Catalogo_Nucleo/02_Batches.csv', ['ID_BATCH', 'ID_ARTICULO', 'ARCHIVO_BATCH'],
              [(0, 0, ND)] + [(b, B[b]['art'], bat_files[b]) for b in sorted(bat_files)])
    write_cat('01_Catalogo_Nucleo/03_Modo_ionizacion.csv', ['ID_MODO_IONIZACION', 'MODO_IONIZACION', 'DESCRIPCION'], simple(MODOS))
    write_cat('01_Catalogo_Nucleo/04_Actividades_biologicas.csv', ['ID_ACTIVIDAD_BIOLOGICA', 'ACTIVIDAD_BIOLOGICA', 'DESCRIPCION'],
              simple(ACTIVIDADES))
    write_cat('02_Catalogo_Especie/01_Reinos.csv', ['ID_REINO', 'REINO', 'DESCRIPCION'], T['reino'])
    write_cat('02_Catalogo_Especie/02_Filos.csv', ['ID_FILO', 'ID_REINO', 'FILO', 'DESCRIPCION'], T['filo'])
    write_cat('02_Catalogo_Especie/03_Clases_taxonomicas.csv', ['ID_CLASE_TAXONOMICA', 'ID_FILO', 'CLASE_TAXONOMICA', 'DESCRIPCION'], T['clase'])
    write_cat('02_Catalogo_Especie/04_Ordenes.csv', ['ID_ORDEN', 'ID_CLASE_TAXONOMICA', 'ORDEN', 'DESCRIPCION'], T['orden'])
    write_cat('02_Catalogo_Especie/05_Familias.csv', ['ID_FAMILIA', 'ID_ORDEN', 'FAMILIA', 'DESCRIPCION'], T['familia'])
    write_cat('02_Catalogo_Especie/06_Generos.csv', ['ID_GENERO', 'ID_FAMILIA', 'GENERO', 'DESCRIPCION'], T['genero'])
    write_cat('02_Catalogo_Especie/07_Especies.csv', ['ID_ESPECIE', 'ID_GENERO', 'NOMBRE_CIENTIFICO', 'NOMBRE_COMUN', 'DESCRIPCION'], T['especie'])
    write_cat('03_Catalogo_Metabolito/01_Niveles_identificacion.csv', ['ID_NIVEL_IDENTIFICACION', 'NIVEL_IDENTIFICACION', 'DESCRIPCION'], simple(NIVELES))
    write_cat('03_Catalogo_Metabolito/02_Superclases_quimicas.csv', ['ID_SUPERCLASE_QUIMICA', 'SUPERCLASE_QUIMICA', 'DESCRIPCION'],
              [(0, NE, ND)] + [(sup_id[s_], s_, SUPER_DESC.get(s_, 'Superclase quimica (ClassyFire)')) for s_ in sups])
    write_cat('03_Catalogo_Metabolito/03_Clases_quimicas.csv', ['ID_CLASE_QUIMICA', 'ID_SUPERCLASE_QUIMICA', 'CLASE_QUIMICA', 'DESCRIPCION'],
              [(0, 0, NE, ND)] + [(cls_id[c_], sup_id.get(cls_best_sup[c_], 0), c_,
                                   f"Clase reportada en {len(cls_nb[c_])} batch(es): " + ', '.join(f'BAT{x:04d}' for x in sorted(cls_nb[c_])))
                                  for c_ in clss])
    write_cat('03_Catalogo_Metabolito/04_Aductos.csv', ['ID_ADUCTO', 'ADUCTO', 'DESCRIPCION'],
              [(0, NE, ND)] + [(add_id[a], a, adduct_desc(a)) for a in adds])
    write_cat('03_Catalogo_Metabolito/05_Metabolitos.csv', ['ID_METABOLITO', 'NOMBRE_METABOLITO', 'FORMULA_MOLECULAR', 'ID_CLASE_QUIMICA', 'DESCRIPCION'],
              met_rows)
    write_cat('04_Catalogo_Muestra/01_Columnas_cromatograficas.csv', ['ID_COLUMNA_CROMATOGRAFICA', 'COLUMNA_CROMATOGRAFICA', 'DESCRIPCION'],
              [(0, NE, ND)] + [(col_id[k], COLUMNAS[k][0], COLUMNAS[k][1]) for k in col_keys])
    write_cat('04_Catalogo_Muestra/02_Tipos_muestra.csv', ['ID_TIPO_MUESTRA', 'TIPO_MUESTRA', 'DESCRIPCION'], simple(TIPOS_MUESTRA))
    write_cat('04_Catalogo_Muestra/03_Partes_planta_estudiadas.csv', ['ID_PARTE_ESTUDIADA', 'PARTE_PLANTA_ESTUDIADA', 'DESCRIPCION'], simple(PARTES))
    write_cat('04_Catalogo_Muestra/04_Tipos_cultivo.csv', ['ID_TIPO_CULTIVO', 'TIPO_CULTIVO', 'DESCRIPCION'], simple(TIPOS_CULTIVO))
    write_cat('04_Catalogo_Muestra/05_Metodos_extraccion.csv', ['ID_METODO_EXTRACCION', 'METODO_EXTRACCION', 'DESCRIPCION'],
              [(0, NE, ND)] + [(metodo_id[k], METODOS[k], 'Batches: ' + (', '.join(f'BAT{b:04d}' for b in sorted(
                  {b for (b, c), i in samp_info.items() if c is not None and i['ID_METODO_EXTRACCION'] == metodo_id[k]})) or
                  'ninguno (solo articulo)')) for k in met_keys])
    write_cat('04_Catalogo_Muestra/06_Muestras_Batch.csv',
              ['ID_MUESTRA', 'ID_BATCH', 'CODIGO_MUESTRA', 'ID_ESPECIE', 'ID_PARTE_ESTUDIADA', 'ID_TIPO_MUESTRA', 'ID_TIPO_CULTIVO',
               'ID_METODO_EXTRACCION', 'GRUPO_EXPERIMENTAL', 'REPLICA', 'DESCRIPCION'], muestras)
    write_cat('05_Pivotes/Registo_Actividades_biologicas.csv',
              ['ID_REGISTRO', 'ID_ARTICULO', 'ID_ESPECIE', 'ID_MUESTRA', 'ID_METABOLITO', 'ID_ACTIVIDAD_BIOLOGICA', 'TIPO_EVIDENCIA',
               'ENSAYO', 'VALOR_ACTIVIDAD', 'UNIDAD_ACTIVIDAD', 'FUENTE'], piv)

    # ================================================= Dataset.csv
    print('Escribiendo Dataset.csv...')
    header = ['ID_ARTICULO', 'ID_BATCH', 'ID_MUESTRA'] + TAXK + ['ID_TIPO_MUESTRA', 'ID_PARTE_ESTUDIADA', 'ID_TIPO_CULTIVO',
              'ID_METODO_EXTRACCION', 'ID_COLUMNA_CROMATOGRAFICA', 'ID_MODO_IONIZACION', 'ID_NIVEL_IDENTIFICACION',
              'ID_SUPERCLASE_QUIMICA', 'ID_CLASE_QUIMICA', 'ID_ADUCTO', 'ID_METABOLITO', 'ID_ACTIVIDAD_BIOLOGICA',
              'FORMULA_MOLECULAR', 'MASA_MONOISOTOPICA', 'RELACION_MASA_CARGA', 'TIEMPO_RETENCION_MINUTOS', 'ALTURA_PICO',
              'VALOR_ACTIVIDAD', 'UNIDAD_ACTIVIDAD']
    def fnum(x, nd):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return ''
        return f'{x:.{nd}f}'.rstrip('0').rstrip('.') if nd else str(x)
    def fint(x):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return ''
        r = round(float(x), 4)
        return str(int(r)) if r == int(r) else f'{r:.4f}'.rstrip('0')
    total = 0
    stats = []
    with open(os.path.join(OUT, 'Dataset.csv'), 'w', encoding='utf-8', newline='') as fout:
        fout.write(';'.join(header) + '\n')
        for b in sorted(data):
            cfg = B[b]; d = data[b]; f = d['feats'].set_index('fid'); v = d['vals']
            art = cfg['art']
            col_batch = col_id.get(cfg['columna'], 0) if cfg['columna'] else 0
            # columnas por feature
            fcache = {}
            for fid_, r in f.iterrows():
                n = r['name']
                k = key_name(n) if n else None
                if k:
                    mid_, mfo, sid, cid_ = met_info[k]
                else:
                    mid_, mfo = 1, ''
                    sid, cid_ = class_ids(r['sup_h'], r['cl_h'])
                fo = r['formula'] if r['formula'] else mfo
                mass = r['mass'] if not math.isnan(r['mass']) else (mono_mass(fo) if fo else None)
                mode = r['mode']
                colf = col_id['GC'] if mode == 'EI' else col_batch
                lvl = nivel(r['level'], bool(n))
                fcache[fid_] = [str(colf), str(modo_id.get(mode, 0)), str(lvl), str(sid), str(cid_),
                                str(add_id.get(r['add_n'], 0)), str(mid_), fo, fnum(mass, 5), fnum(r['mz'], 5), fnum(r['rt'], 4)]
            n_rows = 0
            def emit(info, fid_, val):
                nonlocal n_rows
                fc = fcache[fid_]
                base = [str(art), str(b), str(info['ID_MUESTRA'])] + [str(info[k]) for k in TAXK] + \
                       [str(info['ID_TIPO_MUESTRA']), str(info['ID_PARTE_ESTUDIADA']), str(info['ID_TIPO_CULTIVO']),
                        str(info['ID_METODO_EXTRACCION'])] + fc[:7]
                tail = fc[7:] + [fint(val)]
                meds = med_by_sample.get(info.get('_key'), [])
                if meds:
                    for aid, mv, uni, _, _ in meds:
                        fout.write(';'.join(base + [str(aid)] + tail + [str(mv), uni]) + '\n'); n_rows += 1
                else:
                    fout.write(';'.join(base + ['0'] + tail + ['', '']) + '\n'); n_rows += 1
            code_info = {}
            for code in d['samples']:
                info = dict(samp_info[(b, code)]); info['_key'] = (b, code)
                code_info[code] = info
            for fid_, code, val in zip(v['fid'].values, v['muestra'].values, v['valor'].values):
                emit(code_info[code], fid_, float(val))
            sin = set(f.index) - set(v['fid'].values)
            gen = dict(samp_info[(b, None)]); gen['_key'] = None
            for fid_ in sorted(sin):
                emit(gen, fid_, None)
            total += n_rows
            stats.append((b, len(f), len(d['samples']), n_rows))
            print(f'  B{b:02d}: {n_rows} filas', flush=True)
    print('Total filas Dataset:', total)
    pd.DataFrame(stats, columns=['batch', 'features', 'muestras', 'filas']).to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stats.csv'), index=False)


if __name__ == '__main__':
    main()
