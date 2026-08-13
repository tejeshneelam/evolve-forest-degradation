"""
EvOLve — ga/run_ga.py
Entry point: run the full GA and save best chromosome.

Usage:
    python ga/run_ga.py

Outputs:
    results/ga_results.json       — full history + best chromosome
    results/best_thresholds.json  — season-aware thresholds for alerting
"""

import os
import json
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ga.ga_optimizer import GeneticAlgorithm
from ga.fitness import evaluate_chromosome

RESULTS_DIR = 'results'

def main():
    print("=" * 60)
    print("EvOLve Genetic Algorithm — Hyperparameter + Threshold Optimization")
    print("=" * 60)

    ga = GeneticAlgorithm(
        pop_size=20,
        n_generations=30,
        mutation_rate=0.15,
        elite_fraction=0.20,
        fitness_fn=evaluate_chromosome,
        results_dir=RESULTS_DIR,
    )

    best = ga.run()

    # Save best thresholds separately for use by the dashboard + alerting
    thresholds = {
        'ndvi_thresh_dry':      round(best.ndvi_thresh_dry, 4),
        'ndvi_thresh_monsoon':  round(best.ndvi_thresh_monsoon, 4),
        'ndvi_thresh_retreat':  round(best.ndvi_thresh_retreat, 4),
        'description': {
            'dry':      'Jan–May: dry season threshold',
            'monsoon':  'Jun–Sep: peak monsoon threshold',
            'retreat':  'Oct–Dec: post-monsoon retreat threshold',
        },
        'best_fitness': round(best.fitness, 4),
        'best_config': {
            'lr':           round(best.lr, 6),
            'dropout':      round(best.dropout, 4),
            'hidden_dim':   best.hidden_dim,
            'num_layers':   best.num_layers,
        }
    }

    out_path = os.path.join(RESULTS_DIR, 'best_thresholds.json')
    with open(out_path, 'w') as f:
        json.dump(thresholds, f, indent=2)

    print(f"\n✅ Best thresholds saved: {out_path}")
    print(json.dumps(thresholds, indent=2))


if __name__ == '__main__':
    main()
