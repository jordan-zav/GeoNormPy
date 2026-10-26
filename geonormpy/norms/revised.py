"""Revised sequential and matrix CIPW profiles, implemented from equations.

References: Verma et al. (2003), pp. 197-216; Pruseth (2009), tables 1-3
and steps 1-25. Mineral inventories use formula moles (FAp uses P2O5=3).
The historical kernel is deliberately not used by either revised solver.
"""

from collections.abc import Mapping
from math import fsum, isfinite

import numpy as np

from ..core.iron import apply_iron_policy
from ..errors import GeoNormPyError

EPS = 1e-12
OXYGEN_MASS = 15.9994
# Published oxide masses, internally consistent mineral masses derived below.
MASSES = {
    "SiO2": 60.0843, "TiO2": 79.8658, "Al2O3": 101.961276,
    "Fe2O3": 159.6882, "FeO": 71.8444, "MgO": 40.3044,
    "CaO": 56.0774, "Na2O": 61.97894, "K2O": 94.196,
    "P2O5": 141.944522, "MnO": 70.93745, "NiO": 74.6928,
    "CoO": 74.9326, "SrO": 103.6194, "BaO": 153.3264,
    "Rb2O": 186.935, "Cs2O": 281.8103, "Li2O": 29.8814,
    "V2O3": 149.8812, "Cr2O3": 151.9904, "ZrO2": 123.2228,
    "CO2": 44.0095, "S": 32.066, "F": 18.9984032,
    "Cl": 35.4527, "SO3": 80.0642,
}
PRUSETH_UNSUPPORTED = {"CoO", "Rb2O", "Cs2O", "Li2O", "V2O3", "Cl", "SO3"}
POOLS = {"FeO": ("MnO", "NiO", "CoO"), "CaO": ("SrO", "BaO"),
         "Na2O": ("Li2O",), "K2O": ("Rb2O", "Cs2O"), "Cr2O3": ("V2O3",)}
# Equivalent oxide consumption per formula mole, plus oxygen displacement.
COMPOSITIONS = {
    "Q": {"SiO2": 1}, "Cor": {"Al2O3": 1},
    "Or": {"K2O": .5, "Al2O3": .5, "SiO2": 3},
    "Ab": {"Na2O": .5, "Al2O3": .5, "SiO2": 3},
    "An": {"CaO": 1, "Al2O3": 1, "SiO2": 2},
    "Le": {"K2O": .5, "Al2O3": .5, "SiO2": 2},
    "Ne": {"Na2O": .5, "Al2O3": .5, "SiO2": 1},
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
    "FAp": {"CaO": 10, "P2O5": 3, "F": 2, "O": -1},
    "Cc": {"CaO": 1, "CO2": 1}, "Nc": {"Na2O": 1, "CO2": 1},
    "Py": {"FeO": 1, "S": 2, "O": -1},
    "Fl": {"CaO": 1, "F": 2, "O": -1},
    "Hl": {"Na2O": .5, "Cl": 1, "O": -.5},
    "Th": {"Na2O": 1, "SO3": 1},
    "ns": {"Na2O": 1, "SiO2": 1}, "ks": {"K2O": 1, "SiO2": 1},
}


def clean_input(chemistry, profile):
    if not isinstance(chemistry, Mapping):
        raise GeoNormPyError("invalid_analysis", "Oxides must be a mapping.")
    output = {}
    for key, value in chemistry.items():
        if key not in MASSES and key not in {"FeOT", "Fe2O3T"}:
            raise GeoNormPyError("unsupported_oxide", f"Unsupported oxide: {key}; use wt% oxide columns only.", field=str(key))
        if value is None:
            continue
        if isinstance(value, (bool, np.bool_)):
            raise GeoNormPyError("invalid_measurement", "Boolean measurements are not allowed.", field=key)
        try:
            number = float(value)
        except (ValueError, TypeError, OverflowError) as error:
            raise GeoNormPyError("invalid_measurement", "Enter a finite nonnegative measurement.", field=key) from error
        if not isfinite(number) or number < 0:
            raise GeoNormPyError("invalid_measurement", "Enter a finite nonnegative measurement.", field=key)
        if profile == "pruseth2009" and key in PRUSETH_UNSUPPORTED and number > 0:
            raise GeoNormPyError("unsupported_profile_oxide", f"{key} is outside the published Pruseth 2009 input set. Use verma2003 or omit only if analytically justified.", field=key)
        output[key] = number
    return output


