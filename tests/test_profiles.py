"""Published-number, conservation and integration tests for named profiles."""

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from geonormpy import available_profiles, cipw, cipw_safe
from geonormpy.cli import main
from geonormpy.core.iron import apply_iron_policy
from geonormpy.norms.batch import calculate_cipw_dataframe
from geonormpy.norms.revised import MASSES
from geonormpy.workflow import process_batch

NEW_PROFILES = ("verma2003", "pruseth2009")
SAMPLE = {"SiO2": 60, "TiO2": .5, "Al2O3": 16, "FeO": 6,
          "Fe2O3": 1, "MgO": 3, "CaO": 5, "Na2O": 4, "K2O": 4, "P2O5": .1}


@pytest.mark.parametrize("case", json.loads((Path(__file__).parent / "fixtures/legacy_profile_reference.json").read_text())["records"])
def test_legacy_profile_matches_frozen_pre_profile_kernel(case):
    result = cipw(case["input"], debug=True)
    expected = case["result"]
    for key in ("minerals_moles", "minerals_wtpercent", "residual_oxides_moles", "residual_oxides_wt"):
        assert result[key] == pytest.approx(expected[key], abs=1e-12)
    for key in ("mass_balance_error", "total_mass_sum"):
        assert result[key] == pytest.approx(expected[key], abs=1e-12)
    for key, value in expected["flags"].items():
        assert result["flags"][key] == value


def test_default_is_legacy_and_registry_cannot_be_mutated():
    registry = available_profiles()
    assert registry["default"] == "extended_cipw_v3"
    assert set(registry["profiles"]) == {"extended_cipw_v3", *NEW_PROFILES}
    registry["profiles"]["verma2003"]["version"] = "corrupt"
    assert available_profiles()["profiles"]["verma2003"]["version"] == "1.0"


@pytest.mark.parametrize("profile", NEW_PROFILES)
def test_profiles_preserve_input_close_mass_and_serialize(profile):
    source = copy.deepcopy(SAMPLE)
    result = cipw(source, profile=profile, iron_policy="measured", strict=True, debug=True)
    assert source == SAMPLE
    assert result["flags"]["calculation_complete"]
    assert result["mass_balance_error"] < 1e-10
    assert result["mass_balance"]["accounted_sum"] == pytest.approx(100, abs=1e-10)
    metadata = result["calculation_metadata"]
    assert metadata["profile"] == profile
    assert metadata["iron_policy_applied"] == "measured"
    assert metadata["iron_parameters"] == {}
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("profile", NEW_PROFILES)
@pytest.mark.parametrize("phase,components", [
    ("Q", {"SiO2": 1}), ("Cor", {"Al2O3": 1}),
    ("Or", {"K2O": .5, "Al2O3": .5, "SiO2": 3}),
    ("Ab", {"Na2O": .5, "Al2O3": .5, "SiO2": 3}),
    ("An", {"CaO": 1, "Al2O3": 1, "SiO2": 2}),
    ("Di", {"CaO": 1, "MgO": 1, "SiO2": 2}),
    ("Hd", {"CaO": 1, "FeO": 1, "SiO2": 2}),
    ("En", {"MgO": 1, "SiO2": 1}), ("Fs", {"FeO": 1, "SiO2": 1}),
    ("Fo", {"MgO": 2, "SiO2": 1}), ("Fa", {"FeO": 2, "SiO2": 1}),
    ("Cs", {"CaO": 2, "SiO2": 1}), ("Mt", {"FeO": 1, "Fe2O3": 1}),
    ("Hm", {"Fe2O3": 1}), ("Ilm", {"FeO": 1, "TiO2": 1}),
    ("Tn", {"CaO": 1, "TiO2": 1, "SiO2": 1}),
    ("Pf", {"CaO": 1, "TiO2": 1}), ("Ru", {"TiO2": 1}),
    ("Z", {"ZrO2": 1, "SiO2": 1}), ("Cm", {"Cr2O3": 1, "FeO": 1}),
    ("Ac", {"Na2O": .5, "Fe2O3": .5, "SiO2": 2}),
    ("Ne", {"Na2O": .5, "Al2O3": .5, "SiO2": 1}),
    ("Le", {"K2O": .5, "Al2O3": .5, "SiO2": 2}),
    ("Kp", {"K2O": .5, "Al2O3": .5, "SiO2": 1}),
    ("Cc", {"CaO": 1, "CO2": 1}),
])
def test_stoichiometric_phases(profile, phase, components):
    sample = {oxide: amount * MASSES[oxide] for oxide, amount in components.items()}
    result = cipw(sample, profile=profile, strict=True, debug=True)
    assert set(result["minerals_moles"]) == {phase}
    assert result["minerals_wtpercent"][phase] == pytest.approx(100, abs=1e-9)
    assert result["mass_balance_error"] < 1e-9


