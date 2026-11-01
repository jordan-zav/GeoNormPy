"""Run real CIPW checks and a synthetic sample for a portfolio capture."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from geonormpy.norms.cipw import cipw


def main():
    print("GeoNormPy | CIPW normative mineralogy", flush=True)
    print("Whole-rock chemistry -> normative mineral assemblage", flush=True)
    print("=" * 76, flush=True)
    print("\n[1/2] Running repository tests: CIPW, profiles and cation conservation\n", flush=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "--tb=short",
         "tests/test_cipw.py", "tests/test_profiles.py", "tests/test_cation_conservation.py"],
        cwd=ROOT,
    )
    if completed.returncode:
        return completed.returncode
    print("\n[2/2] Computing a synthetic granite example (not field data)\n", flush=True)
    sample = {"SiO2": 72.5, "Al2O3": 13.5, "FeOT": 2.5, "MgO": 0.5,
              "CaO": 1.8, "Na2O": 3.4, "K2O": 4.0, "TiO2": 0.3, "P2O5": 0.1}
    result = cipw(sample)
    print("INPUT (wt%)  " + "  ".join(f"{k}={v:g}" for k, v in list(sample.items())[:5]))
    print("             " + "  ".join(f"{k}={v:g}" for k, v in list(sample.items())[5:]))
    print("\nNORMATIVE MINERAL                         wt%")
    print("-" * 46)
    for mineral, value in result["minerals_wtpercent"].items():
        if value > 0:
            print(f"{mineral:<36} {value:9.4f}")
    print("-" * 46)
    print(f"Silica saturation : {result['flags']['silica_saturation']}")
    print(f"Alumina state     : {result['flags']['alumina_state']}")
    print(f"Mass balance error: {result['mass_balance_error']:.3e}")
    print("\nCalculation complete. Normative minerals are not measured modal minerals.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