def normalize(chemistry):
    largest = max(chemistry.values(), default=0)
    if largest <= 0:
        raise GeoNormPyError("empty_analysis", "Total oxide sum must be positive.")
    scaled = {k: v / largest for k, v in chemistry.items()}
    total = fsum(scaled.values())
    return {k: 100 * v / total for k, v in scaled.items()}


class State:
    def __init__(self, moles):
        self.oxides = dict(moles)
        self.minerals = {}
        self.free_oxygen = 0.0
        self.normative_fluorine = 0.0

    def get(self, key):
        return self.oxides.get(key, 0.0)

    def produce(self, key, amount):
        if amount > EPS:
            self.minerals[key] = self.minerals.get(key, 0.0) + float(amount)

    def consume(self, consumption):
        for key, amount in consumption.items():
            new = self.get(key) - amount
            if key != "SiO2" and new < -EPS:
                raise GeoNormPyError("allocation_invariant", f"Negative oxide in {key}: {new}.", field=key)
            self.oxides[key] = 0.0 if abs(new) <= EPS else float(new)

    def form(self, phase, amount):
        if amount <= EPS:
            return
        composition = COMPOSITIONS[phase]
        self.consume({key: coefficient * amount for key, coefficient in composition.items() if key != "O"})
        self.free_oxygen -= composition.get("O", 0) * amount
        self.produce(phase, amount)


def pool_components(chemistry, profile):
    moles = {k: value / MASSES[k] for k, value in chemistry.items()}
    weights = dict(MASSES, O=OXYGEN_MASS)
    pools = {}
    for target, additions in POOLS.items():
        components = (target, *[a for a in additions if profile != "pruseth2009" or a not in PRUSETH_UNSUPPORTED])
        total_moles = fsum(moles.get(k, 0) for k in components)
        if total_moles > 0:
            weights[target] = fsum(chemistry.get(k, 0) for k in components) / total_moles
            pools[target] = {k: moles.get(k, 0) / total_moles for k in components if moles.get(k, 0) > 0}
        for addition in additions:
            moles.pop(addition, None)
        moles[target] = total_moles
    return moles, weights, pools


def apatite(state, profile):
    phosphorus = min(state.get("P2O5"), state.get("CaO") * 3 / 10)
    if phosphorus <= EPS:
        return
    if profile == "verma2003":
        fluorinated = min(phosphorus, state.get("F") * 1.5)
        state.form("FAp", fluorinated / 3)
        state.form("Ap", phosphorus - fluorinated)
    else:
        # Pruseth uses normative fluorapatite even without measured F.
        # Its unmeasured F is an explicit signed mass correction, not input F.
        amount = phosphorus / 3
        state.consume({"P2O5": phosphorus, "CaO": 10 * amount})
        state.produce("FAp", amount)
        state.free_oxygen += amount
        state.normative_fluorine += 2 * amount


def carbonates(state, mode):
    if mode == "calcite":
        state.form("Cc", min(state.get("CaO"), state.get("CO2")))
    elif mode == "sodium_carbonate":
        state.form("Nc", min(state.get("Na2O"), state.get("CO2")))
    # 'free' retains measured CO2 as a separately reported component.


def accessory_allocation(state, profile, carbonate_mode):
    state.form("Z", state.get("ZrO2"))
    if profile == "verma2003":
        apatite(state, profile)
        state.form("Fl", min(state.get("CaO"), state.get("F") / 2))
        state.form("Hl", min(state.get("Na2O") * 2, state.get("Cl")))
        state.form("Th", min(state.get("Na2O"), state.get("SO3")))
        state.form("Py", min(state.get("FeO"), state.get("S") / 2))
        carbonates(state, carbonate_mode)
        state.form("Cm", min(state.get("FeO"), state.get("Cr2O3")))
        state.form("Ilm", min(state.get("FeO"), state.get("TiO2")))
    else:
        # Pruseth step 1; Ti remains provisional until matrix step 8.
        state.form("Py", min(state.get("FeO"), state.get("S") / 2))
        state.form("Cm", min(state.get("FeO"), state.get("Cr2O3")))
        apatite(state, profile)
        carbonates(state, "calcite")
        state.form("Fl", min(state.get("CaO"), state.get("F") / 2))


