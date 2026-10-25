"""
EvOLve Test Suite — tests/test_genetic_algorithm.py
Validates Genetic Algorithm chromosome operators, fitness evaluation, and Pareto frontier.
"""

from ga.ga_optimizer import Chromosome, random_chromosome, tournament_select, crossover, mutate, GENE_BOUNDS
from ga.band_selection_ga import (
    BandChromosome,
    MultiSpectralGA,
    evaluate_band_subset,
    NUM_BANDS
)


def test_chromosome_bounds():
    """Validates that randomly sampled chromosomes respect all configured gene boundaries."""
    c = random_chromosome(seed=42)
    assert GENE_BOUNDS['lr'][0] <= c.lr <= GENE_BOUNDS['lr'][1]
    assert GENE_BOUNDS['dropout'][0] <= c.dropout <= GENE_BOUNDS['dropout'][1]
    assert GENE_BOUNDS['ndvi_thresh_dry'][0] <= c.ndvi_thresh_dry <= GENE_BOUNDS['ndvi_thresh_dry'][1]
    assert GENE_BOUNDS['ndvi_thresh_monsoon'][0] <= c.ndvi_thresh_monsoon <= GENE_BOUNDS['ndvi_thresh_monsoon'][1]


def test_ga_tournament_selection():
    """Tournament selection must always pick the highest-fitness contestant among k participants."""
    pop = [
        Chromosome(fitness=0.45),
        Chromosome(fitness=0.88),
        Chromosome(fitness=0.62),
    ]
    winner = tournament_select(pop, k=3)
    assert winner.fitness == 0.88


def test_ga_crossover():
    """Uniform crossover produces valid children from two parent chromosomes."""
    p1 = Chromosome(lr=1e-4, dropout=0.1, hidden_dim=64)
    p2 = Chromosome(lr=1e-3, dropout=0.4, hidden_dim=256)
    c1, c2 = crossover(p1, p2)
    assert c1.fitness == 0.0
    assert c2.fitness == 0.0
    assert c1.hidden_dim in [64, 256]
    assert c2.hidden_dim in [64, 256]


def test_band_selection_empty_penalty():
    """All-zero band chromosome should receive a harsh penalty."""
    empty_genes = [0] * NUM_BANDS
    f1, latency_red, fitness = evaluate_band_subset(empty_genes)
    assert fitness <= 0.05
    assert f1 <= 0.20


def test_band_selection_synergy_nir_swir():
    """Selecting NIR and SWIR channels should score higher than selecting only visible channels."""
    vis_only = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # B2, B3
    nir_swir = [0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0]  # B4, B8, B11, NDVI, NBR
    f1_vis, _, _ = evaluate_band_subset(vis_only)
    f1_nir, _, _ = evaluate_band_subset(nir_swir)
    assert f1_nir > f1_vis
    assert f1_nir >= 0.90


def test_multispectral_ga_run():
    """MultiSpectralGA must discover a non-empty Pareto frontier and valid knee point."""
    ga = MultiSpectralGA(pop_size=15, n_generations=10, efficiency_weight=0.30, seed=123)
    res = ga.run()
    assert res['status'] == "success"
    assert "best_solution" in res
    best = res['best_solution']
    assert 1 <= best['selected_count'] <= 12
    assert best['accuracy_f1'] > 0.85
    assert best['latency_reduction_pct'] >= 0.0
    assert len(res['pareto_frontier']) > 0
    assert len(res['band_importance']) == 12
