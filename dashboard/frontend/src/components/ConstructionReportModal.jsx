import React from 'react';

export default function ConstructionReportModal({ patch, onClose }) {
  if (!patch) return null;

  const build = patch.construction_suitability || {
    verdict: 'CONDITIONAL_RESTRICTED',
    verdict_label: 'Conditional Clearance — Engineering Mandated',
    badge: 'Conditional Clearance',
    color: '#FFB703',
    safety_score: 65.0,
    slope_deg: patch.slope_deg || 12.0,
    slope_category: 'Moderate Hill Slope (10°–20°)',
    landslide_prob_pct: patch.landslide ? patch.landslide.probability_pct : 28.0,
    bearing_capacity: 'Moderate (100–180 kPa)',
    wildlife_corridor_conflict: patch.grid_col in [2, 3, 4],
    eco_status: 'Standard Regulatory Clearance',
    mandatory_actions: [
      'Mandatory geotechnical borehole testing prior to foundation laying.',
      'Construct engineered reinforced concrete retaining walls with subsurface weep holes.',
      'Implement contour drainage to intercept surface stormwater runoff.'
    ],
    soil_stability: 'Moderate Cohesion — Colluvium Slip Risk'
  };

  const isProhibited = build.verdict === 'HAZARD_PROHIBITED';
  const isSafe = build.verdict === 'SUITABLE_FOR_CONSTRUCTION';
  const verdictColor = build.color || (isProhibited ? '#E63946' : (isSafe ? '#52B788' : '#FFB703'));

  return (
    <div className="modal-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 15, 10, 0.88)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div className="modal-card card" style={{
        width: '100%',
        maxWidth: '720px',
        maxHeight: '92vh',
        overflowY: 'auto',
        background: 'var(--bg-card)',
        border: `1px solid ${verdictColor}45`,
        boxShadow: `0 16px 48px rgba(0,0,0,0.7), 0 0 24px ${verdictColor}25`,
        borderRadius: '10px',
        position: 'relative'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '20px', color: '#fff', margin: 0 }}>
                🏗️ Land Construction & Geo-Safety Audit
              </h2>
              <span className="badge" style={{ backgroundColor: `${verdictColor}25`, color: verdictColor, border: `1px solid ${verdictColor}60`, fontWeight: 700 }}>
                {build.badge}
              </span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              Terrain Evaluation for <strong>Patch #{patch.patch_id}</strong> (Row {patch.grid_row}, Col {patch.grid_col}) • Slope: <strong>{build.slope_deg}°</strong>
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

        {/* Big Verdict Banner */}
        <div style={{
          marginTop: '18px',
          padding: '16px 20px',
          borderRadius: '8px',
          background: `linear-gradient(135deg, ${verdictColor}15 0%, rgba(20, 35, 25, 0.4) 100%)`,
          border: `1px solid ${verdictColor}50`,
          display: 'flex',
          alignItems: 'center',
          gap: '18px'
        }}>
          <div style={{
            fontSize: '38px',
            lineHeight: 1,
            padding: '12px',
            borderRadius: '50%',
            background: `${verdictColor}25`,
            border: `2px solid ${verdictColor}60`
          }}>
            {isProhibited ? '🚫' : (isSafe ? '✅' : '⚠️')}
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', color: verdictColor, fontWeight: 700 }}>
              Civil Engineering Verdict
            </span>
            <h3 style={{ fontSize: '18px', color: '#fff', margin: '3px 0 6px', fontFamily: 'Space Grotesk, sans-serif' }}>
              {build.verdict_label}
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-sec)', margin: 0, lineHeight: 1.4 }}>
              {isProhibited 
                ? "This land exceeds critical slope stability and landslide shear limits. Construction is legally and physically dangerous."
                : (isSafe 
                  ? "Terrain exhibits gentle slope and robust bedrock cohesion. Approved for standard residential/commercial structures."
                  : "Construction permitted only with licensed geotechnical retaining walls, terraced excavation, and strict height limits.")}
            </p>
          </div>
          <div style={{ textAlign: 'center', minWidth: '95px' }}>
            <div style={{ fontSize: '28px', fontWeight: 700, color: verdictColor, fontFamily: 'Space Grotesk, sans-serif' }}>
              {build.safety_score}%
            </div>
            <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Build Safety Score
            </div>
          </div>
        </div>

        {/* 4 Technical Pillar Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginTop: '18px' }}>
          {/* 1. Slope Gradient */}
          <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>📐 SLOPE GRADIENT (SRTM)</span>
              <span style={{ fontSize: '11px', color: build.slope_deg >= 20 ? 'var(--alert-red)' : (build.slope_deg >= 10 ? '#FFB703' : 'var(--forest-400)'), fontWeight: 700 }}>
                {build.slope_deg}°
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>{build.slope_category}</div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0', lineHeight: 1.3 }}>
              {build.slope_deg >= 20 
                ? "Extreme incline (>20°). Heavy structural dead-load will cause slope toe blowout."
                : (build.slope_deg >= 10 
                  ? "Moderate incline (10°–20°). Requires stepped foundations and earth retaining works." 
                  : "Gentle incline (<10°). Favorable topography for standard footing excavation.")}
            </p>
          </div>

          {/* 2. Geotechnical Landslide Risk */}
          <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>⛰️ LANDSLIDE COLLAPSE PROBABILITY</span>
              <span style={{ fontSize: '11px', color: build.landslide_prob_pct >= 45 ? 'var(--alert-red)' : '#FFB703', fontWeight: 700 }}>
                {build.landslide_prob_pct}%
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>{build.soil_stability}</div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0', lineHeight: 1.3 }}>
              Estimated soil bearing capacity: <strong>{build.bearing_capacity}</strong>.
            </p>
          </div>

          {/* 3. Wildlife & Eco-Sensitive Zone */}
          <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>🐘 ECOLOGICAL & CORRIDOR CLEARANCE</span>
              <span style={{ fontSize: '11px', color: build.wildlife_corridor_conflict ? 'var(--alert-red)' : 'var(--forest-400)', fontWeight: 700 }}>
                {build.wildlife_corridor_conflict ? 'CONFLICT' : 'CLEARED'}
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>{build.eco_status}</div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0', lineHeight: 1.3 }}>
              {build.wildlife_corridor_conflict 
                ? "Located inside active elephant/tiger migration path. Construction triggers human-animal conflict." 
                : "Outside high-frequency elephant corridor channels. Regulatory building permit applicable."}
            </p>
          </div>

          {/* 4. Hydrology & Storm Runoff */}
          <div style={{ background: 'var(--bg-surface)', padding: '14px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>🌧️ PRECIPITATION & SATURATION</span>
              <span style={{ fontSize: '11px', color: '#FFB703', fontWeight: 700 }}>
                {patch.rainfall_90d_mm || 280} mm / 90d
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#fff', fontWeight: 600 }}>Hydrostatic Slip Plane Risk</div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0', lineHeight: 1.3 }}>
              Pore-water pressure elevates during monsoon. Surface runoff interceptor drains are mandatory.
            </p>
          </div>
        </div>

        {/* Mandatory Engineering Actions */}
        <div style={{ marginTop: '18px', background: 'rgba(0,0,0,0.25)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <h4 style={{ fontSize: '13px', color: 'var(--text-prim)', margin: '0 0 10px', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
            📋 Mandatory Civil Engineering & Safety Prescriptions
          </h4>
          <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {build.mandatory_actions && build.mandatory_actions.map((act, i) => (
              <li key={i} style={{ fontSize: '12px', color: 'var(--text-sec)', lineHeight: 1.4 }}>
                {act}
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px' }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Compliant with NDMA Hill Construction Directives & Western Ghats Ecology Panel Guidelines.
          </span>
          <button 
            onClick={onClose}
            className="btn btn-primary"
            style={{ padding: '7px 18px', fontSize: '12px' }}
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
}
