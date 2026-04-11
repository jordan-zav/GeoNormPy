"""
GeoNormPy - Core Logic
Developed by Jordan Zavaleta (UNI, Peru)
Part of the igneous rock classification research project.

Geochemical preprocessing utilities: normalization, iron speciation, and
oxide-to-mole conversion for normative calculations.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Tuple

from .constants import FE3_FRACTION_DEFAULT, MOLAR_MASS


def normalize_oxides(oxides: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize oxide wt% to 100%.

    Ignores oxides with None values.
    """
    clean = {k: v for k, v in oxides.items() if v is not None}
    total = sum(clean.values())

    if total <= 0:
        raise ValueError("Total oxide sum must be > 0")

    return {k: 100.0 * v / total for k, v in clean.items()}


def handle_iron(
    oxides: Dict[str, float],
    fe3_fraction: float = FE3_FRACTION_DEFAULT,
    strict: bool = False,
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Handle iron speciation following Le Maitre (2002).

    Supported cases:
    - FeO + Fe2O3 measured
    - partial iron reported
    - total iron as FeOT
    - missing iron

    Notes
    -----
    - If FeOT is provided alone, it is split into FeO and Fe2O3 using a fixed
      Fe3+ / Fe_total ratio.
    - MnO is converted to FeO-equivalent on a molar basis, which is the usual
      normative convention.
    """
    if not (0.0 <= fe3_fraction <= 1.0):
        raise ValueError("fe3_fraction must be between 0 and 1")

    ox = deepcopy(oxides)
    flags = {
        "iron_mode": None,
        "iron_warning": False,
        "warnings": [],
    }

    has_feo = "FeO" in ox
    has_fe2o3 = "Fe2O3" in ox
    has_feot = "FeOT" in ox

    if has_feo and has_fe2o3 and not has_feot:
        flags["iron_mode"] = "measured"

    elif (has_feo ^ has_fe2o3) and not has_feot:
        ox.setdefault("FeO", 0.0)
        ox.setdefault("Fe2O3", 0.0)
        flags["iron_mode"] = "partial_assumed"
        flags["iron_warning"] = True
        flags["warnings"].append(
            "Partial iron speciation assumed (missing FeO or Fe2O3)."
        )

    elif has_feot and not has_feo and not has_fe2o3:
        fe_total = ox.pop("FeOT")
        ox["Fe2O3"] = fe_total * fe3_fraction * 1.11134
        ox["FeO"] = fe_total * (1.0 - fe3_fraction)
        flags["iron_mode"] = "estimated_from_FeOT"
        flags["iron_warning"] = True
        flags["warnings"].append(
            f"Iron speciation estimated from FeOT using fixed Fe3+/Fe ratio ({fe3_fraction:.2f})."
        )

    elif has_feot and (has_feo or has_fe2o3):
        msg = "Inconsistent iron input: FeOT with FeO/Fe2O3."
        flags["iron_mode"] = "inconsistent_input"
        flags["iron_warning"] = True
        flags["warnings"].append(msg)
        if strict:
            raise ValueError(msg)
        ox.pop("FeOT", None)

    else:
        ox["FeO"] = 0.0
        ox["Fe2O3"] = 0.0
        flags["iron_mode"] = "missing"
        flags["iron_warning"] = True
        flags["warnings"].append("No iron reported.")

    if "MnO" in ox:
        mn_wt = ox.pop("MnO")
        feo_equivalent_wt = mn_wt * (MOLAR_MASS["FeO"] / MOLAR_MASS["MnO"])
        ox["FeO"] = ox.get("FeO", 0.0) + feo_equivalent_wt
        flags["warnings"].append("MnO converted to FeO-equivalent on a molar basis.")
        if mn_wt > 0.5:
            flags["iron_warning"] = True
            flags["warnings"].append(
                f"High MnO ({mn_wt:.2f} wt%) may bias FeO-equivalent allocation."
            )

    return ox, flags


def wtpercent_to_moles(oxides: Dict[str, float]) -> Dict[str, float]:
    """
    Convert oxide wt% to moles.

    Only oxides with defined molar masses are converted.
    """
    moles = {}
    for oxide, wt in oxides.items():
        if oxide in MOLAR_MASS:
            if wt < 0:
                raise ValueError(f"Negative wt% for oxide {oxide}")
            moles[oxide] = wt / MOLAR_MASS[oxide]
    return moles