@pytest.mark.parametrize("phase,sample,oxygen", [
    ("Hl", {"Na2O": .5 * MASSES["Na2O"], "Cl": MASSES["Cl"]}, .5),
    ("Fl", {"CaO": MASSES["CaO"], "F": 2 * MASSES["F"]}, 1),
    ("Py", {"FeO": MASSES["FeO"], "S": 2 * MASSES["S"]}, 1),
])
def test_oxygen_is_reported_rather_than_renormalizing_minerals(phase, sample, oxygen):
    result = cipw(sample, profile="verma2003", strict=True)
    scale = 100 / sum(sample.values())
    assert set(result["minerals_moles"]) == {phase}
    assert result["total_mass_sum"] < 100
    assert result["free_components_wtpercent"]["O"] == pytest.approx(oxygen * scale * 15.9994)
    assert result["mass_balance_error"] < 1e-10
    assert not result["flags"]["mass_balance_warning"]


def test_mixed_apatite_uses_measured_f_before_fluorite_and_carbonate():
    sample = {"CaO": 10 * MASSES["CaO"], "P2O5": 3 * MASSES["P2O5"], "F": MASSES["F"]}
    result = cipw(sample, profile="verma2003", strict=True)
    assert set(result["minerals_moles"]) == {"Ap", "FAp"}
    assert result["minerals_moles"]["Ap"] / result["minerals_moles"]["FAp"] == pytest.approx(3)
    assert result["mass_balance_error"] < 1e-10
    sample["CO2"] = MASSES["CO2"]
    result = cipw(sample, profile="verma2003")
    assert "Cc" not in result["minerals_moles"]
    assert result["free_components_wtpercent"]["CO2"] > 0


def test_pruseth_normative_fluorapatite_is_audited_without_measured_f():
    sample = {"CaO": 10 * MASSES["CaO"], "P2O5": 3 * MASSES["P2O5"]}
    result = cipw(sample, profile="pruseth2009", strict=True)
    assert set(result["minerals_moles"]) == {"FAp"}
    assert result["total_mass_sum"] > 100
    assert result["free_components_wtpercent"]["normative_F_correction"] < 0
    assert result["mass_balance"]["accounted_sum"] == pytest.approx(100)


def test_pruseth_reproduces_published_ultrabasic_example():
    # Pruseth (2009), pp. 104-110. Published values are unnormalized 99.72 wt%.
    sample = {"SiO2": 28.03, "TiO2": .97, "Al2O3": 7.84, "FeO": 57.27,
              "Fe2O3": 0, "MgO": .5, "CaO": 4.27, "K2O": .45, "P2O5": .39}
    result = cipw(sample, profile="pruseth2009", iron_policy="measured", strict=True)
    norm = result["minerals_wtpercent"]
    published = {"Cor": 5.669607, "An": 4.592971, "Ilm": 1.842577,
                 "FAp": .923732, "Cs": 4.347064, "Kp": 1.511175}
    for phase, value in published.items():
        assert norm[phase] * .9972 == pytest.approx(value, abs=2e-5)
    assert (norm["Fo"] + norm["Fa"]) * .9972 == pytest.approx(80.85302, abs=3e-5)
    assert result["mass_balance_error"] < 1e-10
    assert not cipw(sample, profile="verma2003")["flags"]["calculation_complete"]


@pytest.mark.parametrize("profile", NEW_PROFILES)
def test_free_phosphorus_is_retained_and_not_silently_lost(profile):
    result = cipw({"SiO2": 60, "P2O5": 1}, profile=profile)
    assert result["free_components_wtpercent"]["P2O5"] == pytest.approx(100 / 61)
    assert result["flags"]["free_components_present"]
    assert result["mass_balance_error"] < 1e-10


@pytest.mark.parametrize("profile", NEW_PROFILES)
@pytest.mark.parametrize("factor", [1e-250, 1e250])
def test_new_profiles_are_scale_invariant(profile, factor):
    baseline = cipw(SAMPLE, profile=profile)
    result = cipw({k: v * factor for k, v in SAMPLE.items()}, profile=profile)
    assert result["minerals_wtpercent"] == pytest.approx(baseline["minerals_wtpercent"], abs=1e-10)


