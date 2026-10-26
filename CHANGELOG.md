# Changelog

## [1.1.0] - 2026-10-26

- Add selectable Verma 2003 sequential and Pruseth 2009 matrix-based CIPW profiles.
- Retain extended_cipw_v3 by default, with a numerical correction at the pyroxene saturation boundary.
- Add measured, fixed-fraction and Le Maitre iron policies independent of profile selection.
- Record versioned calculation metadata in API results and CSV rows; expose profiles and overrides in the CLI.
- Account for substituted components, free components, displaced oxygen and Pruseth normative fluorine explicitly in revised profiles.
- Document profile-specific input sets, common preprocessing conventions and carbonate assumptions.
- Add frozen compatibility results, independent component inventories, silica sweeps, input-safety and installed-wheel checks.
- Include benchmark runners and summaries; preserve all original GeoNormML inputs and models.
- Package JSON regression fixtures in the source distribution so its test suite is reproducible.

## [1.0.0] - 2026-10-25

- First stable release, incorporating the changes prepared as unreleased 0.1.2.

- Validate oxide values and calculation options; keep metadata out of the norm.
- Correct the silica-deficiency phase sequence and calcium priority for anorthite.
- Add perovskite and dicalcium silicate transformations; expose incomplete allocations.
- Preserve unknown mineral abundances in failed batch rows and parse numeric strings.
- Make the installed CLI self-contained through geonormpy.workflow.
- Add structured library errors, safe JSON results, CLI JSON output and per-row error codes.
- Write batch outputs atomically, preserving previous output if writing fails.
- Add stoichiometric phase, oxide-inventory, input-safety and installed-wheel regressions.

## [0.1.1] - 2026-04-06
- Cleaned tracked build artifacts and cached files from the repository.
- Aligned package metadata for release packaging and citation records.
- Verified the test suite and distribution build workflow for publication.

## [0.1.0] - Initial design
- Defined CIPW normative algorithm
- Project architecture established
