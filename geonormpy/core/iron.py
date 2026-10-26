"""Explicit iron policies, independent of the normative allocation algorithm.

Le Maitre (1976) predicts a *mass* FeO/(FeO+Fe2O3) ratio. It must not be
mistaken for the ferric atom fraction used by the fixed policy.
"""

from math import fsum, isfinite
from numbers import Real

from numpy import bool_ as numpy_bool

from ..errors import GeoNormPyError

IRON_POLICIES = ("auto", "measured", "fixed", "le_maitre_volcanic", "le_maitre_plutonic")

def finite_fraction(value, field="fe3_fraction"):
    if isinstance(value, (bool, numpy_bool)) or not isinstance(value, Real) or not isfinite(value) or not 0 <= value <= 1:
        raise GeoNormPyError("invalid_option", f"{field} must be a finite number between 0 and 1.", field=field)
    return float(value)


def apply_iron_policy(chemistry, policy, fraction, masses, strict=False):
    """Resolve Fe only, preserving Mn and other measured chemical components."""
    fraction = finite_fraction(fraction)
    if not isinstance(policy, str) or policy not in IRON_POLICIES:
        raise GeoNormPyError("invalid_option", "Unknown iron policy.", field="iron_policy")
    ox = dict(chemistry)
    flags = {"iron_mode": None, "iron_warning": False, "warnings": [],
             "iron_policy_requested": policy, "iron_policy_applied": None, "iron_parameters": {}}
    pair = "FeO" in ox and "Fe2O3" in ox
    partial = ("FeO" in ox) != ("Fe2O3" in ox)
    totals = [key for key in ("FeOT", "Fe2O3T") if key in ox]
    if len(totals) > 1:
        raise GeoNormPyError("inconsistent_iron", "Use only one total iron representation.", field="FeOT")
    if totals and (pair or partial):
        if strict or policy != "auto":
            raise GeoNormPyError("inconsistent_iron", "Use one iron total or an FeO/Fe2O3 pair, not both.", field="FeOT")
        flags["warnings"].append("Inconsistent total and speciated iron: explicit FeO/Fe2O3 retained.")
        flags["iron_warning"] = True
        ox.pop("FeOT", None)
        ox.pop("Fe2O3T", None)
        totals = []

    if policy == "measured":
        if not pair or totals:
            raise GeoNormPyError("missing_iron_speciation", "The measured policy requires explicit FeO and Fe2O3, including measured zeros.", field="iron_policy")
        flags.update(iron_mode="measured", iron_policy_applied="measured")
        return ox, flags

    if policy == "auto" and not totals:
        ox.setdefault("FeO", 0.0)
        ox.setdefault("Fe2O3", 0.0)
        flags["iron_mode"] = "measured" if pair else "partial_assumed" if partial else "missing"
        flags["iron_policy_applied"] = flags["iron_mode"]
        if not pair:
            flags["iron_warning"] = True
            flags["warnings"].append("Partial iron assumed zero." if partial else "No iron reported.")
        return ox, flags

    total_atoms = ox.get("FeO", 0.0) / masses["FeO"] + 2 * ox.get("Fe2O3", 0.0) / masses["Fe2O3"]
    if totals:
        key = totals[0]
        total_atoms = ox[key] / masses["FeO"] if key == "FeOT" else 2 * ox[key] / masses["Fe2O3"]
    for key in ("FeOT", "Fe2O3T", "FeO", "Fe2O3"):
        ox.pop(key, None)

    ferric = fraction
    applied = "fixed" if policy == "auto" else policy
    parameters = {"fe3_fraction": fraction}
    if policy.startswith("le_maitre_"):
        missing = [key for key in ("SiO2", "Na2O", "K2O") if key not in chemistry]
        if missing:
            raise GeoNormPyError("missing_iron_inputs", f"Le Maitre requires explicit wt% for {', '.join(missing)}.", field="iron_policy")
        # chemistry is already normalized on an anhydrous basis by the caller.
        silica = chemistry["SiO2"]
        alkalis = chemistry["Na2O"] + chemistry["K2O"]
        intercept, si_slope, alk_slope = (.93, .0042, .022) if policy.endswith("volcanic") else (.88, .0016, .027)
        mass_ratio = min(1.0, max(0.0, intercept - si_slope * silica - alk_slope * alkalis))
        ferrous_atoms = mass_ratio / masses["FeO"]
        ferric_atoms = 2 * (1 - mass_ratio) / masses["Fe2O3"]
        ferric = ferric_atoms / fsum((ferrous_atoms, ferric_atoms))
        parameters = {"rock_type": "volcanic" if policy.endswith("volcanic") else "plutonic",
                      "feo_mass_fraction": mass_ratio, "fe3_fraction": ferric,
                      "reference": "Le Maitre (1976), doi:10.1007/BF00399603"}
    ox["FeO"] = total_atoms * (1 - ferric) * masses["FeO"]
    ox["Fe2O3"] = total_atoms * ferric * masses["Fe2O3"] / 2
    flags.update(iron_mode="estimated_from_total" if totals else "repartitioned",
                 iron_warning=True, iron_policy_applied=applied, iron_parameters=parameters)
    flags["warnings"].append(f"Iron partition uses explicit policy {applied}; it is a calculation assumption.")
    return ox, flags
