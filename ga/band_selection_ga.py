"""
EvOLve — ga/band_selection_ga.py
Multi-Objective Genetic Algorithm for Multi-Spectral Band & Index Selection.

Optimizes the feature subset from 12 Sentinel-2 bands and spectral indices
([b_1, ..., b_12] in {0, 1}^12) to:
  1. Maximize Forest Degradation Detection F1-score / Fitness.
  2. Minimize Band Count (reducing cloud GEE transmission bandwidth & model latency).
  3. Discover the Pareto Frontier of Accuracy vs. Computational Cost.
"""

import os
import json
import random
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple, Optional


# ── Spectral Band & Index Definitions ─────────────────────────────────────────

BAND_METADATA = [
    {
        "id": "B2",
        "name": "Blue (490 nm)",
        "category": "Atmospheric / Visible",
        "wavelength": "490 nm",
        "base_weight": 0.35,
        "description": "Atmospheric scattering reference, aerosol discrimination, surface water."
    },
    {
        "id": "B3",
        "name": "Green (560 nm)",
        "category": "Visible Reflector",
        "wavelength": "560 nm",
        "base_weight": 0.45,
        "description": "Peak healthy vegetation green reflection and chlorophyll backscatter."
    },
    {
        "id": "B4",
        "name": "Red (665 nm)",
        "category": "Photosynthetic Absorber",
        "wavelength": "665 nm",
        "base_weight": 0.85,
        "description": "Strong chlorophyll absorption band; crucial for logging contrast and bare soil exposure."
    },
    {
        "id": "B8",
        "name": "NIR Broad (842 nm)",
        "category": "Canopy Architecture",
        "wavelength": "842 nm",
        "base_weight": 0.96,
        "description": "High spongy mesophyll cell scattering; quintessential signal for canopy density and health."
    },
    {
        "id": "B8A",
        "name": "Narrow NIR (865 nm)",
        "category": "Biophysical Reference",
        "wavelength": "865 nm",
        "base_weight": 0.70,
        "description": "Atmospheric water vapor absorption edge; biophysical parameter estimation."
    },
    {
        "id": "B11",
        "name": "SWIR-1 (1610 nm)",
        "category": "Hydration / Burn",
        "wavelength": "1610 nm",
        "base_weight": 0.94,
        "description": "Canopy moisture content and soil hydration indicator; sensitive to selective logging."
    },
    {
        "id": "B12",
        "name": "SWIR-2 (2190 nm)",
        "category": "Thermal / Dry Matter",
        "wavelength": "2190 nm",
        "base_weight": 0.65,
        "description": "Dry dead fuel, charcoal residues, post-fire burn severity, and mineral rock exposure."
    },
    {
        "id": "NDVI",
        "name": "NDVI (NIR-Red)/(NIR+Red)",
        "category": "Vegetation Index",
        "wavelength": "Derived Index",
        "base_weight": 0.95,
        "description": "Standard Normalized Difference Vegetation Index; gold standard for seasonal phenology."
    },
    {
        "id": "EVI",
        "name": "EVI (Enhanced Veg Index)",
        "category": "Vegetation Index",
        "wavelength": "Derived Index",
        "base_weight": 0.82,
        "description": "Atmosphere-corrected index with high sensitivity in dense closed-canopy tropical evergreen biomes."
    },
    {
        "id": "NDWI",
        "name": "NDWI (Canopy Water)",
        "category": "Moisture Index",
        "wavelength": "Derived Index",
        "base_weight": 0.88,
        "description": "Normalized Difference Water Index; tracks drought stress and foliar moisture deficit."
    },
    {
        "id": "NBR",
        "name": "NBR (Burn Ratio)",
        "category": "Disturbance Index",
        "wavelength": "Derived Index",
        "base_weight": 0.91,
        "description": "Normalized Burn Ratio; isolates wildland fire burn scars, slash-and-burn, and thermal scarring."
    },
    {
        "id": "SAVI",
        "name": "SAVI (Soil-Adjusted)",
        "category": "Vegetation Index",
        "wavelength": "Derived Index",
        "base_weight": 0.60,
        "description": "Soil-Adjusted Vegetation Index; suppresses bare ground background in open deciduous woodlands."
    }
]

BAND_KEYS = [b["id"] for b in BAND_METADATA]
NUM_BANDS = len(BAND_KEYS)


# ── Chromosome Representation ─────────────────────────────────────────────────

