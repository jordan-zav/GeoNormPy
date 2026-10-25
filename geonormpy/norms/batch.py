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

import pandas as pd
import json
from geonormpy.norms.cipw import cipw_safe
from geonormpy.errors import GeoNormPyError, error_details
from geonormpy.schema import DIAGNOSTIC_COLUMNS, MINERAL_COLUMNS, OXIDE_COLUMNS


def build_interpretive_flag(res: dict) -> str:
    flags = res.get("flags", {})
    mass_err = res.get("mass_balance_error", 0.0)

    messages = []

    if mass_err > 0.10:
        messages.append("poor_mass_balance")
    elif mass_err > 0.01:
        messages.append("mass_balance_check")

    if flags.get("residual_silica_deficit_moles", 0.0) > 1e-12:
        messages.append("residual_silica_deficit")

    if flags.get("iron_warning"):
        messages.append("iron_speciation_assumed")

    if flags.get("alumina_state") == "peralkaline" and mass_err > 0.10:
        messages.append("peralkaline_sensitivity")

    if flags.get("volatile_fraction_moles", 0.0) > 0.05 and mass_err > 0.10:
        messages.append("volatile_rich_sample")

    if not messages:
        return "ok"

    return "; ".join(messages)


def calculate_cipw_dataframe(
    df: pd.DataFrame,
    fe3_fraction: float = 0.15,
    strict: bool = False
) -> pd.DataFrame:
    """
    Apply CIPW normative calculation to a Pandas DataFrame of geochemical samples.

    Args:
        df: DataFrame where columns are oxides (e.g. 'SiO2', 'Al2O3') and rows are samples.
        fe3_fraction: Default Fe3+ fraction relative to FeOT.
        strict: If True, raise errors on severe iron inconsistencies.

    Returns:
        pd.DataFrame: A new DataFrame with normative wt%, flags, diagnostics,
        and an interpretive text flag column.
    """
    records = []

    for index, row in df.iterrows():
        numeric_row = row.dropna()

        oxides = {}
        for key, value in numeric_row.items():
            if key in OXIDE_COLUMNS:
                oxides[key] = value

        try:
            outcome = cipw_safe(oxides, fe3_fraction=fe3_fraction, strict=strict)
            if not outcome['ok']:
                error = outcome['error']
                raise GeoNormPyError(error['code'], error['message'], field=error['field'], details=error['details'])
            res = outcome['result']

            row_result = {**res["minerals_wtpercent"]}
            row_result["silica_saturation"] = res["flags"].get("silica_saturation")
            row_result["alumina_state"] = res["flags"].get("alumina_state")
            row_result["mass_balance_error"] = res["mass_balance_error"]
            row_result["interpretive_flag"] = build_interpretive_flag(res)
            row_result["calc_error"] = None
            row_result["error_code"] = None
            row_result["error_json"] = None

        except Exception as e:
            row_result = {
                "silica_saturation": None,
                "alumina_state": None,
                "mass_balance_error": None,
                "interpretive_flag": "calculation_failed",
                "calc_error": str(e),
                "error_code": error_details(e)['code'],
                "error_json": json.dumps(error_details(e), allow_nan=False),
            }

        records.append(row_result)

    results_df = pd.DataFrame(records, index=df.index)
    for column in DIAGNOSTIC_COLUMNS + MINERAL_COLUMNS:
        if column not in results_df:
            results_df[column] = float("nan")

    non_mineral_cols = DIAGNOSTIC_COLUMNS

    mineral_cols = [col for col in results_df.columns if col not in non_mineral_cols]
    successful = results_df["calc_error"].isna() if "calc_error" in results_df else pd.Series(False, index=results_df.index)
    results_df.loc[successful, mineral_cols] = results_df.loc[successful, mineral_cols].fillna(0.0)

    ordered_present_diagnostics = [
        column for column in DIAGNOSTIC_COLUMNS if column in results_df.columns
    ]
    ordered_present_minerals = [
        mineral for mineral in MINERAL_COLUMNS if mineral in results_df.columns
    ]
    remaining_columns = [
        column
        for column in results_df.columns
        if column not in ordered_present_diagnostics + ordered_present_minerals
    ]
    results_df = results_df[
        remaining_columns + ordered_present_diagnostics + ordered_present_minerals
    ]

    return results_df
