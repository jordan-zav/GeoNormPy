"""Controlled accessory-branch comparison using reference-adjusted chemistry.

pyrolite is an isolated comparator, not an oracle. Apatite outputs are kept
separate because its fluorinated branches have different output conventions.
"""

import argparse
import hashlib
import json
import logging
import random
import sys
import warnings
from pathlib import Path

import pandas as pd
from benchmark_cipw import REFERENCE_NAMES

from geonormpy import __version__, cipw
from geonormpy.norms.revised import MASSES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-deps", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.reference_deps))
    from pyrolite.mineral.normative import CIPW_norm

    warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
    logging.getLogger("pyrolite").setLevel(logging.ERROR)
    rng = random.Random(2026102607)
    mapping = dict(REFERENCE_NAMES, Z="zircon", Cm="chromite", Fl="fluorite",
                   Hl="halite", Th="thenardite", Py="pyrite", Nc="cancrinite", Cc="calcite")
    mapping.pop("Ap")
    output = {"seed": 2026102607, "reference": "pyrolite 0.3.8.post1", "groups": {},
              "version": __version__,
              "scope": "Reference-adjusted oxide inputs, measured iron, sodium-carbonate assumption; apatite excluded from maximum difference."}
    for group in ("substitutions", "balanced_accessories", "fluorine_excess", "limiting_reagents"):
        rows = []
        for _ in range(500):
            row = {"SiO2": rng.uniform(45, 75), "Al2O3": rng.uniform(12, 20), "TiO2": .5,
                   "FeO": rng.uniform(3, 8), "Fe2O3": rng.uniform(1, 3), "MgO": rng.uniform(1, 8),
                   "CaO": rng.uniform(4, 10), "Na2O": rng.uniform(2, 6), "K2O": rng.uniform(1, 5),
                   "P2O5": rng.uniform(.1, 1), "MnO": .2}
            for key in ("Ni", "Co", "Sr", "Ba", "Rb", "Cs", "Li", "Zr", "Cr", "V"):
                row[key] = rng.uniform(1, 200)
            # All these columns use ppm in the comparator, including CO2/SO3.
            for key in ("F", "Cl", "S", "CO2", "SO3"):
                row[key] = 0. if group == "substitutions" else rng.uniform(10, 300)
            if group == "fluorine_excess":
                row["F"] = rng.uniform(10000, 40000)
            elif group == "limiting_reagents":
                row.update(FeO=.01, Na2O=.01, CaO=.01, Cl=30000., S=30000., SO3=30000.)
            rows.append(row)
        external = CIPW_norm(pd.DataFrame(rows), adjust_all_Fe=False, rounding=12,
                             return_adjusted_input=True, return_free_components=True)
        adjusted = external.reindex(columns=list(MASSES), fill_value=0.).fillna(0.)
        records = []
        for index, sample in enumerate(adjusted.to_dict("records")):
            result = cipw(sample, profile="verma2003", iron_policy="measured", carbonate_mode="sodium_carbonate", debug=True)
            differences = {key: abs(result["minerals_wtpercent"].get(key, 0.) - external.loc[index, name]) for key, name in mapping.items()}
            phase = max(differences, key=differences.get)
            records.append({"row": index, "complete": result["flags"]["calculation_complete"],
                            "reference_no_deficit": abs(external.loc[index, "FREE_DEFSIO2"]) < 1e-8,
                            "largest_difference_phase": phase, "max_difference_pp": differences[phase],
                            "local_mass_error": result["mass_balance_error"],
                            "local_apatite_total": sum(result["minerals_wtpercent"].get(k, 0) for k in ("Ap", "FAp")),
                            "reference_apatite": external.loc[index, "apatite"],
                            "reference_fluorapatite": external.loc[index, "fluroapatite"]})
        frame = pd.DataFrame(records)
        frame.to_csv(args.output / f"{group}.csv", index=False)
        shared = frame.complete & frame.reference_no_deficit
        output["groups"][group] = {"rows": len(frame), "shared_no_deficit": int(shared.sum()),
                                    "max_difference_shared_pp": float(frame.loc[shared, "max_difference_pp"].max()),
                                    "rows_shared_above_0_01pp": int((frame.loc[shared, "max_difference_pp"] > .01).sum()),
                                    "max_local_mass_error_complete": float(frame.loc[frame.complete, "local_mass_error"].max()),
                                    "largest_difference_phases": frame.largest_difference_phase.value_counts().to_dict()}
    witnesses = []
    for phase, reference_name, reagent, value in (("Hl", "halite", "Cl", 4.),
                                                  ("Hl", "halite", "Cl", .05),
                                                  ("Py", "pyrite", "S", .05)):
        source = {"SiO2": 60., "Al2O3": 0., "TiO2": 0., "FeO": .1 if phase == "Py" else 0.,
                  "Fe2O3": 0., "MgO": 0., "CaO": 0., "Na2O": .1 if phase == "Hl" else 0.,
                  "K2O": 0., "P2O5": 0., "MnO": 0.}
        for key in ("Ni", "Co", "Sr", "Ba", "Rb", "Cs", "Li", "Zr", "Cr", "V", "F", "Cl", "S", "CO2", "SO3"):
            source[key] = 0.
        source[reagent] = value * 1e4
        # Both-zero iron prevents the reference's automatic repartition. For
        # pyrite use an explicit positive ferric measurement as well.
        if phase == "Py":
            source["Fe2O3"] = .01
        external = CIPW_norm(pd.DataFrame([source]), adjust_all_Fe=False, rounding=12,
                             return_adjusted_input=True, return_free_components=True)
        adjusted = external.reindex(columns=list(MASSES), fill_value=0.).iloc[0].to_dict()
        result = cipw(adjusted, profile="verma2003", iron_policy="measured")
        theoretical = (min(2 * adjusted["Na2O"] / MASSES["Na2O"], adjusted["Cl"] / MASSES["Cl"]) if phase == "Hl" else
                       min(adjusted["FeO"] / MASSES["FeO"], adjusted["S"] / (2 * MASSES["S"])))
        witnesses.append({"phase": phase, "input_wtpercent": adjusted,
                          "hand_formula_moles": theoretical,
                          "local_formula_moles": result["minerals_moles"][phase],
                          "local_wtpercent": result["minerals_wtpercent"][phase],
                          "reference_wtpercent": float(external.loc[0, reference_name])})
    output["limiting_reagent_witnesses"] = witnesses
    root = Path(__file__).resolve().parents[1]
    output["source_sha256"] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                               for name in ("geonormpy/norms/revised.py", "tests/test_profile_properties.py",
                                            "benchmarks/benchmark_accessories.py")}
    (args.output / "summary.json").write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
