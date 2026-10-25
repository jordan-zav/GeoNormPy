import random

import pytest

from geonormpy.core.chemistry import normalize_oxides
from geonormpy.core.constants import MOLAR_MASS
from geonormpy.norms.cipw import cipw


# Independently stated oxide equivalents per mineral formula mole. These
# checks include residuals and do not infer validity from a sum near 100%.
EQUIVALENTS = {
    'Q': {'SiO2': 1}, 'Cor': {'Al2O3': 1},
    'Or': {'K2O': .5, 'Al2O3': .5, 'SiO2': 3},
    'Ab': {'Na2O': .5, 'Al2O3': .5, 'SiO2': 3},
    'An': {'CaO': 1, 'Al2O3': 1, 'SiO2': 2},
    'Ne': {'Na2O': .5, 'Al2O3': .5, 'SiO2': 1},
    'Le': {'K2O': .5, 'Al2O3': .5, 'SiO2': 2},
    'Kp': {'K2O': .5, 'Al2O3': .5, 'SiO2': 1},
    'Ac': {'Na2O': .5, 'Fe2O3': .5, 'SiO2': 2},
    'Di': {'CaO': 1, 'MgO': 1, 'SiO2': 2},
    'Hd': {'CaO': 1, 'FeO': 1, 'SiO2': 2},
    'Wo': {'CaO': 1, 'SiO2': 1}, 'Cs': {'CaO': 2, 'SiO2': 1},
    'En': {'MgO': 1, 'SiO2': 1}, 'Fs': {'FeO': 1, 'SiO2': 1},
    'Fo': {'MgO': 2, 'SiO2': 1}, 'Fa': {'FeO': 2, 'SiO2': 1},
    'Mt': {'FeO': 1, 'Fe2O3': 1}, 'Hm': {'Fe2O3': 1},
    'Ilm': {'FeO': 1, 'TiO2': 1}, 'Ru': {'TiO2': 1},
    'Tn': {'CaO': 1, 'TiO2': 1, 'SiO2': 1}, 'Pf': {'CaO': 1, 'TiO2': 1},
    'Z': {'ZrO2': 1, 'SiO2': 1}, 'Cm': {'FeO': 1, 'Cr2O3': 1},
    'Ap': {'CaO': 10/3, 'P2O5': 1},
    'ns': {'Na2O': 1, 'SiO2': 1}, 'ks': {'K2O': 1, 'SiO2': 1},
    'Cc': {'CaO': 1, 'CO2': 1},
}


@pytest.mark.parametrize('seed', range(100))
def test_oxide_equivalent_inventory_is_conserved_even_for_incomplete_norms(seed):
    rng = random.Random(seed)
    oxides = {name: rng.uniform(.01, maximum) for name, maximum in {
        'SiO2': 80, 'Al2O3': 25, 'MgO': 30, 'CaO': 30, 'FeO': 15,
        'Fe2O3': 10, 'Na2O': 10, 'K2O': 10, 'TiO2': 5, 'P2O5': 2,
        'ZrO2': .1, 'Cr2O3': .1, 'CO2': .1,
    }.items()}
    result = cipw(oxides, debug=True)
    normalized = normalize_oxides(oxides)
    inventory = dict(result['residual_oxides_moles'])
    for mineral, amount in result['minerals_moles'].items():
        assert amount >= 0
        for oxide, coefficient in EQUIVALENTS[mineral].items():
            inventory[oxide] = inventory.get(oxide, 0) + coefficient * amount
    for oxide, weight in normalized.items():
        assert inventory.get(oxide, 0) == pytest.approx(weight / MOLAR_MASS[oxide], abs=1e-10)
