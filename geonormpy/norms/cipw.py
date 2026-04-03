"""
GeoNormPy - Core Logic
Developed by Jordan Zavaleta (UNI, Peru)
Part of the igneous rock classification research project.

CIPW Normative Mineralogy

Scientifically explicit, numerically robust implementation
of the classical CIPW norm.
"""

from __future__ import annotations

from typing import Dict

from ..core.chemistry import handle_iron, wtpercent_to_moles
from ..core.constants import MOLAR_MASS
from ..core.minerals import MINERAL_MOLAR_MASS

EPS = 1e-12

TRACKED_OXIDES = [
    "SiO2",
    "Al2O3",
    "FeO",
    "Fe2O3",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "TiO2",
    "P2O5",
    "ZrO2",
    "Cr2O3",
    "MnO",
    "CO2",
    "S",
    "F",
    "Cl",
    "SO3",
]


def normalize_anhydrous(oxides: Dict[str, float]) -> Dict[str, float]:
    clean = {k: v for k, v in oxides.items() if v is not None}
    total = sum(clean.values())

    if total <= 0:
        raise ValueError("Oxide sum must be > 0")

    return {k: 100.0 * v / total for k, v in clean.items()}


class ChemicalState:
    def __init__(self, oxides: Dict[str, float]):
        self.oxides = dict(oxides)
        self.minerals: Dict[str, float] = {}

    def get(self, key: str) -> float:
        return self.oxides.get(key, 0.0)

    def consume(self, **kwargs):
        for key, value in kwargs.items():
            self.oxides[key] = self.get(key) - value

            if key != "SiO2" and self.oxides[key] < -EPS:
                raise ValueError(f"Negative oxide {key}: {self.oxides[key]}")

            if abs(self.oxides[key]) < EPS:
                self.oxides[key] = 0.0

    def produce(self, mineral: str, amount: float):
        if amount > EPS:
            self.minerals[mineral] = self.minerals.get(mineral, 0.0) + amount

    def clip(self):
        for key, value in self.oxides.items():
            if abs(value) < EPS:
                self.oxides[key] = 0.0
            elif key != "SiO2" and value < 0:
                raise ValueError(f"Negative oxide {key}: {value}")

    def clean_minerals(self):
        self.minerals = {
            key: value
            for key, value in self.minerals.items()
            if value > EPS
        }


def form_volatiles(state: ChemicalState, flags: dict):
    removed = 0.0

    co2 = state.get("CO2")
    if co2 > 0:
        cc = min(co2, state.get("CaO"))
        state.consume(CO2=cc, CaO=cc)
        state.produce("Cc", cc)
        removed += cc

    fluorine = state.get("F")
    if fluorine > 0:
        fl = min(fluorine / 2.0, state.get("CaO"))
        state.consume(F=fl * 2.0, CaO=fl)
        state.produce("Fl", fl)
        removed += fl

    sulfur = state.get("S")
    if sulfur > 0:
        py = min(sulfur / 2.0, state.get("FeO"))
        state.consume(S=py * 2.0, FeO=py)
        state.produce("Py", py)
        removed += py

    chlorine = state.get("Cl")
    if chlorine > 0:
        hl = min(chlorine, state.get("Na2O") * 2.0)
        state.consume(Cl=hl, Na2O=hl / 2.0)
        state.produce("Hl", hl)
        removed += hl

    so3 = state.get("SO3")
    if so3 > 0:
        th = min(so3, state.get("Na2O"))
        state.consume(SO3=th, Na2O=th)
        state.produce("Th", th)
        removed += th

    flags["volatile_fraction_moles"] = removed


def form_accessories(state: ChemicalState):
    z = state.get("ZrO2")
    if z > 0:
        state.consume(ZrO2=z, SiO2=z)
        state.produce("Z", z)

    ap = min(state.get("P2O5"), state.get("CaO") / (10.0 / 3.0))
    if ap > 0:
        state.consume(P2O5=ap, CaO=ap * (10.0 / 3.0))
        state.produce("Ap", ap)

    cm = min(state.get("Cr2O3"), state.get("FeO"))
    if cm > 0:
        state.consume(Cr2O3=cm, FeO=cm)
        state.produce("Cm", cm)

    ilm = min(state.get("TiO2"), state.get("FeO"))
    if ilm > 0:
        state.consume(TiO2=ilm, FeO=ilm)
        state.produce("Ilm", ilm)

    tn = min(state.get("TiO2"), state.get("CaO"), state.get("SiO2"))
    if tn > 0:
        state.consume(TiO2=tn, CaO=tn, SiO2=tn)
        state.produce("Tn", tn)

    ru = state.get("TiO2")
    if ru > 0:
        state.consume(TiO2=ru)
        state.produce("Ru", ru)


