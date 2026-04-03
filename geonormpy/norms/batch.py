import pandas as pd
from geonormpy.norms.cipw import cipw
from geonormpy.schema import DIAGNOSTIC_COLUMNS, MINERAL_COLUMNS


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
            if isinstance(value, (int, float)):
                oxides[key] = float(value)

        try:
            res = cipw(oxides, fe3_fraction=fe3_fraction, strict=strict)

            row_result = {**res["minerals_wtpercent"]}
            row_result["silica_saturation"] = res["flags"].get("silica_saturation")
            row_result["alumina_state"] = res["flags"].get("alumina_state")
            row_result["mass_balance_error"] = res["mass_balance_error"]
            row_result["interpretive_flag"] = build_interpretive_flag(res)
            row_result["calc_error"] = None

        except Exception as e:
            row_result = {
                "silica_saturation": None,
                "alumina_state": None,
                "mass_balance_error": None,
                "interpretive_flag": "calculation_failed",
                "calc_error": str(e),
            }

        records.append(row_result)

    results_df = pd.DataFrame(records, index=df.index)

    non_mineral_cols = DIAGNOSTIC_COLUMNS

    mineral_cols = [col for col in results_df.columns if col not in non_mineral_cols]
    results_df[mineral_cols] = results_df[mineral_cols].fillna(0.0)

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
