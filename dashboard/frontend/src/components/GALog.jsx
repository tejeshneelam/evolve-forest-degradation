import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { api } from '../api/client';

export default function GALog() {
  const [gaData, setGaData]           = useState(null);
  const [thresholds, setThresholds]   = useState(null);
  const [loading, setLoading]         = useState(true);

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
      <div className="page-header">
        <h2 className="page-title">🧬 Genetic Algorithm Adaptation Log</h2>
        <p className="page-subtitle">Historical log of threshold evolution. Evolving season-aware limits automatically to adapt to climate changes without manual retraining.</p>
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
            <h3 className="section-title">📊 Fitness Curve (30 Generations)</h3>
            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={gaData?.history} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="generation" stroke="var(--text-muted)" fontSize={11} name="Gen" />
                  <YAxis domain={[0, 1]} stroke="var(--text-muted)" fontSize={11} />
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
              <div style={{ display: 'flex', justifyContent: 'between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Learning Rate:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config.lr?.toFixed(6)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Dropout Rate:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{(thresholds?.best_config.dropout * 100).toFixed(1)}%</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Transformer Embedding Dimension:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config.hidden_dim}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Transformer Encoder Layers:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>{thresholds?.best_config.num_layers} layers</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Cross Validation folds:</span>
                <strong style={{ marginLeft: 'auto', color: 'var(--forest-300)' }}>3-Fold Stratified CV</strong>
              </div>
              <div style={{ background: 'rgba(82, 183, 136, 0.08)', border: '1px solid rgba(82, 183, 136, 0.2)', padding: '10px 14px', borderRadius: '4px', marginTop: '10px', fontSize: '11px', lineHeight: 1.4, color: 'var(--text-sec)' }}>
                💡 <strong>Adaptation Complete:</strong> Hyperparameters and thresholds were evolved to maximize validation F1-score on regional forest loss patterns. Evolved thresholds are fed into the live alerting pipelines automatically.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
