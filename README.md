<div align="center">

# GeoNormPy

**Reproducible CIPW normative mineralogy for whole-rock geochemistry**

Transform major-oxide analyses into auditable normative mineral assemblages,
diagnostics and batch-ready tables from Python or the command line.

[![Release v0.1.1](https://img.shields.io/github/v/release/jordan-zav/GeoNormPy?color=2563eb)](https://github.com/jordan-zav/GeoNormPy/releases/latest)
[![Tests](https://img.shields.io/github/actions/workflow/status/jordan-zav/GeoNormPy/python-package.yml?branch=main&label=tests)](https://github.com/jordan-zav/GeoNormPy/actions/workflows/python-package.yml)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-0f766e)](LICENSE)

</div>

> [!IMPORTANT]
> A CIPW norm is an idealized calculation from whole-rock chemistry. It is not
> measured modal mineralogy and does not replace petrography, field relations
> or an appropriate classification diagram such as QAPF.

## Workflow at a glance

```text
Major oxides + sample identifiers
              │
              ▼
 Schema validation and iron-speciation handling
              │
              ▼
 Dry normalization ──► sequential CIPW allocation
              │
              ▼
 Normative minerals + mass balance + saturation flags
              │
              ▼
 Python dictionary / pandas table / CSV workflow
```

## Capabilities

| Area | Support |
| --- | --- |
| Calculation | Sequential CIPW normative mineral allocation |
| Iron | Total iron as `FeOT` or explicit `FeO` and `Fe2O3` inputs |
| Diagnostics | Silica saturation, alumina state, mass-balance error and interpretive flags |
| Execution | Single-sample Python API, pandas batch processing and CLI workflows |
| Reproducibility | YAML configuration, schema inspection, templates and input validation |
| Integration | Reusable normative-feature engine for GeoNormML |

## Supported chemistry

Core and accessory inputs include:

`SiO2`, `TiO2`, `Al2O3`, `Fe2O3`, `FeO`, `FeOT`, `MnO`, `MgO`, `CaO`,
`Na2O`, `K2O`, `P2O5`, `ZrO2`, `Cr2O3`, `CO2`, `S`, `F`, `Cl` and `SO3`.

Optional identifier columns include `Sample_ID` and `Notes`. Input chemistry
must use a consistent weight-percent basis and documented treatment of loss on
ignition, below-detection values and total iron.

## Installation

### Latest release

```powershell
python -m pip install geonormpy
```

### Editable source installation

```powershell
git clone https://github.com/jordan-zav/GeoNormPy.git
cd GeoNormPy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

## Quick Python example

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

## Command-line workflow

```powershell
geonormpy --help
geonormpy schema
geonormpy make-template
geonormpy make-config
geonormpy validate --input data/test_data.csv
geonormpy run --config config/workflow.yaml
```

The example batch launcher reads `data/test_data.csv` and writes
`data/normative_results.csv`:

```powershell
python run_GeoNormPy.py
```

## Standard outputs

### Diagnostic fields

- `silica_saturation`
- `alumina_state`
- `mass_balance_error`
- `interpretive_flag`
- `calc_error`

### Normative mineral fields

`Q`, `Cor`, `Or`, `Ab`, `An`, `Le`, `Ne`, `Kp`, `Ac`, `Di`, `Hd`, `Wo`,
`En`, `Fs`, `Fo`, `Fa`, `Mt`, `Hm`, `Ilm`, `Cm`, `Ru`, `Tn`, `Z`, `Ap`,
`Cc`, `Py`, `Fl`, `Hl`, `Th`, `ns` and `ks`.

Downstream software should preserve both the mineral results and the diagnostic
columns. Filtering only the successful rows without retaining the error reason
breaks traceability.

## Scientific boundaries

- Normative phases are calculated end-members, not minerals observed in thin section.
- Iron-speciation assumptions can materially change normative mafic and oxide phases.
- Volatile, alteration and analytical-total problems must be reviewed before interpretation.
- TAS, QAPF, petrography and CIPW answer related but different classification questions.
- A successful mass balance does not prove that the input rock name is correct.

## Development and verification

```powershell
python -m pip install -e .
python -m pytest -q
```

The regression suite covers the CIPW engine, robustness cases, CLI behavior and
configured workflows. See the [complete method description](docs/methods/Algoritmo_GeoNormPy_Completo.md)
and the [audit record](docs/methods/Auditoria_CIPW_Sesion_2026-04-10.md).

## Repository map

| Path | Contents |
| --- | --- |
| `geonormpy/norms` | CIPW and batch calculation engine |
| `geonormpy/core` | Chemistry constants, minerals and shared rules |
| `geonormpy/schema.py` | Supported input/output schema |
| `geonormpy/cli.py` | Command-line interface |
| `config` | Example YAML workflow configuration |
| `tests` | Numerical, robustness, CLI and workflow tests |
| `docs` | Method, theory and audit material |

## Citation

Use the metadata in [CITATION.cff](CITATION.cff) when citing GeoNormPy in a
thesis, article or technical report.

## License and contact

GeoNormPy is distributed under the [GNU General Public License v3.0](LICENSE).

Jordan Zavaleta — GisGeo Dev<br>
[jordanzav@gisgeo.dev](mailto:jordanzav@gisgeo.dev) · [gisgeo.dev](https://gisgeo.dev)
