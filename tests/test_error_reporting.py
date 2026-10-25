import json

import pandas as pd
import pytest

from geonormpy import GeoNormPyError, cipw, cipw_safe
from geonormpy.cli import main
from geonormpy.workflow import process_batch
from geonormpy.norms.batch import calculate_cipw_dataframe


@pytest.mark.parametrize('bad', [True, float('nan'), float('inf'), -1, 'invalid'])
def test_safe_api_returns_error_code_and_field_as_strict_json(bad):
    result = cipw_safe({'SiO2': bad})
    assert not result['ok'] and result['result'] is None
    assert result['error']['code'] == 'invalid_measurement'
    assert result['error']['field'] == 'SiO2'
    json.dumps(result, allow_nan=False)


def test_raising_api_preserves_value_error_compatibility_and_structured_details():
    with pytest.raises(ValueError) as caught:
        cipw({'SiO2': -1})
    assert isinstance(caught.value, GeoNormPyError)
    assert caught.value.to_dict()['field'] == 'SiO2'
    import pickle
    assert pickle.loads(pickle.dumps(caught.value)).to_dict() == caught.value.to_dict()


def test_safe_api_rejects_incomplete_allocation_and_accepts_quartz():
    assert cipw_safe({'SiO2': 30, 'MgO': 25, 'CaO': 45})['error']['code'] == 'allocation_incomplete'
    good = cipw_safe({'SiO2': 100})
    assert good['ok'] and good['result']['minerals_wtpercent'] == {'Q': 100}


@pytest.mark.parametrize('args', [['--json', 'run', '--config', 'missing-file.yaml'],
    ['run', '--config', 'missing-file.yaml', '--json']])
def test_cli_json_failure_is_one_valid_json_object(args, capsys):
    assert main(args) == 1
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload['error']['code'] == 'file_not_found'
    assert output.err == ''


def test_cli_human_error_is_on_stderr_without_traceback(capsys):
    assert main(['run', '--config', 'missing-file.yaml']) == 1
    output = capsys.readouterr()
    assert 'Error [file_not_found]' in output.err
    assert 'Traceback' not in output.err


def test_cli_argument_errors_can_be_json(capsys):
    assert main(['--json', 'no-such-command']) == 1
    assert json.loads(capsys.readouterr().out)['error']['code'] == 'invalid_arguments'


def test_cli_json_schema_has_no_extra_console_lines(capsys):
    assert main(['schema', '--json']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['ok']
    assert 'SiO2' in payload['result']['oxide_columns']


@pytest.mark.parametrize('option', ['--help', '--version'])
def test_json_help_and_version_remain_machine_readable(option, capsys):
    assert main(['--json', option]) == 0
    assert json.loads(capsys.readouterr().out)['ok']


def make_config(tmp_path):
    path = tmp_path / 'input.csv'
    pd.DataFrame([{'Sample_ID': 'ok', 'SiO2': 100}, {'Sample_ID': 'bad', 'SiO2': -1}]).to_csv(path, index=False)
    output = tmp_path / 'output.csv'
    config = tmp_path / 'config.yaml'
    config.write_text(json.dumps({'input': {'file': str(path), 'id_columns': ['Sample_ID']},
        'output': {'file': str(output)}}), encoding='utf-8')
    return config, output


def test_batch_reports_json_per_sample_and_nonzero_cli_status_for_partial_failure(tmp_path, capsys):
    config, path = make_config(tmp_path)
    assert main(['run', '--config', str(config), '--json']) == 1
    response = json.loads(capsys.readouterr().out)
    assert response['result']['failed'] == 1
    assert response['result']['errors'][0]['sample_id'] == 'bad'
    assert response['result']['errors'][0]['error']['field'] == 'SiO2'
    rows = pd.read_csv(path)
    assert rows.loc[0, 'Q'] == 100
    assert pd.isna(rows.loc[1, 'Q'])
    assert rows.loc[1, 'error_code'] == 'invalid_measurement'
    assert json.loads(rows.loc[1, 'error_json'])['field'] == 'SiO2'


def test_console_batch_errors_identify_the_sample_and_field(tmp_path, capsys):
    config, _ = make_config(tmp_path)
    assert main(['run', '--config', str(config)]) == 1
    output = capsys.readouterr()
    assert 'Sample bad' in output.err
    assert '[invalid_measurement]' in output.err
    assert 'SiO2' in output.err
    assert 'Traceback' not in output.err


def test_failed_output_write_preserves_existing_output(tmp_path, monkeypatch):
    config, output = make_config(tmp_path)
    output.write_text('previous output', encoding='utf-8')
    def fail(frame, path, **kwargs):
        path.write_text('partial data', encoding='utf-8')
        raise OSError('disk full')
    monkeypatch.setattr(pd.DataFrame, 'to_csv', fail)
    with pytest.raises(OSError, match='disk full'):
        process_batch(config)
    assert output.read_text(encoding='utf-8') == 'previous output'
    assert not list(tmp_path.glob('.output.csv.*.tmp'))


def test_empty_frame_keeps_diagnostic_columns():
    result = calculate_cipw_dataframe(pd.DataFrame(columns=['SiO2']))
    assert result.empty
    assert 'error_json' in result.columns


def test_titanite_is_provisional_even_when_silica_already_has_a_deficit():
    result = cipw({'SiO2': 2*60.083, 'CaO': 2*56.077, 'Al2O3': 101.961, 'TiO2': 79.866})
    assert 'An' in result['minerals_moles']
    assert 'Pf' in result['minerals_moles']
    assert result['flags']['calculation_complete']
