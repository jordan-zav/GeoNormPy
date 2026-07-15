# GeoNormPy

GeoNormPy is a Python engine for estimating CIPW normative mineralogy from whole-rock geochemical data. The project is oriented toward igneous petrology workflows and reproducible geochemical data processing.


## ⚖️ License (Dual Licensing)

This project is distributed under a **Dual Licensing** model:

1. **Open Source Use (GNU GPLv3):** You can use, study, modify, and redistribute this software for free, provided that any modified version or derivative work is also 100% open source under the GNU GPLv3 license.
2. **Commercial / Private Use (Commercial License):** If you wish to integrate this code into proprietary, closed-source, or commercial software (without the obligation to open your own source code under the GPLv3), you must acquire an exclusive commercial license. Please contact the author to negotiate terms.

For more details, see the [LICENSE](LICENSE) file.

---

## Features

- Sequential CIPW calculation with a numerically robust approach.
- Iron handling based on `FeOT` or explicit `FeO`/`Fe2O3` speciation.
- Diagnostics for silica saturation and alumina state.
- Single-sample and batch processing with `pandas`.
- Automated test suite with `pytest`.

## Installation

```bash
pip install geonormpy
```
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

## Command-Line Interface

GeoNormPy includes a command-line interface so users can inspect the supported
schema, create templates, validate input files, and run workflows.

```bash
geonormpy --help
geonormpy schema
geonormpy validate --input data/test_data.csv
geonormpy make-template
geonormpy make-config
geonormpy run --config config/workflow.yaml
```

### Supported Input Columns

Optional ID columns:
`Sample_ID`, `Notes`

Supported oxide columns:
`SiO2`, `TiO2`, `Al2O3`, `Fe2O3`, `FeO`, `FeOT`, `MnO`, `MgO`, `CaO`, `Na2O`,
`K2O`, `P2O5`, `ZrO2`, `Cr2O3`, `CO2`, `S`, `F`, `Cl`, `SO3`

### Standard Output Columns

Diagnostic columns:
`silica_saturation`, `alumina_state`, `mass_balance_error`, `interpretive_flag`,
`calc_error`

Normative mineral columns:
`Q`, `Cor`, `Or`, `Ab`, `An`, `Le`, `Ne`, `Kp`, `Ac`, `Di`, `Hd`, `Wo`, `En`,
`Fs`, `Fo`, `Fa`, `Mt`, `Hm`, `Ilm`, `Cm`, `Ru`, `Tn`, `Z`, `Ap`, `Cc`, `Py`,
`Fl`, `Hl`, `Th`, `ns`, `ks`

## Development

```bash
pytest -q
```

## Academic Context

This software was developed by Jordan Angel Luciano Zavaleta Reyes in the context of applied research in igneous petrology and computational geochemistry.

## How to Cite

If you use GeoNormPy in a thesis, article, or technical report, please refer to the `CITATION.cff` file.

## License

This project is licensed under the GNU GPLv3 and the Dual Licensing agreement described above. See the [LICENSE](LICENSE) file for more details.
