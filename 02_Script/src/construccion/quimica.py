"""Normalizacion quimica para la construccion del Dataset: formulas, masas, aductos, modos, niveles MSI,
nombres de metabolitos y unificacion de las ontologias de clase quimica de cada laboratorio."""
from __future__ import annotations

import math
import re
import unicodedata

from ..features.quimica import MASA_ISOTOPO, parsear_formula

MASA_PROTON = 1.007276467
MASA_ELECTRON = 0.000548580

# --------------------------------------------------------------------------------------------- formulas y masas


def limpiar_formula(f: object) -> str:
    """'C21 H24 O6' -> 'C21H24O6'; vacia si no es texto util. Conserva cargas (+/-) del final."""
    if not isinstance(f, str):
        return ""
    s = f.strip().replace(" ", "").replace("​", "")
    if s in ("", "-", "--", "/", "nan", "NaN", "None"):
        return ""
    return s


def masa_monoisotopica(formula: str) -> float | None:
    """Masa monoisotopica neutra de la formula (sin cargas). None si no se puede interpretar."""
    f = limpiar_formula(formula).rstrip("+-")
    c = parsear_formula(f)
    if c is None:
        return None
    return round(sum(MASA_ISOTOPO[e] * n for e, n in c.items()), 6)


# --------------------------------------------------------------------------------------------- aductos

_ADUCTO_PARTES = {  # masa que aporta cada termino del aducto (unidades de masa neutra)
    "H": 1.0078250319, "H2": 2.0156500638, "Na": 22.98976966, "K": 38.9637069, "NH4": 18.0338257, "Li": 7.0160040,
    "H2O": 18.0105647, "FA": 46.0054793, "HCOO": 44.9976542, "CH3COO": 59.0133043, "Ac": 60.0211294,
    "HAc": 60.0211294, "ACN": 41.0265491, "CH3OH": 32.0262151, "MeOH": 32.0262151, "Cl": 34.96885271,
    "Br": 78.9183376, "NH3": 17.0265491, "CO2": 43.9898292, "HCOOH": 46.0054793, "C2H3N": 41.0265491,
    "CH3CN": 41.0265491, "IsoProp": 60.0575149, "DMSO": 78.0139355, "TFA": 113.9928, "CH2O2": 46.0054793,
    "C2H4O2": 60.0211294, "Hac": 60.0211294,
}


def normalizar_aducto(a: object) -> str:
    """Lleva cualquier notacion ('M+H', '[M + H]+', 'M+FA-H', '[M+2H]+2', 'M-H2O+H', 'M+NH4') a '[M+H]+'.
    Si hay varios aductos ('M+H, M+NH4') toma el primero. Devuelve '' si no es interpretable."""
    if not isinstance(a, str):
        return ""
    s = a.strip()
    if not s or s.lower() in ("nan", "-", "--", "none", "unknown"):
        return ""
    s = re.split(r"[,;|]", s)[0].strip()
    s = s.replace(" ", "").replace("\u2212", "-").replace("\u2013", "-")
    if s.startswith("["):
        m2 = re.match(r"^\[(\d*M[^\]]*)\]([+-])(\d+)$", s)  # '[M+2H]+2'
        if m2:
            s = f"[{m2.group(1)}]{m2.group(3)}{m2.group(2)}"
        m = re.match(r"^\[(\d*M[^\]]*)\](\d*)([+-]{1,2})?$", s)
        if not m:
            return ""
        nucleo, carga_n, signo = m.group(1), m.group(2), m.group(3) or ""
        if len(signo) == 2:
            carga_n, signo = "2", signo[0]
    else:
        if not re.match(r"^\d*M([+-][A-Za-z0-9]+)*[+-]?$", s):
            return ""
        nucleo, signo, carga_n = s, "", ""
        if s.endswith(("+", "-")) and not re.search(r"[+-]$", s[:-1]):
            nucleo, signo = s[:-1], s[-1]
    nucleo = re.sub(r"(?<=[+-])NA(?![a-z])", "Na", nucleo)
    nucleo = re.sub(r"(?<=[+-])CL(?![a-z])", "Cl", nucleo)
    if nucleo.endswith(("+", "-")):
        signo = signo or nucleo[-1]
        nucleo = nucleo[:-1]
    if not signo:
        signo = "-" if re.search(r"-H$|\+(Cl|Br|FA|HCOO|CH3COO|Ac|Hac|HAc|TFA)(-H)?$", nucleo) else "+"
    if not carga_n:
        mh = re.search(r"[+-](\d+)H(?![a-z0-9])", nucleo)
        carga_n = mh.group(1) if mh and int(mh.group(1)) > 1 else ""
    carga = carga_n if carga_n and carga_n != "1" else ""
    return f"[{nucleo}]{carga}{signo}"


