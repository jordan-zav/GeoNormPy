from geonormpy.norms.cipw import cipw

TOL = 1e-3


def assert_close(a, b, tol=TOL):
    assert abs(a - b) < tol


# ======================================================
# TEST 1 - FELSIC GRANITE (OVERSATURATED)
# ======================================================
def test_granite_oversaturated():
    granite = {
        "SiO2": 72.5,
        "Al2O3": 13.5,
        "FeOT": 2.5,
        "MgO": 0.5,
        "CaO": 1.8,
        "Na2O": 3.4,
        "K2O": 4.0,
        "TiO2": 0.3,
        "P2O5": 0.1,
    }

    res = cipw(granite)
    wt = res["minerals_wtpercent"]
    flags = res["flags"]

    assert "Q" in wt
    assert wt["Q"] > 20.0
    assert flags["silica_saturation"] == "oversaturated"

    assert "Ne" not in wt
    assert "Le" not in wt
    assert "Kp" not in wt

    assert flags["alumina_state"] in ["peraluminous", "metaluminous"]

    assert res["mass_balance_error"] < 1e-3


# ======================================================
# TEST 2 - SUBALKALINE BASALT (THOLEIITIC-LIKE)
# ======================================================
def test_basalt_subalkaline():
    basalt = {
        "SiO2": 49.0,
        "Al2O3": 14.5,
        "FeOT": 10.5,
        "MgO": 7.5,
        "CaO": 10.0,
        "Na2O": 2.5,
        "K2O": 0.8,
        "TiO2": 1.5,
        "P2O5": 0.2,
    }

    res = cipw(basalt)
    wt = res["minerals_wtpercent"]
    flags = res["flags"]

    assert any(k in wt for k in ["Di", "Hd", "En", "Fs", "Fo", "Fa"])

    if "Q" in wt:
        assert wt["Q"] < 5.0

    assert "Ne" not in wt
    assert "Le" not in wt

    assert flags["silica_saturation"] in ["saturated", "oversaturated", "undersaturated"]
    assert res["mass_balance_error"] < 2e-3


# ======================================================
# TEST 3 - ALKALINE MAFIC ROCK (NEPHELINITE-LIKE)
# ======================================================
def test_nephelinite_like():
    nephelinite = {
        "SiO2": 42.0,
        "Al2O3": 14.0,
        "FeOT": 9.0,
        "MgO": 6.0,
        "CaO": 11.0,
        "Na2O": 5.5,
        "K2O": 3.0,
        "TiO2": 2.0,
        "P2O5": 0.6,
    }

    res = cipw(nephelinite)
    wt = res["minerals_wtpercent"]
    flags = res["flags"]

    assert flags["silica_saturation"] in ["saturated", "undersaturated"]

    if flags["silica_saturation"] == "undersaturated":
        assert any(k in wt for k in ["Ne", "Le", "Kp"])

    if any(k in wt for k in ["Ne", "Le", "Kp"]):
        assert "Q" not in wt

    assert res["mass_balance_error"] < 1e-3


# ======================================================
# TEST 4 - HIERARCHICAL IRON HANDLING
# ======================================================
def test_iron_handling_flags():
    sample = {
        "SiO2": 55.0,
        "Al2O3": 16.0,
        "FeOT": 8.0,
        "MgO": 5.0,
        "CaO": 7.0,
        "Na2O": 3.0,
        "K2O": 2.0,
    }

    res = cipw(sample)
    flags = res["flags"]

    assert flags["iron_mode"] == "estimated_from_FeOT"
    assert flags["iron_warning"] is True
    assert isinstance(flags["warnings"], list)


# ======================================================
# TEST 5 - STRICT MODE MUST FAIL
# ======================================================
def test_strict_mode_fails_on_inconsistent_iron():
    bad_sample = {
        "SiO2": 55.0,
        "Al2O3": 16.0,
        "FeOT": 8.0,
        "FeO": 6.0,
        "MgO": 5.0,
        "CaO": 7.0,
        "Na2O": 3.0,
        "K2O": 2.0,
    }

    try:
        cipw(bad_sample, strict=True)
        assert False, "Expected ValueError for inconsistent iron input"
    except ValueError:
        assert True