def sequential_saturated(state):
    state.form("Or", 2 * min(state.get("K2O"), state.get("Al2O3")))
    state.form("Ab", 2 * min(state.get("Na2O"), state.get("Al2O3")))
    state.form("Ac", 2 * min(state.get("Na2O"), state.get("Fe2O3")))
    state.form("ns", state.get("Na2O"))
    state.form("ks", state.get("K2O"))
    state.form("An", min(state.get("CaO"), state.get("Al2O3")))
    state.form("Cor", state.get("Al2O3"))
    state.form("Tn", min(state.get("CaO"), state.get("TiO2")))
    state.form("Ru", state.get("TiO2"))
    state.form("Mt", min(state.get("FeO"), state.get("Fe2O3")))
    state.form("Hm", state.get("Fe2O3"))
    mg, fe = state.get("MgO"), state.get("FeO")
    total = mg + fe
    if total > EPS:
        cpx = min(state.get("CaO"), total)
        di = cpx * mg / total
        state.form("Di", di)
        state.form("Hd", cpx - di)
    state.form("En", state.get("MgO"))
    state.form("Fs", state.get("FeO"))
    state.form("Wo", state.get("CaO"))


def matrix_saturated(state):
    # Pruseth table 1: rows Al2O3, Fe2O3, FeO, MgO, CaO, Na2O, K2O;
    # columns C, Or(oxide unit), Ab(oxide unit), An, En, Fs, Hm.
    matrix = np.array([[1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 1],
                       [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 1, 0, 0],
                       [0, 0, 0, 1, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0],
                       [0, 1, 0, 0, 0, 0, 0]], dtype=float)
    vector = np.array([state.get(k) for k in ("Al2O3", "Fe2O3", "FeO", "MgO", "CaO", "Na2O", "K2O")])
    cor, ort, alb, an, mg, fe, hm = np.linalg.solve(matrix, vector)
    # Active reactions remove the Al2O3 deficiency (paper steps 3-7).
    deficit = max(0.0, -cor)
    cor = max(0.0, cor)
    reduction = min(an, deficit)
    an -= reduction
    wo = reduction
    deficit -= reduction
    ac = min(alb, hm, deficit)
    alb -= ac
    hm -= ac
    deficit -= ac
    ns = min(alb, deficit)
    alb -= ns
    deficit -= ns
    ks = min(ort, deficit)
    ort -= ks
    deficit -= ks
    if deficit > EPS:
        raise GeoNormPyError("allocation_invariant", "Unresolved matrix alumina deficiency.")
    # Ti, Fe oxides, clinopyroxene and hypersthene: paper step 8.
    il = min(state.get("TiO2"), fe)
    fe -= il
    tn = min(state.get("TiO2") - il, wo)
    wo -= tn
    ru = state.get("TiO2") - il - tn
    mt = min(hm, fe)
    hm -= mt
    fe -= mt
    cpx = min(wo, mg + fe)
    di = cpx * mg / (mg + fe) if mg + fe > EPS else 0.0
    hd = cpx - di
    phases = {"Cor": cor, "Or": 2 * ort, "Ab": 2 * alb, "An": an,
              "Ac": 2 * ac, "ns": ns, "ks": ks, "Ilm": il, "Tn": tn,
              "Ru": ru, "Mt": mt, "Hm": hm, "Di": di, "Hd": hd,
              "En": mg - di, "Fs": fe - hd, "Wo": wo - cpx}
    consumed = {}
    for phase, amount in phases.items():
        if amount > EPS:
            for oxide, coefficient in COMPOSITIONS[phase].items():
                consumed[oxide] = consumed.get(oxide, 0) + coefficient * amount
            state.produce(phase, amount)
    state.consume(consumed)


def resolve_silica(state, profile):
    silica = state.get("SiO2")
    if abs(silica) <= EPS:
        state.oxides["SiO2"] = 0.0
        return "saturated", 0.0
    if silica > 0:
        state.form("Q", silica)
        return "oversaturated", 0.0
    deficit = -silica

    def react(source, products, release, capacity=None):
        nonlocal deficit
        available = state.minerals.get(source, 0)
        amount = min(available, max(deficit, 0) / release)
        if capacity is not None:
            amount = min(amount, capacity)
        if amount > 0:
            state.minerals[source] -= amount
            for target, coefficient in products.items():
                state.produce(target, coefficient * amount)
            deficit -= release * amount

    # Reduce the Mg and Fe components of Hy in their original proportion.
    hy = state.minerals.get("En", 0) + state.minerals.get("Fs", 0)
    reduction = min(hy, 2 * deficit)
    if hy > 0:
        en = reduction * state.minerals.get("En", 0) / hy
        fs = reduction - en
        react("En", {"Fo": .5}, .5, en)
        react("Fs", {"Fa": .5}, .5, fs)
    react("Tn", {"Pf": 1}, 1)
    react("Ab", {"Ne": 1}, 2)
    react("Or", {"Le": 1}, 1)
    react("Wo", {"Cs": .5}, .5)
    cpx = state.minerals.get("Di", 0) + state.minerals.get("Hd", 0)
    reduction = min(cpx, max(deficit, 0))
    if cpx > 0:
        di = reduction * state.minerals.get("Di", 0) / cpx
        hd = reduction - di
        react("Di", {"Cs": .5, "Fo": .5}, 1, di)
        react("Hd", {"Cs": .5, "Fa": .5}, 1, hd)
    react("Le", {"Kp": 1}, 1)
    if profile == "pruseth2009":
        # Matrix extension, paper step 20: 2 An -> Cs + 2 C + 3 SiO2.
        react("An", {"Cs": .5, "Cor": 1}, 1.5)
    deficit = max(0.0, deficit)
    if deficit <= EPS:
        deficit = 0.0
    state.oxides["SiO2"] = -deficit
    state.minerals = {k: float(v) for k, v in state.minerals.items() if v > EPS}
    return "undersaturated", deficit