def carga_aducto(aducto: str) -> int:
    m = re.match(r"^\[.*\](\d*)([+-])$", aducto or "")
    if not m:
        return 0
    n = int(m.group(1)) if m.group(1) else 1
    return n if m.group(2) == "+" else -n


def delta_masa_aducto(aducto: str) -> float | None:
    """Masa del ion menos la masa de M (por molecula, antes de dividir por la carga). None si no se puede."""
    m = re.match(r"^\[(\d*)M(.*)\](\d*)([+-])$", aducto or "")
    if not m:
        return None
    resto = m.group(2)
    delta = 0.0
    for signo, n, termino in re.findall(r"([+-])(\d*)([A-Za-z][A-Za-z0-9]*)", resto):
        k = int(n) if n else 1
        if termino not in _ADUCTO_PARTES:
            return None
        delta += (1 if signo == "+" else -1) * k * _ADUCTO_PARTES[termino]
    carga = carga_aducto(aducto)
    delta -= carga * MASA_ELECTRON
    return round(delta, 6)


def multiplicador_aducto(aducto: str) -> int:
    m = re.match(r"^\[(\d*)M", aducto or "")
    return int(m.group(1)) if m and m.group(1) else 1


# --------------------------------------------------------------------------------------------- modos de ionizacion

MODO_POS, MODO_NEG, MODO_EI = 1, 2, 3


def modo_desde_texto(v: object) -> int:
    """'pos', 'POS', 'T3_positive', 'Positive', 'LCMS-neg', '+' ... -> 1/2/3 (0 si no se reconoce)."""
    if not isinstance(v, str):
        return 0
    s = v.strip().lower()
    if not s or s == "nan":
        return 0
    if "gc" in s and "lc" not in s:
        return MODO_EI
    if s in ("ei",) or "electron" in s:
        return MODO_EI
    if "neg" in s or s in ("-", "esi-"):
        return MODO_NEG
    if "pos" in s or s in ("+", "esi+"):
        return MODO_POS
    return 0


def modo_desde_aducto(aducto: str) -> int:
    c = carga_aducto(aducto)
    return MODO_POS if c > 0 else MODO_NEG if c < 0 else 0


# --------------------------------------------------------------------------------------------- niveles MSI


def nivel_msi(v: object, anotado: bool) -> int:
    """Nivel de identificacion MSI (1=I, 2=II, 3=III, 4=IV). Las senales sin nombre son nivel IV.

    Acepta 'I'/'II', 'level1', 'Level 1', 1/2/3, 'A'/'B'/'C', estrellas de LuMing ('***' -> II, '*' -> III)."""
    if not anotado:
        return 4
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 3
    s = str(v).strip().upper().replace("LEVEL", "").replace(" ", "")
    romano = {"I": 1, "II": 2, "III": 3, "IV": 4}
    if s in romano:
        return romano[s]
    if s.replace(".0", "") in ("1", "2", "3", "4"):
        return int(s.replace(".0", ""))
    if s in ("A", "B", "C", "D"):
        return {"A": 1, "B": 2, "C": 3, "D": 4}[s]
    if set(s) == {"*"}:
        return 2 if len(s) >= 2 else 3
    return 3


# --------------------------------------------------------------------------------------------- nombres

_GRIEGAS = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ω": "omega", "κ": "kappa", "λ": "lambda",
            "μ": "mu", "ε": "epsilon", "ψ": "psi"}


