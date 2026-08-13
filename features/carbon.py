"""
EvOLve — features/carbon.py
Carbon Stock Estimation from NDVI proxy.

Tropical forest carbon stock estimation using allometric NDVI relationships:
  Carbon (tons/ha) ≈ AGB_density × forest_cover_fraction
  AGB_density for tropical moist forest = 150–280 tons/ha

NDVI → canopy density → AGB → carbon stock
Carbon loss rate = carbon_loss per year due to degradation.

Also computes economic value of carbon: USD/ton based on carbon market price.
"""

import os
import json
import numpy as np
from typing import Dict


# Biomass constants for tropical moist forest (Wayanad region)
AGB_MAX_TONS_HA     = 250.0   # maximum above-ground biomass density
CARBON_FRACTION     = 0.47    # IPCC standard: 47% of AGB is carbon
PATCH_AREA_HA       = 40.96   # 640m × 640m = 40.96 hectares per patch
CO2_EQUIVALENT      = 44/12   # C → CO2 conversion factor (3.67×)
CARBON_PRICE_USD    = 15.0    # USD per ton CO2 (conservative VCM price)

NDVI_MIN_FOREST = 0.3   # NDVI below this → non-forest
NDVI_MAX_FOREST = 0.85  # NDVI above this → full canopy


def ndvi_to_agb(ndvi: float) -> float:
    """
    Simple linear NDVI → AGB density relationship.
    NDVI of 0.3 → 0 tons/ha (bare / degraded)
    NDVI of 0.85 → AGB_MAX tons/ha (dense forest)
    """
    if ndvi <= NDVI_MIN_FOREST:
        return 0.0
    if ndvi >= NDVI_MAX_FOREST:
        return AGB_MAX_TONS_HA
    frac = (ndvi - NDVI_MIN_FOREST) / (NDVI_MAX_FOREST - NDVI_MIN_FOREST)
    return float(frac * AGB_MAX_TONS_HA)


def compute_carbon_stock(
    patch_path: str,
    months: list,
    degradation_score: float = 0.3,
) -> dict:
    """
    Compute carbon stock per month for one patch.

    Returns:
      carbon_by_month: {month: carbon_tons_CO2_eq}
      carbon_loss_rate: annual carbon loss (tons CO2 / year)
      current_stock: current month carbon stock
    """
    patch = np.load(patch_path).astype(np.float32)  # (T, 8, 64, 64)
    patch[patch == -9999] = np.nan

    ndvi = patch[:, 6, :, :]   # (T, 64, 64)
    T    = patch.shape[0]

    carbon_by_month = {}

    for t, month_label in enumerate(months):
        if t >= T:
            break
        ndvi_mean  = float(np.nanmean(ndvi[t]))
        agb        = ndvi_to_agb(ndvi_mean)               # tons/ha
        carbon_c   = agb * CARBON_FRACTION                 # tons C/ha
        carbon_co2 = carbon_c * CO2_EQUIVALENT             # tons CO2/ha
        total_co2  = carbon_co2 * PATCH_AREA_HA            # tons CO2 for patch
        carbon_by_month[month_label] = round(total_co2, 2)

    # Estimate annual carbon loss from degradation score
    # Degraded patches lose proportionally more carbon
    max_carbon       = ndvi_to_agb(0.75) * CARBON_FRACTION * CO2_EQUIVALENT * PATCH_AREA_HA
    carbon_loss_rate = max_carbon * degradation_score * 0.15   # 15% annual turnover

    current_stock = list(carbon_by_month.values())[-1] if carbon_by_month else 0.0

    return {
        'carbon_by_month':   carbon_by_month,
        'current_stock_tCO2': round(current_stock, 2),
        'annual_loss_tCO2':  round(carbon_loss_rate, 2),
        'carbon_value_usd':  round(current_stock * CARBON_PRICE_USD, 2),
        'annual_loss_usd':   round(carbon_loss_rate * CARBON_PRICE_USD, 2),
    }


def run_carbon_analysis(
    patch_index_path: str        = 'data/patches/patch_index.json',
    patches_dir: str             = 'data/patches',
    classifier_results_path: str = 'results/classifier_results.json',
    output_path: str             = 'results/carbon_stock.json',
) -> dict:

    with open(patch_index_path) as f:
        index = json.load(f)
    with open(classifier_results_path) as f:
        clf = json.load(f)

    months       = index['months']
    patch_scores = clf['patch_scores']
    all_results  = {}

    total_stock    = 0.0
    total_loss_yr  = 0.0

    for entry in index['patches']:
        pid       = entry['patch_id']
        deg_score = patch_scores.get(str(pid), {}).get('degradation_score', 0.3)
        path      = os.path.join(patches_dir, f"patch_{pid:04d}.npy")
        if not os.path.exists(path):
            continue

        result = compute_carbon_stock(path, months, deg_score)
        result.update({
            'grid_row':        entry['grid_row'],
            'grid_col':        entry['grid_col'],
            'degradation_score': round(deg_score, 4),
        })
        all_results[pid] = result

        total_stock   += result['current_stock_tCO2']
        total_loss_yr += result['annual_loss_tCO2']

    summary = {
        'total_stock_tCO2':    round(total_stock, 2),
        'total_annual_loss_tCO2': round(total_loss_yr, 2),
        'total_stock_value_usd':  round(total_stock * CARBON_PRICE_USD, 2),
        'total_annual_loss_usd':  round(total_loss_yr * CARBON_PRICE_USD, 2),
        'carbon_price_usd_per_ton': CARBON_PRICE_USD,
        'n_patches': len(all_results),
        'area_ha':   round(len(all_results) * PATCH_AREA_HA, 1),
        'patches':   all_results,
    }

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n🌿 Carbon Stock Analysis:")
    print(f"   Total stock        : {total_stock:,.1f} tons CO₂ eq")
    print(f"   Annual loss        : {total_loss_yr:,.1f} tons CO₂ / year")
    print(f"   Stock value (est.) : USD {total_stock * CARBON_PRICE_USD:,.0f}")
    print(f"   Annual loss cost   : USD {total_loss_yr * CARBON_PRICE_USD:,.0f}")
    print(f"✅ Saved: {output_path}")

    return summary


if __name__ == '__main__':
    run_carbon_analysis()