@dataclass
class BandChromosome:
    """
    Binary chromosome where genes[i] = 1 if band i is selected, 0 otherwise.
    Length = 12.
    """
    genes: List[int]
    accuracy: float = 0.0          # Estimated detection F1-score [0.0 - 1.0]
    latency_reduction: float = 0.0 # Latency / cloud bandwidth reduction % [0.0 - 100.0]
    fitness: float = 0.0           # Combined multi-objective fitness score
    selected_count: int = 0        # Number of active bands (1 - 12)
    selected_bands: List[str] = None

    def __post_init__(self):
        self.selected_count = sum(self.genes)
        self.selected_bands = [BAND_KEYS[i] for i, bit in enumerate(self.genes) if bit == 1]
        self.latency_reduction = round((1.0 - (self.selected_count / NUM_BANDS)) * 100.0, 1)


# ── Fitness Function with Domain Spectral Synergy ──────────────────────────────

def evaluate_band_subset(
    genes: List[int],
    target_region_type: str = "all_terrain",
    efficiency_weight: float = 0.30
) -> Tuple[float, float, float]:
    """
    Evaluates detection F1-score and multi-objective fitness for a given band selection mask.
    
    Domain Synergies:
      - Essential base: NIR (B8) + Red (B4) or NDVI
      - Moisture/Disturbance: SWIR1 (B11) or NDWI
      - Fire disturbance: NBR or B12
      - Redundancy penalty: Selecting all bands slightly degrades generalization due to collinearity
    """
    selected_indices = [i for i, b in enumerate(genes) if b == 1]
    count = len(selected_indices)

    if count == 0:
        return 0.10, 0.0, 0.01  # Severe penalty for empty chromosome

    selected_set = {BAND_KEYS[i] for i in selected_indices}

    # Base weighted sum of selected bands
    raw_score = 0.0
    for i in selected_indices:
        b_meta = BAND_METADATA[i]
        w = b_meta["base_weight"]

        # Regional adaptation weights
        if target_region_type == "deciduous_fire_prone":
            if b_meta["id"] in ["NBR", "B11", "B12"]:
                w *= 1.25
        elif target_region_type == "evergreen_canopy":
            if b_meta["id"] in ["EVI", "B8", "B8A"]:
                w *= 1.20
        elif target_region_type == "riparian_wetland":
            if b_meta["id"] in ["NDWI", "B11", "B2"]:
                w *= 1.22

        raw_score += w

    # Synergy bonuses
    has_nir = ("B8" in selected_set or "B8A" in selected_set)
    has_red = ("B4" in selected_set)
    has_swir = ("B11" in selected_set or "B12" in selected_set)
    has_ndvi = ("NDVI" in selected_set)
    has_nbr = ("NBR" in selected_set)
    has_ndwi = ("NDWI" in selected_set)

    synergy = 0.0
    if has_nir and has_red:
        synergy += 0.14
    if has_nir and has_swir:
        synergy += 0.16
    if has_ndvi:
        synergy += 0.10
    if has_nbr and has_swir:
        synergy += 0.12
    if has_ndwi and ("B11" in selected_set):
        synergy += 0.08

    # Collinearity / redundancy penalty if too many similar bands selected
    redundancy_penalty = 0.0
    if count >= 10:
        redundancy_penalty = 0.035
    elif count >= 8:
        redundancy_penalty = 0.015

    # Estimate realistic F1-score: asymptotes towards ~0.962
    f1 = 0.45 + (raw_score / 7.5) * 0.32 + synergy * 0.65 - redundancy_penalty
    # Bound F1 realistically
    f1 = float(np.clip(f1, 0.40, 0.964))

    # Latency reduction %: 0% at 12 bands, 91.7% at 1 band
    latency_reduction = (1.0 - (count / NUM_BANDS)) * 100.0

    # Multi-Objective scalarized fitness
    # Fitness balances F1 (accuracy) and Band Efficiency (resource economy)
    eff_norm = 1.0 - (count / NUM_BANDS)
    acc_weight = 1.0 - efficiency_weight
    fitness = (acc_weight * f1) + (efficiency_weight * eff_norm)

    return round(f1, 4), round(latency_reduction, 1), round(fitness, 4)


# ── Multi-Spectral Genetic Algorithm Optimizer ────────────────────────────────

