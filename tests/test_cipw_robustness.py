from geonormpy.norms.cipw import cipw


def test_no_negative_minerals():
    sample = {
        "SiO2": 50,
        "Al2O3": 15,
        "FeOT": 10,
        "MgO": 8,
        "CaO": 10,
        "Na2O": 3,
        "K2O": 1,
    }

    res = cipw(sample)
    for value in res["minerals_moles"].values():
        assert value >= 0.0


def test_q_ne_le_kp_exclusive():
    sample = {
        "SiO2": 44,
        "Al2O3": 13,
        "FeOT": 9,
        "MgO": 6,
        "CaO": 11,
        "Na2O": 5,
        "K2O": 3,
    }

    res = cipw(sample)
    wt = res["minerals_wtpercent"]

    has_quartz = "Q" in wt
    has_feldspathoid = any(k in wt for k in ["Ne", "Le", "Kp"])

    assert not (has_quartz and has_feldspathoid)


def test_missing_minor_oxides():
    sample = {
        "SiO2": 60,
        "Al2O3": 16,
        "FeOT": 7,
        "MgO": 3,
        "CaO": 5,
        "Na2O": 4,
        "K2O": 4,
    }

    res = cipw(sample)
    assert res["mass_balance_error"] < 2e-3


def test_exact_silica_saturation():
    sample = {
        "SiO2": 55,
        "Al2O3": 17,
        "FeOT": 7,
        "MgO": 4,
        "CaO": 6,
        "Na2O": 4,
        "K2O": 2,
    }

    res = cipw(sample)
    wt = res["minerals_wtpercent"]
    saturation = res["flags"]["silica_saturation"]

    assert saturation in ["saturated", "oversaturated"]

    if saturation == "saturated":
        assert "Q" not in wt
        assert "Ne" not in wt
        assert "Le" not in wt
        assert "Kp" not in wt
        assert "Fo" not in wt
        assert "Fa" not in wt
