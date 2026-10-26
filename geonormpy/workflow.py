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

from __future__ import annotations

from pathlib import Path
import os
import tempfile

import pandas as pd
import yaml

from .norms.batch import calculate_cipw_dataframe
from .schema import DEFAULT_CONFIG_PATH, validate_workflow_columns, WORKFLOW_STEPS
from .schema import OXIDE_COLUMNS
from .errors import GeoNormPyError

def load_workflow_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    try:
        with Path(config_path).open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        raise GeoNormPyError('invalid_configuration', f'Invalid YAML configuration: {error}', field='config') from error


def process_batch(config_path: str | Path = DEFAULT_CONFIG_PATH, *, calculation_overrides=None):
    config = load_workflow_config(config_path)
    if not isinstance(config, dict):
        raise GeoNormPyError('invalid_configuration', "Workflow configuration must be a mapping", field='config')
    for section in ('input', 'output', 'calculation', 'workflow'):
        if not isinstance(config.get(section, {}), dict):
            raise GeoNormPyError('invalid_configuration', f'{section} must be a mapping.', field=section)
    for section in ('input', 'output'):
        if not isinstance(config.get(section, {}).get('file'), str) or not config[section]['file'].strip():
            raise GeoNormPyError('invalid_configuration', f'Specify {section}.file in the configuration.', field=f'{section}.file')
    if config.get("calculation", {}).get("method", "cipw") != "cipw":
        raise GeoNormPyError('invalid_configuration', "Unsupported calculation method; use cipw.", field='calculation.method')
    calculation = dict(config.get("calculation", {}))
    allowed = {"method", "profile", "iron_policy", "fe3_fraction", "strict", "mass_tol", "carbonate_mode"}
    if calculation_overrides is not None:
        if not isinstance(calculation_overrides, dict):
            raise GeoNormPyError("invalid_configuration", "Calculation overrides must be a mapping.", field="calculation")
        calculation.update(calculation_overrides)
    unknown = set(calculation) - allowed
    if unknown:
        raise GeoNormPyError("invalid_configuration", f"Unknown calculation options: {sorted(unknown)}.", field="calculation")
    if calculation.get("method", "cipw") != "cipw":
        raise GeoNormPyError("invalid_configuration", "Unsupported calculation method; use cipw.", field="calculation.method")
    from .norms.profiles import validate_options
    validate_options(calculation.get("profile", "extended_cipw_v3"),
                     calculation.get("iron_policy", "auto"), calculation.get("carbonate_mode", "calcite"))
    if config.get("workflow", {}).get("steps", WORKFLOW_STEPS) != WORKFLOW_STEPS:
        raise GeoNormPyError('invalid_configuration', "Unsupported workflow steps or order", field='workflow.steps')

    input_file = Path(config["input"]["file"])
    output_file = Path(config["output"]["file"])

    try:
        df = pd.read_csv(input_file)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise GeoNormPyError('invalid_input_file', f'Cannot parse input CSV: {error}', field='input.file') from error
    if df.empty:
        raise GeoNormPyError('empty_input_file', 'The input CSV contains no samples.', field='input.file')
    validation = validate_workflow_columns(df.columns)

    id_cols = config["input"].get("id_columns", [])
    oxide_cols = config["input"].get("oxide_columns", OXIDE_COLUMNS)
    if not isinstance(id_cols, list) or not isinstance(oxide_cols, list) or not all(isinstance(col, str) for col in id_cols + oxide_cols):
        raise GeoNormPyError('invalid_configuration', 'id_columns and oxide_columns must be lists of column names.', field='input')
    use_cols = [col for col in oxide_cols if col in df.columns and col in OXIDE_COLUMNS]

    if not use_cols:
        raise GeoNormPyError('missing_oxide_columns', "No configured oxide columns were found in the input file.", field='input.oxide_columns')

    if validation["unknown_columns"]:
        print(
            "Warning: unknown columns found in input file: "
            + ", ".join(validation["unknown_columns"])
        )

    if validation["missing_recommended_columns"]:
        print(
            "Warning: recommended columns missing from input file: "
            + ", ".join(validation["missing_recommended_columns"])
        )

    results_df = calculate_cipw_dataframe(
        df[use_cols],
        fe3_fraction=calculation.get("fe3_fraction", 0.15),
        strict=calculation.get("strict", False),
        profile=calculation.get("profile", "extended_cipw_v3"),
        iron_policy=calculation.get("iron_policy", "auto"),
        carbonate_mode=calculation.get("carbonate_mode", "calcite"),
        mass_tol=calculation.get("mass_tol", 1e-6),
    )

    insert_index = 0
    for column in id_cols:
        if column in df.columns:
            results_df.insert(insert_index, column, df[column])
            insert_index += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_file.parent, prefix=f'.{output_file.name}.', suffix='.tmp', delete=False) as temporary:
            temporary_path = Path(temporary.name)
        results_df.to_csv(temporary_path, index=False)
        os.replace(temporary_path, output_file)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(
        "Processing complete. "
        f"Used {len(use_cols)} oxide columns and generated {len(results_df.columns)} "
        f"columns in: {output_file}"
    )


    return output_file