class MultiSpectralGA:
    """
    Genetic Algorithm tailored for Multi-Spectral Feature & Band Selection.
    """

    def __init__(
        self,
        pop_size: int = 30,
        n_generations: int = 25,
        mutation_rate: float = 0.10,
        efficiency_weight: float = 0.30,
        target_region_type: str = "all_terrain",
        seed: Optional[int] = None
    ):
        self.pop_size = max(10, min(100, pop_size))
        self.n_generations = max(10, min(60, n_generations))
        self.mutation_rate = max(0.02, min(0.35, mutation_rate))
        self.efficiency_weight = efficiency_weight
        self.target_region_type = target_region_type

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.population: List[BandChromosome] = []
        self.history: List[Dict[str, Any]] = []
        self.pareto_frontier: List[Dict[str, Any]] = []

    def initialize_population(self):
        """Creates initial binary population with diverse bit distributions."""
        self.population = []
        for _ in range(self.pop_size):
            # Random bitmask with random sparsity
            p_on = random.uniform(0.25, 0.75)
            genes = [1 if random.random() < p_on else 0 for _ in range(NUM_BANDS)]
            if sum(genes) == 0:
                genes[random.randint(0, NUM_BANDS - 1)] = 1
            chrom = BandChromosome(genes=genes)
            self.population.append(chrom)

    def evaluate_chromosome(self, chrom: BandChromosome):
        f1, latency_red, fitness = evaluate_band_subset(
            chrom.genes,
            target_region_type=self.target_region_type,
            efficiency_weight=self.efficiency_weight
        )
        chrom.accuracy = f1
        chrom.latency_reduction = latency_red
        chrom.fitness = fitness

    def tournament_selection(self, k: int = 3) -> BandChromosome:
        contestants = random.sample(self.population, min(k, len(self.population)))
        return max(contestants, key=lambda c: c.fitness)

    def crossover(self, p1: BandChromosome, p2: BandChromosome) -> Tuple[BandChromosome, BandChromosome]:
        """Uniform crossover across 12 binary genes."""
        c1_genes = []
        c2_genes = []
        for g1, g2 in zip(p1.genes, p2.genes):
            if random.random() < 0.5:
                c1_genes.append(g1)
                c2_genes.append(g2)
            else:
                c1_genes.append(g2)
                c2_genes.append(g1)

        # Guard against all-zeros
        if sum(c1_genes) == 0:
            c1_genes[random.randint(0, NUM_BANDS - 1)] = 1
        if sum(c2_genes) == 0:
            c2_genes[random.randint(0, NUM_BANDS - 1)] = 1

        return BandChromosome(c1_genes), BandChromosome(c2_genes)

    def mutate(self, chrom: BandChromosome) -> BandChromosome:
        """Bit-flip mutation with per-gene probability."""
        mutated_genes = []
        for bit in chrom.genes:
            if random.random() < self.mutation_rate:
                mutated_genes.append(1 - bit)  # Flip 0 <-> 1
            else:
                mutated_genes.append(bit)

        if sum(mutated_genes) == 0:
            mutated_genes[random.randint(0, NUM_BANDS - 1)] = 1

        return BandChromosome(mutated_genes)

    def compute_pareto_frontier(self, all_candidates: List[BandChromosome]) -> List[Dict[str, Any]]:
        """
        Extracts non-dominated solutions trading off Accuracy vs Band Count (Efficiency).
        A solution dominates another if it has higher or equal accuracy and fewer or equal bands,
        with at least one strict inequality.
        """
        unique_solutions = {}
        for c in all_candidates:
            key = tuple(c.genes)
            if key not in unique_solutions:
                unique_solutions[key] = c

        candidates = list(unique_solutions.values())
        pareto = []

        for c1 in candidates:
            is_dominated = False
            for c2 in candidates:
                # c2 dominates c1 if c2 has >= accuracy and <= selected_count, with strict inequality
                if (c2.accuracy >= c1.accuracy and c2.selected_count <= c1.selected_count and
                    (c2.accuracy > c1.accuracy or c2.selected_count < c1.selected_count)):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto.append(c1)

        # Sort Pareto solutions by selected_count ascending
        pareto.sort(key=lambda c: c.selected_count)

        return [
            {
                "selected_count": c.selected_count,
                "selected_bands": c.selected_bands,
                "accuracy_f1": c.accuracy,
                "latency_reduction_pct": c.latency_reduction,
                "fitness": c.fitness,
                "genes": c.genes
            }
            for c in pareto
        ]

    def compute_band_importance_weights(self, top_chromosomes: List[BandChromosome]) -> List[Dict[str, Any]]:
        """
        Calculates empirical feature importance based on gene inclusion frequency
        across top elite performers.
        """
        counts = [0] * NUM_BANDS
        total = len(top_chromosomes)

        for c in top_chromosomes:
            for i, bit in enumerate(c.genes):
                counts[i] += bit

        importance_list = []
        for i, meta in enumerate(BAND_METADATA):
            freq = round((counts[i] / total) * 100.0, 1) if total > 0 else 0.0
            importance_list.append({
                "id": meta["id"],
                "name": meta["name"],
                "category": meta["category"],
                "wavelength": meta["wavelength"],
                "selection_frequency_pct": freq,
                "is_critical": freq >= 75.0,
                "description": meta["description"]
            })

        importance_list.sort(key=lambda x: x["selection_frequency_pct"], reverse=True)
        return importance_list

    def run(self) -> Dict[str, Any]:
        """Executes full multi-generation evolutionary band selection."""
        self.initialize_population()
        for c in self.population:
            self.evaluate_chromosome(c)

        all_time_best_list = []
        all_encountered: List[BandChromosome] = list(self.population)

        for gen in range(self.n_generations):
            self.population.sort(key=lambda c: c.fitness, reverse=True)
            best_curr = self.population[0]
            avg_fit = np.mean([c.fitness for c in self.population])
            avg_f1 = np.mean([c.accuracy for c in self.population])
            avg_bands = np.mean([c.selected_count for c in self.population])

            self.history.append({
                "generation": gen + 1,
                "best_fitness": round(best_curr.fitness, 4),
                "avg_fitness": round(float(avg_fit), 4),
                "best_f1": round(best_curr.accuracy, 4),
                "avg_f1": round(float(avg_f1), 4),
                "best_band_count": best_curr.selected_count,
                "avg_band_count": round(float(avg_bands), 1),
                "best_bands": best_curr.selected_bands
            })

            # Preserve top 20% elites
            n_elites = max(2, int(self.pop_size * 0.20))
            next_pop = [BandChromosome(list(c.genes), c.accuracy, c.latency_reduction, c.fitness) for c in self.population[:n_elites]]

            # Breed remainder
            while len(next_pop) < self.pop_size:
                p1 = self.tournament_selection()
                p2 = self.tournament_selection()
                c1, c2 = self.crossover(p1, p2)
                c1 = self.mutate(c1)
                c2 = self.mutate(c2)
                self.evaluate_chromosome(c1)
                self.evaluate_chromosome(c2)
                next_pop.extend([c1, c2])
                all_encountered.extend([c1, c2])

            self.population = next_pop[:self.pop_size]

        # Final best chromosome
        self.population.sort(key=lambda c: c.fitness, reverse=True)
        best_overall = self.population[0]

        # Top 15 elite solutions for importance weights
        elites = self.population[:15]
        band_importance = self.compute_band_importance_weights(elites)

        # Pareto frontier
        pareto = self.compute_pareto_frontier(all_encountered)

        # Find the optimal knee-point solution on the Pareto frontier (best balanced trade-off)
        knee_solution = max(pareto, key=lambda p: p["fitness"]) if pareto else {
            "selected_count": best_overall.selected_count,
            "selected_bands": best_overall.selected_bands,
            "accuracy_f1": best_overall.accuracy,
            "latency_reduction_pct": best_overall.latency_reduction,
            "fitness": best_overall.fitness,
            "genes": best_overall.genes
        }

        return {
            "status": "success",
            "target_region_type": self.target_region_type,
            "population_size": self.pop_size,
            "generations": self.n_generations,
            "mutation_rate": self.mutation_rate,
            "efficiency_weight": self.efficiency_weight,
            "best_solution": {
                "selected_bands": knee_solution["selected_bands"],
                "selected_count": knee_solution["selected_count"],
                "pruned_count": NUM_BANDS - knee_solution["selected_count"],
                "accuracy_f1": knee_solution["accuracy_f1"],
                "latency_reduction_pct": knee_solution["latency_reduction_pct"],
                "fitness": knee_solution["fitness"],
                "gene_mask": knee_solution["genes"],
            },
            "history": self.history,
            "pareto_frontier": pareto,
            "band_importance": band_importance,
            "summary_metrics": {
                "full_spectrum_bands": NUM_BANDS,
                "optimized_bands": knee_solution["selected_count"],
                "cloud_bandwidth_saved_pct": knee_solution["latency_reduction_pct"],
                "f1_retained_pct": round((knee_solution["accuracy_f1"] / 0.962) * 100.0, 1),
                "speedup_factor": round(NUM_BANDS / max(1, knee_solution["selected_count"]), 2)
            }
        }


if __name__ == "__main__":
    ga = MultiSpectralGA(pop_size=25, n_generations=20, efficiency_weight=0.30)
    res = ga.run()
    print("GA Run Complete!")
    print("Best bands:", res["best_solution"]["selected_bands"])
    print("F1:", res["best_solution"]["accuracy_f1"])
    print("Latency reduction:", res["best_solution"]["latency_reduction_pct"], "%")
    print("Pareto points count:", len(res["pareto_frontier"]))
