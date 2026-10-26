"""Independent component inventories and adversarial profile properties.

These checks reconstruct each oxide, not just a total mass sum. The phase
formulae below are a test oracle independent of the allocation solver.
"""

import json
import math
import random

import pandas as pd
import pytest

from geonormpy import cipw, cipw_safe
from geonormpy.core.constants import MOLAR_MASS
from geonormpy.norms.batch import calculate_cipw_dataframe
from geonormpy.norms.revised import MASSES

PROFILES = ("extended_cipw_v3", "verma2003", "pruseth2009")
FORMULAE = {
    "Q": {"SiO2": 1}, "Cor": {"Al2O3": 1},
    "Or": {"K2O": .5, "Al2O3": .5, "SiO2": 3},
    "Ab": {"Na2O": .5, "Al2O3": .5, "SiO2": 3},
    "An": {"CaO": 1, "Al2O3": 1, "SiO2": 2},
    "Ne": {"Na2O": .5, "Al2O3": .5, "SiO2": 1},
    "Le": {"K2O": .5, "Al2O3": .5, "SiO2": 2},
    "Kp": {"K2O": .5, "Al2O3": .5, "SiO2": 1},
    "Ac": {"Na2O": .5, "Fe2O3": .5, "SiO2": 2},
    "Di": {"CaO": 1, "MgO": 1, "SiO2": 2},
    "Hd": {"CaO": 1, "FeO": 1, "SiO2": 2},
    "Wo": {"CaO": 1, "SiO2": 1}, "Cs": {"CaO": 2, "SiO2": 1},
    "En": {"MgO": 1, "SiO2": 1}, "Fs": {"FeO": 1, "SiO2": 1},
    "Fo": {"MgO": 2, "SiO2": 1}, "Fa": {"FeO": 2, "SiO2": 1},
    "Mt": {"FeO": 1, "Fe2O3": 1}, "Hm": {"Fe2O3": 1},
    "Ilm": {"FeO": 1, "TiO2": 1}, "Cm": {"FeO": 1, "Cr2O3": 1},
    "Ru": {"TiO2": 1}, "Tn": {"CaO": 1, "TiO2": 1, "SiO2": 1},
    "Pf": {"CaO": 1, "TiO2": 1}, "Z": {"ZrO2": 1, "SiO2": 1},
    "Ap": {"CaO": 10 / 3, "P2O5": 1},
    "FAp": {"CaO": 10, "P2O5": 3, "F": 2},
    "Cc": {"CaO": 1, "CO2": 1}, "Nc": {"Na2O": 1, "CO2": 1},
    "Py": {"FeO": 1, "S": 2}, "Fl": {"CaO": 1, "F": 2},
    "Hl": {"Na2O": .5, "Cl": 1}, "Th": {"Na2O": 1, "SO3": 1},
    "ns": {"Na2O": 1, "SiO2": 1}, "ks": {"K2O": 1, "SiO2": 1},
}
SUBSTITUTIONS = (("FeO", "MnO", "NiO", "CoO"), ("CaO", "SrO", "BaO"),
                 ("Na2O", "Li2O"), ("K2O", "Rb2O", "Cs2O"), ("Cr2O3", "V2O3"))
PRUSETH_EXCLUDED = {"CoO", "Rb2O", "Cs2O", "Li2O", "V2O3", "Cl", "SO3"}
BASE = {"SiO2": 60., "Al2O3": 16., "TiO2": .5, "FeO": 6., "Fe2O3": 1.,
        "MgO": 3., "CaO": 5., "Na2O": 4., "K2O": 4., "P2O5": .1, "MnO": .2}


