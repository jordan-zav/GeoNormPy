"""Reproducible numerical and cross-implementation CIPW benchmarks.

All outputs require an explicit destination outside the source dataset. This
script does not train models or replace normative columns in an input table.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import random
import subprocess
import sys
import time
import types
import warnings
from collections import Counter
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from geonormpy.core.chemistry import handle_iron, normalize_oxides
from geonormpy.core.constants import MOLAR_MASS as MASS
from geonormpy.norms.cipw import cipw

# Formula-mole oxide equivalents independently stated for conservation checks.
# Halide/sulfide equivalents include displaced oxygen on the oxide basis;
# this inventory check is distinct from actual gravimetric oxygen closure.
EQUIVALENTS = {
    "Q": {"SiO2": 1}, "Cor": {"Al2O3": 1},
    "Or": {"K2O": .5, "Al2O3": .5, "SiO2": 3},
    "Ab": {"Na2O": .5, "Al2O3": .5, "SiO2": 3},
    "An": {"CaO": 1, "Al2O3": 1, "SiO2": 2},
    "Ne": {"Na2O": .5, "Al2O3": .5, "SiO2": 1},
    "Le": {"K2O": .5, "Al2O3": .5, "SiO2": 2},
    "Kp": {"K2O": .5, "Al2O3": .5, "SiO2": 1},
    "Ac": {"Na2O": .5, "Fe2O3": .5, "SiO2": 2},
    "Di": {"CaO": 1, "MgO": 1, "SiO2": 2},
    "Hd": {"CaO": 1, "FeO": 1, "SiO2": 2},
    "Wo": {"CaO": 1, "SiO2": 1}, "Cs": {"CaO": 2, "SiO2": 1},
    "En": {"MgO": 1, "SiO2": 1}, "Fs": {"FeO": 1, "SiO2": 1},
    "Fo": {"MgO": 2, "SiO2": 1}, "Fa": {"FeO": 2, "SiO2": 1},
    "Mt": {"FeO": 1, "Fe2O3": 1}, "Hm": {"Fe2O3": 1},
    "Ilm": {"FeO": 1, "TiO2": 1}, "Ru": {"TiO2": 1},
    "Tn": {"CaO": 1, "TiO2": 1, "SiO2": 1},
    "Pf": {"CaO": 1, "TiO2": 1}, "Z": {"ZrO2": 1, "SiO2": 1},
    "Cm": {"FeO": 1, "Cr2O3": 1}, "Ap": {"CaO": 10 / 3, "P2O5": 1},
    "ns": {"Na2O": 1, "SiO2": 1}, "ks": {"K2O": 1, "SiO2": 1},
    "Cc": {"CaO": 1, "CO2": 1}, "Py": {"FeO": 1, "S": 2},
    "Fl": {"CaO": 1, "F": 2}, "Hl": {"Na2O": .5, "Cl": 1},
    "Th": {"Na2O": 1, "SO3": 1},
}
REFERENCE_NAMES = {
    "Q": "quartz", "Cor": "corundum", "Or": "orthoclase", "Ab": "albite",
    "An": "anorthite", "Ne": "nepheline", "Le": "leucite", "Kp": "kaliophilite",
    "Ac": "acmite", "Di": "clinoenstatite", "Hd": "clinoferrosilite",
    "Wo": "wollastonite", "Cs": "dicalcium silicate", "En": "enstatite",
    "Fs": "ferrosilite", "Fo": "forsterite", "Fa": "fayalite", "Mt": "magnetite",
    "Hm": "hematite", "Ilm": "ilmenite", "Ru": "rutile", "Tn": "titanite",
    "Pf": "perovskite", "Ap": "apatite", "ns": "sodium metasilicate",
    "ks": "potassium metasilicate",
}
MAJORS = ["SiO2", "TiO2", "Al2O3", "FeO", "Fe2O3", "MgO", "CaO", "Na2O", "K2O", "P2O5"]


def prepared(sample):
    resolved, _ = handle_iron(normalize_oxides(sample))
    return normalize_oxides(resolved)


def inventory_error(sample, result):
    inventory = dict(result["residual_oxides_moles"])
    for mineral, amount in result["minerals_moles"].items():
        for oxide, coefficient in EQUIVALENTS[mineral].items():
            inventory[oxide] = inventory.get(oxide, 0.0) + coefficient * amount
    source = prepared(sample)
    return max(abs(inventory.get(k, 0) - source.get(k, 0) / MASS[k]) for k in MASS)


def endmember_checks(destination):
    records = []
    for mineral, coefficients in EQUIVALENTS.items():
        sample = {oxide: coefficient * MASS[oxide] for oxide, coefficient in coefficients.items()}
        result = cipw(sample, debug=True)
        phases = result["minerals_moles"]
        records.append({"mineral": mineral, "phase_set_correct": set(phases) == {mineral},
                        "complete": result["flags"]["calculation_complete"],
                        "mineral_sum": result["total_mass_sum"],
                        "mass_warning": result["flags"]["mass_balance_warning"],
                        "oxide_inventory_error_moles": inventory_error(sample, result)})
    pd.DataFrame(records).to_csv(destination, index=False)
    return {"cases": len(records),
            "correct_phase_sets": sum(r["phase_set_correct"] for r in records),
            "complete": sum(r["complete"] for r in records),
            "mass_warnings": sum(r["mass_warning"] for r in records),
            "max_inventory_error_moles": max(r["oxide_inventory_error_moles"] for r in records)}


def random_compositions(count, seed, extended=False):
    rng = random.Random(seed)
    maximums = {"SiO2": 80, "Al2O3": 25, "MgO": 30, "CaO": 30, "FeO": 15,
                "Fe2O3": 10, "Na2O": 12, "K2O": 12, "TiO2": 5, "P2O5": 2}
    if extended:
        maximums.update({"CO2": 3, "F": 1, "Cl": 1, "S": 1, "SO3": 1,
                         "Cr2O3": .2, "ZrO2": .2})
    return [{k: rng.uniform(.0001, limit) for k, limit in maximums.items()} for _ in range(count)]


def standalone_checks(samples):
    errors = []
    residuals = Counter()
    sums = []
    max_inventory = 0.0
    incompatible = 0
    complete = 0
    started = time.perf_counter()
    for index, sample in enumerate(samples):
        try:
            result = cipw(sample, debug=True)
            max_inventory = max(max_inventory, inventory_error(sample, result))
            residuals.update(result["residual_oxides_moles"].keys())
            phases = result["minerals_moles"]
            incompatible += bool(phases.get("Q", 0) > 1e-9 and
                                 any(phases.get(m, 0) > 1e-9 for m in ("Ne", "Le", "Kp", "Fo", "Fa")))
            complete += result["flags"]["calculation_complete"]
            sums.append(result["total_mass_sum"])
            assert all(np.isfinite(v) and v >= 0 for v in phases.values())
        except (ValueError, TypeError, ArithmeticError, AssertionError, KeyError) as error:
            errors.append({"index": index, "error": str(error)})
    return {"rows": len(samples), "errors": errors[:10], "error_count": len(errors),
            "complete": complete, "incompatible_quartz_assemblages": incompatible,
            "max_oxide_inventory_error_moles": max_inventory,
            "residual_components": dict(residuals),
            "min_mineral_sum": min(sums) if sums else None,
            "max_mineral_sum": max(sums) if sums else None,
            "seconds_including_inventory_checks": time.perf_counter() - started}


def harmonized_major_frame(samples):
    # Compare the same major-only chemistry after one explicit Fe/Mn policy.
    # Minor/volatile branches and Mn mass substitution are separate experiments.
    rows = []
    for sample in samples:
        major_input = {k: v for k, v in sample.items() if k in MAJORS or k in {"FeOT", "MnO"}}
        rows.append({k: v for k, v in prepared(major_input).items() if k in MAJORS})
    frame = pd.DataFrame(rows).reindex(columns=MAJORS, fill_value=0).fillna(0.0)
    specified = (frame.FeO.gt(0) & frame.Fe2O3.gt(0)) | np.isclose(frame.FeO + frame.Fe2O3, 0)
    # pyrolite otherwise automatically re-partitions singular Fe components.
    excluded = int((~specified).sum())
    frame = frame.loc[specified].reset_index(drop=True)
    frame = frame.div(frame.sum(axis=1), axis=0) * 100
    return frame, excluded


def reference_comparison(samples, reference, destination):
    frame, excluded = harmonized_major_frame(samples)
    started = time.perf_counter()
    local_results = [cipw(row, debug=True) for row in frame.to_dict("records")]
    local_seconds = time.perf_counter() - started
    local = pd.DataFrame([r["minerals_wtpercent"] for r in local_results]).reindex(columns=REFERENCE_NAMES).fillna(0)
    started = time.perf_counter()
    external_input = frame.copy()
    # Explicit float zeros avoid integer-typed missing columns inside the
    # reference's NumPy conversion. They represent omitted branches in this
    # controlled major-only comparison, not additional measurements.
    for column in ("MnO", "CO2", "SO3", "F", "Cl", "S", "Ni", "Co", "Sr", "Ba",
                   "Rb", "Cs", "Li", "Zr", "Cr", "V"):
        external_input[column] = 0.0
    external = reference(external_input, adjust_all_Fe=False, rounding=8, return_adjusted_input=True)
    reference_seconds = time.perf_counter() - started
    # Fail rather than silently compare different iron partitions.
    for oxide in ("FeO", "Fe2O3"):
        assert np.allclose(external[oxide], frame[oxide], atol=2e-6, rtol=0), oxide
    external_minerals = pd.DataFrame({key: external[name] for key, name in REFERENCE_NAMES.items()})
    differences = (local - external_minerals).abs()
    complete = np.array([r["flags"]["calculation_complete"] for r in local_results])
    rows = pd.DataFrame({"row": np.arange(len(frame)), "local_complete": complete,
                         "local_sum": [r["total_mass_sum"] for r in local_results],
                         "reference_sum_nonduplicated": external[[name for key, name in REFERENCE_NAMES.items()]].sum(axis=1),
                         "maximum_mineral_difference_pp": differences.max(axis=1)})
    rows.to_csv(destination, index=False)
    per_mineral = {key: {"mean_abs_pp": float(differences.loc[complete, key].mean()),
                         "max_abs_pp": float(differences.loc[complete, key].max())}
                   for key in REFERENCE_NAMES}
    return {"input_rows": len(samples), "rows_compared": len(frame),
            "excluded_to_preserve_iron_partition": excluded,
            "local_complete_rows": int(complete.sum()),
            "complete_rows_with_any_difference_gt_0_01pp": int((differences.loc[complete].max(axis=1) > .01).sum()),
            "complete_rows_with_any_difference_gt_0_1pp": int((differences.loc[complete].max(axis=1) > .1).sum()),
            "max_abs_difference_complete_pp": float(differences.loc[complete].to_numpy().max()),
            "median_max_difference_complete_pp": float(differences.loc[complete].max(axis=1).median()),
            "per_mineral": per_mineral,
            "local_seconds": local_seconds, "reference_seconds": reference_seconds,
            "scope": "Same major-only normalized inputs and Fe partition; no trace/volatile branches. "
                     "Absolute differences in wt percentage points, not relative errors or geological accuracy."}


def load_published_engine():
    module = types.ModuleType("geonormpy.norms._published_benchmark")
    module.__package__ = "geonormpy.norms"
    source = subprocess.check_output(["git", "show", "v1.0.0:geonormpy/norms/cipw.py"], cwd=ROOT, text=True, encoding="utf-8")
    # Execute only the local repository's fixed release tag for the paired
    # benchmark. Its source hash is included in the output manifest.
    exec(compile(source, "v1.0.0_cipw.py", "exec"), module.__dict__)  # noqa: S102
    return module.cipw, hashlib.sha256(source.encode()).hexdigest()


def stability_checks(samples):
    published, source_hash = load_published_engine()
    scale_error = 0.0
    permutation_error = 0.0
    release_error = 0.0
    labels_changed = 0
    for sample in samples[:200]:
        result = cipw(sample)
        before = published(sample)
        labels_changed += result["flags"]["silica_saturation"] != before["flags"]["silica_saturation"]
        for name in EQUIVALENTS:
            release_error = max(release_error, abs(result["minerals_wtpercent"].get(name, 0) - before["minerals_wtpercent"].get(name, 0)))
        for factor in (1e-250, 1e-6, 1e6, 1e250):
            scaled = cipw({k: v * factor for k, v in sample.items()})
            for mineral in EQUIVALENTS:
                scale_error = max(scale_error, abs(result["minerals_wtpercent"].get(mineral, 0) - scaled["minerals_wtpercent"].get(mineral, 0)))
        permuted = cipw(dict(reversed(list(sample.items()))))
        for mineral in EQUIVALENTS:
            permutation_error = max(permutation_error, abs(result["minerals_wtpercent"].get(mineral, 0) - permuted["minerals_wtpercent"].get(mineral, 0)))
    return {"base_rows": min(200, len(samples)), "scale_cases": min(200, len(samples)) * 4,
            "max_scale_difference_pp": scale_error, "max_order_difference_pp": permutation_error,
            "max_local_vs_release_difference_pp": release_error,
            "local_vs_release_saturation_changes_random_rows": labels_changed,
            "published_tag_source_sha256": source_hash}


def iron_sensitivity(samples, destination):
    shifts, flips, records = [], 0, []
    for index, sample in enumerate(samples[:200]):
        # Collapse measured Fe into a deliberately assumed total, then vary
        # Fe3+/total atom fractions. This is sensitivity, not five true analyses.
        total = sample.get("FeO", 0) + sample.get("Fe2O3", 0) * 2 * MASS["FeO"] / MASS["Fe2O3"]
        total_input = {k: v for k, v in sample.items() if k not in {"FeO", "Fe2O3"}}
        total_input["FeOT"] = total
        results = [cipw(total_input, fe3_fraction=f) for f in (0, .1, .15, .3, .5)]
        for fraction, result in zip((0, .1, .15, .3, .5), results):
            records.append({"sample": index, "ferric_fraction": fraction,
                            "quartz": result["minerals_wtpercent"].get("Q", 0),
                            "saturation": result["flags"]["silica_saturation"],
                            "complete": result["flags"]["calculation_complete"]})
        shifts.append(max(r["minerals_wtpercent"].get("Q", 0) for r in results) -
                      min(r["minerals_wtpercent"].get("Q", 0) for r in results))
        flips += len({r["flags"]["silica_saturation"] for r in results}) > 1
    pd.DataFrame(records).to_csv(destination, index=False)
    return {"base_rows": len(shifts), "ferric_atom_fractions": [0, .1, .15, .3, .5],
            "rows_changing_saturation": flips, "median_quartz_range_pp": float(np.median(shifts)),
            "maximum_quartz_range_pp": max(shifts)}


def plot_comparisons(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for filename, label, color in (
        ("reference_synthetic_major.csv", "Sintéticos", "#246a73"),
        ("reference_public_551.csv", "Públicos", "#b65f33"),
        ("reference_local_major.csv", "GeoNormML", "#6756a5"),
    ):
        path = output / filename
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        values = np.sort(frame.loc[frame.local_complete, "maximum_mineral_difference_pp"])
        axes[0].plot(values, np.arange(1, len(values) + 1) / len(values), label=f"{label} (n={len(values)})", color=color)
    axes[0].set_xlabel("Mayor diferencia por mineral (puntos porcentuales)")
    axes[0].set_ylabel("Fracción acumulada de normas completas")
    axes[0].set_title("GeoNormPy local frente a pyrolite")
    axes[0].legend(fontsize=8)
    sensitivity = pd.read_csv(output / "iron_sensitivity.csv")
    for _, frame in sensitivity.groupby("sample"):
        axes[1].plot(frame.ferric_fraction, frame.quartz, color="#246a73", alpha=.15, linewidth=.7)
    axes[1].set_xlabel("Fracción atómica Fe³⁺ / Fe total asumida")
    axes[1].set_ylabel("Cuarzo normativo (% en peso)")
    axes[1].set_title("Sensibilidad al hierro: 200 composiciones sintéticas")
    fig.suptitle("Comparación controlada de óxidos mayores; no es validación modal", fontsize=11)
    fig.tight_layout()
    fig.savefig(output / "benchmark_comparison.png", dpi=180)
    fig.savefig(output / "benchmark_comparison.pdf")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-deps", type=Path, required=True)
    parser.add_argument("--local-dataset", type=Path)
    parser.add_argument("--random-count", type=int, default=2000)
    args = parser.parse_args()
    if args.random_count < 200:
        parser.error("Use at least 200 compositions")
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.reference_deps.resolve()))
    from pyrolite.mineral.normative import CIPW_norm
    from pyrolite.util.meta import pyrolite_datafolder

    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
    logging.getLogger("pyrolite").setLevel(logging.ERROR)
    seed = 20261025
    major = random_compositions(args.random_count, seed)
    extended = random_compositions(args.random_count, seed + 1, extended=True)
    summary = {"seed": seed, "python": platform.python_version(),
               "dependencies": {n: version(n) for n in ("numpy", "pandas", "periodictable", "pyrolite")},
               "local_cipw_sha256": hashlib.sha256((ROOT / "geonormpy/norms/cipw.py").read_bytes()).hexdigest(),
               "synthetic_major": standalone_checks(major),
               "synthetic_extended": standalone_checks(extended),
               "endmembers": endmember_checks(args.output / "endmembers.csv"),
               "stability": stability_checks(major),
               "iron_sensitivity": iron_sensitivity(major, args.output / "iron_sensitivity.csv")}
    summary["reference_synthetic_major"] = reference_comparison(major, CIPW_norm, args.output / "reference_synthetic_major.csv")
    public_path = pyrolite_datafolder() / "testing/CIPW_Verma_Test.csv"
    raw = pd.read_csv(public_path)
    samples = []
    adjusted_samples = []
    for _, row in raw.iterrows():
        sample = {oxide: pd.to_numeric(row.get(oxide.upper()), errors="coerce") for oxide in MAJORS}
        sample = {k: float(v) for k, v in sample.items() if pd.notna(v)}
        # Where measured speciation is absent, use the same declared 0.15
        # ferric fraction in both engines; never mix FeOT with measured iron.
        if sample.get("FeO", 0) + sample.get("Fe2O3", 0) == 0:
            total = pd.to_numeric(row.get("FEOT"), errors="coerce")
            if not pd.notna(total) or total <= 0:
                ferric_total = pd.to_numeric(row.get("FE2O3T"), errors="coerce")
                total = ferric_total * 2 * MASS["FeO"] / MASS["Fe2O3"]
            if pd.notna(total) and total > 0:
                sample.pop("FeO", None)
                sample.pop("Fe2O3", None)
                sample["FeOT"] = float(total)
        samples.append(sample)
        adjusted = {oxide: pd.to_numeric(row.get(oxide.upper() + "ADJ"), errors="coerce") for oxide in MAJORS}
        adjusted = {k: float(v) for k, v in adjusted.items() if pd.notna(v)}
        if sum(adjusted.values()) > 0:
            adjusted_samples.append(adjusted)
    summary["public_dataset"] = {"name": public_path.name, "source_rows": len(samples),
                                "sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
                                "input_columns": "Raw major oxides, measured Fe or explicit shared fixed fraction for total Fe.",
                                "comparison": reference_comparison(samples, CIPW_norm, args.output / "reference_public_551.csv"),
                                "preadjusted_rows_available": len(adjusted_samples),
                                "preadjusted_rows_missing": len(samples) - len(adjusted_samples),
                                "preadjusted_comparison": reference_comparison(adjusted_samples, CIPW_norm, args.output / "reference_public_adjusted.csv")}
    if args.local_dataset:
        raw = pd.read_excel(args.local_dataset, sheet_name="training_ready_final")
        samples = [{k: float(v) for k, v in row.items() if (k in MASS or k == "FeOT") and pd.notna(v)}
                   for row in raw.to_dict("records")]
        summary["local_dataset"] = {"sha256": hashlib.sha256(args.local_dataset.read_bytes()).hexdigest(),
                                    "standalone": standalone_checks(samples),
                                    "comparison": reference_comparison(samples, CIPW_norm, args.output / "reference_local_major.csv")}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
    plot_comparisons(args.output)
    compact = {key: {k: v for k, v in value.items() if k not in {"per_mineral", "errors"}} if isinstance(value, dict) else value
               for key, value in summary.items() if key not in {"public_dataset", "local_dataset"}}
    compact["public_dataset_comparison"] = {k: v for k, v in summary["public_dataset"]["comparison"].items() if k != "per_mineral"}
    if "local_dataset" in summary:
        compact["local_dataset_comparison"] = {k: v for k, v in summary["local_dataset"]["comparison"].items() if k != "per_mineral"}
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
