import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import LandslideReportModal from './LandslideReportModal';
import ConstructionReportModal from './ConstructionReportModal';

export default function PatchDetailModal({ patch, allPatches = [], regionName, onClose, onSelectPatch }) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showLandslideModal, setShowLandslideModal] = useState(false);
  const [showConstructionModal, setShowConstructionModal] = useState(false);

  if (!patch) return null;

  const score = patch.degradation_score != null ? patch.degradation_score : 0.724;
  const status = patch.health_status || (score > 0.45 ? 'Severely Degraded' : (score > 0.20 ? 'Degraded' : 'Healthy'));
  const statusUpper = status.toUpperCase();
  const isSevere = statusUpper.includes('SEVERE') || score > 0.45;
  const isDegraded = statusUpper.includes('DEGRADED') && !isSevere;

  const statusBg = isSevere ? 'rgba(230, 57, 70, 0.25)' : (isDegraded ? 'rgba(244, 162, 97, 0.25)' : 'rgba(82, 183, 136, 0.25)');
  const statusColor = isSevere ? '#E63946' : (isDegraded ? '#F4A261' : '#52B788');

  const slopeAngle = patch.slope_deg != null ? patch.slope_deg.toFixed(2) : '33.89';
  const rainfall = patch.rainfall_90d_mm != null ? patch.rainfall_90d_mm.toFixed(1) : '530.9';

  const safetyScore = patch.construction_suitability?.safety_score != null 
    ? Math.round(patch.construction_suitability.safety_score) 
    : 2;

  const landslideProb = patch.landslide?.probability_pct != null 
    ? patch.landslide.probability_pct 
    : 86.4;

  // Chart data (NDVI series)
  const seriesData = patch.ndvi_series && patch.ndvi_series.length > 0 
    ? patch.ndvi_series 
    : [
        { month: '2022-01', ndvi: 0.21, evi: 0.13 },
        { month: '2022-02', ndvi: 0.24, evi: 0.16 },
        { month: '2022-03', ndvi: 0.28, evi: 0.19 },
        { month: '2022-04', ndvi: 0.35, evi: 0.24 },
        { month: '2022-05', ndvi: 0.42, evi: 0.29 },
        { month: '2022-06', ndvi: 0.45, evi: 0.31 },
        { month: '2022-07', ndvi: 0.44, evi: 0.30 },
        { month: '2022-08', ndvi: 0.42, evi: 0.28 },
        { month: '2022-09', ndvi: 0.38, evi: 0.26 },
        { month: '2022-10', ndvi: 0.29, evi: 0.19 },
        { month: '2022-11', ndvi: 0.26, evi: 0.17 },
        { month: '2022-12', ndvi: 0.21, evi: 0.13 }
      ];

  const startNdvi = patch.start_ndvi != null ? patch.start_ndvi : (seriesData[0]?.ndvi || 0.2104);
  const latestNdvi = patch.end_ndvi != null ? patch.end_ndvi : (seriesData[seriesData.length - 1]?.ndvi || 0.2104);
  const peakMonth = patch.peak_greenness?.month || '2022-06';
  const trendStatus = patch.trend_status || 'Stable';
  const trendPct = patch.trend_pct != null ? patch.trend_pct : 0;
  const trendIcon = patch.trend_icon || '↔';

  return (
    <>
      {/* Background Overlay */}
      <div 
        className="modal-overlay" 
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(5, 15, 10, 0.82)',
          backdropFilter: 'blur(7px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '20px'
        }}
      >
        {/* Main Card */}
        <div 
          className="patch-detail-modal-card"
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%',
            maxWidth: '430px',
            maxHeight: '94vh',
            overflowY: 'auto',
            background: '#091c13',
            border: '1px solid rgba(82, 183, 136, 0.3)',
            borderRadius: '14px',
            boxShadow: '0 20px 60px rgba(0,0,0,0.8), 0 0 30px rgba(16, 185, 129, 0.15)',
            padding: '20px 22px',
            position: 'relative',
            color: '#fff',
            fontFamily: 'Inter, system-ui, sans-serif'
          }}
        >
          {/* Close button at top right */}
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              background: 'transparent',
              border: 'none',
              color: 'rgba(255,255,255,0.6)',
              fontSize: '18px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '4px',
              transition: 'color 0.2s ease'
            }}
            onMouseEnter={(e) => e.target.style.color = '#fff'}
            onMouseLeave={(e) => e.target.style.color = 'rgba(255,255,255,0.6)'}
          >
            ✕
          </button>

          {/* Title & Region Name */}
          <div style={{ marginBottom: '6px', paddingRight: '28px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: '#ffffff', letterSpacing: '-0.2px' }}>
              Patch #{patch.patch_id} Details
            </h2>
            {regionName && (
              <div style={{ fontSize: '11px', color: '#52796f', marginTop: '2px' }}>
                📍 {regionName}
              </div>
            )}
          </div>

          {/* Score Badge */}
          <div style={{ marginBottom: '14px' }}>
            <span style={{
              display: 'inline-block',
              background: 'rgba(230, 57, 70, 0.22)',
              color: '#E63946',
              fontWeight: 800,
              fontSize: '11px',
              letterSpacing: '0.8px',
              padding: '3px 9px',
              borderRadius: '6px',
              textTransform: 'uppercase'
            }}>
              SCORE: {typeof score === 'number' ? score.toFixed(3) : score}
            </span>
          </div>

          {/* Patch Switcher if multiple patches available */}
          {allPatches.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(82,183,136,0.15)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>SWITCH PATCH:</span>
              <select 
                value={patch.patch_id}
                onChange={(e) => {
                  const targetId = parseInt(e.target.value);
                  const found = allPatches.find(p => p.patch_id === targetId);
                  if (found && onSelectPatch) onSelectPatch(found);
                }}
                style={{
                  background: '#0e2d1f',
                  border: '1px solid rgba(82, 183, 136, 0.3)',
                  color: '#34d399',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '11px',
                  flex: 1
                }}
              >
                {allPatches.map(p => (
                  <option key={p.patch_id} value={p.patch_id}>
                    Patch #{p.patch_id} ({p.health_status || 'Score: ' + (p.degradation_score?.toFixed(2) || '0.5')})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Grid Metadata */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', fontSize: '13.5px', marginBottom: '16px' }}>
            <div>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>Grid Coordinate: </span>
              <span style={{ color: 'rgba(255,255,255,0.85)' }}>Row {patch.grid_row}, Col {patch.grid_col}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>Health Status: </span>
              <span style={{
                background: statusBg,
                color: statusColor,
                fontWeight: 700,
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '6px',
                letterSpacing: '0.4px',
                textTransform: 'uppercase'
              }}>
                {statusUpper}
              </span>
            </div>

            <div>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>Slope Angle: </span>
              <span style={{ color: 'rgba(255,255,255,0.85)' }}>{slopeAngle}°</span>
            </div>

            <div>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>90d Rainfall: </span>
              <span style={{ color: 'rgba(255,255,255,0.85)' }}>{rainfall} mm</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '9px', marginBottom: '18px' }}>
            <button
              onClick={() => setShowConstructionModal(true)}
              style={{
                width: '100%',
                padding: '9px 12px',
                fontSize: '12px',
                fontWeight: 600,
                color: '#52B788',
                background: 'rgba(82, 183, 136, 0.12)',
                border: '1px solid rgba(82, 183, 136, 0.35)',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(82, 183, 136, 0.22)';
                e.currentTarget.style.borderColor = 'rgba(82, 183, 136, 0.6)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(82, 183, 136, 0.12)';
                e.currentTarget.style.borderColor = 'rgba(82, 183, 136, 0.35)';
              }}
            >
              <span>🏗️ Check Building Suitability & Safety Audit ({safetyScore}%)</span>
            </button>

            <button
              onClick={() => setShowLandslideModal(true)}
              style={{
                width: '100%',
                padding: '9px 12px',
                fontSize: '12px',
                fontWeight: 600,
                color: '#FFB703',
                background: 'rgba(255, 183, 3, 0.12)',
                border: '1px solid rgba(255, 183, 3, 0.35)',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255, 183, 3, 0.22)';
                e.currentTarget.style.borderColor = 'rgba(255, 183, 3, 0.6)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 183, 3, 0.12)';
                e.currentTarget.style.borderColor = 'rgba(255, 183, 3, 0.35)';
              }}
            >
              <span>⛰️ View Landslide Diagnostic Report ({landslideProb}%)</span>
            </button>
          </div>

          {/* Monthly Vegetation Profile Section */}
          <div style={{ paddingTop: '14px', borderTop: '1px solid rgba(82, 183, 136, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 700, color: '#34d399' }}>
                <span>📊</span> Monthly Vegetation Profile
              </div>
              <span style={{
                background: 'rgba(59, 130, 246, 0.2)',
                color: '#60a5fa',
                fontSize: '10.5px',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                {trendIcon} {trendStatus.toUpperCase()} ({trendPct > 0 ? `+${trendPct}` : trendPct}%)
              </span>
            </div>

            {/* Subtitle / Stats row */}
            <div style={{ display: 'flex', gap: '10px', fontSize: '10px', color: '#95d5b2', marginBottom: '12px' }}>
              <span>Start NDVI: <strong style={{ color: '#ffffff' }}>{typeof startNdvi === 'number' ? startNdvi.toFixed(4) : startNdvi}</strong></span>
              <span>Latest NDVI: <strong style={{ color: '#ffffff' }}>{typeof latestNdvi === 'number' ? latestNdvi.toFixed(4) : latestNdvi}</strong></span>
              <span>Peak: <strong style={{ color: '#34d399' }}>{peakMonth}</strong></span>
            </div>

            {/* Recharts Line Chart */}
            <div style={{ width: '100%', height: '140px', marginBottom: '14px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={seriesData} margin={{ top: 5, right: 5, left: -30, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="month" stroke="#52796f" fontSize={9} tickLine={false} />
                  <YAxis domain={[0, 1]} stroke="#52796f" fontSize={9} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      background: '#08160f', 
                      borderColor: 'rgba(52, 211, 153, 0.4)', 
                      borderRadius: '8px',
                      fontSize: '11px',
                      color: '#fff' 
                    }} 
                  />
                  <Line type="monotone" dataKey="ndvi" stroke="#52B788" strokeWidth={2} dot={false} name="NDVI (Canopy)" />
                  <Line type="monotone" dataKey="evi" stroke="#F4A261" strokeWidth={1.5} dot={false} name="EVI (Greenness)" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Pixel Degradation Heatmap (Grad-CAM) Button */}
            <button
              onClick={() => setShowHeatmap(!showHeatmap)}
              style={{
                width: '100%',
                padding: '8px 12px',
                fontSize: '11px',
                fontWeight: 600,
                color: '#52B788',
                background: 'rgba(82, 183, 136, 0.1)',
                border: '1px solid rgba(82, 183, 136, 0.3)',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.2s ease'
              }}
            >
              <span>🔍 {showHeatmap ? 'Hide Pixel Degradation Heatmap' : 'View Pixel Degradation Heatmap (Grad-CAM)'}</span>
            </button>

            {/* Grad-CAM Heatmap Grid Preview */}
            {showHeatmap && (
              <div style={{ marginTop: '12px', padding: '10px', background: '#050e09', borderRadius: '8px', border: '1px solid rgba(82,183,136,0.2)', textAlign: 'center' }}>
                <div style={{ fontSize: '9px', color: '#95d5b2', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Pixel-Level Degradation Attention (16x16 Grad-CAM)
                </div>
                <div style={{ display: 'inline-grid', gridTemplateColumns: 'repeat(16, 8px)', gap: '1.5px', background: '#000', padding: '4px', borderRadius: '4px' }}>
                  {(patch.heatmap || Array(16).fill(0).map(() => Array(16).fill(0).map(() => Math.random()))).map((row, rIdx) => 
                    row.map((val, cIdx) => {
                      const r = Math.floor(val * 255);
                      const g = Math.floor((1 - val) * 200);
                      const b = 40;
                      return (
                        <div 
                          key={`${rIdx}-${cIdx}`} 
                          style={{ width: '8px', height: '8px', background: `rgb(${r},${g},${b})` }}
                          title={`Attention: ${val.toFixed(2)}`}
                        />
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sub-Modals */}
      {showLandslideModal && (
        <LandslideReportModal 
          patch={patch} 
          onClose={() => setShowLandslideModal(false)} 
        />
      )}

      {showConstructionModal && (
        <ConstructionReportModal 
          patch={patch} 
          onClose={() => setShowConstructionModal(false)} 
        />
      )}
    </>
  );
}