def assert_inventory(source, result, profile):
    reconstructed = dict(result["residual_oxides_moles"])
    for phase, amount in result["minerals_moles"].items():
        for oxide, coefficient in FORMULAE[phase].items():
            reconstructed[oxide] = reconstructed.get(oxide, 0.) + coefficient * amount
    if profile == "pruseth2009":
        reconstructed["F"] = reconstructed.get("F", 0.) - 2 * result["minerals_moles"].get("FAp", 0.)
    for group in SUBSTITUTIONS:
        target = group[0]
        total = math.fsum(source.get(k, 0.) / MASSES[k] for k in group)
        amount = reconstructed.pop(target, 0.)
        for oxide in group:
            reconstructed[oxide] = amount * source.get(oxide, 0.) / MASSES[oxide] / total if total else 0.
    for oxide in set(MASSES) | set(reconstructed):
        assert reconstructed.get(oxide, 0.) == pytest.approx(source.get(oxide, 0.) / MASSES[oxide], abs=2e-10), oxide


@pytest.mark.parametrize("profile", PROFILES[1:])
@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("distribution", ["dense", "sparse", "logarithmic"])
def test_random_component_conservation_and_metamorphic_properties(profile, seed, distribution):
    rng = random.Random(2026102600 + seed)
    keys = [k for k in MASSES if profile != "pruseth2009" or k not in PRUSETH_EXCLUDED]
    for index in range(1000):
        source = {k: (10 ** rng.uniform(-14, 2) if distribution == "logarithmic" else rng.uniform(0, 60)) for k in keys}
        if distribution == "sparse":
            source = {k: (v if rng.random() > .7 else 0.) for k, v in source.items()}
        if not any(source.values()):
            source["SiO2"] = 1.
        total = math.fsum(source.values())
        expected = {k: 100 * v / total for k, v in source.items()}
        result = cipw(source, profile=profile, iron_policy="measured", debug=True)
        assert result["adjusted_input_wtpercent"] == pytest.approx(expected, abs=1e-11)
        assert_inventory(expected, result, profile)
        assert result["mass_balance"]["inventory_sum_including_silica_deficit"] == pytest.approx(100, abs=1e-7)
        assert all(math.isfinite(v) and v >= 0 for v in result["minerals_wtpercent"].values())
        if result["flags"]["calculation_complete"]:
            assert result["mass_balance_error"] < 1e-7
        phases = result["minerals_moles"]
        assert not (phases.get("Q", 0) > 1e-10 and any(phases.get(k, 0) > 1e-10 for k in ("Fo", "Fa", "Ne", "Le", "Kp")))
        json.dumps(result, allow_nan=False)
        if index < 10:
            reverse = cipw(dict(reversed(list(source.items()))), profile=profile, iron_policy="measured")
            assert reverse["minerals_wtpercent"] == pytest.approx(result["minerals_wtpercent"], abs=1e-8)
            for factor in (1e-200, 1e200):
                scaled = cipw({k: v * factor for k, v in source.items()}, profile=profile, iron_policy="measured")
                assert scaled["minerals_wtpercent"] == pytest.approx(result["minerals_wtpercent"], abs=1e-8)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("fraction", [0., .01, .15, .5, .99, 1.])
def test_fixed_total_iron_matches_equivalent_measured_pair(profile, fraction):
    masses = MOLAR_MASS if profile == PROFILES[0] else MASSES
    total = BASE["FeO"] + 2 * BASE["Fe2O3"] * masses["FeO"] / masses["Fe2O3"]
    source = {k: v for k, v in BASE.items() if k not in {"FeO", "Fe2O3"}}
    assumed = cipw(dict(source, FeOT=total), profile=profile, iron_policy="fixed", fe3_fraction=fraction)
    measured = cipw(dict(source, FeO=total * (1 - fraction),
                         Fe2O3=total * fraction * masses["Fe2O3"] / (2 * masses["FeO"])),
                    profile=profile, iron_policy="measured")
    assert assumed["minerals_wtpercent"] == pytest.approx(measured["minerals_wtpercent"], abs=1e-10)


