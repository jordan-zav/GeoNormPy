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

import argparse
import contextlib
import io
import json
import sys
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
from .workflow import process_batch, load_workflow_config
from .errors import GeoNormPyError, error_details
from . import __version__


class GeoNormArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise GeoNormPyError('invalid_arguments', message + ' Use --help for usage.')


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
    frame = pd.read_csv(output_path)
    errors = []
    for index, row in frame.iterrows():
        if pd.notna(row.get('calc_error')):
            errors.append({'row': int(index), 'sample_id': str(row.get('Sample_ID', index)),
                'error': json.loads(row['error_json'])})
    args.result = {'output': str(output_path), 'samples': len(frame), 'failed': len(errors), 'errors': errors}
    print(f"Batch run completed. Output file: {output_path}")
    if errors:
        print(f"{len(errors)} sample(s) failed. Inspect calc_error, error_code and error_json in the output.")
        if not getattr(args, 'json', False):
            for failure in errors:
                detail = failure['error']
                print(f"Sample {failure['sample_id']} (row {failure['row']}): Error [{detail['code']}]: {detail['message']}", file=sys.stderr)
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = GeoNormArgumentParser(
        prog="geonormpy",
        description=(
            "GeoNormPy: CIPW normative mineralogy tools with schema help, "
            "input templates, workflow configs, validation, and batch execution."
        ),
    )
    parser.add_argument('--json', action='store_true', help='Emit one JSON response on stdout, including errors.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
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
    for command in (schema_parser, template_parser, config_parser, validate_parser, run_parser):
        command.add_argument('--json', action='store_true', default=argparse.SUPPRESS,
            help='Emit one JSON response on stdout, including errors.')

    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_mode = '--json' in arguments
    try:
        if json_mode and any(flag in arguments for flag in ('--help', '-h', '--version')):
            result = {'version': __version__} if '--version' in arguments else {'help': build_parser().format_help()}
            print(json.dumps({'ok': True, 'result': result, 'error': None}, allow_nan=False))
            return 0
        args = build_parser().parse_args(arguments)
        if not json_mode:
            return args.func(args)
        if args.command == 'schema':
            args.format = 'json'
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            status = args.func(args)
        result = getattr(args, 'result', None)
        if args.command == 'schema':
            result = json.loads(buffer.getvalue())
        elif result is None:
            result = {'message': buffer.getvalue().strip()}
        error = None if status == 0 else GeoNormPyError(
            'batch_sample_errors' if args.command == 'run' else 'validation_failed',
            'Some samples failed; inspect result.errors.' if args.command == 'run' else 'Input validation failed.').to_dict()
        print(json.dumps({'ok': status == 0, 'result': result, 'error': error}, allow_nan=False))
        return status
    except Exception as error:
        detail = error_details(error)
        if json_mode:
            print(json.dumps({'ok': False, 'result': None, 'error': detail}, allow_nan=False))
        else:
            print(f"Error [{detail['code']}]: {detail['message']}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
