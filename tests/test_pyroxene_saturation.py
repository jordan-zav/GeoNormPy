import pytest

from geonormpy.core.constants import MOLAR_MASS
from geonormpy.norms.cipw import cipw


@pytest.mark.parametrize("mg_fraction", [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
def test_stoichiometric_clinopyroxenes_are_silica_saturated(mg_fraction):
    sample = {
        "SiO2": 2 * MOLAR_MASS["SiO2"],
        "CaO": MOLAR_MASS["CaO"],
        "MgO": mg_fraction * MOLAR_MASS["MgO"],
        "FeO": (1 - mg_fraction) * MOLAR_MASS["FeO"],
        "Fe2O3": 0.0,
    }
    result = cipw(sample, strict=True, debug=True)

    assert result["flags"]["silica_saturation"] == "saturated"
    assert result["flags"]["calculation_complete"]
    assert result["residual_oxides_moles"] == {}
    assert set(result["minerals_moles"]) <= {"Di", "Hd"}
    di = result["minerals_moles"].get("Di", 0)
    hd = result["minerals_moles"].get("Hd", 0)
    assert di / (di + hd) == pytest.approx(mg_fraction, abs=1e-14)
