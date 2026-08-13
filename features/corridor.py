"""
EvOLve — features/corridor.py
Wildlife Corridor Health & Break Detection.

Uses degradation scores + patch adjacency to:
1. Build a connectivity graph of forest patches
2. Identify healthy corridors (contiguous healthy patches)
3. Flag broken corridors (gaps between healthy zones)
4. Score each corridor: Intact / Weakened / Broken

Wayanad Wildlife Sanctuary context: elephants and tigers use
north-south corridors — degradation in these is critical.
"""

import os
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional


@dataclass
class Corridor:
    corridor_id: int
    patches: List[int]               # list of patch IDs in this corridor
    status: str                      # 'Intact' | 'Weakened' | 'Broken'
    mean_degradation: float          # 0.0 healthy → 1.0 fully degraded
    length_km: float                 # approximate length
    break_points: List[int]          # patch IDs where corridor is weakest


class CorridorAnalyzer:
    """
    Builds and scores wildlife corridors from patch degradation scores.
    """

    PATCH_SIZE_M = 640      # each 64×64 patch at 10m = 640m × 640m
    GRID_ROWS    = 8
    GRID_COLS    = 8

    # Degradation thresholds
    INTACT_THRESH   = 0.20   # < 20% degraded → intact
    WEAKENED_THRESH = 0.45   # < 45% degraded → weakened
    # >= 45% → broken

    def __init__(self, patch_index_path: str, scores_path: str):
        with open(patch_index_path) as f:
            self.index = json.load(f)

        with open(scores_path) as f:
            results = json.load(f)

        # Build score lookup: patch_id → degradation_score
        self.scores: Dict[int, float] = {}
        for pid_str, v in results['patch_scores'].items():
            self.scores[int(pid_str)] = v['degradation_score']

        # Build grid: row,col → patch_id
        self.grid = {}
        self.patch_meta = {}
        for entry in self.index['patches']:
            r, c = entry['grid_row'], entry['grid_col']
            pid  = entry['patch_id']
            self.grid[(r, c)]  = pid
            self.patch_meta[pid] = entry

    def get_degradation(self, pid: int) -> float:
        return self.scores.get(pid, 0.5)

    def classify_patch(self, pid: int) -> str:
        s = self.get_degradation(pid)
        if s < self.INTACT_THRESH:   return 'Intact'
        if s < self.WEAKENED_THRESH: return 'Weakened'
        return 'Broken'

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int,int]]:
        """4-connectivity neighbors (N, S, E, W)."""
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if (nr, nc) in self.grid:
                neighbors.append((nr, nc))
        return neighbors

    def find_corridors(self) -> List[Corridor]:
        """
        Find all contiguous groups of patches forming corridors using BFS.
        North-south columns are classic wildlife corridors in Wayanad.
        """
        corridors = []
        visited   = set()

        # Prioritize vertical (N-S) columns as main corridors
        for col in range(self.GRID_COLS):
            col_patches = []
            for row in range(self.GRID_ROWS):
                if (row, col) in self.grid:
                    col_patches.append(self.grid[(row, col)])

            if not col_patches:
                continue

            scores = [self.get_degradation(pid) for pid in col_patches]
            mean_deg = float(np.mean(scores))

            # Classify
            if mean_deg < self.INTACT_THRESH:
                status = 'Intact'
            elif mean_deg < self.WEAKENED_THRESH:
                status = 'Weakened'
            else:
                status = 'Broken'

            # Find break points (patches with score > 0.5)
            breaks = [pid for pid, s in zip(col_patches, scores) if s > 0.5]

            length_km = (len(col_patches) * self.PATCH_SIZE_M) / 1000.0

            corridors.append(Corridor(
                corridor_id      = col,
                patches          = col_patches,
                status           = status,
                mean_degradation = round(mean_deg, 4),
                length_km        = round(length_km, 2),
                break_points     = breaks,
            ))

        return corridors

    def analyze(self) -> dict:
        corridors = self.find_corridors()

        summary = {
            'total_corridors': len(corridors),
            'intact':    sum(1 for c in corridors if c.status == 'Intact'),
            'weakened':  sum(1 for c in corridors if c.status == 'Weakened'),
            'broken':    sum(1 for c in corridors if c.status == 'Broken'),
            'corridors': [asdict(c) for c in corridors],
            'patch_health': {str(pid): {
                'score':  self.get_degradation(pid),
                'status': self.classify_patch(pid),
                'grid_row': self.patch_meta[pid]['grid_row'],
                'grid_col': self.patch_meta[pid]['grid_col'],
            } for pid in self.scores},
        }

        print(f"\n🐘 Wildlife Corridor Analysis:")
        print(f"   Intact   : {summary['intact']} corridors")
        print(f"   Weakened : {summary['weakened']} corridors")
        print(f"   Broken   : {summary['broken']} corridors")

        return summary


def run_corridor_analysis(
    patch_index_path: str = 'data/patches/patch_index.json',
    scores_path: str      = 'results/classifier_results.json',
    output_path: str      = 'results/corridor_analysis.json',
):
    analyzer = CorridorAnalyzer(patch_index_path, scores_path)
    result   = analyzer.analyze()

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"✅ Corridor analysis saved: {output_path}")
    return result


if __name__ == '__main__':
    run_corridor_analysis()
