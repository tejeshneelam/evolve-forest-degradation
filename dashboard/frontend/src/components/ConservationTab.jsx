import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function ConservationTab() {
  const [carbon, setCarbon]         = useState(null);
  const [reforested, setReforested] = useState(null);
  const [route, setRoute]           = useState(null);
  const [loading, setLoading]       = useState(true);

  // Route Planning Inputs
  const [startPatch, setStartPatch] = useState(0);
  const [endPatch, setEndPatch]     = useState(63);
  const [routeLoading, setRouteLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getCarbon(),
      api.getReforestation()
    ]).then(([carb, ref]) => {
      setCarbon(carb);
      setReforested(ref);
      setLoading(false);
    }).catch(err => {
      console.error("Error loading conservation metrics:", err);
      setLoading(false);
    });
  }, []);

  const handleFindRoute = () => {
    if (startPatch === endPatch) return;
    setRouteLoading(true);
    setRoute(null);
    api.getPatrolRoute(startPatch, endPatch)
      .then(res => {
        setRoute(res);
        setRouteLoading(false);
      })
      .catch(err => {
        console.error("Route planning error:", err);
        setRouteLoading(false);
      });
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Opening Conservation & Planning Vault...</span>
      </div>
    );
  }

  return (
    <div className="conservation-page">
      <div className="page-header">
        <h2 className="page-title">🌱 Conservation Actions & Planning</h2>
        <p className="page-subtitle">Reforestation priority modeling, carbon valuation assets, and safe ranger patrol route pathfinding.</p>
      </div>

      <div className="page-body">
        {/* Top: Carbon Stock Meter */}
        {carbon && (
          <div className="carbon-stock-banner card" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px', background: 'linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%)' }}>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TOTAL CO₂ STORAGE</span>
              <h3 style={{ fontSize: '24px', color: '#fff', marginTop: '4px' }}>{carbon.total_stock_tCO2?.toLocaleString()} t</h3>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ESTIMATED FOREST ASSET VALUE</span>
              <h3 style={{ fontSize: '24px', color: 'var(--forest-500)', marginTop: '4px' }}>${carbon.total_stock_value_usd?.toLocaleString()}</h3>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ANNUAL CO₂ DESTRUCTION COST</span>
              <h3 style={{ fontSize: '24px', color: 'var(--alert-red)', marginTop: '4px' }}>-{carbon.total_annual_loss_tCO2?.toLocaleString()} t</h3>
            </div>
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>YEARLY VALUE LOSS (USD)</span>
              <h3 style={{ fontSize: '24px', color: 'var(--alert-red)', marginTop: '4px' }}>-${carbon.total_annual_loss_usd?.toLocaleString()}</h3>
            </div>
          </div>
        )}

        <div className="grid-2">
          {/* Left: Reforestation Priorities */}
          <div className="reforestation-card card">
            <h3 className="section-title">🌱 Reforestation Priorities (Reforest Map)</h3>
            <div style={{ maxHeight: '350px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {reforested?.top_candidates.map((c, idx) => (
                <div key={idx} className="ref-item" style={{ background: 'var(--bg-surface)', padding: '12px 14px', borderRadius: '4px', borderLeft: '3px solid var(--forest-500)' }}>
                  <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>Rank {c.priority_rank}: Patch {c.patch_id}</span>
                    <span className="badge badge-healthy" style={{ marginLeft: 'auto', fontSize: '10px' }}>Priority: {c.priority_score.toFixed(3)}</span>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>{c.justification}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Safe Ranger Patrol Route Planner */}
          <div className="route-card card">
            <h3 className="section-title">🧭 Safe Ranger Patrol Router (A* Solver)</h3>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '14px' }}>
              Calculates the safest traversal path between any two patches. Automatically avoids active forest fire risk, high landslide slopes, and animal zones.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 60px', gap: '10px', alignItems: 'end', marginBottom: '16px' }}>
              <div>
                <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>START PATCH</label>
                <select 
                  value={startPatch} 
                  onChange={(e) => setStartPatch(parseInt(e.target.value))}
                  style={{ width: '100%', padding: '6px', background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px' }}
                >
                  {Array.from({ length: 64 }, (_, i) => (
                    <option key={i} value={i}>Patch {i}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>DESTINATION PATCH</label>
                <select 
                  value={endPatch} 
                  onChange={(e) => setEndPatch(parseInt(e.target.value))}
                  style={{ width: '100%', padding: '6px', background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', borderRadius: '4px' }}
                >
                  {Array.from({ length: 64 }, (_, i) => (
                    <option key={i} value={i}>Patch {i}</option>
                  ))}
                </select>
              </div>

              <button 
                className="btn btn-primary" 
                onClick={handleFindRoute}
                disabled={routeLoading}
                style={{ padding: '8px', fontSize: '11px', whiteSpace: 'nowrap' }}
              >
                {routeLoading ? 'Solving...' : 'Solve Path'}
              </button>
            </div>

            {/* Path Results */}
            {route && (
              <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '4px', maxHeight: '200px', overflowY: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'between', fontSize: '12px', color: 'var(--text-sec)', marginBottom: '8px' }}>
                  <span>📏 Distance: <strong>{route.distance_km} km</strong></span>
                  <span style={{ marginLeft: 'auto' }}>🛡️ Traversal Risk: <strong>{route.total_risk}</strong></span>
                </div>
                
                <div style={{ fontSize: '12px', color: '#fff', marginBottom: '8px' }}>
                  <strong>Optimal Path:</strong> <span style={{ color: 'var(--forest-500)' }}>{route.path.join(' ➔ ')}</span>
                </div>

                {route.warnings.length > 0 && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px', marginTop: '8px' }}>
                    <span style={{ fontSize: '10px', color: 'var(--alert-red)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>🚨 PATH TRAVERSAL WARNINGS</span>
                    <ul style={{ paddingLeft: '14px', fontSize: '10px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      {route.warnings.map((w, idx) => (
                        <li key={idx} style={{ listStyleType: 'disc' }}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
