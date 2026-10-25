"""
EvOLve Test Suite — tests/test_geotechnical_physics.py
Validates physical landslide diagnostics and geotechnical building suitability scoring.
"""

from dashboard.backend.services.inference_service import (
    compute_landslide_diagnostics,
    compute_construction_suitability
)


def test_landslide_gentle_slope_low_risk():
    """Gentle slope (<10 deg) with healthy forest cover should yield Low landslide probability."""
    patch = {
        'slope_deg': 4.5,
        'treecover_pct': 88.0,
        'loss_rate': 0.002,
        'rainfall_90d_mm': 120.0,
    }
    diag = compute_landslide_diagnostics(patch)
    assert diag['risk_level'] == "Low"
    assert diag['probability'] < 0.25
    assert len(diag['recommended_mitigations']) > 0


def test_landslide_steep_slope_critical_risk():
    """Steep slope (>25 deg) with decayed canopy and torrential rain should yield High or Critical risk."""
    patch = {
        'slope_deg': 29.0,
        'treecover_pct': 22.0,
        'loss_rate': 0.08,
        'rainfall_90d_mm': 380.0,
    }
    diag = compute_landslide_diagnostics(patch)
    assert diag['risk_level'] in ["Critical", "High"]
    assert diag['probability'] >= 0.45
    assert any("shear stress" in r for r in diag['primary_reasons'])


def test_construction_suitability_gentle_slope():
    """Low incline (<10 deg) with low landslide risk must be SUITABLE_FOR_CONSTRUCTION."""
    patch = {
        'slope_deg': 4.0,
        'treecover_pct': 70.0,
        'loss_rate': 0.0,
    }
    ls_diag = {'probability': 0.08}
    res = compute_construction_suitability(patch, ls_diag, is_corridor_active=False)
    assert res['verdict'] == "SUITABLE_FOR_CONSTRUCTION"
    assert res['safety_score'] >= 72.0


def test_construction_suitability_moderate_slope():
    """Moderate incline (10-20 deg) must receive CONDITIONAL_RESTRICTED clearance with engineered mitigations."""
    patch = {
        'slope_deg': 14.5,
        'treecover_pct': 60.0,
        'loss_rate': 0.01,
    }
    ls_diag = {'probability': 0.28}
    res = compute_construction_suitability(patch, ls_diag, is_corridor_active=False)
    assert res['verdict'] == "CONDITIONAL_RESTRICTED"
    assert any("retaining walls" in act for act in res['mandatory_actions'])


def test_construction_suitability_steep_hazard_prohibited():
    """Steep mountain slope (>20 deg) or high landslide probability must be HAZARD_PROHIBITED."""
    patch = {
        'slope_deg': 24.0,
        'treecover_pct': 30.0,
        'loss_rate': 0.05,
    }
    ls_diag = {'probability': 0.62}
    res = compute_construction_suitability(patch, ls_diag, is_corridor_active=False)
    assert res['verdict'] == "HAZARD_PROHIBITED"
    assert any("moratorium" in act for act in res['mandatory_actions'])


def test_wildlife_corridor_active_penalty():
    """Active wildlife migration corridor triggers mandatory ecological deduction."""
    patch = {
        'slope_deg': 8.0,
        'treecover_pct': 65.0,
        'loss_rate': 0.0,
    }
    ls_diag = {'probability': 0.15}
    res_no_corridor = compute_construction_suitability(patch, ls_diag, is_corridor_active=False)
    res_with_corridor = compute_construction_suitability(patch, ls_diag, is_corridor_active=True)
    assert res_with_corridor['safety_score'] < res_no_corridor['safety_score']

