# GeoNormPy

GeoNormPy is a Python engine for estimating CIPW normative mineralogy from whole-rock geochemical data. The project is oriented toward igneous petrology workflows and reproducible geochemical data processing.

## Features

- Sequential CIPW calculation with a numerically robust approach.
- Iron handling based on `FeOT` or explicit `FeO`/`Fe2O3` speciation.
- Diagnostics for silica saturation and alumina state.
- Single-sample and batch processing with `pandas`.
- Automated test suite with `pytest`.

## Installation

```bash
git clone https://github.com/jordan-zav/GeoNormPy.git
cd GeoNormPy
pip install -e .
```

## Quick Start

```python
from geonormpy.norms.cipw import cipw

sample = {
    "SiO2": 72.5,
    "Al2O3": 13.5,
    "FeOT": 2.5,
    "MgO": 0.5,
    "CaO": 1.8,
    "Na2O": 3.4,
    "K2O": 4.0,
}

result = cipw(sample)
print(result["minerals_wtpercent"])
print(result["flags"])
```

## Batch Processing

```bash
python run_GeoNormPy.py
```

The script reads `data/test_data.csv` and generates `data/normative_results.csv`.

## Development

```bash
pytest -q
```

## Academic Context

This software was developed by Jordan Angel Luciano Zavaleta Reyes in the context of applied research in igneous petrology and computational geochemistry.

## How to Cite

If you use GeoNormPy in a thesis, article, or technical report, please refer to the `CITATION.cff` file.

## License

This project is distributed under the MIT License.
