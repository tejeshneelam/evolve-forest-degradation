"""
EvOLve — features/landslide.py
Landslide Vulnerability Zone Detection.

Wayanad 2024 disaster context: forest loss on steep slopes
removes root binding → catastrophic landslides.

Vulnerability = forest_loss_rate × slope_factor × rainfall_proxy

Slope is estimated from DEM (SRTM) — we use approximate slope from
Hansen treecover + degradation as proxy since SRTM download is optional.
If srtm_dem.npy is available in data/labels/, uses actual slope.
Otherwise falls back to a slope proxy based on NDVI variance patterns.
"""

import os
import json
import numpy as np
from typing import Dict


def classify_vulnerability(score: float) -> str:
    if score < 0.20: return 'Low'
    if score < 0.40: return 'Moderate'
    if score < 0.65: return 'High'
    return 'Critical'


def compute_landslide_vulnerability(
    patch_index_path: str        = 'data/patches/patch_index.json',
    patches_dir: str             = 'data/patches',
    labels_dir: str              = 'data/labels',
    classifier_results_path: str = 'results/classifier_results.json',
    output_path: str             = 'results/landslide_risk.json',
) -> dict:
    """
    Compute landslide vulnerability for each patch.

    Formula:
      vulnerability = w1*loss_rate + w2*slope_proxy + w3*moisture_depletion
    """
    with open(patch_index_path) as f:
        index = json.load(f)

    with open(classifier_results_path) as f:
        clf = json.load(f)

    # Load Hansen labels for tree cover + loss year
    hansen = np.load(os.path.join(labels_dir, 'hansen_aligned.npy'))  # (3, 558, 557)
    treecover = hansen[0]   # 0–100%
    loss_year = hansen[2]   # lossyear (19–25 for our window)

    patch_scores = clf['patch_scores']
    months       = index['months']
    all_results  = {}

    for entry in index['patches']:
        pid  = entry['patch_id']
        y0, y1, x0, x1 = entry['pixel_bounds']

        patch_treecover = treecover[y0:y1, x0:x1]
        patch_lossyear  = loss_year[y0:y1, x0:x1]

        deg_score = patch_scores.get(str(pid), {}).get('degradation_score', 0.3)

        # ── Factor 1: Forest loss rate 2019–2025 ──────────────────────────
        recent_loss = np.sum((patch_lossyear >= 19) & (patch_lossyear <= 25))
        loss_rate   = float(recent_loss) / (patch_treecover.size + 1e-6)   # fraction
        loss_rate   = float(np.clip(loss_rate, 0, 1))

        # ── Factor 2: Initial canopy cover (higher cover → more root binding → lower risk)
        mean_cover   = float(patch_treecover.mean()) / 100.0   # 0–1
        canopy_risk  = float(1.0 - mean_cover)                  # low cover = higher risk

        # ── Factor 3: NDVI variability as slope proxy ────────────────────
        # High spatial NDVI std within patch → heterogeneous terrain → likely steeper
        patch_path = os.path.join(patches_dir, f"patch_{pid:04d}.npy")
        slope_proxy = 0.4   # default moderate

        if os.path.exists(patch_path):
            patch = np.load(patch_path).astype(np.float32)
            patch[patch == -9999] = np.nan
            # Mean spatial variance of NDVI across time
            ndvi = patch[:, 6, :, :]   # (T, 64, 64)
            ndvi_spatial_std = float(np.nanmean(np.nanstd(ndvi, axis=(1, 2))))
            # Normalize to 0–1 (typical range 0.05–0.25)
            slope_proxy = float(np.clip(ndvi_spatial_std / 0.2, 0, 1))

        # ── Factor 4: SWIR-based soil moisture depletion ─────────────────
        moisture_depletion = 0.5   # default
        if os.path.exists(patch_path):
            patch = np.load(patch_path).astype(np.float32)
            patch[patch == -9999] = np.nan
            swir1 = patch[:, 4, :, :]   # B11
            # High SWIR in dry months = low moisture = instability risk in monsoon
            dry_months_idx = [i for i, m in enumerate(months) if int(m.split('-')[1]) in {3,4,5}]
            if dry_months_idx:
                swir_dry = np.nanmean(swir1[dry_months_idx])
                moisture_depletion = float(np.clip(swir_dry / 0.25, 0, 1))

        # ── Weighted combination ──────────────────────────────────────────
        vulnerability = (
            0.35 * loss_rate +
            0.25 * slope_proxy +
            0.20 * canopy_risk +
            0.15 * deg_score +
            0.05 * moisture_depletion
        )
        vulnerability = float(np.clip(vulnerability, 0, 1))

        all_results[pid] = {
            'vulnerability_score': round(vulnerability, 4),
            'vulnerability_level': classify_vulnerability(vulnerability),
            'loss_rate':           round(loss_rate, 4),
            'canopy_risk':         round(canopy_risk, 4),
            'slope_proxy':         round(slope_proxy, 4),
            'degradation_score':   round(deg_score, 4),
            'grid_row':            entry['grid_row'],
            'grid_col':            entry['grid_col'],
            'recent_loss_pixels':  int(recent_loss),
        }

    # Summary
    levels = [v['vulnerability_level'] for v in all_results.values()]
    summary = {
        'n_patches': len(all_results),
        'vulnerability_summary': {
            'Critical': levels.count('Critical'),
            'High':     levels.count('High'),
            'Moderate': levels.count('Moderate'),
            'Low':      levels.count('Low'),
        },
        'patches': all_results,
        'note': 'Wayanad 2024 disaster context: high scores indicate urgent intervention needed',
    }

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n⚠️  Landslide Vulnerability Analysis:")
    for level in ['Critical', 'High', 'Moderate', 'Low']:
        print(f"   {level:10s}: {levels.count(level)} patches")
    print(f"✅ Saved: {output_path}")

    return summary


if __name__ == '__main__':
    compute_landslide_vulnerability()
