# Copyright (c) 2026 Jordan Zavaleta
# This file is part of GeoNormPy.
# GeoNormPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
GeoNormPy - Core Logic
Developed by Jordan Zavaleta (UNI, Peru)
Part of the igneous rock classification research project.

Geochemical preprocessing utilities: normalization, iron speciation, and
oxide-to-mole conversion for normative calculations.
"""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite, fsum
from typing import Dict, Tuple

from numpy import bool_ as numpy_bool

from .constants import FE3_FRACTION_DEFAULT, MOLAR_MASS
from ..errors import GeoNormPyError


def clean_oxide_values(oxides: Mapping[str, float]) -> Dict[str, float]:
    """Validate canonical oxide inputs without treating metadata as chemistry."""
    if not isinstance(oxides, Mapping):
        raise GeoNormPyError('invalid_analysis', "Oxides must be a mapping of oxide names to measurements")
    clean = {}
    for key, value in oxides.items():
        if key not in MOLAR_MASS and key != "FeOT":
            raise GeoNormPyError('unsupported_oxide', f"Unsupported oxide: {key}. Pass only supported oxide columns, without IDs, trace ppm or LOI.", field=str(key))
        if value is None:
            continue
        if isinstance(value, (bool, numpy_bool)):
            raise GeoNormPyError('invalid_measurement', f"Invalid numeric measurement for {key}: boolean values are not measurements.", field=key)
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise GeoNormPyError('invalid_measurement', f"Invalid numeric measurement for {key}: enter a finite, nonnegative number.", field=key) from error
        if not isfinite(number) or number < 0:
            raise GeoNormPyError('invalid_measurement', f"Invalid numeric measurement for {key}: enter a finite, nonnegative number.", field=key)
        clean[key] = number
    return clean


def normalize_oxides(oxides: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize oxide wt% to 100%.

    Ignores oxides with None values.
    """
    clean = clean_oxide_values(oxides)
    largest = max(clean.values(), default=0.0)
    if largest <= 0:
        raise GeoNormPyError('empty_analysis', "Total oxide sum must be > 0. Supply measured oxide values.")
    scaled = {key: value / largest for key, value in clean.items()}
    total = fsum(scaled.values())
    return {key: 100.0 * value / total for key, value in scaled.items()}


def handle_iron(
    oxides: Dict[str, float],
    fe3_fraction: float = FE3_FRACTION_DEFAULT,
    strict: bool = False,
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Use measured iron or an explicitly assumed fixed ferric fraction.

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
    if isinstance(fe3_fraction, (bool, numpy_bool)) or not isinstance(fe3_fraction, (int, float)) or not (0.0 <= fe3_fraction <= 1.0):
        raise GeoNormPyError('invalid_option', "fe3_fraction must be a number between 0 and 1.", field='fe3_fraction')

    ox = clean_oxide_values(oxides)
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
        ox["Fe2O3"] = fe_total * fe3_fraction * MOLAR_MASS["Fe2O3"] / (2 * MOLAR_MASS["FeO"])
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
            raise GeoNormPyError('inconsistent_iron', msg + " Use total iron alone or an explicit FeO/Fe2O3 pair.", field='FeOT')
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
    for oxide, wt in clean_oxide_values(oxides).items():
        if oxide in MOLAR_MASS:
            if wt < 0:
                raise ValueError(f"Negative wt% for oxide {oxide}")
            moles[oxide] = wt / MOLAR_MASS[oxide]
    return moles
