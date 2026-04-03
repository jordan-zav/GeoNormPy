from geonormpy.cli import main


def test_schema_command(capsys):
    assert main(["schema"]) == 0
    output = capsys.readouterr().out
    assert "Supported oxide columns:" in output
    assert "Normative mineral output columns:" in output


def test_make_template_command(tmp_path):
    output_path = tmp_path / "template.csv"
    assert main(["make-template", "--output", str(output_path)]) == 0
    assert output_path.exists()


def test_make_config_command(tmp_path):
    output_path = tmp_path / "workflow.yaml"
    assert main(["make-config", "--output", str(output_path)]) == 0
    assert output_path.exists()


def test_validate_command_success(capsys):
    assert main(["validate", "--input", "data/test_data.csv"]) == 0
    output = capsys.readouterr().out
    assert "Validation passed." in output
