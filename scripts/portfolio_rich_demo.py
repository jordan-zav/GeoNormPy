"""Present real CIPW checks and synthetic chemistry; Rich is a demo-only dependency."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.text import Text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from geonormpy.norms.cipw import cipw

SAMPLE = {"SiO2": 72.5, "Al2O3": 13.5, "FeOT": 2.5, "MgO": 0.5,
          "CaO": 1.8, "Na2O": 3.4, "K2O": 4.0, "TiO2": 0.3, "P2O5": 0.1}
TESTS = ["tests/test_cipw.py", "tests/test_profiles.py", "tests/test_cation_conservation.py"]
NAMES = {"Ap": "Apatite", "Ilm": "Ilmenite", "Or": "Orthoclase", "Ab": "Albite",
         "An": "Anorthite", "Cor": "Corundum", "Mt": "Magnetite", "En": "Enstatite",
         "Fs": "Ferrosilite", "Q": "Quartz"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, help="Save actual output as SVG and HTML, with test evidence.")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    console = Console(width=104, height=40, record=True, style="#dce5ef", highlight=False,
                      legacy_windows=False, safe_box=False, force_terminal=True, color_system="truecolor")
    console.print()
    console.print("  $ python scripts/portfolio_rich_demo.py", style="#7c91a9")
    console.print()
    console.print(Panel(
        "[bold #f1f5f9]GeoNormPy[/]  [#57dbc7]/  CIPW normative mineralogy[/]\n"
        "[#9aadc2]Reproducible calculations from whole-rock chemistry[/]",
        border_style="#305568", padding=(0, 2),
    ))
    console.print()
    with tempfile.TemporaryDirectory(prefix="geonormpy-demo-") as scratch:
        report = Path(scratch) / "tests.xml"
        with console.status("[bold #57dbc7]Running CIPW, profile and cation-conservation tests..."):
            command = [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=short",
                       f"--junitxml={report}", *TESTS]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if completed.returncode:
            console.print(completed.stdout, markup=False)
            console.print(completed.stderr, markup=False)
            return completed.returncode
        suites = ET.parse(report).getroot().iter("testsuite")
        counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
        elapsed = 0.0
        for suite in suites:
            for key in counts:
                counts[key] += int(suite.get(key, "0"))
            elapsed += float(suite.get("time", "0"))
        passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
        if args.export_dir:
            args.export_dir.mkdir(parents=True, exist_ok=True)
            (args.export_dir / "tests.xml").write_bytes(report.read_bytes())
            (args.export_dir / "pytest-output.txt").write_text(completed.stdout, encoding="utf-8")
    console.print(Panel(
        f"[bold #57dbc7]PASS  {passed} tests[/]  [#9aadc2]|  {elapsed:.2f}s  |  "
        "CIPW / profiles / cation conservation[/]",
        border_style="#244a48", padding=(0, 2),
    ))
    console.print()
    result = cipw(SAMPLE)
    inputs = Table(box=box.SIMPLE, width=47, padding=(0, 1), border_style="#305568")
    inputs.add_column("MAJOR OXIDES", style="#b2c3d5")
    inputs.add_column("wt%", justify="right", style="#f1f5f9")
    for oxide, value in SAMPLE.items():
        inputs.add_row(oxide, f"{value:.2f}")
    inputs.add_section()
    inputs.add_row("Synthetic granite", "Example")
    minerals = Table(box=box.SIMPLE, width=47, padding=(0, 1), border_style="#305568")
    minerals.add_column("NORMATIVE MINERALS", style="#b2c3d5")
    minerals.add_column("wt%", justify="right", style="#57dbc7")
    for mineral, value in sorted(result["minerals_wtpercent"].items(), key=lambda item: -item[1]):
        if value > 0:
            minerals.add_row(f"{NAMES.get(mineral, mineral)} ({mineral})", f"{value:.4f}")
    console.print(Columns([inputs, Text(" "), minerals], padding=(0, 1)))
    console.print()
    flags = result["flags"]
    console.print(Panel(
        f"[#9aadc2]SILICA[/]  [bold #e8bf75]{flags['silica_saturation']}[/]"
        f"     [#9aadc2]ALUMINA[/]  [bold #e8bf75]{flags['alumina_state']}[/]\n"
        f"[#9aadc2]MASS BALANCE ERROR[/]  [#dce5ef]{result['mass_balance_error']:.3e}[/]",
        title="[bold #9aadc2]CALCULATION DIAGNOSTICS[/]", title_align="left",
        border_style="#305568", padding=(0, 2),
    ))
    console.print("  [#7c91a9]Synthetic example. Normative mineralogy is calculated, not measured modal mineralogy.[/]")
    console.print()
    if args.export_dir:
        theme = TerminalTheme((13, 20, 34), (220, 229, 239),
                              [(13, 20, 34), (230, 110, 110), (87, 219, 199), (232, 191, 117),
                               (125, 165, 221), (187, 153, 220), (87, 219, 199), (220, 229, 239)])
        svg = console.export_svg(title="GeoNormPy / Python", theme=theme, clear=False)
        svg = re.sub(r"@font-face\s*\{.*?\}", "", svg, flags=re.S)
        svg = svg.replace("font-family: Fira Code, monospace;", "font-family: Consolas, monospace;")
        (args.export_dir / "cipw-terminal-v2.svg").write_text(svg, encoding="utf-8")
        (args.export_dir / "cipw-terminal-v2.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8"><title>GeoNormPy</title>'
            '<style>html,body{margin:0;background:#0d1422}svg{display:block;width:100%;height:auto}</style>'
            '</head><body>' + svg + '</body></html>', encoding="utf-8")
        (args.export_dir / "calculation.json").write_text(json.dumps({"input": SAMPLE, "result": result,
            "tests": counts, "elapsed_seconds": elapsed}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
