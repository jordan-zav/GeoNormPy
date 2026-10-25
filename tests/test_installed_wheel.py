import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_installed_wheel_cli_runs_without_checkout(tmp_path):
    wheel = os.environ.get('GEONORMPY_AUDIT_WHEEL')
    if not wheel:
        pytest.skip('Set GEONORMPY_AUDIT_WHEEL to test a built distribution')
    sample = tmp_path / 'input.csv'
    sample.write_text('Sample_ID,SiO2,Al2O3,FeOT,MgO,CaO,Na2O,K2O\nA,60,16,7,3,5,4,4\n', encoding='utf-8')
    output = tmp_path / 'output.csv'
    config = tmp_path / 'workflow.yaml'
    # JSON is valid YAML and avoids Windows path escaping ambiguity.
    config.write_text(json.dumps({'input': {'file': str(sample), 'oxide_columns':
        ['SiO2', 'Al2O3', 'FeOT', 'MgO', 'CaO', 'Na2O', 'K2O'], 'id_columns': ['Sample_ID']},
        'output': {'file': str(output)}}), encoding='utf-8')
    code = ('import sys;sys.path.insert(0,sys.argv[1]);'
        'from geonormpy.cli import main;raise SystemExit(main(["run","--config",sys.argv[2],"--json"]))')
    process = subprocess.run([sys.executable, '-I', '-c', code, str(Path(wheel).resolve()), str(config)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stdout + process.stderr
    assert json.loads(process.stdout)['ok']
    assert output.exists()
    assert 'Sample_ID' in output.read_text(encoding='utf-8')
