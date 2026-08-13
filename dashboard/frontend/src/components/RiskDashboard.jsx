import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function RiskDashboard() {
  const [fireData, setFireData]     = useState(null);
  const [landslide, setLandslide]   = useState(null);
  const [encroachment, setEncroach] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [filterSeverity, setFilter] = useState('ALL');

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
      <div className="page-header">
        <h2 className="page-title">🔥 Environmental Risk & Threat Dashboard</h2>
        <p className="page-subtitle">Predictive models monitoring fire risks, landslide vulnerability, and illegal forest encroachment in real time.</p>
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
            <div className="metric-label">High Landslide Hazard Patches (Wayanad)</div>
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
            <h3 className="section-title">⛰️ Landslide Hazard Assessment</h3>
            <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Patch ID</th>
                    <th>Slope Index</th>
                    <th>Recent Loss</th>
                    <th>Risk Level</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(landslide?.patches || {}).filter(([_, p]) => p.vulnerability_score > 0.4).map(([pid, p]) => (
                    <tr key={pid}>
                      <td><strong>Patch {pid}</strong></td>
                      <td>{(p.slope_proxy * 10).toFixed(1)}°</td>
                      <td>{p.recent_loss_pixels} px</td>
                      <td>
                        <span className={`badge badge-${p.vulnerability_level.toLowerCase()}`}>
                          {p.vulnerability_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Encroachment Alerts Panel */}
          <div className="encroachment-card card">
            <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 className="section-title" style={{ margin: 0 }}>🚨 Encroachment & Path Logging</h3>
              <select 
                value={filterSeverity} 
                onChange={(e) => setFilter(e.target.value)}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px', padding: '4px 8px', fontSize: '11px', marginLeft: 'auto' }}
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
                  <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>Patch {a.patch_id} — {a.alert_type}</span>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: 'auto' }}>📅 {a.month}</span>
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
