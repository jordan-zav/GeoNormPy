from pathlib import Path

from run_GeoNormPy import DEFAULT_CONFIG_PATH, load_workflow_config, process_batch


def test_workflow_config_exists():
    assert Path(DEFAULT_CONFIG_PATH).exists()


def test_workflow_config_has_expected_keys():
    config = load_workflow_config()

    assert "input" in config
    assert "calculation" in config
    assert "workflow" in config
    assert "output" in config
    assert "oxide_columns" in config["input"]


def test_process_batch_from_config(tmp_path):
    output_file = tmp_path / "normative_results.csv"

    config = load_workflow_config()
    config["output"]["file"] = str(output_file)

    custom_config = tmp_path / "workflow.yaml"
    custom_config.write_text(
        "\n".join(
            [
                "input:",
                f"  file: {config['input']['file']}",
                "  id_columns:",
                "    - Sample_ID",
                "    - Notes",
                "  oxide_columns:",
            ]
            + [f"    - {oxide}" for oxide in config["input"]["oxide_columns"]]
            + [
                "calculation:",
                "  method: cipw",
                "  fe3_fraction: 0.15",
                "  strict: false",
                "workflow:",
                "  steps:",
                "    - read_csv",
                "    - select_valid_columns",
                "    - run_cipw",
                "    - append_id_columns",
                "    - export_csv",
                "output:",
                f"  file: {output_file.as_posix()}",
            ]
        ),
        encoding="utf-8",
    )

    process_batch(custom_config)

    assert output_file.exists()
