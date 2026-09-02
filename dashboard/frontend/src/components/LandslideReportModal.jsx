import React from 'react';

export default function LandslideReportModal({ patch, onClose }) {
  if (!patch || !patch.landslide) return null;

  const diag = patch.landslide;
  const metrics = diag.metrics;
  const factors = diag.factors;

  const getRiskColor = (level) => {
    switch (level) {
      case 'Critical': return 'var(--alert-red)';
      case 'High':     return '#FF5722';
      case 'Moderate': return 'var(--alert-orange)';
      default:         return 'var(--alert-green)';
    }
  };

  const riskColor = getRiskColor(diag.risk_level);

  return (
    <div className="modal-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 15, 10, 0.85)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div className="modal-card card" style={{
        width: '100%',
        maxWidth: '680px',
        maxHeight: '90vh',
        overflowY: 'auto',
        background: 'var(--bg-card)',
        border: `1px solid ${riskColor}40`,
        boxShadow: `0 12px 40px rgba(0,0,0,0.6), 0 0 20px ${riskColor}20`,
        position: 'relative'
      }}>
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid rgba(82,183,136,0.15)', paddingBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '20px', color: '#fff', margin: 0 }}>
                ⛰️ Landslide Hazard Diagnostic Report
              </h2>
              <span className="badge" style={{ backgroundColor: `${riskColor}25`, color: riskColor, border: `1px solid ${riskColor}60` }}>
                {diag.risk_level} Risk
              </span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              Patch ID: <strong>{patch.patch_id}</strong> (Row {patch.grid_row}, Col {patch.grid_col}) • Lat/Lon: [{patch.center ? patch.center.map(c => c.toFixed(4)).join(', ') : 'N/A'}]
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="btn btn-secondary" 
            style={{ padding: '6px 12px', fontSize: '12px', cursor: 'pointer' }}
          >
            ✕ Close
          </button>
        </div>

        {/* Probability Meter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', margin: '20px 0', padding: '16px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(82,183,136,0.1)' }}>
          <div style={{ textAlign: 'center', minWidth: '110px' }}>
            <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '32px', fontWeight: 700, color: riskColor, lineHeight: 1 }}>
              {diag.probability_pct}%
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Probability
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${diag.probability_pct}%`, backgroundColor: riskColor, borderRadius: '4px', transition: 'width 0.6s ease' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '6px' }}>
              <span>0% Safe</span>
              <span>25% Moderate</span>
              <span>45% High</span>
              <span>65%+ Critical</span>
            </div>
          </div>
        </div>

        {/* Physical Satellite Metrics */}
        <h4 className="section-title" style={{ fontSize: '13px', marginBottom: '10px' }}>
          🛰️ Earth Observation Physics Indicators
        </h4>
        <div className="grid-4" style={{ gap: '10px', marginBottom: '20px' }}>
          <div style={{ background: 'rgba(82,183,136,0.05)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(82,183,136,0.1)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>SLOPE (SRTM)</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>{metrics.slope_angle_deg}°</div>
            <div style={{ fontSize: '9px', color: metrics.slope_angle_deg > 15 ? 'var(--alert-red)' : 'var(--forest-300)' }}>
              {metrics.slope_angle_deg > 15 ? 'Critical Gradient' : 'Stable Incline'}
            </div>
          </div>

          <div style={{ background: 'rgba(82,183,136,0.05)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(82,183,136,0.1)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>CANOPY COVER</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>{metrics.tree_cover_pct}%</div>
            <div style={{ fontSize: '9px', color: metrics.tree_cover_pct < 40 ? 'var(--alert-orange)' : 'var(--forest-500)' }}>
              {metrics.tree_cover_pct < 40 ? 'Depleted Root Layer' : 'Intact Root Anchor'}
            </div>
          </div>

          <div style={{ background: 'rgba(82,183,136,0.05)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(82,183,136,0.1)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FOREST LOSS</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>{metrics.recent_loss_pct}%</div>
            <div style={{ fontSize: '9px', color: metrics.recent_loss_pct > 1.5 ? 'var(--alert-red)' : 'var(--forest-300)' }}>
              {metrics.recent_loss_pct > 1.5 ? 'Active Clearing' : 'Minimal Loss'}
            </div>
          </div>

          <div style={{ background: 'rgba(82,183,136,0.05)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(82,183,136,0.1)' }}>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>90D RAINFALL (CHIRPS)</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>{metrics.rainfall_90d_mm} mm</div>
            <div style={{ fontSize: '9px', color: metrics.rainfall_90d_mm > 250 ? 'var(--alert-red)' : 'var(--forest-300)' }}>
              {metrics.rainfall_90d_mm > 250 ? 'Pore Saturation High' : 'Safe Hydrology'}
            </div>
          </div>
        </div>

        {/* Physical Causality Breakdown */}
        <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px', border: '1px solid rgba(82,183,136,0.1)' }}>
          <h4 style={{ fontSize: '12px', color: 'var(--forest-300)', margin: '0 0 8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            🔍 Diagnostic Analysis (Why is this place at risk?)
          </h4>
          <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--text-sec)', lineHeight: 1.5 }}>
            {diag.primary_reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>

        {/* Actionable Mitigations */}
        <div style={{ background: 'rgba(82,183,136,0.08)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(82,183,136,0.2)' }}>
          <h4 style={{ fontSize: '12px', color: '#52B788', margin: '0 0 8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            🛡️ Recommended Engineering & Bio-Mitigations
          </h4>
          <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#fff', lineHeight: 1.5 }}>
            {diag.recommended_mitigations.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
