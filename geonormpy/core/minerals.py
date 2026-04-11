"""
Normative mineral definitions (CIPW)
===================================
Molar masses and idealized compositions of CIPW minerals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Mineral:
    name: str
    formula: str
    molar_mass: float


MINERALS: Dict[str, Mineral] = {
    # Salic minerals
    "Q":   Mineral("Q",   "SiO2", 60.083),
    "Cor": Mineral("Cor", "Al2O3", 101.961),
    "Or":  Mineral("Or",  "KAlSi3O8", 278.33),
    "Ab":  Mineral("Ab",  "NaAlSi3O8", 262.22),
    "An":  Mineral("An",  "CaAl2Si2O8", 278.21),

    # Feldspathoids
    "Le":  Mineral("Le",  "KAlSi2O6", 218.25),
    "Ne":  Mineral("Ne",  "NaAlSiO4", 142.05),
    "Kp":  Mineral("Kp",  "KAlSiO4", 158.16),

    # Mafic silicates
    "Ac":  Mineral("Ac",  "NaFeSi2O6", 231.00),
    "Di":  Mineral("Di",  "CaMgSi2O6", 216.55),
    "Hd":  Mineral("Hd",  "CaFeSi2O6", 248.09),
    "Wo":  Mineral("Wo",  "CaSiO3", 116.16),
    "En":  Mineral("En",  "MgSiO3", 100.39),
    "Fs":  Mineral("Fs",  "FeSiO3", 131.93),
    "Fo":  Mineral("Fo",  "Mg2SiO4", 140.69),
    "Fa":  Mineral("Fa",  "Fe2SiO4", 203.77),

    # Oxides and accessories
    "Mt":  Mineral("Mt",  "Fe3O4", 231.54),
    "Hm":  Mineral("Hm",  "Fe2O3", 159.69),
    "Ilm": Mineral("Ilm", "FeTiO3", 151.71),
    "Cm":  Mineral("Cm",  "FeCr2O4", 223.84),
    "Ru":  Mineral("Ru",  "TiO2", 79.87),
    "Tn":  Mineral("Tn",  "CaTiSiO5", 196.06),
    "Z":   Mineral("Z",   "ZrSiO4", 183.31),
    # Classical CIPW normative apatite convention after Cross et al. (1902):
    # Ca(10/3)(PO4)2, i.e. 10/3 mol CaO per mol P2O5. This differs from the
    # mineralogical apatite formula Ca10(PO4)6(OH,F,Cl)2, but it is the
    # established normative representation and must stay consistent with the
    # stoichiometry used in `norms/cipw.py`.
    "Ap":  Mineral("Ap",  "Ca(10/3)(PO4)2", 328.86),

    # Volatiles, carbonates, salts
    "Cc":  Mineral("Cc",  "CaCO3", 100.09),
    "Py":  Mineral("Py",  "FeS2", 119.98),
    "Fl":  Mineral("Fl",  "CaF2", 78.07),
    "Hl":  Mineral("Hl",  "NaCl", 58.44),
    "Th":  Mineral("Th",  "Na2SO4", 142.04),

    # Metasilicates
    "ns":  Mineral("ns",  "Na2SiO3", 122.06),
    "ks":  Mineral("ks",  "K2SiO3", 154.28),
}


MINERAL_MOLAR_MASS = {k: v.molar_mass for k, v in MINERALS.items()}
