"""
EvOLve — features/reforestation.py
Reforestation Priority Map.

Ranks degraded patches for reforestation priority based on:
  1. Degradation severity (higher = more urgent)
  2. Historical forest cover (was it forest before?)
  3. Wildlife corridor connectivity (would restoring it reconnect a broken corridor?)
  4. Water proximity (SWIR-detected moisture = better reforestation success)
  5. Surrounding patch health (good neighbors → natural seed source)

Outputs: ranked list of top-N patches with priority scores and justification.
"""

import os
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class ReforestationCandidate:
    patch_id:          int
    priority_rank:     int
    priority_score:    float     # 0.0 (low) → 1.0 (highest priority)
    degradation_score: float
    corridor_benefit:  float     # would restoring this patch help a corridor?
    water_proximity:   float     # likelihood of water availability
    neighbor_health:   float     # mean health of adjacent patches
    tree_cover_2000:   float     # original forest cover %
    justification:     str
    grid_row:          int
    grid_col:          int


GRID_ROWS = 8
GRID_COLS = 8


def get_neighbor_scores(pid_scores: Dict[int, float], entry: dict,
                        patch_meta: Dict) -> float:
    """Average degradation of 4 neighbors (lower = healthier neighbors)."""
    row, col = entry['grid_row'], entry['grid_col']
    grid     = patch_meta   # {(row,col): pid}
    neighbors = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = row+dr, col+dc
        if (nr, nc) in grid:
            npid = grid[(nr, nc)]
            neighbors.append(pid_scores.get(npid, 0.5))
    if neighbors:
        return 1.0 - float(np.mean(neighbors))   # higher = healthier neighbors
    return 0.5


def compute_reforestation_priorities(
    patch_index_path: str        = 'data/patches/patch_index.json',
    patches_dir: str             = 'data/patches',
    labels_dir: str              = 'data/labels',
    classifier_results_path: str = 'results/classifier_results.json',
    corridor_path: str           = 'results/corridor_analysis.json',
    output_path: str             = 'results/reforestation_priority.json',
    top_n: int = 15,
) -> dict:

    with open(patch_index_path) as f:
        index = json.load(f)
    with open(classifier_results_path) as f:
        clf = json.load(f)

    # Load corridor data if available
    corridor_patches = set()
    if os.path.exists(corridor_path):
        with open(corridor_path) as f:
            corr = json.load(f)
        for c in corr.get('corridors', []):
            if c['status'] in ('Weakened', 'Broken'):
                corridor_patches.update(c['patches'])

    # Load Hansen for tree cover
    hansen = np.load(os.path.join(labels_dir, 'hansen_aligned.npy'))
    treecover = hansen[0]

    patch_scores = clf['patch_scores']
    months       = index['months']

    # Build grid map: (row,col) → patch_id
    patch_meta = {}
    grid_map   = {}
    for entry in index['patches']:
        pid = entry['patch_id']
        patch_meta[pid] = entry
        grid_map[(entry['grid_row'], entry['grid_col'])] = pid

    # Score lookup
    deg_scores = {int(k): v['degradation_score'] for k, v in patch_scores.items()}

    candidates = []

    for entry in index['patches']:
        pid  = entry['patch_id']
        y0, y1, x0, x1 = entry['pixel_bounds']

        deg_score = deg_scores.get(pid, 0.5)

        # Only consider degraded patches for reforestation
        if deg_score < 0.15:
            continue

        # Factor 1: degradation severity
        degrad_priority = deg_score

        # Factor 2: original tree cover
        tc2000         = float(treecover[y0:y1, x0:x1].mean()) / 100.0
        original_forest = tc2000

        # Factor 3: corridor benefit
        corridor_benefit = 1.0 if pid in corridor_patches else 0.3

        # Factor 4: water proximity (SWIR moisture)
        water_proximity = 0.4
        patch_path = os.path.join(patches_dir, f"patch_{pid:04d}.npy")
        if os.path.exists(patch_path):
            patch = np.load(patch_path).astype(np.float32)
            patch[patch == -9999] = np.nan
            # Higher NIR relative to SWIR = more moisture
            nir_mean  = float(np.nanmean(patch[:, 3, :, :]))
            swir_mean = float(np.nanmean(patch[:, 4, :, :]))
            moisture  = (nir_mean - swir_mean) / (nir_mean + swir_mean + 1e-6)
            water_proximity = float(np.clip((moisture + 1) / 2, 0, 1))

        # Factor 5: neighbor health (seed source)
        neighbor_health = get_neighbor_scores(deg_scores, entry, grid_map)

        # Weighted priority score
        priority = (
            0.30 * degrad_priority +
            0.20 * original_forest +
            0.25 * corridor_benefit +
            0.15 * water_proximity +
            0.10 * neighbor_health
        )
        priority = float(np.clip(priority, 0, 1))

        # Justification string
        reasons = []
        if deg_score > 0.5:    reasons.append(f"high degradation ({deg_score:.2f})")
        if corridor_benefit > 0.5: reasons.append("would restore wildlife corridor")
        if tc2000 > 0.6:       reasons.append(f"was dense forest in 2000 ({tc2000*100:.0f}% cover)")
        if water_proximity > 0.6: reasons.append("good moisture availability")
        if neighbor_health > 0.6: reasons.append("healthy neighboring patches for seed source")
        justification = "Priority: " + "; ".join(reasons) if reasons else "Moderate degradation"

        candidates.append(ReforestationCandidate(
            patch_id          = pid,
            priority_rank     = 0,   # set after sorting
            priority_score    = round(priority, 4),
            degradation_score = round(deg_score, 4),
            corridor_benefit  = round(corridor_benefit, 4),
            water_proximity   = round(water_proximity, 4),
            neighbor_health   = round(neighbor_health, 4),
            tree_cover_2000   = round(tc2000 * 100, 1),
            justification     = justification,
            grid_row          = entry['grid_row'],
            grid_col          = entry['grid_col'],
        ))

    # Sort by priority
    candidates.sort(key=lambda c: c.priority_score, reverse=True)
    for i, c in enumerate(candidates):
        c.priority_rank = i + 1

    top = candidates[:top_n]

    result = {
        'total_degraded_patches': len(candidates),
        'top_n':    top_n,
        'top_candidates': [asdict(c) for c in top],
        'all_candidates': [asdict(c) for c in candidates],
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n🌱 Reforestation Priority Map:")
    print(f"   {len(candidates)} degraded patches ranked")
    print(f"   Top 3 priorities:")
    for c in top[:3]:
        print(f"     Rank {c.priority_rank}: Patch {c.patch_id} "
              f"(score={c.priority_score:.3f}) — {c.justification}")
    print(f"✅ Saved: {output_path}")

    return result


if __name__ == '__main__':
    compute_reforestation_priorities()
