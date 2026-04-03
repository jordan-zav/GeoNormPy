"""
Fundamental constants for normative geochemistry
================================================
All molar masses in g/mol.
Developed by Jordan Zavaleta (UNI, Peru)
"""

from typing import Dict

# -------------------------
# Oxide molar masses
# -------------------------

# Consolidación de masas molares para GeoNormPy
MOLAR_MASS: Dict[str, float] = {
    "SiO2": 60.083,
    "Al2O3": 101.961,
    "FeO": 71.844,
    "Fe2O3": 159.688,
    "MgO": 40.304,
    "CaO": 56.077,
    "Na2O": 61.979,
    "K2O": 94.196,
    "TiO2": 79.866,
    "P2O5": 141.944,
    "MnO": 70.937,
    "ZrO2": 123.22,
    "Cr2O3": 151.99,
    "CO2": 44.01,
    "S": 32.06,
    "F": 19.00,
    "Cl": 35.45,
    "SO3": 80.06,
}

# -------------------------
# Iron speciation defaults
# -------------------------

#: Default Fe3+ / Fe_total ratio after Le Maitre (2002)
FE3_FRACTION_DEFAULT = 0.15

# -------------------------
# Numerical tolerances
# -------------------------

#: Default numerical tolerance for geochemical calculations (EPS)
EPS = 1e-12