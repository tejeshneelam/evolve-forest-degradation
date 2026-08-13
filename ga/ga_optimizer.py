"""
EvOLve — ga/ga_optimizer.py
Genetic Algorithm for hyperparameter optimization + adaptive threshold evolution.

Chromosome encodes:
  - Model hyperparameters (lr, dropout, hidden_dim)
  - Season-aware NDVI alert thresholds (dry / monsoon / retreat)
  - Reconstruction loss weight

GA Operations: Tournament selection → Uniform crossover → Gaussian mutation
Fitness: F1 score on validation patches
"""

import os
import json
import random
import numpy as np
from copy import deepcopy
from dataclasses import dataclass, asdict, field
from typing import List, Optional


# ── Chromosome Definition ─────────────────────────────────────────────────────

@dataclass
class Chromosome:
    """One individual in the GA population."""
    # Model hyperparameters
    lr:              float = 3e-4
    dropout:         float = 0.2
    hidden_dim:      int   = 128
    nhead:           int   = 4
    num_layers:      int   = 4

    # Season-aware NDVI alert thresholds
    # Dry season (Jan–May): forests more stressed → lower threshold acceptable
    ndvi_thresh_dry:      float = 0.45
    # Monsoon (Jun–Sep): lush → anomaly only if truly low
    ndvi_thresh_monsoon:  float = 0.55
    # Post-monsoon retreat (Oct–Dec): moderate
    ndvi_thresh_retreat:  float = 0.50

    # MTAE loss weights
    lambda_recon:    float = 1.0
    lambda_contrast: float = 0.5

    # Fitness (set after evaluation)
    fitness: float = 0.0


# Gene bounds for clipping during mutation
GENE_BOUNDS = {
    'lr':                (1e-5, 1e-2),
    'dropout':           (0.05, 0.5),
    'hidden_dim':        (64, 256),      # will be rounded to int
    'nhead':             (2, 8),         # must divide hidden_dim
    'num_layers':        (2, 6),
    'ndvi_thresh_dry':   (0.25, 0.70),
    'ndvi_thresh_monsoon':(0.30, 0.75),
    'ndvi_thresh_retreat':(0.25, 0.70),
    'lambda_recon':      (0.5, 2.0),
    'lambda_contrast':   (0.1, 1.0),
}


