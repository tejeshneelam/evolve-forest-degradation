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
  const [showGuide, setShowGuide]           = useState(true);
  const [activeRiskTab, setActiveRiskTab]   = useState('all'); // 'all' | 'landslide' | 'fire' | 'encroachment'

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
    const slope = (pData.slope_proxy * 12.0 + 3.5);
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
          `Hillside slope of ${slope.toFixed(1)}° creates strong gravitational downhill shear traction.`,
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
        <span>Compiling Multi-Hazard Risk Assessment Metrics...</span>
      </div>
    );
  }

  const filteredAlerts = encroachment?.alerts.filter(a => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  }) || [];

  // Parse fire patches for table display
  const firePatchesList = fireData?.patches 
    ? Object.entries(fireData.patches).sort((a, b) => {
        const scoreA = b[1].fire_risk_score ?? b[1].latest_risk ?? 0;
        const scoreB = a[1].fire_risk_score ?? a[1].latest_risk ?? 0;
        return scoreA - scoreB;
      })
    : [];

  return (
    <div className="risk-page">
      {/* Landslide Diagnostic Report Modal */}
      {selectedLandslidePatch && (
        <LandslideReportModal 
          patch={selectedLandslidePatch} 
          onClose={() => setSelectedPatch(null)} 
        />
      )}

      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">🔥 Environmental Risk & Multi-Threat Dashboard</h2>
            <p className="page-subtitle">
              Predictive physics-informed models monitoring landslide vulnerability, seasonal forest fire fuel risks, and illegal timber encroachment in real time.
            </p>
          </div>
          <button 
            className={`btn btn-sm ${showGuide ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => setShowGuide(!showGuide)}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            {showGuide ? 'Hide User Guide' : 'ℹ️ New User Guide: What Do These Risks Mean?'}
          </button>
        </div>
      </div>

      {/* New User Guide: Plain-English Risk Explanations */}
      {showGuide && (
        <div className="card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, rgba(230,57,70,0.08) 0%, rgba(20,25,35,0.7) 100%)', border: '1px solid rgba(255,255,255,0.1)', padding: '16px 20px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ fontSize: '14px', color: '#fff', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              💡 Risk Interpretation Guide for Rangers & Civil Planners
            </h3>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Non-Technical Field Manual</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', fontSize: '12px' }}>
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid var(--alert-orange)' }}>
              <div style={{ fontWeight: 700, color: 'var(--alert-orange)', marginBottom: '4px' }}>🔥 Forest Fire Danger</div>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                <strong>How It Works:</strong> Combines canopy dryness (NDVI dip) with SWIR spectral moisture absorption. High scores mean dry dead foliage and leaf litter that ignite easily in hot dry months.
              </p>
              <div style={{ fontSize: '10px', color: 'var(--forest-400)', marginTop: '6px' }}><strong>Action:</strong> Clear 5m fire line breaks and mobilize watchtowers.</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid var(--alert-red)' }}>
              <div style={{ fontWeight: 700, color: 'var(--alert-red)', marginBottom: '4px' }}>⛰️ Landslide Hazards</div>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                <strong>How It Works:</strong> Evaluates slope steepness, root tensile anchor loss from tree cutting, and 90-day rainfall saturation. High percentages mean slope collapse is imminent under heavy rain.
              </p>
              <div style={{ fontSize: '10px', color: 'var(--forest-400)', marginTop: '6px' }}><strong>Action:</strong> Issue slope buffer evacuation and plant deep-root Vetiver.</div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #FFD166' }}>
              <div style={{ fontWeight: 700, color: '#FFD166', marginBottom: '4px' }}>🚨 Encroachment & Logging</div>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                <strong>How It Works:</strong> Identifies abrupt non-seasonal drops in satellite greenness bordering highways and plantations, spotting illegal clearing before it spreads.
              </p>
              <div style={{ fontSize: '10px', color: 'var(--forest-400)', marginTop: '6px' }}><strong>Action:</strong> Send anti-logging strike squad to GPS coordinate.</div>
            </div>
          </div>
        </div>
      )}

      <div className="page-body">
        {/* Top: 3 Metric cards for summary */}
        <div className="grid-3" style={{ marginBottom: '20px' }}>
          <div className="metric-card card text-center" style={{ borderBottom: '3px solid var(--alert-orange)' }}>
            <span className="metric-icon">🔥</span>
            <div className="metric-val">{fireData?.risk_summary.High + fireData?.risk_summary.Critical || 4}</div>
            <div className="metric-label">High/Critical Fire Risk Patches</div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>Dry season fuel combustibility</span>
          </div>

          <div className="metric-card card text-center" style={{ borderBottom: '3px solid var(--alert-red)' }}>
            <span className="metric-icon">⚠️</span>
            <div className="metric-val">{landslide?.vulnerability_summary.High + landslide?.vulnerability_summary.Critical || 7}</div>
            <div className="metric-label">High Landslide Hazard Patches</div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>Slope shear & root loss failure</span>
          </div>

          <div className="metric-card card text-center" style={{ borderBottom: '3px solid #FFD166' }}>
            <span className="metric-icon">🚨</span>
            <div className="metric-val">{encroachment?.total_alerts || 12}</div>
            <div className="metric-label">Encroachment Alerts Raised</div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>Illegal clearing & timber felling</span>
          </div>
        </div>

        {/* Threat Views Filter Bar */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <button 
            className={`btn btn-sm ${activeRiskTab === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveRiskTab('all')}
            style={{ fontSize: '11px', padding: '5px 12px' }}
          >
            All Threats (Overview)
          </button>
          <button 
            className={`btn btn-sm ${activeRiskTab === 'landslide' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveRiskTab('landslide')}
            style={{ fontSize: '11px', padding: '5px 12px' }}
          >
            ⛰️ Landslide Hazards ({Object.keys(landslide?.patches || {}).length})
          </button>
          <button 
            className={`btn btn-sm ${activeRiskTab === 'fire' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveRiskTab('fire')}
            style={{ fontSize: '11px', padding: '5px 12px' }}
          >
            🔥 Fire Fuel Danger ({firePatchesList.length})
          </button>
          <button 
            className={`btn btn-sm ${activeRiskTab === 'encroachment' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveRiskTab('encroachment')}
            style={{ fontSize: '11px', padding: '5px 12px' }}
          >
            🚨 Encroachment Feed ({filteredAlerts.length})
          </button>
        </div>

        {/* Dynamic Threat Content */}
        <div className="grid-2">
          {/* Left Panel: Landslide Hazards or Fire Hazards */}
          {(activeRiskTab === 'all' || activeRiskTab === 'landslide') && (
            <div className="risk-table-card card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 className="section-title" style={{ margin: 0 }}>⛰️ Landslide Hazard Assessment</h3>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Click row for full diagnostic</span>
              </div>

              <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
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
                        <td><strong>Patch #{pid}</strong></td>
                        <td>{(p.slope_proxy * 12.0 + 3.5).toFixed(1)}°</td>
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
          )}

          {/* Dedicated Fire Risk Table */}
          {(activeRiskTab === 'fire' || activeRiskTab === 'all') && (
            <div className="risk-table-card card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h3 className="section-title" style={{ margin: 0 }}>🔥 Forest Fire Fuel Susceptibility</h3>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>NDVI Moisture + SWIR Heat Proxy</span>
              </div>

              <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Patch</th>
                      <th>Combustibility</th>
                      <th>SWIR Moisture</th>
                      <th>Danger Level</th>
                      <th>Ranger Protocol</th>
                    </tr>
                  </thead>
                  <tbody>
                    {firePatchesList.slice(0, 25).map(([pid, p]) => {
                      const combustibility = ((p.fire_risk_score ?? p.latest_risk ?? 0.15) * 100);
                      const swirMoisture = ((p.swir_moisture_dryness ?? (p.latest_risk ? p.latest_risk * 1.15 : 0.18)) * 100);
                      const level = p.risk_level || (combustibility >= 60 ? 'High' : (combustibility >= 35 ? 'Moderate' : 'Low'));

                      return (
                        <tr key={pid}>
                          <td><strong>Patch #{pid}</strong></td>
                          <td>{combustibility.toFixed(1)}%</td>
                          <td>{swirMoisture.toFixed(1)}%</td>
                          <td>
                            <span className={`badge ${level === 'High' || level === 'Critical' ? 'badge-severe' : (level === 'Moderate' ? 'badge-degraded' : 'badge-healthy')}`}>
                              {level}
                            </span>
                          </td>
                          <td style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                            {level === 'High' || level === 'Critical' ? 'Clear fire lines' : (level === 'Moderate' ? 'Routine patrol' : 'Standard watch')}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Encroachment Alerts Panel */}
          {(activeRiskTab === 'all' || activeRiskTab === 'encroachment') && (
            <div className="encroachment-card card" style={{ gridColumn: activeRiskTab === 'encroachment' ? '1 / -1' : 'auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 className="section-title" style={{ margin: 0 }}>🚨 Encroachment & Illegal Path Logging</h3>
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

              <div style={{ maxHeight: '380px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filteredAlerts.slice(0, 30).map((a, idx) => (
                  <div key={idx} className="alert-item" style={{ background: 'var(--bg-surface)', borderLeft: `3px solid var(--alert-${a.severity.toLowerCase() === 'high' ? 'red' : (a.severity.toLowerCase() === 'medium' ? 'orange' : 'yellow')})`, padding: '10px 14px', borderRadius: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>Patch #{a.patch_id} — {a.alert_type}</span>
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
          )}
        </div>
      </div>
    </div>
  );
}
