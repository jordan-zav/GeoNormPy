from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from .schema import (
    DEFAULT_CONFIG_PATH,
    DIAGNOSTIC_COLUMNS,
    ID_COLUMNS,
    MINERAL_COLUMNS,
    OXIDE_COLUMNS,
    WORKFLOW_STEPS,
    build_template_dataframe,
    expected_output_columns,
    validate_workflow_columns,
)


def load_workflow_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load a GeoNormPy workflow YAML configuration file."""
    with Path(config_path).open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def process_batch(config_path: str | Path = DEFAULT_CONFIG_PATH) -> Path:
    """Run the configured batch workflow and return the output CSV path."""
    from run_GeoNormPy import process_batch as _process_batch

    _process_batch(config_path)
    config = load_workflow_config(config_path)
    return Path(config["output"]["file"])


def format_schema_text() -> str:
    """Return a human-readable description of GeoNormPy inputs and outputs."""
    lines = [
        "GeoNormPy input schema",
        "",
        "Optional ID columns:",
        ", ".join(ID_COLUMNS),
        "",
        "Supported oxide columns:",
        ", ".join(OXIDE_COLUMNS),
        "",
        "Diagnostic output columns:",
        ", ".join(DIAGNOSTIC_COLUMNS),
        "",
        "Normative mineral output columns:",
        ", ".join(MINERAL_COLUMNS),
        "",
        "Default workflow steps:",
        ", ".join(WORKFLOW_STEPS),
    ]
    return "\n".join(lines)


def build_default_config() -> dict:
    """Return the default batch workflow configuration."""
    return {
        "input": {
            "file": "data/test_data.csv",
            "id_columns": ID_COLUMNS,
            "oxide_columns": OXIDE_COLUMNS,
        },
        "calculation": {
            "method": "cipw",
            "fe3_fraction": 0.15,
            "strict": False,
        },
        "workflow": {
            "steps": WORKFLOW_STEPS,
        },
        "output": {
            "file": "data/normative_results.csv",
        },
    }


def cmd_schema(args: argparse.Namespace) -> int:
    if args.format == "json":
        import json

        payload = {
            "id_columns": ID_COLUMNS,
            "oxide_columns": OXIDE_COLUMNS,
            "diagnostic_output_columns": DIAGNOSTIC_COLUMNS,
            "mineral_output_columns": MINERAL_COLUMNS,
            "expected_output_columns": expected_output_columns(),
            "workflow_steps": WORKFLOW_STEPS,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(format_schema_text())
    return 0


def cmd_make_template(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_template_dataframe().to_csv(output_path, index=False)
    print(f"Template CSV written to {output_path}")
    return 0


def cmd_make_config(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as config_file:
        yaml.safe_dump(build_default_config(), config_file, sort_keys=False)
    print(f"Workflow config written to {output_path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    df = pd.read_csv(input_path)
    validation = validate_workflow_columns(df.columns)

    print(f"Input file: {input_path}")
    print(f"Recognized ID columns: {', '.join(validation['recognized_id_columns']) or 'None'}")
    print(
        "Recognized oxide columns: "
        f"{', '.join(validation['recognized_oxide_columns']) or 'None'}"
    )
    print(f"Unknown columns: {', '.join(validation['unknown_columns']) or 'None'}")
    print(
        "Missing recommended columns: "
        f"{', '.join(validation['missing_recommended_columns']) or 'None'}"
    )

    if not validation["recognized_oxide_columns"]:
        print("Validation failed: no supported oxide columns were found.")
        return 1

    print("Validation passed.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    output_path = process_batch(args.config)
    print(f"Batch run completed. Output file: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geonormpy",
        description=(
            "GeoNormPy: CIPW normative mineralogy tools with schema help, "
            "input templates, workflow configs, validation, and batch execution."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    schema_parser = subparsers.add_parser(
        "schema",
        help="Show supported input columns, workflow steps, and output columns.",
    )
    schema_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Choose a human-readable text view or JSON schema output.",
    )
    schema_parser.set_defaults(func=cmd_schema)

    template_parser = subparsers.add_parser(
        "make-template",
        help="Write an example CSV input template with supported columns.",
    )
    template_parser.add_argument(
        "--output",
        default="data/geonormpy_input_template.csv",
        help="Path where the example CSV template will be written.",
    )
    template_parser.set_defaults(func=cmd_make_template)

    config_parser = subparsers.add_parser(
        "make-config",
        help="Write an example workflow YAML configuration file.",
    )
    config_parser.add_argument(
        "--output",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path where the example workflow YAML will be written.",
    )
    config_parser.set_defaults(func=cmd_make_config)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an input CSV against the supported GeoNormPy columns.",
    )
    validate_parser.add_argument(
        "--input",
        required=True,
        help="Path to the input CSV file to validate.",
    )
    validate_parser.set_defaults(func=cmd_validate)

    run_parser = subparsers.add_parser(
        "run",
        help="Run the configured batch workflow from a YAML config file.",
    )
    run_parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the workflow YAML configuration file.",
    )
    run_parser.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
