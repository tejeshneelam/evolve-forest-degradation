import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function ConservationTab() {
  const [carbon, setCarbon]         = useState(null);
  const [reforested, setReforested] = useState(null);
  const [route, setRoute]           = useState(null);
  const [loading, setLoading]       = useState(true);
  const [showFormula, setShowFormula] = useState(false);

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
        <span>Opening Conservation & Carbon Vault...</span>
      </div>
    );
  }

  return (
    <div className="conservation-page">
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">🌱 Conservation Actions, Carbon Economics & Patrol Planning</h2>
            <p className="page-subtitle">
              IPCC allometric carbon stock accounting, AI reforestation prioritization, and least-cost safe ranger patrol route pathfinding.
            </p>
          </div>
          <button 
            className={`btn btn-sm ${showFormula ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => setShowFormula(!showFormula)}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            {showFormula ? 'Hide Formula Guide' : '📐 How Are These Carbon Numbers Calculated?'}
          </button>
        </div>
      </div>

      {/* Scientific Methodology & Carbon Calculation Formula Breakdown */}
      {showFormula && (
        <div className="formula-guide-card card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, rgba(82,183,136,0.12) 0%, rgba(15,25,20,0.8) 100%)', border: '1px solid rgba(82,183,136,0.35)', padding: '18px 22px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ fontSize: '15px', color: '#fff', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              📐 Carbon Stock Accounting Methodology (IPCC Tier 1 / 2 Allometry)
            </h3>
            <span style={{ fontSize: '10px', color: 'var(--forest-400)', fontWeight: 600 }}>Voluntary Carbon Market (VCM) Standard</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginTop: '14px', fontSize: '12px' }}>
            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <strong style={{ color: 'var(--forest-400)', display: 'block', marginBottom: '4px' }}>1. Sentinel-2 → Biomass (AGB)</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4, fontSize: '11px' }}>
                Canopy greenness from Sentinel-2 NDVI is converted into Above-Ground Biomass density:
                <br/><br/>
                <code style={{ color: '#fff', background: 'rgba(0,0,0,0.3)', padding: '2px 4px', borderRadius: '3px' }}>
                  AGB = ((NDVI - 0.3) / 0.55) × 250 t/ha
                </code>
                <br/><br/>
                (250 t/ha is the IPCC standard maximum for dense Western Ghats tropical evergreen forest).
              </p>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <strong style={{ color: 'var(--forest-400)', display: 'block', marginBottom: '4px' }}>2. Biomass → Carbon → CO₂e</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4, fontSize: '11px' }}>
                Dry tree wood contains <strong>47% elemental carbon</strong> (IPCC standard fraction).
                <br/><br/>
                To convert Carbon to CO₂ equivalent, we multiply by the molecular weight ratio (44/12 = 3.667):
                <br/><br/>
                <code style={{ color: '#fff', background: 'rgba(0,0,0,0.3)', padding: '2px 4px', borderRadius: '3px' }}>
                  tCO₂ = AGB × 0.47 × (44/12)
                </code>
              </p>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <strong style={{ color: 'var(--forest-400)', display: 'block', marginBottom: '4px' }}>3. Area Scaling (40.96 ha)</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4, fontSize: '11px' }}>
                Each patch is 64×64 pixels at 10m spatial resolution = 640m × 640m = <strong>40.96 hectares</strong>.
                <br/><br/>
                Total patch CO₂ = tCO₂/ha × 40.96 ha.
                <br/><br/>
                Summed across all 64 patches in Wayanad Muthanga = <strong>~252,000 metric tons of CO₂</strong> stored.
              </p>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <strong style={{ color: '#FFB703', display: 'block', marginBottom: '4px' }}>4. Economic Valuation ($15/ton)</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4, fontSize: '11px' }}>
                Carbon credits trade on Voluntary Carbon Markets (VCM) at <strong>$15.00 USD / tCO₂</strong>.
                <br/><br/>
                Forest standing asset value:
                <br/>
                <code style={{ color: '#52B788', background: 'rgba(0,0,0,0.3)', padding: '2px 4px', borderRadius: '3px' }}>
                  252,000 t × $15 = $3.78 Million
                </code>
                <br/><br/>
                Annual forest loss (-1,300 t/yr) destroys <strong>-$19,500/yr</strong> in natural capital.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="page-body">
        {/* Top: Carbon Stock Meter with Explanatory Badges */}
        {carbon && (
          <div className="carbon-stock-banner card" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px', background: 'linear-gradient(135deg, var(--bg-card) 0%, var(--bg-surface) 100%)' }}>
            <div title="Computed via Sentinel-2 NDVI canopy proxy scaled across 40.96 ha patches using IPCC 47% carbon fraction and 3.67x molecular weight">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TOTAL CO₂ STORAGE</span>
                <span style={{ fontSize: '9px', color: 'var(--forest-400)' }}>ℹ️ 64 Patches</span>
              </div>
              <h3 style={{ fontSize: '24px', color: '#fff', marginTop: '4px' }}>{carbon.total_stock_tCO2?.toLocaleString()} t</h3>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Standing natural biomass stock</span>
            </div>

            <div title="Valued under Voluntary Carbon Market (VCM) offset rate of $15.00 USD per ton of sequestered CO2">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ESTIMATED ASSET VALUE</span>
                <span style={{ fontSize: '9px', color: 'var(--forest-400)' }}>$15/ton VCM</span>
              </div>
              <h3 style={{ fontSize: '24px', color: 'var(--forest-500)', marginTop: '4px' }}>${carbon.total_stock_value_usd?.toLocaleString()}</h3>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Monetary carbon credit valuation</span>
            </div>

            <div title="Annual carbon release caused by canopy thinning and deforested patches">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ANNUAL CO₂ EMISSION LOSS</span>
                <span style={{ fontSize: '9px', color: 'var(--alert-red)' }}>Degradation</span>
              </div>
              <h3 style={{ fontSize: '24px', color: 'var(--alert-red)', marginTop: '4px' }}>-{carbon.total_annual_loss_tCO2?.toLocaleString()} t/yr</h3>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Emissions released into atmosphere</span>
            </div>

            <div title="Financial capital destroyed every year due to unmitigated degradation">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>YEARLY VALUE DESTROYED</span>
                <span style={{ fontSize: '9px', color: 'var(--alert-red)' }}>Economic Cost</span>
              </div>
              <h3 style={{ fontSize: '24px', color: 'var(--alert-red)', marginTop: '4px' }}>-${carbon.total_annual_loss_usd?.toLocaleString()}</h3>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Lost environmental asset capital</span>
            </div>
          </div>
        )}

        <div className="grid-2">
          {/* Left: Reforestation Priorities */}
          <div className="reforestation-card card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 className="section-title" style={{ margin: 0 }}>🌱 AI Reforestation Priority Queue</h3>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Ranked by Slope & Canopy Loss</span>
            </div>
            <div style={{ maxHeight: '380px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {reforested?.top_candidates.map((c, idx) => (
                <div key={idx} className="ref-item" style={{ background: 'var(--bg-surface)', padding: '12px 14px', borderRadius: '4px', borderLeft: '3px solid var(--forest-500)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>Rank #{c.priority_rank}: Patch #{c.patch_id}</span>
                    <span className="badge badge-healthy" style={{ marginLeft: 'auto', fontSize: '10px' }}>Priority: {c.priority_score.toFixed(3)}</span>
                  </div>
                  <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>{c.justification}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Safe Ranger Patrol Route Planner */}
          <div className="patrol-route-card card">
            <h3 className="section-title">🛡️ Safe Ranger Patrol Route Planner</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-sec)', marginBottom: '16px' }}>
              A* pathfinding algorithm computing the safest traversal route across the sanctuary, avoiding degraded steep terrain and high landslide probability zones.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '12px', alignItems: 'end', marginBottom: '16px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>START POST (PATCH ID)</label>
                <input 
                  type="number" 
                  min={0} 
                  max={63} 
                  value={startPatch} 
                  onChange={(e) => setStartPatch(parseInt(e.target.value) || 0)}
                  style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82,183,136,0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', width: '100%' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>DESTINATION POST (PATCH ID)</label>
                <input 
                  type="number" 
                  min={0} 
                  max={63} 
                  value={endPatch} 
                  onChange={(e) => setEndPatch(parseInt(e.target.value) || 0)}
                  style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82,183,136,0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', width: '100%' }}
                />
              </div>

              <button 
                className="btn btn-primary"
                onClick={handleFindRoute}
                disabled={routeLoading || startPatch === endPatch}
                style={{ padding: '7px 14px', fontSize: '12px', height: '34px' }}
              >
                {routeLoading ? 'Computing...' : 'Find Safe Path'}
              </button>
            </div>

            {route && (
              <div className="route-result" style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(82, 183, 136, 0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--forest-500)' }}>Optimal Patrol Path Identified</span>
                  <span className="badge badge-healthy">Safety Score: {(100 - route.total_cost * 10).toFixed(0)}%</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Total Distance: <strong>{route.path_length_km} km</strong> ({route.path.length} waypoints)
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '10px' }}>
                  {route.path.map((pid, idx) => (
                    <span key={idx} style={{ background: 'rgba(82, 183, 136, 0.1)', color: '#fff', border: '1px solid rgba(82, 183, 136, 0.3)', padding: '2px 6px', borderRadius: '3px', fontSize: '10px' }}>
                      {pid} {idx < route.path.length - 1 ? '→' : ''}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
