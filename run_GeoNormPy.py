from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from geonormpy.norms.batch import calculate_cipw_dataframe


DEFAULT_CONFIG_PATH = Path("config/workflow.yaml")


def load_workflow_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def process_batch(config_path: str | Path = DEFAULT_CONFIG_PATH):
    config = load_workflow_config(config_path)

    input_file = Path(config["input"]["file"])
    output_file = Path(config["output"]["file"])

    df = pd.read_csv(input_file)

    id_cols = config["input"].get("id_columns", [])
    oxide_cols = config["input"].get("oxide_columns", [])
    use_cols = [col for col in oxide_cols if col in df.columns]

    if not use_cols:
        raise ValueError("No configured oxide columns were found in the input file.")

    calculation = config.get("calculation", {})
    results_df = calculate_cipw_dataframe(
        df[use_cols],
        fe3_fraction=calculation.get("fe3_fraction", 0.15),
        strict=calculation.get("strict", False),
    )

    insert_index = 0
    for column in id_cols:
        if column in df.columns:
            results_df.insert(insert_index, column, df[column])
            insert_index += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_file, index=False)

    print(
        "Processing complete. "
        f"Used {len(use_cols)} oxide columns and generated {len(results_df.columns)} "
        f"columns in: {output_file}"
    )


if __name__ == "__main__":
    process_batch()
