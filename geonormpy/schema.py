"""
Shared schema definitions for GeoNormPy inputs, workflow configuration,
and batch outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from .core.minerals import MINERALS

DEFAULT_CONFIG_PATH = Path("config/workflow.yaml")

ID_COLUMNS: List[str] = ["Sample_ID", "Notes"]

OXIDE_COLUMNS: List[str] = [
    "SiO2",
    "TiO2",
    "Al2O3",
    "Fe2O3",
    "FeO",
    "FeOT",
    "MnO",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
    "ZrO2",
    "Cr2O3",
    "CO2",
    "S",
    "F",
    "Cl",
    "SO3",
]

DIAGNOSTIC_COLUMNS: List[str] = [
    "silica_saturation",
    "alumina_state",
    "mass_balance_error",
    "interpretive_flag",
    "calc_error",
]

MINERAL_COLUMNS: List[str] = list(MINERALS.keys())

WORKFLOW_STEPS: List[str] = [
    "read_csv",
    "select_valid_columns",
    "run_cipw",
    "append_id_columns",
    "export_csv",
]


def expected_output_columns() -> List[str]:
    """Return the standard output column order for batch results."""
    return ID_COLUMNS + DIAGNOSTIC_COLUMNS + MINERAL_COLUMNS


def validate_workflow_columns(columns: Iterable[str]) -> Dict[str, List[str]]:
    """
    Validate input columns against the supported GeoNormPy schema.

    Returns a dictionary with recognized ID columns, recognized oxide columns,
    unknown columns, and missing recommended columns.
    """
    column_list = list(columns)
    recognized_ids = [column for column in ID_COLUMNS if column in column_list]
    recognized_oxides = [column for column in OXIDE_COLUMNS if column in column_list]

    known_columns = set(ID_COLUMNS) | set(OXIDE_COLUMNS)
    unknown_columns = [column for column in column_list if column not in known_columns]
    missing_recommended = [
        column for column in ["SiO2", "Al2O3", "Na2O", "K2O"] if column not in column_list
    ]

    return {
        "recognized_id_columns": recognized_ids,
        "recognized_oxide_columns": recognized_oxides,
        "unknown_columns": unknown_columns,
        "missing_recommended_columns": missing_recommended,
    }


def build_template_dataframe() -> pd.DataFrame:
    """Create an empty one-row input template with the standard columns."""
    ordered_columns = ID_COLUMNS + OXIDE_COLUMNS
    template = {column: [""] for column in ordered_columns}
    template["Sample_ID"] = ["Example-01"]
    template["Notes"] = ["Example whole-rock analysis"]
    return pd.DataFrame(template)

