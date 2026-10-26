"""Versioned calculation profiles and orthogonal iron policies."""

from copy import deepcopy

from ..core.iron import IRON_POLICIES
from ..errors import GeoNormPyError

DEFAULT_PROFILE = "extended_cipw_v3"
PROFILES = {
    DEFAULT_PROFILE: {
        "version": "3.1", "algorithm": "legacy_sequential",
        "description": "GeoNormPy 1.0 conventions with the numerical pyroxene correction.",
        "reference": "GeoNormPy 1.0.0; local numerical correction 2026-10-25",
    },
    "verma2003": {
        "version": "1.0", "algorithm": "revised_sequential",
        "description": "Revised sequential norm, variable component masses, free oxygen and mixed apatite.",
        "reference": "Verma et al. (2003), A revised CIPW norm, pp. 197-216",
    },
    "pruseth2009": {
        "version": "1.0", "algorithm": "matrix_provisional_and_reactions",
        "description": "Matrix-derived provisional minerals, normative fluorapatite and extreme-deficit extension.",
        "reference": "Pruseth (2009), doi:10.1007/s12040-009-0010-0",
    },
}
PROFILE_ALIASES = {"legacy": DEFAULT_PROFILE, "current": DEFAULT_PROFILE,
                   "verma_2003": "verma2003", "pruseth_2009": "pruseth2009"}
CARBONATE_MODES = ("calcite", "sodium_carbonate", "free")


def resolve_profile(profile):
    if not isinstance(profile, str):
        raise GeoNormPyError("invalid_option", "profile must be a profile name.", field="profile")
    name = PROFILE_ALIASES.get(profile, profile)
    if name not in PROFILES:
        raise GeoNormPyError("invalid_option", f"Unknown CIPW profile: {profile}. Choose {', '.join(PROFILES)}.", field="profile")
    return name


def validate_options(profile, iron_policy, carbonate_mode):
    name = resolve_profile(profile)
    if not isinstance(iron_policy, str) or iron_policy not in IRON_POLICIES:
        raise GeoNormPyError("invalid_option", f"Choose an iron_policy from {IRON_POLICIES}.", field="iron_policy")
    if not isinstance(carbonate_mode, str) or carbonate_mode not in CARBONATE_MODES:
        raise GeoNormPyError("invalid_option", f"Choose a carbonate_mode from {CARBONATE_MODES}.", field="carbonate_mode")
    if name != "verma2003" and carbonate_mode != "calcite":
        raise GeoNormPyError("invalid_option", "This carbonate option belongs to verma2003; other profiles use calcite.", field="carbonate_mode")
    return name


def available_profiles():
    """Return detached, JSON-serializable descriptions for API and CLI clients."""
    from ..core.constants import MOLAR_MASS
    from .revised import MASSES, PRUSETH_UNSUPPORTED
    descriptions = deepcopy(PROFILES)
    descriptions[DEFAULT_PROFILE]["supported_oxides"] = sorted(set(MOLAR_MASS) | {"FeOT"})
    descriptions["verma2003"]["supported_oxides"] = sorted(set(MASSES) | {"FeOT", "Fe2O3T"})
    descriptions["pruseth2009"]["supported_oxides"] = sorted((set(MASSES) - PRUSETH_UNSUPPORTED) | {"FeOT", "Fe2O3T"})
    for name in descriptions:
        descriptions[name]["validation_status"] = "numerically_benchmarked_not_petrologically_certified"
        descriptions[name]["input_basis"] = "Common 100 wt% basis; no paper-specific preprocessing or intermediate rounding."
    descriptions["verma2003"]["limitations"] = ["No modal cancrinite estimator; carbonate allocation is an explicit assumption."]
    descriptions["pruseth2009"]["limitations"] = ["Normative fluorapatite requires a signed fluorine mass correction."]
    return {"default": DEFAULT_PROFILE, "profiles": descriptions,
            "iron_policies": list(IRON_POLICIES), "carbonate_modes_verma2003": list(CARBONATE_MODES)}
