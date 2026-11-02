# GeoNormPy 1.1.0: delivery state and remaining work

[Español](STATUS.es.md) · [Publishing procedure](PUBLISHING.md)

The 1.1.0 engine provides three versioned profiles: extended_cipw_v3 (default
compatibility, profile 3.1), verma2003 (1.0) and pruseth2009 (1.0). Iron policy
is selected independently. The corrected default is not numerically identical
to the historical 1.0.0 release.

## Implemented and checked

- Python API, safe structured errors, CLI, batch workflow and per-row metadata.
- Frozen compatibility cases, pure-phase and component-inventory checks,
  input validation, silica-boundary tests and profile comparisons.
- Public-composition and controlled pyrolite comparisons, with documented
  exclusions and harmonized input conventions.
- Wheel and source-distribution metadata checks, source regression resources
  and CLI tests importing the real wheel outside the source checkout.
- GeoNormML declares an exact 1.1.0 dependency and exercises real profile outputs
  through feature preparation, preprocessing and a synthetic prediction fixture.

See the [profile validation report](validacion_perfiles_20261026.md),
[expanded tests](pruebas_ampliadas_20261026.md) and
[profile conventions](PERFILES_CIPW.md). These reports retain their original
dates, inputs and interpretation limits.

## Scientific limits

Normative mineral allocation is not measured modal mineralogy. Numerical
conservation can hold through free components and signed corrections while a
calculation remains incomplete; inspect status and warnings. Profile choice,
iron policy, carbonate assumptions and apatite conventions are part of the
contract, not interchangeable implementation details.

A complete external comparison of every accessory/minor branch and extreme
composition remains open. Existing pyrolite comparisons are controlled numerical
comparisons, not independent certification of every phase or of petrographic
truth. Reference cases with published inputs and phase results are required to
extend that evidence. Better closure does not establish better ML accuracy.

## Delivery and reproducibility

Version 1.0.0 and the congress-era 0.1.1 retain their history. The 1.1.0 release
has distinct artifacts and hashes; do not overwrite old PyPI distributions or
reinterpret historical training features as outputs of the corrected engine.
Follow the [publication checklist](PUBLISHING.md), including testing the built
wheel and extracted source distribution.

GeoNormML is a separate consumer. Its adopted plutonic v5 contract uses
Verma2003 1.0, fixed ferric fraction 0.15, calcite assumption and Ap + FAp.
GeoNormPy itself supplies no fitted rock classifier and makes no claim of
externally validated ML predictions.
