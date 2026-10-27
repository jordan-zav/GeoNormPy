<p align="center"><strong>English</strong> · <a href="README.es.md">Español</a></p>

<div align="center">

# GeoNormPy

**Reproducible CIPW normative mineralogy for whole-rock geochemistry**

Transform major-oxide analyses into auditable normative mineral assemblages,
diagnostics and batch-ready tables from Python or the command line.

[![Release](https://img.shields.io/github/v/release/jordan-zav/GeoNormPy?color=2563eb)](https://github.com/jordan-zav/GeoNormPy/releases/latest)
[![Tests](https://img.shields.io/github/actions/workflow/status/jordan-zav/GeoNormPy/python-package.yml?branch=main&label=tests)](https://github.com/jordan-zav/GeoNormPy/actions/workflows/python-package.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-0f766e)](LICENSE)

</div>

> [!IMPORTANT]
> A CIPW norm is an idealized calculation from whole-rock chemistry. It is not
> measured modal mineralogy and does not replace petrography, field relations
> or an appropriate classification diagram such as QAPF.

## Legacy and congress reference

The earlier GeoNormPy / GeoNormML work was **presented as a technical paper at the
[XXIII Peruvian Geological Congress (CPG XXIII)](https://congresosgp.org.pe/)**,
organized by the Sociedad Geológica del Perú in 2026. That research generation
is identified as **Legacy**; its historical figures are not current benchmarks.

GeoNormPy 1.0.0 is retained as a Legacy release. The congress material advertised
0.1.1, an earlier publication cut. The corrected extended_cipw_v3 3.1 profile in
1.1.0 is not identical to either earlier release. Verma 2003 and Pruseth 2009 are
calculation profiles, not trained classifiers. Numerical closure does not establish
an improvement in ML accuracy. See [citation metadata](CITATION.cff) and the
[GeoNormML generation decision](https://github.com/jordan-zav/GeoNormML/blob/main/docs/revisiones/modelos_legacy_y_vigentes.md).


## Methodological scope and critical assessment

Engine tests check numerical behavior, component inventories and errors in the
documented cases; they do not certify measured mineralogy or classifier accuracy.
An inventory can close through free components and signed corrections while the
mineral allocation remains incomplete. Inspect calculation status, supported
chemistry and warnings rather than relying on closure alone.

Profile comparisons must align inputs, units, normalization and iron policy,
while declaring apatite and carbonate conventions. Replacing the profile that
generated an ML model's features requires reevaluation under the same design.
The completed review neither attributes Legacy metric differences to a GeoNormPy
failure nor demonstrates that better closure improves ML accuracy. The
[GeoNormML methodology and critique](https://github.com/jordan-zav/GeoNormML/blob/main/README.md#current-methodology-and-critical-assessment)
distinguishes checked results from the nested and independent evaluation still
required for future selection procedures.

## Workflow at a glance

~~~text
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
~~~

## Capabilities

| Area | Support |
| --- | --- |
| Calculation | Sequential CIPW normative mineral allocation |
| Iron | Total iron as <code>FeOT</code> or explicit <code>FeO</code> and <code>Fe2O3</code> inputs |
| Diagnostics | Silica saturation, alumina state, mass-balance error and interpretive flags |
| Execution | Single-sample Python API, pandas batch processing and CLI workflows |
| Reproducibility | YAML configuration, schema inspection, templates and input validation |
| Integration | Reusable normative-feature engine for GeoNormML |

## Supported chemistry

### Model scope

Version 1.1.0 offers extended_cipw_v3 (default compatibility), verma2003 and
pruseth2009 profiles, with independently selected iron policies. Their input
sets, apatite conventions and free-component accounting differ. Unresolved
allocations are reported explicitly; the safe API returns a structured error.
See [profiles and scientific conventions](docs/PERFILES_CIPW.md) and
[model limits and errors](docs/ERRORS.md).

Core and accessory inputs include:

<code>SiO2</code>, <code>TiO2</code>, <code>Al2O3</code>, <code>Fe2O3</code>, <code>FeO</code>, <code>FeOT</code>, <code>MnO</code>, <code>MgO</code>, <code>CaO</code>,
<code>Na2O</code>, <code>K2O</code>, <code>P2O5</code>, <code>ZrO2</code>, <code>Cr2O3</code>, <code>CO2</code>, <code>S</code>, <code>F</code>, <code>Cl</code> and <code>SO3</code>.

Optional identifier columns include <code>Sample_ID</code> and <code>Notes</code>. Input chemistry
must use a consistent weight-percent basis and documented treatment of loss on
ignition, below-detection values and total iron.

## Installation

### Latest release

~~~powershell
python -m pip install geonormpy
~~~

### Editable source installation

~~~powershell
git clone https://github.com/jordan-zav/GeoNormPy.git
cd GeoNormPy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
~~~

## Quick Python example

~~~python
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
~~~

## Command-line workflow

~~~powershell
geonormpy --help
geonormpy schema
geonormpy make-template
geonormpy make-config
geonormpy validate --input data/test_data.csv
geonormpy run --config config/workflow.yaml
~~~

The example batch launcher reads <code>data/test_data.csv</code> and writes
<code>data/normative_results.csv</code>:

~~~powershell
python run_GeoNormPy.py
~~~

## Standard outputs

### Diagnostic fields

- <code>silica_saturation</code>
- <code>alumina_state</code>
- <code>mass_balance_error</code>
- <code>interpretive_flag</code>
- <code>calc_error</code>

### Normative mineral fields

<code>Q</code>, <code>Cor</code>, <code>Or</code>, <code>Ab</code>, <code>An</code>, <code>Le</code>, <code>Ne</code>, <code>Kp</code>, <code>Ac</code>, <code>Di</code>, <code>Hd</code>, <code>Wo</code>,
<code>En</code>, <code>Fs</code>, <code>Fo</code>, <code>Fa</code>, <code>Mt</code>, <code>Hm</code>, <code>Ilm</code>, <code>Cm</code>, <code>Ru</code>, <code>Tn</code>, <code>Z</code>, <code>Ap</code>,
<code>Cc</code>, <code>Py</code>, <code>Fl</code>, <code>Hl</code>, <code>Th</code>, <code>ns</code> and <code>ks</code>.

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

Version 1.1.0 adds three selectable CIPW profiles:
extended_cipw_v3 (default compatibility), verma2003 and pruseth2009.
Iron policies can be selected independently. Results record the selected
profile, its version and calculation assumptions. See
[profiles, API, CLI and scientific conventions](docs/PERFILES_CIPW.md).

~~~powershell
python -m pip install -e .
python -m pytest -q
~~~

The regression suite covers the CIPW engine, robustness cases, CLI behavior and
configured workflows. See the [complete method description](docs/methods/Algoritmo_GeoNormPy_Completo.md)
and the [audit record](docs/methods/Auditoria_CIPW_Sesion_2026-04-10.md).

## Repository map

The [extended CIPW benchmarks](docs/benchmarks_y_metodos_cipw_20261025.md)
compare the major-oxide core with pyrolite, document numerical stability and
iron sensitivity, and distinguish unresolved allocations from valid norms.
See the [benchmark runner](benchmarks/README.md) for reproducible commands.

| Path | Contents |
| --- | --- |
| <code>geonormpy/norms</code> | CIPW and batch calculation engine |
| <code>geonormpy/core</code> | Chemistry constants, minerals and shared rules |
| <code>geonormpy/schema.py</code> | Supported input/output schema |
| <code>geonormpy/cli.py</code> | Command-line interface |
| <code>config</code> | Example YAML workflow configuration |
| <code>tests</code> | Numerical, robustness, CLI and workflow tests |
| <code>docs</code> | Method, theory and audit material |

## Citation

Version 1.0.0 introduced structured errors and JSON output. See [errors and integration](docs/ERRORS.md) and [PyPI publishing](docs/PUBLISHING.md).

Use the metadata in [CITATION.cff](CITATION.cff) when citing GeoNormPy in a
thesis, article or technical report.

## License and contact

GeoNormPy is distributed under the [GNU General Public License v3.0](LICENSE).

Jordan Zavaleta — GisGeo Dev<br>
[jordanzav@gisgeo.dev](mailto:jordanzav@gisgeo.dev) · [gisgeo.dev](https://gisgeo.dev)