def form_iron_oxides(state: ChemicalState):
    mt = min(state.get("Fe2O3"), state.get("FeO"))
    if mt > 0:
        state.consume(Fe2O3=mt, FeO=mt)
        state.produce("Mt", mt)

    hm = state.get("Fe2O3")
    if hm > 0:
        state.consume(Fe2O3=hm)
        state.produce("Hm", hm)


def form_feldspars_and_residual_alkalis(state: ChemicalState):
    ort = min(state.get("K2O"), state.get("Al2O3"))
    if ort > 0:
        state.consume(K2O=ort, Al2O3=ort, SiO2=6.0 * ort)
        state.produce("Or", 2.0 * ort)

    ab = min(state.get("Na2O"), state.get("Al2O3"))
    if ab > 0:
        state.consume(Na2O=ab, Al2O3=ab, SiO2=6.0 * ab)
        state.produce("Ab", 2.0 * ab)

    an = min(state.get("CaO"), state.get("Al2O3"))
    if an > 0:
        state.consume(CaO=an, Al2O3=an, SiO2=2.0 * an)
        state.produce("An", an)

    cor = state.get("Al2O3")
    if cor > 0:
        state.consume(Al2O3=cor)
        state.produce("Cor", cor)

    ac = min(state.get("Na2O"), state.get("Fe2O3"))
    if ac > 0:
        state.consume(Na2O=ac, Fe2O3=ac, SiO2=4.0 * ac)
        state.produce("Ac", 2.0 * ac)

    na_residual = state.get("Na2O")
    if na_residual > 0:
        state.consume(Na2O=na_residual, SiO2=na_residual)
        state.produce("ns", na_residual)

    k_residual = state.get("K2O")
    if k_residual > 0:
        state.consume(K2O=k_residual, SiO2=k_residual)
        state.produce("ks", k_residual)


def form_mafic_silicates(state: ChemicalState):
    mg_available = state.get("MgO")
    fe_available = state.get("FeO")
    mgfe = mg_available + fe_available

    if mgfe > 0:
        cpx_total = min(state.get("CaO"), mgfe)
        mg_ratio = mg_available / (mgfe + EPS)
        fe_ratio = fe_available / (mgfe + EPS)

        di = cpx_total * mg_ratio
        hd = cpx_total * fe_ratio

        if di > 0 or hd > 0:
            state.consume(
                CaO=cpx_total,
                MgO=di,
                FeO=hd,
                SiO2=2.0 * cpx_total,
            )
            state.produce("Di", di)
            state.produce("Hd", hd)

    mg_left = state.get("MgO")
    fe_left = state.get("FeO")
    hy = mg_left + fe_left

    if hy > 0:
        en = mg_left
        fs = fe_left
        state.consume(MgO=en, FeO=fs, SiO2=hy)
        state.produce("En", en)
        state.produce("Fs", fs)

    ca_left = state.get("CaO")
    if ca_left > 0 and (state.get("MgO") + state.get("FeO")) < EPS:
        state.consume(CaO=ca_left, SiO2=ca_left)
        state.produce("Wo", ca_left)


