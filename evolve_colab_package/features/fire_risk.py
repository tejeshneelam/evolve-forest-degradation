"""
EvOLve — features/fire_risk.py
Fire Risk Prediction Map using SWIR bands + NDVI + seasonal patterns.

Fire risk = function of:
  - Low NDVI (dry / stressed vegetation)
  - High SWIR (B11/B12) reflectance = dry biomass
  - Dry season months (Jan–May for Wayanad)
  - Degraded patches (already stressed forest)

Output: fire_risk score 0.0–1.0 per patch per recent month
"""

import os
import json
import numpy as np
from typing import Dict, List


# Months classified as dry/fire-prone for Wayanad region
DRY_MONTHS  = {1, 2, 3, 4, 5, 10, 11, 12}   # Jan–May and Oct–Dec
FIRE_SEASON = {2, 3, 4, 5}                    # Peak fire risk Feb–May


def compute_fire_risk(
    patch_path: str,         # path to .npy patch file
    months: List[str],       # list of month labels (e.g. '2025-05')
    degradation_score: float = 0.5,
) -> Dict[str, float]:
    """
    Compute fire risk score for each month in a patch's time series.

    Band indices: B2=0, B3=1, B4=2, B8=3, B11=4, B12=5, NDVI=6, EVI=7

    Returns: dict of {month_label: fire_risk_score}
    """
    patch = np.load(patch_path).astype(np.float32)   # (T, 8, 64, 64)
    patch[patch == -9999] = np.nan

    risk_scores = {}

    for t, month_label in enumerate(months):
        if t >= patch.shape[0]:
            break

        month_num = int(month_label.split('-')[1])   # 1–12
        slice_t   = patch[t]                         # (8, 64, 64)

        # Band values (spatial mean)
        ndvi = float(np.nanmean(slice_t[6]))   # NDVI
        evi  = float(np.nanmean(slice_t[7]))   # EVI
        swir1 = float(np.nanmean(slice_t[4]))  # B11 (SWIR1)
        swir2 = float(np.nanmean(slice_t[5]))  # B12 (SWIR2)

        # Normalized Difference Vegetation Index already computed
        # NDWI-like moisture index using NIR and SWIR
        nir  = float(np.nanmean(slice_t[3]))   # B8
        moisture = (nir - swir1) / (nir + swir1 + 1e-6)   # ~ [-1, 1], higher = wetter

        # ── Fire risk factors (each 0–1) ──────────────────────────────────

        # 1. Dryness: lower NDVI = drier = more fire risk
        #    Normalize: typical healthy NDVI 0.5–0.8, fire risk when < 0.4
        ndvi_risk = float(np.clip((0.5 - ndvi) / 0.5, 0, 1))

        # 2. SWIR brightness: high SWIR = dry standing biomass (fire fuel)
        #    Typical SWIR in 0–0.3 range after normalization
        swir_risk = float(np.clip(swir1 / 0.3, 0, 1))

        # 3. Low moisture content
        moisture_risk = float(np.clip((0 - moisture) / 1.0, 0, 1))

        # 4. Seasonal multiplier (fire season gets 1.5×)
        season_mult = 1.5 if month_num in FIRE_SEASON else (0.8 if month_num in DRY_MONTHS else 0.4)

        # 5. Existing degradation amplifies risk
        deg_risk = degradation_score

        # Weighted combination
        raw_risk = (
            0.30 * ndvi_risk +
            0.25 * swir_risk +
            0.20 * moisture_risk +
            0.25 * deg_risk
        ) * season_mult

        final_risk = float(np.clip(raw_risk, 0.0, 1.0))
        risk_scores[month_label] = round(final_risk, 4)

    return risk_scores


def classify_risk(score: float) -> str:
    if score < 0.25:  return 'Low'
    if score < 0.50:  return 'Moderate'
    if score < 0.75:  return 'High'
    return 'Critical'


def run_fire_risk_analysis(
    patch_index_path: str    = 'data/patches/patch_index.json',
    patches_dir: str         = 'data/patches',
    classifier_results_path: str = 'results/classifier_results.json',
    output_path: str         = 'results/fire_risk.json',
    recent_months: int       = 12,   # only compute for last N months
) -> dict:
    """
    Compute fire risk for all patches for recent months.
    """
    with open(patch_index_path) as f:
        index = json.load(f)

    with open(classifier_results_path) as f:
        clf_results = json.load(f)

    months       = index['months'][-recent_months:]   # last N months
    patch_scores = clf_results['patch_scores']

    all_results = {}
    patch_latest_risk = {}   # patch_id → latest month risk (for dashboard)

    for entry in index['patches']:
        pid      = entry['patch_id']
        deg_score = patch_scores.get(str(pid), {}).get('degradation_score', 0.5)
        patch_path = os.path.join(patches_dir, f"patch_{pid:04d}.npy")

        if not os.path.exists(patch_path):
            continue

        risk_by_month = compute_fire_risk(patch_path, months, deg_score)

        # Latest month risk
        latest_risk = list(risk_by_month.values())[-1] if risk_by_month else 0.0

        all_results[pid] = {
            'degradation_score': deg_score,
            'risk_by_month':     risk_by_month,
            'latest_risk':       round(latest_risk, 4),
            'risk_level':        classify_risk(latest_risk),
            'grid_row':          entry['grid_row'],
            'grid_col':          entry['grid_col'],
        }
        patch_latest_risk[pid] = latest_risk

    # Summary
    n_critical = sum(1 for v in all_results.values() if v['risk_level'] == 'Critical')
    n_high     = sum(1 for v in all_results.values() if v['risk_level'] == 'High')
    n_mod      = sum(1 for v in all_results.values() if v['risk_level'] == 'Moderate')
    n_low      = sum(1 for v in all_results.values() if v['risk_level'] == 'Low')

    summary = {
        'months_analyzed': months,
        'n_patches':   len(all_results),
        'risk_summary': {
            'Critical': n_critical, 'High': n_high,
            'Moderate': n_mod,      'Low':  n_low,
        },
        'patches': all_results,
    }

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n🔥 Fire Risk Analysis:")
    print(f"   Critical: {n_critical} patches")
    print(f"   High    : {n_high} patches")
    print(f"   Moderate: {n_mod} patches")
    print(f"   Low     : {n_low} patches")
    print(f"✅ Saved: {output_path}")

    return summary


if __name__ == '__main__':
    run_fire_risk_analysis()