def random_chromosome(seed: Optional[int] = None) -> Chromosome:
    """Sample a random chromosome within gene bounds."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    hidden_choices = [64, 96, 128, 160, 192, 256]
    nhead_choices  = [2, 4, 8]

    c = Chromosome(
        lr              = 10 ** np.random.uniform(-4.5, -2),
        dropout         = np.random.uniform(*GENE_BOUNDS['dropout']),
        hidden_dim      = random.choice(hidden_choices),
        nhead           = random.choice(nhead_choices),
        num_layers      = random.randint(*GENE_BOUNDS['num_layers']),
        ndvi_thresh_dry     = np.random.uniform(*GENE_BOUNDS['ndvi_thresh_dry']),
        ndvi_thresh_monsoon  = np.random.uniform(*GENE_BOUNDS['ndvi_thresh_monsoon']),
        ndvi_thresh_retreat = np.random.uniform(*GENE_BOUNDS['ndvi_thresh_retreat']),
        lambda_recon    = np.random.uniform(*GENE_BOUNDS['lambda_recon']),
        lambda_contrast = np.random.uniform(*GENE_BOUNDS['lambda_contrast']),
    )
    return c


def _clip(value, gene: str):
    lo, hi = GENE_BOUNDS[gene]
    return float(np.clip(value, lo, hi))


# ── Genetic Operations ────────────────────────────────────────────────────────

def tournament_select(population: List[Chromosome], k: int = 3) -> Chromosome:
    """Tournament selection: pick best of k random individuals."""
    contestants = random.sample(population, min(k, len(population)))
    return max(contestants, key=lambda c: c.fitness)


def crossover(parent1: Chromosome, parent2: Chromosome) -> tuple:
    """Uniform crossover: each gene independently from either parent."""
    child1, child2 = deepcopy(parent1), deepcopy(parent2)
    genes = [g for g in GENE_BOUNDS.keys()]

    for gene in genes:
        if random.random() < 0.5:
            setattr(child1, gene, getattr(parent2, gene))
            setattr(child2, gene, getattr(parent1, gene))

    child1.fitness = 0.0
    child2.fitness = 0.0
    return child1, child2


def mutate(chromosome: Chromosome, mutation_rate: float = 0.15,
           sigma: float = 0.1) -> Chromosome:
    """
    Gaussian mutation on continuous genes.
    For integer genes (hidden_dim, nhead, num_layers): random perturbation.
    """
    c = deepcopy(chromosome)

    if random.random() < mutation_rate:
        c.lr = float(np.clip(c.lr * (1 + np.random.randn() * sigma),
                             *GENE_BOUNDS['lr']))

    if random.random() < mutation_rate:
        c.dropout = float(np.clip(c.dropout + np.random.randn() * 0.05,
                                  *GENE_BOUNDS['dropout']))

    for thresh_gene in ['ndvi_thresh_dry', 'ndvi_thresh_monsoon', 'ndvi_thresh_retreat']:
        if random.random() < mutation_rate:
            val = getattr(c, thresh_gene) + np.random.randn() * 0.05
            setattr(c, thresh_gene, _clip(val, thresh_gene))

    if random.random() < mutation_rate:
        hidden_choices = [64, 96, 128, 160, 192, 256]
        c.hidden_dim = random.choice(hidden_choices)

    if random.random() < mutation_rate:
        c.num_layers = int(np.clip(c.num_layers + random.choice([-1, 1]),
                                   *GENE_BOUNDS['num_layers']))

    if random.random() < mutation_rate:
        c.lambda_recon = float(np.clip(
            c.lambda_recon + np.random.randn() * 0.1, *GENE_BOUNDS['lambda_recon']))

    if random.random() < mutation_rate:
        c.lambda_contrast = float(np.clip(
            c.lambda_contrast + np.random.randn() * 0.1, *GENE_BOUNDS['lambda_contrast']))

    c.fitness = 0.0
    return c


# ── GA Main Loop ──────────────────────────────────────────────────────────────

class GeneticAlgorithm:
    """
    Full GA for EvOLve hyperparameter + threshold optimization.

    Parameters
    ----------
    pop_size       : population size
    n_generations  : number of generations
    mutation_rate  : per-gene mutation probability
    elite_fraction : fraction of top individuals preserved each gen
    fitness_fn     : callable(Chromosome) → float (F1 score)
    results_dir    : where to save progress + best chromosome
    """

    def __init__(
        self,
        pop_size: int = 20,
        n_generations: int = 30,
        mutation_rate: float = 0.15,
        elite_fraction: float = 0.2,
        fitness_fn=None,
        results_dir: str = 'results',
    ):
        self.pop_size       = pop_size
        self.n_generations  = n_generations
        self.mutation_rate  = mutation_rate
        self.n_elite        = max(1, int(pop_size * elite_fraction))
        self.fitness_fn     = fitness_fn
        self.results_dir    = results_dir
        os.makedirs(results_dir, exist_ok=True)

        self.population: List[Chromosome] = []
        self.history: List[dict] = []

    def initialize(self):
        """Create initial random population."""
        self.population = [random_chromosome(seed=i) for i in range(self.pop_size)]
        print(f"GA initialized: {self.pop_size} chromosomes, {self.n_generations} generations")

    def evaluate_population(self):
        """Evaluate fitness for all unevaluated chromosomes."""
        for i, chrom in enumerate(self.population):
            if chrom.fitness == 0.0:
                try:
                    chrom.fitness = self.fitness_fn(chrom)
                except Exception as e:
                    print(f"  Fitness eval error for chrom {i}: {e}")
                    chrom.fitness = 0.01

    def step(self) -> List[Chromosome]:
        """One generation: evaluate → select → crossover → mutate."""
        self.evaluate_population()
        self.population.sort(key=lambda c: c.fitness, reverse=True)

        # Elitism: keep top N
        next_pop = deepcopy(self.population[:self.n_elite])

        # Fill rest with offspring
        while len(next_pop) < self.pop_size:
            p1 = tournament_select(self.population)
            p2 = tournament_select(self.population)
            c1, c2 = crossover(p1, p2)
            c1 = mutate(c1, self.mutation_rate)
            c2 = mutate(c2, self.mutation_rate)
            next_pop.extend([c1, c2])

        self.population = next_pop[:self.pop_size]
        return self.population

    def run(self) -> Chromosome:
        """Full GA run. Returns best chromosome found."""
        self.initialize()

        for gen in range(1, self.n_generations + 1):
            self.step()

            best    = self.population[0]
            avg_fit = np.mean([c.fitness for c in self.population])

            entry = {
                'generation':   gen,
                'best_fitness': round(best.fitness, 4),
                'avg_fitness':  round(avg_fit, 4),
                'best_chrom':   {k: round(v, 5) if isinstance(v, float) else v
                                 for k, v in asdict(best).items()},
            }
            self.history.append(entry)

            print(f"Gen {gen:3d}/{self.n_generations} | "
                  f"Best F1={best.fitness:.4f} | Avg F1={avg_fit:.4f} | "
                  f"LR={best.lr:.5f} | NDVI_dry={best.ndvi_thresh_dry:.3f} | "
                  f"NDVI_mon={best.ndvi_thresh_monsoon:.3f}")

            # Save progress
            self._save_progress(best)

        best = max(self.population, key=lambda c: c.fitness)
        print(f"\n✅ GA complete. Best F1={best.fitness:.4f}")
        print(f"   lr={best.lr:.6f}, dropout={best.dropout:.3f}, "
              f"hidden={best.hidden_dim}, layers={best.num_layers}")
        print(f"   NDVI thresholds: dry={best.ndvi_thresh_dry:.3f}, "
              f"monsoon={best.ndvi_thresh_monsoon:.3f}, "
              f"retreat={best.ndvi_thresh_retreat:.3f}")
        return best

    def _save_progress(self, best: Chromosome):
        path = os.path.join(self.results_dir, 'ga_results.json')
        with open(path, 'w') as f:
            json.dump({
                'best_chromosome': asdict(best),
                'history':         self.history,
            }, f, indent=2)
