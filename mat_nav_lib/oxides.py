"""Static oxide list for glass science applications.

Based on GlassPy GlassNet element_features (68 elements) mapped to their
common oxide forms used in glass composition design.
"""

from __future__ import annotations

from typing import TypedDict


class OxideInfo(TypedDict):
    formula: str
    name_ko: str
    molar_mass: float
    category: str  # network_former | network_modifier | intermediate | other


OXIDE_LIST: list[OxideInfo] = [
    # ── Network Formers (망목형성체) ──
    {"formula": "SiO2",   "name_ko": "이산화규소",     "molar_mass": 60.08,  "category": "network_former"},
    {"formula": "B2O3",   "name_ko": "산화붕소",       "molar_mass": 69.62,  "category": "network_former"},
    {"formula": "P2O5",   "name_ko": "오산화인",       "molar_mass": 141.94, "category": "network_former"},
    {"formula": "GeO2",   "name_ko": "이산화저마늄",   "molar_mass": 104.64, "category": "network_former"},
    {"formula": "As2O3",  "name_ko": "삼산화비소",     "molar_mass": 197.84, "category": "network_former"},
    {"formula": "Sb2O3",  "name_ko": "삼산화안티몬",   "molar_mass": 291.52, "category": "network_former"},
    {"formula": "V2O5",   "name_ko": "오산화바나듐",   "molar_mass": 181.88, "category": "network_former"},
    {"formula": "TeO2",   "name_ko": "이산화텔루륨",   "molar_mass": 159.60, "category": "network_former"},
    {"formula": "SeO2",   "name_ko": "이산화셀레늄",   "molar_mass": 110.96, "category": "network_former"},

    # ── Network Modifiers (망목수식체) ──
    {"formula": "Na2O",   "name_ko": "산화나트륨",     "molar_mass": 61.98,  "category": "network_modifier"},
    {"formula": "K2O",    "name_ko": "산화칼륨",       "molar_mass": 94.20,  "category": "network_modifier"},
    {"formula": "Li2O",   "name_ko": "산화리튬",       "molar_mass": 29.88,  "category": "network_modifier"},
    {"formula": "Rb2O",   "name_ko": "산화루비듐",     "molar_mass": 186.94, "category": "network_modifier"},
    {"formula": "Cs2O",   "name_ko": "산화세슘",       "molar_mass": 281.81, "category": "network_modifier"},
    {"formula": "CaO",    "name_ko": "산화칼슘",       "molar_mass": 56.08,  "category": "network_modifier"},
    {"formula": "MgO",    "name_ko": "산화마그네슘",   "molar_mass": 40.30,  "category": "network_modifier"},
    {"formula": "BaO",    "name_ko": "산화바륨",       "molar_mass": 153.33, "category": "network_modifier"},
    {"formula": "SrO",    "name_ko": "산화스트론튬",   "molar_mass": 103.62, "category": "network_modifier"},
    {"formula": "BeO",    "name_ko": "산화베릴륨",     "molar_mass": 25.01,  "category": "network_modifier"},
    {"formula": "PbO",    "name_ko": "산화납",         "molar_mass": 223.20, "category": "network_modifier"},
    {"formula": "Ag2O",   "name_ko": "산화은",         "molar_mass": 231.74, "category": "network_modifier"},
    {"formula": "Tl2O",   "name_ko": "산화탈륨",       "molar_mass": 424.77, "category": "network_modifier"},
    {"formula": "HgO",    "name_ko": "산화수은",       "molar_mass": 216.59, "category": "network_modifier"},

    # ── Intermediate Oxides (중간산화물) ──
    {"formula": "Al2O3",  "name_ko": "산화알루미늄",   "molar_mass": 101.96, "category": "intermediate"},
    {"formula": "TiO2",   "name_ko": "이산화티타늄",   "molar_mass": 79.87,  "category": "intermediate"},
    {"formula": "ZrO2",   "name_ko": "이산화지르코늄", "molar_mass": 123.22, "category": "intermediate"},
    {"formula": "ZnO",    "name_ko": "산화아연",       "molar_mass": 81.38,  "category": "intermediate"},
    {"formula": "Fe2O3",  "name_ko": "산화철(III)",    "molar_mass": 159.69, "category": "intermediate"},
    {"formula": "FeO",    "name_ko": "산화철(II)",     "molar_mass": 71.84,  "category": "intermediate"},
    {"formula": "Bi2O3",  "name_ko": "산화비스무트",   "molar_mass": 465.96, "category": "intermediate"},
    {"formula": "Ga2O3",  "name_ko": "산화갈륨",       "molar_mass": 187.44, "category": "intermediate"},
    {"formula": "In2O3",  "name_ko": "산화인듐",       "molar_mass": 277.64, "category": "intermediate"},
    {"formula": "HfO2",   "name_ko": "산화하프늄",     "molar_mass": 210.49, "category": "intermediate"},
    {"formula": "Sc2O3",  "name_ko": "산화스칸듐",     "molar_mass": 137.91, "category": "intermediate"},
    {"formula": "SnO2",   "name_ko": "이산화주석",     "molar_mass": 150.71, "category": "intermediate"},

    # ── Transition Metal Oxides (전이금속 산화물) ──
    {"formula": "MnO",    "name_ko": "산화망간(II)",   "molar_mass": 70.94,  "category": "other"},
    {"formula": "MnO2",   "name_ko": "이산화망간",     "molar_mass": 86.94,  "category": "other"},
    {"formula": "CoO",    "name_ko": "산화코발트",     "molar_mass": 74.93,  "category": "other"},
    {"formula": "NiO",    "name_ko": "산화니켈",       "molar_mass": 74.69,  "category": "other"},
    {"formula": "CuO",    "name_ko": "산화구리(II)",   "molar_mass": 79.55,  "category": "other"},
    {"formula": "Cu2O",   "name_ko": "산화구리(I)",    "molar_mass": 143.09, "category": "other"},
    {"formula": "Cr2O3",  "name_ko": "산화크롬",       "molar_mass": 151.99, "category": "other"},
    {"formula": "WO3",    "name_ko": "삼산화텅스텐",   "molar_mass": 231.84, "category": "other"},
    {"formula": "MoO3",   "name_ko": "삼산화몰리브덴", "molar_mass": 143.94, "category": "other"},
    {"formula": "Nb2O5",  "name_ko": "오산화니오브",   "molar_mass": 265.81, "category": "other"},
    {"formula": "Ta2O5",  "name_ko": "오산화탄탈럼",   "molar_mass": 441.89, "category": "other"},
    {"formula": "CdO",    "name_ko": "산화카드뮴",     "molar_mass": 128.41, "category": "other"},

    # ── Rare Earth Oxides (희토류 산화물) ──
    {"formula": "La2O3",  "name_ko": "산화란타넘",     "molar_mass": 325.81, "category": "other"},
    {"formula": "CeO2",   "name_ko": "산화세륨",       "molar_mass": 172.12, "category": "other"},
    {"formula": "Nd2O3",  "name_ko": "산화네오디뮴",   "molar_mass": 336.48, "category": "other"},
    {"formula": "Pr2O3",  "name_ko": "산화프라세오디뮴","molar_mass": 329.81, "category": "other"},
    {"formula": "Sm2O3",  "name_ko": "산화사마륨",     "molar_mass": 348.72, "category": "other"},
    {"formula": "Eu2O3",  "name_ko": "산화유로퓸",     "molar_mass": 351.93, "category": "other"},
    {"formula": "Gd2O3",  "name_ko": "산화가돌리늄",   "molar_mass": 362.50, "category": "other"},
    {"formula": "Tb2O3",  "name_ko": "산화터븀",       "molar_mass": 365.85, "category": "other"},
    {"formula": "Dy2O3",  "name_ko": "산화디스프로슘", "molar_mass": 372.99, "category": "other"},
    {"formula": "Ho2O3",  "name_ko": "산화홀뮴",       "molar_mass": 377.86, "category": "other"},
    {"formula": "Er2O3",  "name_ko": "산화에르븀",     "molar_mass": 382.56, "category": "other"},
    {"formula": "Tm2O3",  "name_ko": "산화툴륨",       "molar_mass": 385.87, "category": "other"},
    {"formula": "Yb2O3",  "name_ko": "산화이테르븀",   "molar_mass": 394.08, "category": "other"},
    {"formula": "Lu2O3",  "name_ko": "산화루테튬",     "molar_mass": 397.93, "category": "other"},
    {"formula": "Y2O3",   "name_ko": "산화이트륨",     "molar_mass": 225.81, "category": "other"},

    # ── Halides & Others (할로겐화물 등) ──
    {"formula": "F",      "name_ko": "불소",           "molar_mass": 19.00,  "category": "other"},
    {"formula": "Cl",     "name_ko": "염소",           "molar_mass": 35.45,  "category": "other"},
    {"formula": "Br",     "name_ko": "브롬",           "molar_mass": 79.90,  "category": "other"},
    {"formula": "I",      "name_ko": "요오드",         "molar_mass": 126.90, "category": "other"},
    {"formula": "S",      "name_ko": "황",             "molar_mass": 32.07,  "category": "other"},
    {"formula": "N",      "name_ko": "질소",           "molar_mass": 14.01,  "category": "other"},
    {"formula": "C",      "name_ko": "탄소",           "molar_mass": 12.01,  "category": "other"},
    {"formula": "H2O",    "name_ko": "물",             "molar_mass": 18.02,  "category": "other"},
]


def get_oxides(*, category: str | None = None) -> list[OxideInfo]:
    """Return the oxide list, optionally filtered by category.

    Args:
        category: One of 'network_former', 'network_modifier',
                  'intermediate', 'other'. If None, returns all.
    """
    if category is None:
        return list(OXIDE_LIST)
    return [o for o in OXIDE_LIST if o["category"] == category]


def get_oxide_formulas(*, category: str | None = None) -> list[str]:
    """Return only the formula strings."""
    return [o["formula"] for o in get_oxides(category=category)]