def silica_desaturation(state: ChemicalState, flags: dict):
    deficit = -state.get("SiO2")

    if abs(deficit) < EPS:
        flags["silica_saturation"] = "saturated"
        state.oxides["SiO2"] = 0.0
        return

    if deficit < 0:
        quartz = -deficit
        state.produce("Q", quartz)
        flags["silica_saturation"] = "oversaturated"
        state.oxides["SiO2"] = 0.0
        return

    flags["silica_saturation"] = "undersaturated"

    hy = state.minerals.get("En", 0.0) + state.minerals.get("Fs", 0.0)
    if hy > 0:
        reducible_hy = min(hy, 2.0 * deficit)
        en_share = state.minerals.get("En", 0.0) / hy
        fs_share = state.minerals.get("Fs", 0.0) / hy

        en_reduced = reducible_hy * en_share
        fs_reduced = reducible_hy * fs_share

        state.minerals["En"] = max(0.0, state.minerals.get("En", 0.0) - en_reduced)
        state.minerals["Fs"] = max(0.0, state.minerals.get("Fs", 0.0) - fs_reduced)
        state.produce("Fo", en_reduced / 2.0)
        state.produce("Fa", fs_reduced / 2.0)

        deficit -= reducible_hy / 2.0

    if deficit > 0:
        ab = state.minerals.get("Ab", 0.0)
        reducible_ab = min(ab, deficit / 2.0)
        if reducible_ab > 0:
            state.minerals["Ab"] = max(0.0, ab - reducible_ab)
            state.produce("Ne", reducible_ab)
            deficit -= 2.0 * reducible_ab

    if deficit > 0:
        or_amount = state.minerals.get("Or", 0.0)
        reducible_or = min(or_amount, deficit)
        if reducible_or > 0:
            state.minerals["Or"] = max(0.0, or_amount - reducible_or)
            state.produce("Le", reducible_or)
            deficit -= reducible_or

    if deficit > 0:
        le_amount = state.minerals.get("Le", 0.0)
        reducible_le = min(le_amount, deficit)
        if reducible_le > 0:
            state.minerals["Le"] = max(0.0, le_amount - reducible_le)
            state.produce("Kp", reducible_le)
            deficit -= reducible_le

    flags["residual_silica_deficit_moles"] = max(0.0, deficit)
    state.oxides["SiO2"] = 0.0
    state.clean_minerals()


def cipw(
    oxides: Dict[str, float],
    fe3_fraction: float = 0.15,
    strict: bool = False,
    mass_tol: float = 1e-6,
    debug: bool = False,
):

    ox = normalize_anhydrous(oxides)
    ox, iron_flags = handle_iron(ox, fe3_fraction=fe3_fraction, strict=strict)
    ox = normalize_anhydrous(ox)

    flags = {
        "volatile_fraction_moles": 0.0,
        "silica_saturation": None,
        "alumina_state": None,
        "norm_model": "extended_cipw_v2",
        "mass_balance_warning": False,
        "residual_silica_deficit_moles": 0.0,
    }
    flags.update(iron_flags)

    moles = wtpercent_to_moles(ox)
    for oxide in TRACKED_OXIDES:
        moles.setdefault(oxide, 0.0)

    state = ChemicalState(moles)

    al_initial = state.get("Al2O3")
    na_initial = state.get("Na2O")
    k_initial = state.get("K2O")
    ca_initial = state.get("CaO")

    a_cnk = al_initial / (ca_initial + na_initial + k_initial + EPS)

    if (na_initial + k_initial) > al_initial:
        flags["alumina_state"] = "peralkaline"
    elif a_cnk > 1.0:
        flags["alumina_state"] = "peraluminous"
    else:
        flags["alumina_state"] = "metaluminous"

    form_volatiles(state, flags)
    state.clip()

    form_accessories(state)
    state.clip()

    form_feldspars_and_residual_alkalis(state)
    state.clip()

    form_iron_oxides(state)
    state.clip()

    form_mafic_silicates(state)
    state.clip()

    silica_desaturation(state, flags)
    state.clip()
    state.clean_minerals()

    wt = {}
    for mineral, moles_value in state.minerals.items():
        if mineral in MINERAL_MOLAR_MASS and moles_value > 0:
            wt[mineral] = moles_value * MINERAL_MOLAR_MASS[mineral]

    total_input_mass = sum(ox.values())
    wt_pct = {mineral: 100.0 * mass / total_input_mass for mineral, mass in wt.items()}

    actual_sum = sum(wt_pct.values())
    mass_err = abs(100.0 - actual_sum)
    flags["mass_balance_warning"] = mass_err > mass_tol

    result = {
        "minerals_moles": state.minerals,
        "minerals_wtpercent": wt_pct,
        "flags": flags,
        "mass_balance_error": mass_err,
        "total_mass_sum": actual_sum,
    }

    if debug:
        residual_oxides_moles = {
            oxide: value
            for oxide, value in state.oxides.items()
            if abs(value) > EPS
        }
        residual_oxides_wt = {
            oxide: value * MOLAR_MASS[oxide]
            for oxide, value in residual_oxides_moles.items()
            if oxide in MOLAR_MASS
        }

        result["residual_oxides_moles"] = residual_oxides_moles
        result["residual_oxides_wt"] = residual_oxides_wt

    return result