def limpiar_nombre(n: object) -> str:
    """Nombre legible: sin espacios dobles, sin asteriscos finales, sin comillas de Excel."""
    if not isinstance(n, str):
        return ""
    s = unicodedata.normalize("NFKC", n).strip().strip('"').strip()
    s = re.sub(r"\s+", " ", s)
    s = s.rstrip("*").strip()
    if s.lower() in ("", "nan", "-", "--", "unknown", "none", "null", "na", "n/a") or re.fullmatch(r"[-\s]*", s):
        return ""
    return s


def clave_nombre(n: str) -> str:
    """Clave de comparacion para unificar el mismo metabolito escrito de formas distintas."""
    s = limpiar_nombre(n).lower()
    for g, t in _GRIEGAS.items():
        s = s.replace(g, t)
    s = s.replace(".alpha.", "alpha").replace(".beta.", "beta").replace(".gamma.", "gamma")
    s = re.sub(r"[\s'’`´\"]", "", s)
    s = s.replace("–", "-").replace("—", "-").replace("_", "-")
    return s


def es_nombre_desconocido(n: str) -> bool:
    s = limpiar_nombre(n).lower()
    if not s:
        return True
    return bool(re.fullmatch(r"(unknown|unk|feature|metab|com|m\d+t\d+|no annotation|not annotated).*", s)) or \
        bool(re.fullmatch(r"[\d.]+(_[\d.]+)?m?/?z?", s))


# --------------------------------------------------------------------------------------------- ontologia de clases

# Superclases unificadas (ID, nombre, descripcion). El ID 0 es "No especificado".
SUPERCLASES = [
    (1, "Flavonoides", "Flavonas, flavonoles, flavanonas, isoflavonas, antocianinas, chalconas, flavanoles y glicosidos"),
    (2, "Acidos fenolicos y fenilpropanoides", "Acidos hidroxicinamicos e hidroxibenzoicos, fenoles simples y fenilpropanoides no flavonoides"),
    (3, "Lignanos y cumarinas", "Lignanos, neolignanos, cumarinas y sus glicosidos"),
    (4, "Taninos", "Taninos hidrolizables y condensados (proantocianidinas)"),
    (5, "Estilbenos", "Estilbenos y derivados (resveratrol, piceatanol)"),
    (6, "Xantonas", "Xantonas y benzofenonas"),
    (7, "Quinonas", "Antraquinonas, naftoquinonas y benzoquinonas"),
    (8, "Alcaloides", "Alcaloides y derivados nitrogenados de origen vegetal"),
    (9, "Terpenoides", "Mono-, sesqui-, di- y triterpenoides, saponinas triterpenicas e iridoides"),
    (10, "Esteroides", "Esteroides, fitoesteroles, glicoalcaloides esteroidales y ecdisteroides"),
    (11, "Lipidos", "Acidos grasos, glicerolipidos, glicerofosfolipidos, esfingolipidos y oxilipinas"),
    (12, "Aminoacidos y derivados", "Aminoacidos, peptidos y derivados"),
    (13, "Nucleotidos y derivados", "Nucleosidos, nucleotidos, purinas y pirimidinas"),
    (14, "Acidos organicos", "Acidos carboxilicos, cetoacidos e hidroxiacidos no clasificados en otra familia"),
    (15, "Carbohidratos", "Azucares, alcoholes de azucar, oligosacaridos y glicosidos simples"),
    (16, "Vitaminas y cofactores", "Vitaminas, coenzimas y cofactores"),
    (17, "Bencenoides", "Bencenos y derivados no fenolicos"),
    (18, "Compuestos heterociclicos", "Compuestos organoheterociclicos no alcaloideos"),
    (19, "Compuestos organicos oxigenados", "Alcoholes, aldehidos, cetonas y eteres no clasificados en otra familia"),
    (20, "Compuestos organicos nitrogenados", "Aminas, amidas y otros compuestos nitrogenados no alcaloideos"),
    (21, "Otros", "Compuestos con clase reportada que no encaja en las familias anteriores"),
    (22, "Policetidos", "Policetidos aromaticos y ciclicos no flavonoides (floroglucinoles, cromanos)"),
]
# Abreviaturas de categorias de LIPID MAPS y equivalentes
_TOKENS_SUPERCLASE = {"fa": 11, "gp": 11, "gl": 11, "sl": 11, "sp": 11, "st": 10, "pr": 9, "pk": 22, "sl | cer": 11,
                      "car": 11, "lpc": 11, "lpe": 11, "pc": 11, "pe": 11, "tg": 11, "dg": 11, "mg": 11}