@pytest.mark.parametrize("profile", PROFILES[1:])
def test_silica_sweep_is_continuous_and_conserves_components(profile):
    previous = None
    for step in range(1001):
        sample = dict(BASE, SiO2=step / 10)
        result = cipw(sample, profile=profile, iron_policy="measured", debug=True)
        assert_inventory(result["adjusted_input_wtpercent"], result, profile)
        if previous is not None:
            assert max(abs(result["minerals_wtpercent"].get(k, 0) - previous.get(k, 0))
                       for k in set(previous) | set(result["minerals_wtpercent"])) < 2
        previous = result["minerals_wtpercent"]


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("bad", [True, -1., float("nan"), float("inf"), "bad", [], {}])
def test_invalid_measurements_are_json_serializable_failures(profile, bad):
    outcome = cipw_safe(dict(BASE, SiO2=bad), profile=profile)
    assert not outcome["ok"]
    json.dumps(outcome, allow_nan=False)


@pytest.mark.parametrize("profile", PROFILES)
def test_mixed_batch_preserves_failed_rows_and_repeated_indices(profile):
    frame = pd.DataFrame([BASE, dict(BASE, SiO2=-1), BASE], index=[5, 5, 9])
    result = calculate_cipw_dataframe(frame, profile=profile)
    assert list(result.index) == [5, 5, 9]
    assert pd.isna(result.iloc[0].calc_error)
    assert result.iloc[1].error_code == "invalid_measurement"
    assert pd.isna(result.iloc[1].Q)
    assert result.iloc[2].Q == pytest.approx(result.iloc[0].Q)


@pytest.mark.parametrize("phase,source,expected_moles", [
    ("Hl", {"SiO2": 60., "Na2O": .1, "Cl": 4.}, .2 / MASSES["Na2O"]),
    ("Th", {"SiO2": 60., "Na2O": .1, "SO3": 4.}, .1 / MASSES["Na2O"]),
    ("Py", {"SiO2": 60., "FeO": .1, "S": 4.}, .1 / MASSES["FeO"]),
    ("Fl", {"SiO2": 60., "CaO": .1, "F": 4.}, .1 / MASSES["CaO"]),
    ("Cm", {"SiO2": 60., "FeO": .1, "Cr2O3": 4.}, .1 / MASSES["FeO"]),
    ("Ilm", {"SiO2": 60., "FeO": .1, "TiO2": 4.}, .1 / MASSES["FeO"]),
    ("Hl", {"SiO2": 60., "Na2O": .1, "Cl": .05}, .05 / MASSES["Cl"]),
    ("Py", {"SiO2": 60., "FeO": .1, "S": .05}, .025 / MASSES["S"]),
])
def test_accessory_limiting_reagent_matches_hand_calculation(phase, source, expected_moles):
    result = cipw(source, profile="verma2003", strict=True)
    assert result["minerals_moles"][phase] == pytest.approx(expected_moles * 100 / sum(source.values()), abs=1e-12)
    assert result["mass_balance_error"] < 1e-9


@pytest.mark.parametrize("mode,phase", [("calcite", "Cc"), ("sodium_carbonate", "Nc"), ("free", None)])
def test_carbonate_hypothesis_matches_hand_calculation(mode, phase):
    source = {"SiO2": 60., "CO2": .2, "CaO": 2., "Na2O": 2.}
    result = cipw(source, profile="verma2003", carbonate_mode=mode, strict=True)
    if phase:
        assert result["minerals_moles"][phase] == pytest.approx(.2 / MASSES["CO2"] * 100 / 64.2)
    else:
        assert result["free_components_wtpercent"]["CO2"] == pytest.approx(.2 * 100 / 64.2)
    assert result["mass_balance_error"] < 1e-9


@pytest.mark.parametrize("profile", PROFILES[1:])
@pytest.mark.parametrize("fraction", [0., .15, 1.])
def test_total_iron_oxide_representations_are_equivalent(profile, fraction):
    source = {k: v for k, v in BASE.items() if k not in {"FeO", "Fe2O3"}}
    ferrous = cipw(dict(source, FeOT=10.), profile=profile, iron_policy="fixed", fe3_fraction=fraction)
    ferric = cipw(dict(source, Fe2O3T=10 * MASSES["Fe2O3"] / (2 * MASSES["FeO"])),
                  profile=profile, iron_policy="fixed", fe3_fraction=fraction)
    assert ferric["minerals_wtpercent"] == pytest.approx(ferrous["minerals_wtpercent"], abs=1e-10)
