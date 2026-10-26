"""Compare named profiles on synthetic, public and optional local chemistry.

Reference dependencies are external to the package. No input file is modified.
Outputs include incomplete allocations rather than hiding their frequency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from benchmark_cipw import (
    MAJORS,
    REFERENCE_NAMES,
    harmonized_major_frame,
    random_compositions,
)

from geonormpy import __version__, cipw

PROFILES = ("extended_cipw_v3", "verma2003", "pruseth2009")


def stress(samples, profile, output, name):
    records = []
    start = time.perf_counter()
    for index, sample in enumerate(samples):
        result = cipw(sample, profile=profile)
        complete = result["flags"]["calculation_complete"]
        scale_error = 0.0
        if index < 100:
            scaled = cipw({k: v * 1e200 for k, v in sample.items()}, profile=profile)
            scale_error = max(abs(result["minerals_wtpercent"].get(k, 0) - scaled["minerals_wtpercent"].get(k, 0))
                              for k in set(result["minerals_wtpercent"]) | set(scaled["minerals_wtpercent"]))
        inventory = result.get("mass_balance", {}).get("inventory_sum_including_silica_deficit", np.nan)
        records.append({"row": index, "complete": complete, "mass_error": result["mass_balance_error"],
                        "inventory_error": abs(100 - inventory), "scale_difference_pp": scale_error,
                        "saturation": result["flags"]["silica_saturation"]})
    frame = pd.DataFrame(records)
    frame.to_csv(output / f"{name}_{profile}.csv", index=False)
    return {"rows": len(frame), "complete": int(frame.complete.sum()),
            "incomplete": int((~frame.complete).sum()),
            "max_mass_error_complete": float(frame.loc[frame.complete, "mass_error"].max()),
            "max_inventory_error": None if profile == PROFILES[0] else float(frame.inventory_error.max()),
            "max_scale_difference_pp_100_rows": float(frame.scale_difference_pp.max()),
            "seconds": time.perf_counter() - start}


def compare(samples, reference, output, name):
    frame, excluded = harmonized_major_frame(samples)
    external_input = frame.copy()
    for column in ("MnO", "CO2", "SO3", "F", "Cl", "S", "Ni", "Co", "Sr", "Ba", "Rb", "Cs", "Li", "Zr", "Cr", "V"):
        external_input[column] = 0.0
    external = reference(external_input, adjust_all_Fe=False, rounding=8,
                         return_adjusted_input=True, return_free_components=True)
    reference_complete = external.FREE_DEFSIO2.abs().lt(1e-6).to_numpy()
    for oxide in ("FeO", "Fe2O3"):
        if not np.allclose(external[oxide], frame[oxide], atol=2e-6, rtol=0):
            raise ValueError("Reference changed iron speciation")
    summary = {"source_rows": len(samples), "compared_rows": len(frame), "excluded_iron": excluded,
               "reference_without_silica_deficit": int(reference_complete.sum())}
    for profile in PROFILES:
        results = [cipw(row, profile=profile, iron_policy="measured") for row in frame.to_dict("records")]
        local = pd.DataFrame([r["minerals_wtpercent"] for r in results]).reindex(columns=REFERENCE_NAMES).fillna(0.0)
        # Pruseth has normative fluorapatite without measured F; compare the
        # remaining phases, and report apatite separately instead of masking it.
        keys = list(REFERENCE_NAMES)
        if profile == "pruseth2009":
            keys.remove("Ap")
        differences = pd.DataFrame({k: (local[k] - external[v]).abs() for k, v in REFERENCE_NAMES.items() if k in keys})
        complete = np.array([r["flags"]["calculation_complete"] for r in results])
        shared = complete & reference_complete
        records = pd.DataFrame({"row": range(len(frame)), "complete": complete,
                                "reference_without_silica_deficit": reference_complete,
                                "max_difference_pp": differences.max(axis=1),
                                "apatite_local": [r["minerals_wtpercent"].get("Ap", 0) + r["minerals_wtpercent"].get("FAp", 0) for r in results],
                                "apatite_reference": external.apatite})
        records.to_csv(output / f"{name}_{profile}.csv", index=False)
        summary[profile] = {"complete": int(complete.sum()), "incomplete": int((~complete).sum()),
                            "rows_reporting_unused_components": sum(bool(r["flags"].get("free_components_present")) for r in results),
                            "shared_without_silica_deficit": int(shared.sum()),
                            "max_difference_shared_pp": float(differences.loc[shared].max().max()),
                            "shared_rows_above_0_01pp": int((differences.loc[shared].max(axis=1) > .01).sum()),
                            "max_difference_complete_pp": float(differences.loc[complete].max().max()),
                            "median_max_difference_complete_pp": float(differences.loc[complete].max(axis=1).median()),
                            "complete_rows_above_0_01pp": int((differences.loc[complete].max(axis=1) > .01).sum()),
                            "apatite_included_in_phase_comparison": profile != "pruseth2009"}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-deps", type=Path, required=True)
    parser.add_argument("--local-dataset", type=Path)
    parser.add_argument("--count", type=int, default=2000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.reference_deps.resolve()))
    from pyrolite.mineral.normative import CIPW_norm
    from pyrolite.util.meta import pyrolite_datafolder

    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
    logging.getLogger("pyrolite").setLevel(logging.ERROR)
    major = random_compositions(args.count, 20261026)
    extended = random_compositions(args.count, 20261027, extended=True)
    public_path = pyrolite_datafolder() / "testing/CIPW_Verma_Test.csv"
    raw = pd.read_csv(public_path)
    samples = []
    for _, row in raw.iterrows():
        sample = {k: float(row[k.upper()]) for k in MAJORS if pd.notna(row.get(k.upper()))}
        if sample.get("FeO", 0) + sample.get("Fe2O3", 0) == 0 and pd.notna(row.get("FEOT")):
            sample = {k: v for k, v in sample.items() if k not in {"FeO", "Fe2O3"}}
            sample["FeOT"] = float(row.FEOT)
        elif sample.get("FeO", 0) + sample.get("Fe2O3", 0) == 0 and pd.notna(row.get("FE2O3T")):
            sample = {k: v for k, v in sample.items() if k not in {"FeO", "Fe2O3"}}
            sample["FeOT"] = float(row.FE2O3T) * 2 * 71.8444 / 159.6882
        samples.append(sample)
    summary = {"version": __version__, "python": platform.python_version(), "seed_major": 20261026,
               "seed_extended": 20261027, "reference": "pyrolite 0.3.8.post1; controlled major-only comparison",
               "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
               "stress": {}, "reference_synthetic": compare(major, CIPW_norm, args.output, "reference_synthetic"),
               "reference_public": compare(samples, CIPW_norm, args.output, "reference_public")}
    root = Path(__file__).resolve().parents[1]
    summary["source_sha256"] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                for name in ("geonormpy/norms/cipw.py", "geonormpy/norms/revised.py",
                                             "geonormpy/core/iron.py", "benchmarks/benchmark_profiles.py")}
    for profile in PROFILES:
        eligible = extended if profile != "pruseth2009" else [{k: v for k, v in row.items() if k not in {"Cl", "SO3"}} for row in extended]
        summary["stress"][profile] = {"major": stress(major, profile, args.output, "stress_major"),
                                         "extended": stress(eligible, profile, args.output, "stress_extended")}
    if args.local_dataset:
        local = pd.read_excel(args.local_dataset)
        local_samples = [{k: float(row[k]) for k in MAJORS + ["FeOT", "MnO"] if k in row and pd.notna(row[k])} for _, row in local.iterrows()]
        summary["local_sha256"] = hashlib.sha256(args.local_dataset.read_bytes()).hexdigest()
        summary["reference_local"] = compare(local_samples, CIPW_norm, args.output, "reference_local")
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