# Etiquetas que describen el origen o uso del compuesto (mzCloud), no su clase quimica
_NO_QUIMICAS = re.compile(r"endogenous metabolites|natural products|pesticides|herbicides|drugs|therapeutics|extractables|"
                          r"leachables|doping|food additives|cosmetic|toxins|veterinary|^[/\\]+$", re.I)
_REGLAS_SUPERCLASE: list[tuple[str, int]] = [
    (r"stilben", 5), (r"xanthon|benzophenon", 6), (r"tannin|proanthocyan|gallotannin|ellagitannin", 4),
    (r"flavon|flavan|flavonoid|anthocyan|chalcon|isoflav|aurone|catechin|isoflavonoid|neoflavonoid", 1),
    (r"lignan|coumarin|neolignan", 3), (r"quinon", 7),
    (r"steroid|sterol|ecdyster|withanolid|cardenolid|bufanolid|steroidal", 10),
    (r"alkaloid|indole|isoquinolin|quinolin|pyrrolizidin|tropane|purine alkaloid|phenolamine|plumerane|morphinan|carbolin", 8),
    (r"terpen|saponin|iridoid|prenol|carotenoid|isoprenoid|monoterp|sesquiterp|diterp|triterp", 9),
    (r"lipid|fatty|glycerophospho|sphingo|glycerolipid|lpc|lpe|\bpc\b|\bpe\b|oxylipin|eicosan|octadecan|lyso|wax|glycerid|acyl", 11),
    (r"amino acid|peptide|amino-acid|aminoacid", 12),
    (r"nucleo|purine|pyrimidine", 13),
    (r"vitamin|cofactor|coenzyme", 16),
    (r"polyketide|phloroglucinol|chroman(?!one)", 22),
    (r"phenolic|phenol|hydroxycinnamic|cinnamic|phenylpropano|benzoic acid|hydroxybenzoic|tyrosol", 2),
    (r"carbohydrate|saccharide|sugar|glycoside|polyol", 15),
    (r"organic acid|carboxylic|keto acid|hydroxy acid|dicarboxylic|tricarboxylic|phosphoric acid|phosphate ester", 14),
    (r"benzen|benzenoid|naphthalen|phenanthren|anthracen", 17),
    (r"heterocycl|azole|azine|pyran|furan|organoheterocyclic|pyridin|pteridin|chromone|benzopyran", 18),
    (r"organonitrogen|amine|amide|nitrogen", 20),
    (r"alcohol|aldehyde|ketone|ether|carbonyl|organic oxygen|organooxygen|lacton", 19),
]
_EXCLUSIONES = {"", "-", "--", "nan", "others", "other", "unclassified", "unknown", "none", "not available", "na"}


def superclase_unificada(*etiquetas: object) -> int:
    """ID de superclase unificada a partir de las etiquetas de clase del laboratorio (de la mas especifica a la
    mas general). Devuelve 0 si ninguna etiqueta es informativa."""
    textos = [str(e).strip().lower() for e in etiquetas if isinstance(e, str)]
    textos = [t for t in textos if t not in _EXCLUSIONES and not _NO_QUIMICAS.search(t)]
    for t in textos:
        if t in _TOKENS_SUPERCLASE:
            return _TOKENS_SUPERCLASE[t]
        for patron, sc in _REGLAS_SUPERCLASE:
            if re.search(patron, t):
                return sc
    return 21 if textos else 0


def etiqueta_clase(*etiquetas: object) -> str:
    """Etiqueta de clase quimica (la mas especifica informativa), normalizada en espacios y mayuscula inicial."""
    for e in etiquetas:
        if isinstance(e, str):
            s = re.sub(r"\s+", " ", e).strip().strip(";").strip()
            if s.lower() not in _EXCLUSIONES and not s.lower().startswith("hash(") and not _NO_QUIMICAS.search(s):
                return s[:1].upper() + s[1:]
    return ""
