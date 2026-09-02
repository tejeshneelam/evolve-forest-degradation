import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import LandslideReportModal from './LandslideReportModal';

export default function RiskDashboard() {
  const [fireData, setFireData]             = useState(null);
  const [landslide, setLandslide]           = useState(null);
  const [encroachment, setEncroach]         = useState(null);
  const [loading, setLoading]               = useState(true);
  const [filterSeverity, setFilter]         = useState('ALL');
  const [selectedLandslidePatch, setSelectedPatch] = useState(null);

  useEffect(() => {
    Promise.all([
      api.getFireRisk(),
      api.getLandslide(),
      api.getEncroachment()
    ]).then(([fire, land, enc]) => {
      setFireData(fire);
      setLandslide(land);
      setEncroach(enc);
      setLoading(false);
    }).catch(err => {
      console.error("Error loading risks:", err);
      setLoading(false);
    });
  }, []);

  const openDiagnosticForPatch = (pid, pData) => {
    // Construct patch diagnostic representation
    const slope = (pData.slope_proxy * 10.0);
    const lossPct = pData.recent_loss_pixels ? (pData.recent_loss_pixels / 40.96) : 2.1;
    const probability = pData.vulnerability_score;
    const probPct = (probability * 100).toFixed(1);

    const diag = {
      patch_id: pid,
      grid_row: Math.floor(parseInt(pid) / 8),
      grid_col: parseInt(pid) % 8,
      landslide: {
        probability: probability,
        probability_pct: probPct,
        risk_level: pData.vulnerability_level,
        metrics: {
          slope_angle_deg: slope.toFixed(1),
          tree_cover_pct: Math.max(20, 95 - lossPct * 8).toFixed(1),
          recent_loss_pct: lossPct.toFixed(2),
          rainfall_90d_mm: 310,
        },
        factors: {
          slope_weight: Math.min(1.0, slope / 25.0).toFixed(3),
          root_decay_weight: Math.min(1.0, lossPct / 5.0).toFixed(3),
          pore_pressure_weight: 0.88,
        },
        primary_reasons: [
          `Hillside slope of ${slope.toFixed(1)}° creates strong gravitational downhill traction.`,
          `Recent forest loss removes subsoil root anchors, increasing soil shearing vulnerability.`,
          `Monsoon heavy precipitation saturates sub-surface soil horizons, creating hydrostatic slip planes.`
        ],
        recommended_mitigations: [
          "Deploy deep-rooting bio-stabilization plants (Vetiver grass & native deep-rooted trees).",
          "Construct contoured slope drainage diversion channels to prevent water accumulation.",
          "Restrict cutting unpaved access paths that trigger slope toe failures."
        ]
      }
    };
    setSelectedPatch(diag);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Compiling Risk Assessment Metrics...</span>
      </div>
    );
  }

  const filteredAlerts = encroachment?.alerts.filter(a => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  }) || [];

  return (
    <div className="risk-page">
      {/* Landslide Diagnostic Report Modal */}
      {selectedLandslidePatch && (
        <LandslideReportModal 
          patch={selectedLandslidePatch} 
          onClose={() => setSelectedPatch(null)} 
        />
      )}

      <div className="page-header">
        <h2 className="page-title">🔥 Environmental Risk & Threat Dashboard</h2>
        <p className="page-subtitle">Predictive physics-informed models monitoring landslide vulnerability, fire risks, and illegal forest encroachment in real time.</p>
      </div>

      <div className="page-body">
        {/* Top: 3 Metric cards for summary */}
        <div className="grid-3" style={{ marginBottom: '24px' }}>
          <div className="metric-card card text-center">
            <span className="metric-icon">🔥</span>
            <div className="metric-val">{fireData?.risk_summary.High + fireData?.risk_summary.Critical || 0}</div>
            <div className="metric-label">High/Critical Fire Risk Patches</div>
          </div>
          <div className="metric-card card text-center">
            <span className="metric-icon">⚠️</span>
            <div className="metric-val">{landslide?.vulnerability_summary.High + landslide?.vulnerability_summary.Critical || 0}</div>
            <div className="metric-label">High Landslide Hazard Patches</div>
          </div>
          <div className="metric-card card text-center">
            <span className="metric-icon">🚨</span>
            <div className="metric-val">{encroachment?.total_alerts || 0}</div>
            <div className="metric-label">Total Encroachment Alerts Raised</div>
          </div>
        </div>

        <div className="grid-2">
          {/* Landslide Threat Table */}
          <div className="risk-table-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 className="section-title" style={{ margin: 0 }}>⛰️ Landslide Hazard Assessment</h3>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Click any row to open full diagnostic</span>
            </div>

            <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Patch</th>
                    <th>Slope</th>
                    <th>Risk Score</th>
                    <th>Hazard Level</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(landslide?.patches || {}).sort((a, b) => b[1].vulnerability_score - a[1].vulnerability_score).map(([pid, p]) => (
                    <tr 
                      key={pid} 
                      onClick={() => openDiagnosticForPatch(pid, p)}
                      style={{ cursor: 'pointer' }}
                      title="Click to view detailed landslide diagnostic report"
                    >
                      <td><strong>Patch {pid}</strong></td>
                      <td>{(p.slope_proxy * 10).toFixed(1)}°</td>
                      <td>{(p.vulnerability_score * 100).toFixed(1)}%</td>
                      <td>
                        <span className={`badge badge-${p.vulnerability_level.toLowerCase()}`}>
                          {p.vulnerability_level}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-secondary" 
                          style={{ padding: '3px 8px', fontSize: '10px', color: '#FFB703', borderColor: 'rgba(255, 183, 3, 0.4)' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            openDiagnosticForPatch(pid, p);
                          }}
                        >
                          Diagnostic ↗
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Encroachment Alerts Panel */}
          <div className="encroachment-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 className="section-title" style={{ margin: 0 }}>🚨 Encroachment & Path Logging</h3>
              <select 
                value={filterSeverity} 
                onChange={(e) => setFilter(e.target.value)}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px', padding: '4px 8px', fontSize: '11px' }}
              >
                <option value="ALL">All Alerts</option>
                <option value="High">High Severity</option>
                <option value="Medium">Medium Severity</option>
                <option value="Low">Low Severity</option>
              </select>
            </div>

            <div style={{ maxHeight: '330px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filteredAlerts.slice(0, 30).map((a, idx) => (
                <div key={idx} className="alert-item" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid var(--alert-${a.severity.toLowerCase() === 'high' ? 'red' : (a.severity.toLowerCase() === 'medium' ? 'orange' : 'yellow')})`, padding: '10px 14px', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>Patch {a.patch_id} — {a.alert_type}</span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>📅 {a.month}</span>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-sec)', marginTop: '4px', lineHeight: 1.4 }}>{a.description}</p>
                </div>
              ))}
              {filteredAlerts.length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>No alerts matched this filter.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
