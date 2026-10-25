from copy import deepcopy
import json

import numpy as np
import pandas as pd
import pytest

from geonormpy.norms.cipw import cipw
from geonormpy.norms.batch import calculate_cipw_dataframe
from geonormpy.norms.cipw import ChemicalState, silica_desaturation


SAMPLE = {'SiO2': 60, 'Al2O3': 16, 'FeOT': 7, 'MgO': 3, 'CaO': 5, 'Na2O': 4, 'K2O': 4}


@pytest.mark.parametrize('bad', [True, np.bool_(True), float('nan'), float('inf'), -1, 'bad'])
def test_invalid_measurement_never_produces_a_norm(bad):
    with pytest.raises(ValueError):
        cipw(dict(SAMPLE, SiO2=bad))


@pytest.mark.parametrize('name', ['Sample_ID', 'Sr', 'LOI'])
def test_unknown_components_cannot_silently_dilute_normalization(name):
    with pytest.raises(ValueError, match='Unsupported'):
        cipw(dict(SAMPLE, **{name: 500}))


@pytest.mark.parametrize('name,value', [('mass_tol', -1), ('mass_tol', float('nan')), ('mass_tol', float('inf')),
    ('mass_tol', True), ('strict', 'false'), ('debug', 'false'), ('fe3_fraction', True)])
def test_invalid_calculation_options_are_rejected(name, value):
    with pytest.raises(ValueError):
        cipw(SAMPLE, **{name: value})


def test_batch_ignores_numeric_sample_identifiers_and_trace_metadata():
    plain = calculate_cipw_dataframe(pd.DataFrame([SAMPLE]))
    enriched = calculate_cipw_dataframe(pd.DataFrame([dict(SAMPLE, Sample_ID=2026, Sr=900)]))
    pd.testing.assert_frame_equal(plain, enriched)


def test_batch_parses_numeric_text_instead_of_dropping_chemistry():
    plain = calculate_cipw_dataframe(pd.DataFrame([SAMPLE]))
    text = calculate_cipw_dataframe(pd.DataFrame([{key: str(value) for key, value in SAMPLE.items()}]))
    pd.testing.assert_frame_equal(plain, text)


def test_failed_batch_row_does_not_look_like_measured_zero_mineralogy():
    result = calculate_cipw_dataframe(pd.DataFrame([SAMPLE, dict(SAMPLE, SiO2=-1)]))
    assert result.loc[0, 'Q'] > 0
    assert pd.isna(result.loc[1, 'Q'])
    assert result.loc[1, 'calc_error']


def test_input_is_immutable_and_valid_output_is_strict_json():
    sample = deepcopy(SAMPLE)
    result = cipw(sample, debug=True)
    assert sample == SAMPLE
    json.dumps(result, allow_nan=False)


def test_unresolved_silica_deficit_is_explicit_and_strict_calculation_refuses_it():
    sample = {'SiO2': 30, 'MgO': 25, 'CaO': 45}
    result = cipw(sample, debug=True)
    assert not result['flags']['calculation_complete']
    assert result['residual_oxides_moles']['SiO2'] < 0
    with pytest.raises(ValueError, match='incomplete'):
        cipw(sample, strict=True)


@pytest.mark.parametrize('oxides,mineral', [
    ({'SiO2': 60.083}, 'Q'),
    ({'Al2O3': 101.961}, 'Cor'),
    ({'SiO2': 6*60.083, 'Al2O3': 101.961, 'K2O': 94.196}, 'Or'),
    ({'SiO2': 6*60.083, 'Al2O3': 101.961, 'Na2O': 61.979}, 'Ab'),
    ({'SiO2': 2*60.083, 'Al2O3': 101.961, 'CaO': 56.077}, 'An'),
    ({'SiO2': 2*60.083, 'MgO': 40.304, 'CaO': 56.077}, 'Di'),
    ({'SiO2': 60.083, 'MgO': 2*40.304}, 'Fo'),
])
def test_stoichiometric_endmembers_produce_expected_phases(oxides, mineral):
    result = cipw(oxides)
    assert result['minerals_wtpercent'][mineral] == pytest.approx(100, abs=.006)
    assert all(name == mineral or amount < 1e-8 for name, amount in result['minerals_wtpercent'].items())


@pytest.mark.parametrize('deficit,expected', [
    (1, {'Or': 1, 'Ab': .5, 'Ne': .5}),
    (3, {'Le': 1, 'Ne': 1}),
    (4, {'Kp': 1, 'Ne': 1}),
])
def test_feldspathoid_sequence_conserves_formula_moles(deficit, expected):
    state = ChemicalState({'SiO2': -deficit})
    state.minerals = {'Or': 1, 'Ab': 1}
    flags = {}
    silica_desaturation(state, flags)
    assert state.minerals == pytest.approx(expected)
    assert flags['residual_silica_deficit_moles'] == 0


def test_larnite_can_close_a_calcium_silicate_deficit():
    result = cipw({'SiO2': 60.083, 'CaO': 2*56.077})
    assert result['minerals_wtpercent'] == pytest.approx({'Cs': 100}, abs=.001)
    assert result['flags']['calculation_complete']


def test_anorthite_has_priority_over_titanite_for_calcium():
    result = cipw({'SiO2': 3*60.083, 'CaO': 56.077, 'Al2O3': 101.961, 'TiO2': 79.866})
    assert 'An' in result['minerals_moles']
    assert 'Ru' in result['minerals_moles']
    assert 'Tn' not in result['minerals_moles']


def test_sphene_can_release_silica_as_perovskite():
    state = ChemicalState({'SiO2': -1})
    state.minerals = {'Tn': 1}
    flags = {}
    silica_desaturation(state, flags)
    assert state.minerals == {'Pf': 1}
    assert flags['residual_silica_deficit_moles'] == 0


@pytest.mark.parametrize('factor', [1e-300, 1e300])
def test_normalization_is_scale_invariant_without_overflow(factor):
    baseline = cipw(SAMPLE)
    scaled = cipw({key: value*factor for key, value in SAMPLE.items()})
    assert scaled['minerals_wtpercent'] == pytest.approx(baseline['minerals_wtpercent'])