def calculate_revised(chemistry, *, profile, iron_policy, fe3_fraction, carbonate_mode, strict, mass_tol, debug):
    raw = normalize(clean_input(chemistry, profile))
    resolved, iron_flags = apply_iron_policy(raw, iron_policy, fe3_fraction, MASSES, strict)
    adjusted = normalize(resolved)
    moles, weights, pools = pool_components(adjusted, profile)
    state = State(moles)
    accessory_allocation(state, profile, carbonate_mode)
    alumina = state.get("Al2O3")
    alkalis = state.get("Na2O") + state.get("K2O")
    alumina_state = ("peralkaline" if alkalis > alumina else
                     "peraluminous" if alumina > alkalis + state.get("CaO") else "metaluminous")
    (sequential_saturated if profile == "verma2003" else matrix_saturated)(state)
    saturation, deficit = resolve_silica(state, profile)
    mineral_masses = {phase: fsum(coefficient * weights[oxide] for oxide, coefficient in composition.items())
                      for phase, composition in COMPOSITIONS.items()}
    minerals = {phase: amount * mineral_masses[phase] for phase, amount in state.minerals.items()}
    free = {key: value * weights[key] for key, value in state.oxides.items() if key != "SiO2" and value > EPS}
    if state.free_oxygen > 0:
        free["O"] = state.free_oxygen * OXYGEN_MASS
    if state.normative_fluorine > 0:
        free["normative_F_correction"] = -state.normative_fluorine * MASSES["F"]
    total = fsum(minerals.values())
    accounted = fsum((total, *free.values()))
    error = abs(100 - accounted)
    complete = deficit <= EPS and bool(minerals)
    flags = dict(iron_flags, norm_model=profile, silica_saturation=saturation,
                 alumina_state=alumina_state, residual_silica_deficit_moles=deficit,
                 calculation_complete=complete, mass_balance_warning=error > mass_tol,
                 free_components_present=any(v > EPS for k, v in free.items() if k != "O"),
                 volatile_fraction_moles=fsum(state.minerals.get(k, 0) for k in ("Cc", "Nc", "Fl", "Py", "Hl", "Th")))
    if flags["free_components_present"]:
        flags["warnings"].append("Unused components are reported separately; inspect free_components_wtpercent.")
    if state.normative_fluorine:
        flags["warnings"].append("Pruseth normative fluorapatite includes a signed fluorine correction, not measured fluorine.")
    if strict and not complete:
        raise GeoNormPyError("allocation_incomplete", "CIPW allocation is incomplete: unresolved silica deficit or no normative phases.", details={"residual_silica_deficit_moles": deficit})
    result = {"minerals_moles": state.minerals, "minerals_wtpercent": minerals, "flags": flags,
              "mass_balance_error": error, "total_mass_sum": total,
              "free_components_wtpercent": free,
              "mass_balance": {"mineral_sum": total, "free_component_sum": fsum(free.values()),
                               "accounted_sum": accounted, "error": error,
                               "inventory_sum_including_silica_deficit": accounted - deficit * MASSES["SiO2"],
                               "normative_fluorine_moles": state.normative_fluorine,
                               "oxygen_released_moles": state.free_oxygen,
                               "basis": "100 wt% post-iron input; no mineral renormalization"},
              "adjusted_input_wtpercent": adjusted,
              "component_pools": pools, "effective_molar_masses": weights}
    if debug:
        result["residual_oxides_moles"] = {k: v for k, v in state.oxides.items() if abs(v) > EPS}
        result["residual_oxides_wt"] = {k: v * weights[k] for k, v in result["residual_oxides_moles"].items()}
    return result
