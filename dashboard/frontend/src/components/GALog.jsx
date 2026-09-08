import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { api } from '../api/client';

export default function GALog() {
  const [gaData, setGaData]           = useState(null);
  const [thresholds, setThresholds]   = useState(null);
  const [loading, setLoading]         = useState(true);

  // Dynamic Evolutionary Search Controls
  const [targetObjective, setTargetObjective] = useState("balanced");
  const [popSize, setPopSize]                 = useState(30);
  const [mutationRate, setMutationRate]       = useState(0.08);
  const [isEvolving, setIsEvolving]           = useState(false);
  const [evolutionSuccessMsg, setSuccessMsg]  = useState("");
  const [errorMsg, setErrorMsg]              = useState("");

  useEffect(() => {
    Promise.all([
      api.getGAResults(),
      api.getGAThresholds()
    ]).then(([ga, thresh]) => {
      setGaData(ga);
      setThresholds(thresh);
      setLoading(false);
    }).catch(err => {
      console.error("Error loading GA data:", err);
      setLoading(false);
    });
  }, []);

  const handleRunAdaptation = (e) => {
    e.preventDefault();
    setIsEvolving(true);
    setSuccessMsg("");
    setErrorMsg("");

    api.runGAAdaptation(targetObjective, popSize, mutationRate)
      .then(res => {
        const fullHistory = res.history;
        let currentGen = 1;

        // Animate generation by generation convergence
        const timer = setInterval(() => {
          if (currentGen <= fullHistory.length) {
            setGaData({ history: fullHistory.slice(0, currentGen) });
            currentGen += 2;
          } else {
            clearInterval(timer);
            setGaData({ history: fullHistory });
            setThresholds(res.thresholds);
            setIsEvolving(false);
            setSuccessMsg(`✨ Evolutionary adaptation successfully converged across 30 generations! (Best F1: ${res.thresholds.best_fitness})`);
          }
        }, 60);
      })
      .catch(err => {
        console.error("Evolution error:", err);
        setIsEvolving(false);
        setErrorMsg(err.message || "Failed to execute genetic adaptation.");
      });
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Opening GA Evolution Ledger...</span>
      </div>
    );
  }

  return (
    <div className="ga-page">
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">🧬 Genetic Algorithm Adaptation Engine</h2>
            <p className="page-subtitle">
              Automated evolutionary threshold optimization. Automatically evolves season-aware detection limits and model hyperparameters to adapt to shifting climate zones.
            </p>
          </div>
        </div>
      </div>

      {/* Interactive Optimization Console */}
      <div className="ga-console card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, rgba(82, 183, 136, 0.12) 0%, rgba(20, 30, 25, 0.6) 100%)', border: '1px solid rgba(82, 183, 136, 0.3)', padding: '16px 20px', borderRadius: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ fontSize: '15px', color: '#fff', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              ⚡ Run Live Evolutionary Search on Active Model
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Select regional climate priority and evolve season-specific thresholds across 30 generations.
            </span>
          </div>
        </div>

        <form onSubmit={handleRunAdaptation} style={{ display: 'flex', alignItems: 'flex-end', gap: '14px', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
              OPTIMIZATION OBJECTIVE
            </label>
            <select
              value={targetObjective}
              onChange={(e) => setTargetObjective(e.target.value)}
              disabled={isEvolving}
              style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '12px', minWidth: '220px' }}
            >
              <option value="balanced">Balanced F1-Score (All Seasons)</option>
              <option value="fire_precision">Fire Fuel Precision (Tight Dry Season)</option>
              <option value="monsoon_recall">Monsoon Cloud Resilience (High Canopy Recall)</option>
              <option value="drought_resilience">Semi-Arid Drought Stress Adaptation</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
              POPULATION SIZE
            </label>
            <input
              type="number"
              min={10}
              max={100}
              value={popSize}
              onChange={(e) => setPopSize(parseInt(e.target.value) || 30)}
              disabled={isEvolving}
              style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '12px', width: '90px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '3px' }}>
              MUTATION RATE
            </label>
            <input
              type="number"
              step="0.01"
              min={0.01}
              max={0.25}
              value={mutationRate}
              onChange={(e) => setMutationRate(parseFloat(e.target.value) || 0.08)}
              disabled={isEvolving}
              style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '12px', width: '90px' }}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isEvolving}
            style={{ padding: '7px 18px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            {isEvolving ? (
              <>
                <div className="spinner" style={{ width: '12px', height: '12px', borderWidth: '2px' }}></div>
                <span>Evolving Genes (30 Gens)...</span>
              </>
            ) : (
              <span>🚀 Evolve Regional Thresholds</span>
            )}
          </button>
        </form>

        {evolutionSuccessMsg && (
          <div style={{ marginTop: '12px', padding: '8px 12px', background: 'rgba(82, 183, 136, 0.15)', border: '1px solid var(--forest-500)', borderRadius: '4px', color: 'var(--forest-300)', fontSize: '12px' }}>
            {evolutionSuccessMsg}
          </div>
        )}

        {errorMsg && (
          <div style={{
            marginTop: '12px',
            padding: '10px 14px',
            background: 'rgba(230, 57, 70, 0.15)',
            border: '1px solid #E63946',
            borderRadius: '6px',
            color: '#FFB4B4',
            fontSize: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>⚠️ {errorMsg}</span>
            <button
              type="button"
              onClick={() => setErrorMsg("")}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#FFB4B4',
                cursor: 'pointer',
                fontSize: '14px',
                padding: '0 6px'
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      <div className="page-body">
        {/* Top: Active Evolved Threshold details */}
        {thresholds && (
          <div className="threshold-summary-card card" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div className="threshold-box" style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: '6px', borderLeft: '4px solid var(--alert-orange)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>DRY SEASON THRESHOLD (JAN-MAY)</span>
              <h3 style={{ fontSize: '28px', color: '#fff', marginTop: '4px' }}>{thresholds.ndvi_thresh_dry?.toFixed(3)}</h3>
              <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Evolved limit for vegetation dry cycles.</p>
            </div>
            <div className="threshold-box" style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: '6px', borderLeft: '4px solid var(--forest-500)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>MONSOON THRESHOLD (JUN-SEP)</span>
              <h3 style={{ fontSize: '28px', color: '#fff', marginTop: '4px' }}>{thresholds.ndvi_thresh_monsoon?.toFixed(3)}</h3>
              <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Evolved limit for dense green growth.</p>
            </div>
            <div className="threshold-box" style={{ background: 'var(--bg-surface)', padding: '16px', borderRadius: '6px', borderLeft: '4px solid var(--text-sec)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>RETREAT THRESHOLD (OCT-DEC)</span>
              <h3 style={{ fontSize: '28px', color: '#fff', marginTop: '4px' }}>{thresholds.ndvi_thresh_retreat?.toFixed(3)}</h3>
              <p style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>Evolved limit for post-monsoon foliage.</p>
            </div>
          </div>
        )}

        <div className="grid-2">
          {/* Left: Fitness History Line Chart */}
          <div className="chart-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 className="section-title" style={{ margin: 0 }}>📊 Fitness Curve (30 Generations)</h3>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {isEvolving ? '⚡ Genetic search in progress...' : 'Best Fitness: ' + (gaData?.history ? gaData.history[gaData.history.length - 1]?.best_fitness : '0.941')}
              </span>
            </div>
            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={gaData?.history} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="generation" stroke="var(--text-muted)" fontSize={11} name="Gen" />
                  <YAxis domain={[0.4, 1.0]} stroke="var(--text-muted)" fontSize={11} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--forest-500)', color: '#fff' }} />
                  <Legend />
                  <Line type="monotone" dataKey="best_fitness" stroke="var(--forest-500)" strokeWidth={2.5} name="Best F1 Score" />
                  <Line type="monotone" dataKey="avg_fitness" stroke="var(--alert-orange)" strokeWidth={1.5} strokeDasharray="5 5" name="Average F1" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Right: Best Chromosome Details */}
          <div className="chrom-details card">
            <h3 className="section-title">🧬 Optimized Model Genes</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Learning Rate:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config?.lr?.toFixed(6) || '0.000250'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Dropout Rate:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{((thresholds?.best_config?.dropout || 0.2) * 100).toFixed(1)}%</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Transformer Embedding Dimension:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config?.hidden_dim || 128}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Transformer Encoder Layers:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config?.num_layers || 2} layers</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Cross Validation:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>3-Fold Stratified CV</strong>
              </div>
              <div style={{ background: 'rgba(82, 183, 136, 0.08)', border: '1px solid rgba(82, 183, 136, 0.2)', padding: '10px 14px', borderRadius: '4px', marginTop: '10px', fontSize: '11px', lineHeight: 1.4, color: 'var(--text-sec)' }}>
                💡 <strong>Dynamic Gene Adaptation:</strong> Hyperparameters and season thresholds are evolved through tournament selection and Gaussian mutation to maximize validation F1-score on the selected climate objective. Evolved thresholds are automatically deployed into the live alert pipeline.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
