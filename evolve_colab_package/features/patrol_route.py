"""
EvOLve — features/patrol_route.py
Ranger Safe Patrol Route Planner using A* pathfinding.

Rangers need to:
  - Reach degraded / alerted patches for inspection
  - Avoid high fire risk zones
  - Avoid known wildlife conflict zones (low NDVI corridors)
  - Prefer patches with good data quality (high valid_fraction)

Each patch is a node in an 8×8 grid graph.
Edge cost = risk of traversing that patch.
A* finds the minimum-risk path between any two patches.
"""

import os
import json
import heapq
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class PatrolRoute:
    start_patch: int
    end_patch:   int
    path:        List[int]          # ordered list of patch IDs
    total_risk:  float
    distance_km: float
    waypoints:   List[dict]         # [{patch_id, grid_row, grid_col, risk_level}]
    warnings:    List[str]          # hazards along the route


PATCH_SIZE_KM = 0.64   # 640m per patch


class PatrolRoutePlanner:
    """A* pathfinder on the 8×8 patch grid."""

    def __init__(
        self,
        patch_index_path: str        = 'data/patches/patch_index.json',
        classifier_results_path: str = 'results/classifier_results.json',
        fire_risk_path: str          = 'results/fire_risk.json',
        corridor_path: str           = 'results/corridor_analysis.json',
    ):
        with open(patch_index_path) as f:
            index = json.load(f)

        # Build lookup tables
        self.entries   = {e['patch_id']: e for e in index['patches']}
        self.grid_map  = {(e['grid_row'], e['grid_col']): e['patch_id']
                          for e in index['patches']}
        self.pid_to_rc = {e['patch_id']: (e['grid_row'], e['grid_col'])
                          for e in index['patches']}

        # Load degradation scores
        self.deg_scores: Dict[int, float] = {}
        if os.path.exists(classifier_results_path):
            with open(classifier_results_path) as f:
                clf = json.load(f)
            for pid_str, v in clf['patch_scores'].items():
                self.deg_scores[int(pid_str)] = v['degradation_score']

        # Load fire risk
        self.fire_risk: Dict[int, float] = {}
        if os.path.exists(fire_risk_path):
            with open(fire_risk_path) as f:
                fr = json.load(f)
            for pid_str, v in fr['patches'].items():
                self.fire_risk[int(pid_str)] = v['latest_risk']

        # Load corridor info (wildlife zones)
        self.wildlife_patches: set = set()
        if os.path.exists(corridor_path):
            with open(corridor_path) as f:
                corr = json.load(f)
            for c in corr.get('corridors', []):
                if c['status'] == 'Intact':
                    # Intact corridors = active wildlife zones (avoid at dusk/dawn)
                    self.wildlife_patches.update(c['patches'])

    def patch_cost(self, pid: int) -> float:
        """
        Traversal cost for a patch (lower = safer to traverse).
        Combines fire risk + degradation + wildlife conflict risk.
        """
        fire    = self.fire_risk.get(pid, 0.3)
        deg     = self.deg_scores.get(pid, 0.3)
        wildlife = 0.4 if pid in self.wildlife_patches else 0.1

        # Rangers should avoid high-fire and high-wildlife-conflict areas
        cost = 0.4 * fire + 0.3 * deg + 0.3 * wildlife
        return float(np.clip(cost, 0.01, 1.0))

    def heuristic(self, pid: int, goal: int) -> float:
        """Manhattan distance heuristic on the grid."""
        r1, c1 = self.pid_to_rc[pid]
        r2, c2 = self.pid_to_rc[goal]
        return abs(r1 - r2) + abs(c1 - c2)

    def get_neighbors(self, pid: int) -> List[int]:
        """4-connected neighbors of a patch."""
        r, c = self.pid_to_rc[pid]
        neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if (nr, nc) in self.grid_map:
                neighbors.append(self.grid_map[(nr, nc)])
        return neighbors

    def find_route(self, start_pid: int, end_pid: int) -> Optional[PatrolRoute]:
        """
        A* pathfinding from start patch to end patch.
        Returns PatrolRoute or None if no path exists.
        """
        if start_pid not in self.pid_to_rc or end_pid not in self.pid_to_rc:
            return None

        if start_pid == end_pid:
            entry = self.entries[start_pid]
            return PatrolRoute(
                start_patch = start_pid,
                end_patch   = end_pid,
                path        = [start_pid],
                total_risk  = 0.0,
                distance_km = 0.0,
                waypoints   = [{'patch_id': start_pid, 'grid_row': entry['grid_row'],
                                'grid_col': entry['grid_col'],
                                'risk_level': self._classify_risk(self.patch_cost(start_pid))}],
                warnings    = [],
            )

        # A* open set: (f_score, patch_id)
        open_set = [(0.0, start_pid)]
        came_from: Dict[int, Optional[int]] = {start_pid: None}
        g_score: Dict[int, float] = {start_pid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end_pid:
                # Reconstruct path
                path = []
                node = end_pid
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()

                # Build waypoints and warnings
                waypoints = []
                warnings  = []
                for pid in path:
                    entry = self.entries[pid]
                    cost  = self.patch_cost(pid)
                    wp = {
                        'patch_id': pid,
                        'grid_row': entry['grid_row'],
                        'grid_col': entry['grid_col'],
                        'risk_level': self._classify_risk(cost),
                        'fire_risk': round(self.fire_risk.get(pid, 0.0), 3),
                        'deg_score': round(self.deg_scores.get(pid, 0.0), 3),
                    }
                    waypoints.append(wp)

                    if self.fire_risk.get(pid, 0) > 0.6:
                        warnings.append(f"High fire risk at Patch {pid} — proceed with caution")
                    if pid in self.wildlife_patches and self.deg_scores.get(pid, 0) < 0.3:
                        warnings.append(f"Active wildlife corridor at Patch {pid} — use daytime only")
                    if self.deg_scores.get(pid, 0) > 0.7:
                        warnings.append(f"Severely degraded terrain at Patch {pid} — unstable ground")

                total_risk  = g_score[end_pid]
                distance_km = (len(path) - 1) * PATCH_SIZE_KM

                return PatrolRoute(
                    start_patch = start_pid,
                    end_patch   = end_pid,
                    path        = path,
                    total_risk  = round(total_risk, 4),
                    distance_km = round(distance_km, 2),
                    waypoints   = waypoints,
                    warnings    = warnings,
                )

            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + self.patch_cost(neighbor)

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor]  = tentative_g
                    came_from[neighbor] = current
                    f_score = tentative_g + self.heuristic(neighbor, end_pid)
                    heapq.heappush(open_set, (f_score, neighbor))

        return None   # No path found

    @staticmethod
    def _classify_risk(cost: float) -> str:
        if cost < 0.25: return 'Safe'
        if cost < 0.50: return 'Caution'
        if cost < 0.75: return 'Risky'
        return 'Avoid'


def find_patrol_route(
    start_patch_id: int,
    end_patch_id:   int,
    patch_index_path: str        = 'data/patches/patch_index.json',
    classifier_results_path: str = 'results/classifier_results.json',
    fire_risk_path: str          = 'results/fire_risk.json',
    corridor_path: str           = 'results/corridor_analysis.json',
) -> dict:
    planner = PatrolRoutePlanner(
        patch_index_path, classifier_results_path, fire_risk_path, corridor_path
    )
    route = planner.find_route(start_patch_id, end_patch_id)

    if route is None:
        return {'error': f'No path found from patch {start_patch_id} to {end_patch_id}'}

    result = asdict(route)
    print(f"\n🧭 Patrol Route: Patch {start_patch_id} → {end_patch_id}")
    print(f"   Path      : {' → '.join(str(p) for p in route.path)}")
    print(f"   Distance  : {route.distance_km:.2f} km")
    print(f"   Risk score: {route.total_risk:.4f}")
    if route.warnings:
        print(f"   Warnings  :")
        for w in route.warnings:
            print(f"     ⚠️  {w}")

    return result