@pytest.mark.parametrize("profile", NEW_PROFILES)
@pytest.mark.parametrize("oxide", ["MnO", "NiO", "SrO", "BaO"])
def test_minor_substitutions_preserve_mass_instead_of_converting_weight(profile, oxide):
    sample = dict(SAMPLE, **{oxide: 1.25})
    result = cipw(sample, profile=profile, strict=True)
    assert result["mass_balance_error"] < 1e-9
    assert result["mass_balance"]["inventory_sum_including_silica_deficit"] == pytest.approx(100, abs=1e-9)


@pytest.mark.parametrize("oxide", ["CoO", "Rb2O", "Cs2O", "Li2O", "V2O3"])
def test_verma_additional_substitutions(oxide):
    result = cipw(dict(SAMPLE, **{oxide: .1}), profile="verma2003", strict=True)
    assert result["mass_balance_error"] < 1e-9
    rejected = cipw_safe(dict(SAMPLE, **{oxide: .1}), profile="pruseth2009")
    assert rejected["error"]["code"] == "unsupported_profile_oxide"


@pytest.mark.parametrize("policy", ["fixed", "le_maitre_volcanic", "le_maitre_plutonic"])
def test_iron_policy_conserves_atoms_and_reports_assumptions(policy):
    chemistry = {"SiO2": 60, "Na2O": 4, "K2O": 4, "FeOT": 10}
    output, flags = apply_iron_policy(chemistry, policy, .2, MASSES)
    assert output["FeO"] / MASSES["FeO"] + 2 * output["Fe2O3"] / MASSES["Fe2O3"] == pytest.approx(10 / MASSES["FeO"])
    assert flags["iron_policy_applied"] == policy
    if policy == "fixed":
        assert flags["iron_parameters"]["fe3_fraction"] == .2
    else:
        expected = .93 - .0042 * 60 - .022 * 8 if policy.endswith("volcanic") else .88 - .0016 * 60 - .027 * 8
        assert output["FeO"] / (output["FeO"] + output["Fe2O3"]) == pytest.approx(expected)


@pytest.mark.parametrize("profile", ["extended_cipw_v3", *NEW_PROFILES])
def test_measured_policy_does_not_guess_missing_speciation(profile):
    result = cipw_safe({"SiO2": 60, "FeOT": 10}, profile=profile, iron_policy="measured")
    assert not result["ok"]
    assert result["error"]["code"] == "missing_iron_speciation"


@pytest.mark.parametrize("options", [{"profile": "imaginary"}, {"iron_policy": "imaginary"},
    {"profile": True}, {"carbonate_mode": True}, {"profile": "pruseth2009", "carbonate_mode": "free"}])
def test_invalid_profiles_do_not_silently_fall_back(options):
    assert cipw_safe(SAMPLE, **options)["error"]["code"] == "invalid_option"


def test_batch_keeps_profile_metadata_for_both_good_and_failed_rows():
    frame = calculate_cipw_dataframe(pd.DataFrame([SAMPLE, dict(SAMPLE, SiO2=-1)]), profile="verma2003", iron_policy="measured")
    assert list(frame.norm_profile) == ["verma2003", "verma2003"]
    assert pd.isna(frame.loc[1, "Q"])
    assert json.loads(frame.loc[0, "calculation_metadata_json"])["iron_policy_applied"] == "measured"
    assert json.loads(frame.loc[1, "calculation_metadata_json"])["profile"] == "verma2003"


def test_cli_profile_override_is_saved_without_modifying_yaml(tmp_path, capsys):
    source = tmp_path / "source.csv"
    pd.DataFrame([SAMPLE]).to_csv(source, index=False)
    output = tmp_path / "output.csv"
    config = tmp_path / "config.yaml"
    content = json.dumps({"input": {"file": str(source)}, "output": {"file": str(output)},
                          "calculation": {"profile": "extended_cipw_v3"}})
    config.write_text(content, encoding="utf-8")
    assert main(["run", "--config", str(config), "--profile", "pruseth2009", "--iron-policy", "measured", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    assert config.read_text(encoding="utf-8") == content
    assert pd.read_csv(output).norm_profile.iloc[0] == "pruseth2009"


def test_cli_profiles_json(capsys):
    assert main(["profiles", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "pruseth2009" in payload["result"]["profiles"]


def test_misspelled_configuration_option_is_rejected_before_output(tmp_path):
    config = tmp_path / "wrong.yaml"
    config.write_text(json.dumps({"input": {"file": "absent.csv"}, "output": {"file": "output.csv"},
                                 "calculation": {"prfile": "verma2003"}}))
    with pytest.raises(ValueError, match="Unknown calculation"):
        process_batch(config)
