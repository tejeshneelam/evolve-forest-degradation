import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Popup, useMap } from 'react-leaflet';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { api } from '../api/client';
import LandslideReportModal from './LandslideReportModal';
import ConstructionReportModal from './ConstructionReportModal';

// Helper component to smoothly re-center the map when region changes
function MapRecenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 13);
    }
  }, [center, map]);
  return null;
}

const REGION_PRESETS = [
  {
    name: "Wayanad Wildlife Sanctuary, India",
    bbox: [76.325, 11.625, 76.375, 11.675],
    center: [11.650, 76.350],
    desc: "Muthanga Range pilot study area"
  },
  {
    name: "Silent Valley National Park, India",
    bbox: [76.400, 11.050, 76.450, 11.100],
    center: [11.075, 76.425],
    desc: "Biodiverse tropical evergreen rainforest in Western Ghats"
  },
  {
    name: "Amazon Rainforest, Peru (Madre de Dios)",
    bbox: [-69.350, -12.650, -69.300, -12.600],
    center: [-12.625, -69.325],
    desc: "South American tropical rainforest canopy"
  },
  {
    name: "Congo Basin, DRC (Salonga Reserve)",
    bbox: [20.800, -2.150, 20.850, -2.100],
    center: [-2.125, 20.825],
    desc: "Central African peatland and dense canopy"
  }
];

export default function ForestMap() {
  const [mapData, setMapData]                 = useState(null);
  const [selectedPatch, setSelectedPatch]     = useState(null);
  const [patchSeries, setPatchSeries]         = useState(null);
  const [showHeatmap, setShowHeatmap]         = useState(false);
  const [loading, setLoading]                 = useState(true);
  
  // Date and Time Range selector states
  const [startDate, setStartDate]             = useState("2022-01");
  const [endDate, setEndDate]                 = useState("2024-12");

  // Map view layers: 'health' | 'landslide' | 'construction'
  const [mapMode, setMapMode]                 = useState('health');

  // Dynamic Region selection states
  const [selectedPreset, setSelectedPreset]   = useState(0);
  const [customBBox, setCustomBBox]           = useState("76.325, 11.625, 76.375, 11.675");
  const [isProcessingGEE, setIsProcessingGEE] = useState(false);
  const [geeStatusMsg, setGeeStatusMsg]       = useState('');
  
  // Diagnostic modals
  const [activeDiagnosticPatch, setActiveDiagnosticPatch]     = useState(null);
  const [activeConstructionPatch, setActiveConstructionPatch] = useState(null);

  useEffect(() => {
    // Check if an existing dynamic region is loaded, otherwise load baseline patches
    api.getCurrentRegion()
      .then(dyn => {
        if (dyn && dyn.patches) {
          setMapData(dyn);
          if (dyn.start_date) setStartDate(dyn.start_date);
          if (dyn.end_date) setEndDate(dyn.end_date);
          setLoading(false);
        } else {
          return api.getPatches().then(data => {
            setMapData(data);
            setLoading(false);
          });
        }
      })
      .catch(err => {
        console.error("Error initializing map:", err);
        setLoading(false);
      });
  }, []);

  const handlePatchClick = (patch) => {
    setSelectedPatch(patch.patch_id);
    setShowHeatmap(false);
    
    // If dynamic region already has ndvi_series inside the patch object, use it directly
    if (patch.ndvi_series && patch.ndvi_series.length > 0) {
      setPatchSeries(patch);
    } else {
      setPatchSeries(null);
      api.getNDVISeries(patch.patch_id)
        .then(data => {
          // Merge patch metadata with series data
          setPatchSeries({
            ...patch,
            ...data
          });
        })
        .catch(err => console.error("Error loading series:", err));
    }
  };

  const handleTriggerGEE = (e) => {
    e.preventDefault();
    let bbox = null;
    let name = "Selected Region";

    if (selectedPreset === -1) {
      // Custom coordinates
      try {
        const parts = customBBox.split(',').map(s => parseFloat(s.trim()));
        if (parts.length === 4 && parts.every(p => !isNaN(p))) {
          bbox = parts;
          name = "Custom Global ROI";
        } else {
          alert("Please enter 4 valid coordinates: min_lon, min_lat, max_lon, max_lat");
          return;
        }
      } catch {
        alert("Invalid coordinate string");
        return;
      }
    } else {
      const p = REGION_PRESETS[selectedPreset];
      bbox = p.bbox;
      name = p.name;
    }

    setIsProcessingGEE(true);
    setGeeStatusMsg(`🛰️ Querying Earth Engine from ${startDate} to ${endDate}...`);

    api.processRegion(bbox, name, 24, startDate, endDate)
      .then(res => {
        setMapData(res);
        setIsProcessingGEE(false);
        setGeeStatusMsg('');
        setSelectedPatch(null);
        setPatchSeries(null);
      })
      .catch(err => {
        console.error("GEE Ingestion failed:", err);
        alert(`Earth Engine Error: ${err.message}`);
        setIsProcessingGEE(false);
        setGeeStatusMsg('');
      });
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Loading Forest Intelligence Map...</span>
      </div>
    );
  }

  const center = mapData?.aoi?.center || [11.65, 76.35];

  // Dynamic patch color based on active map layer mode
  const getPatchColor = (patch) => {
    if (mapMode === 'construction') {
      const verdict = patch.construction_suitability?.verdict;
      if (verdict === 'SUITABLE_FOR_CONSTRUCTION') return '#52B788'; // Safe green
      if (verdict === 'CONDITIONAL_RESTRICTED') return '#FFB703';    // Conditional yellow
      return '#E63946'; // Hazard red
    }
    
    if (mapMode === 'landslide') {
      const level = patch.landslide?.risk_level;
      if (level === 'Critical') return '#E63946';
      if (level === 'High') return '#FF5722';
      if (level === 'Moderate') return '#FFB703';
      return '#52B788';
    }

    // Default: Forest Health Degradation Score
    const score = patch.degradation_score || 0.0;
    if (score < 0.20) return '#52B788'; // Green
    if (score < 0.45) return '#F4A261'; // Orange
    return '#E63946'; // Red
  };

  // Convert pixel bounds or use dynamic bounds
  const getGeoBounds = (patch) => {
    if (patch.bounds && patch.bounds.length === 2) {
      return patch.bounds;
    }
    // Fallback for baseline Wayanad
    const latSize = (11.675 - 11.625) / 8;
    const lonSize = (76.375 - 76.325) / 8;
    const latMax = 11.675 - patch.grid_row * latSize;
    const latMin = latMax - latSize;
    const lonMin = 76.325 + patch.grid_col * lonSize;
    const lonMax = lonMin + lonSize;
    return [[latMin, lonMin], [latMax, lonMax]];
  };

  return (
    <div className="forest-map-page">
      {/* Landslide Diagnostic Modal */}
      {activeDiagnosticPatch && (
        <LandslideReportModal 
          patch={activeDiagnosticPatch} 
          onClose={() => setActiveDiagnosticPatch(null)} 
        />
      )}

      {/* Construction Feasibility Modal */}
      {activeConstructionPatch && (
        <ConstructionReportModal
          patch={activeConstructionPatch}
          onClose={() => setActiveConstructionPatch(null)}
        />
      )}

      {/* Header & Global Earth Engine Controls */}
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              🌍 Global Forest Health & Terrain Map <span className="badge" style={{ background: 'rgba(82, 183, 136, 0.2)', color: 'var(--forest-300)', fontSize: '11px' }}>v2.0 GEE Live</span>
            </h2>
            <p className="page-subtitle">
              Select any forest region on Earth and a custom time period. Evaluates forest degradation, landslide hazard zones, and mountain construction suitability.
            </p>
          </div>

          {/* Earth Engine Selector Toolbar with Date Range */}
          <form onSubmit={handleTriggerGEE} style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--bg-card)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(82, 183, 136, 0.25)', flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>TARGET REGION</label>
              <select 
                value={selectedPreset} 
                onChange={(e) => setSelectedPreset(parseInt(e.target.value))}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', maxWidth: '210px' }}
                disabled={isProcessingGEE}
              >
                {REGION_PRESETS.map((p, i) => (
                  <option key={i} value={i}>{p.name}</option>
                ))}
                <option value={-1}>Custom Bounding Box (Lat/Lon)...</option>
              </select>
            </div>

            {selectedPreset === -1 && (
              <div>
                <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>MIN_LON, MIN_LAT, MAX_LON, MAX_LAT</label>
                <input 
                  type="text" 
                  value={customBBox} 
                  onChange={(e) => setCustomBBox(e.target.value)}
                  placeholder="e.g. 76.32, 11.62, 76.37, 11.67"
                  style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', width: '200px' }}
                  disabled={isProcessingGEE}
                />
              </div>
            )}

            {/* Start Date */}
            <div>
              <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>FROM (START DATE)</label>
              <input
                type="month"
                value={startDate}
                min="2018-01"
                max="2025-12"
                onChange={(e) => setStartDate(e.target.value)}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '5px 8px', borderRadius: '4px', fontSize: '11px' }}
                disabled={isProcessingGEE}
              />
            </div>

            {/* End Date */}
            <div>
              <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>TO (END DATE)</label>
              <input
                type="month"
                value={endDate}
                min="2018-01"
                max="2025-12"
                onChange={(e) => setEndDate(e.target.value)}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '5px 8px', borderRadius: '4px', fontSize: '11px' }}
                disabled={isProcessingGEE}
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={isProcessingGEE}
              style={{ padding: '7px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', alignSelf: 'flex-end' }}
            >
              {isProcessingGEE ? (
                <>
                  <div className="spinner" style={{ width: '12px', height: '12px', borderWidth: '2px' }}></div>
                  <span>Querying GEE...</span>
                </>
              ) : (
                <span>⚡ Run Analysis</span>
              )}
            </button>
          </form>
        </div>

        {/* Live GEE Telemetry banner */}
        {isProcessingGEE && (
          <div style={{ marginTop: '12px', padding: '10px 14px', background: 'rgba(233, 196, 106, 0.1)', border: '1px solid var(--alert-orange)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
            <span>{geeStatusMsg} (Processing Sentinel-2 & DEM data on Earth Engine cloud...)</span>
          </div>
        )}
      </div>

      {/* Active Monitoring Scope & Metrics Bar */}
      {mapData && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '12px',
          marginBottom: '14px',
          background: 'linear-gradient(135deg, rgba(20,35,25,0.85) 0%, rgba(10,20,15,0.95) 100%)',
          padding: '12px 16px',
          borderRadius: '8px',
          border: '1px solid rgba(82,183,136,0.35)'
        }}>
          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>📅 Monitoring Window</span>
            <div style={{ fontSize: '13px', color: '#fff', fontWeight: 700, marginTop: '2px' }}>
              {mapData.start_date || startDate} → {mapData.end_date || endDate}
            </div>
            <span style={{ fontSize: '10px', color: 'var(--forest-400)' }}>
              {mapData.total_months || (mapData.months ? mapData.months.length : 24)} months active
            </span>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>🌲 Degraded Patches</span>
            <div style={{ fontSize: '15px', color: (mapData.summary?.degraded_patches || 0) > 20 ? 'var(--alert-red)' : 'var(--alert-orange)', fontWeight: 700, marginTop: '2px' }}>
              {mapData.summary?.degraded_patches || 0} / {mapData.summary?.total_patches || 64}
            </div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
              {mapData.summary?.degradation_pct || 0}% of sanctuary
            </span>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>💨 Biomass CO₂ Stored</span>
            <div style={{ fontSize: '15px', color: 'var(--forest-400)', fontWeight: 700, marginTop: '2px' }}>
              {mapData.summary?.total_carbon_tCO2 ? `${(mapData.summary.total_carbon_tCO2 / 1000).toFixed(1)}K t` : '252.0K t'}
            </div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
              ${mapData.summary?.total_carbon_value_usd ? (mapData.summary.total_carbon_value_usd / 1000000).toFixed(2) : '3.78'}M VCM Asset
            </span>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>⛰️ Landslide Hazard</span>
            <div style={{ fontSize: '15px', color: '#FFB703', fontWeight: 700, marginTop: '2px' }}>
              {mapData.summary?.landslide_high_risk_patches || 7} High/Critical
            </div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Pore-water shear risk</span>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>🏗️ Construction Safety</span>
            <div style={{ fontSize: '13px', fontWeight: 700, marginTop: '2px', color: '#52B788' }}>
              {mapData.summary?.safe_build_patches || 38} Safe <span style={{ color: 'var(--text-muted)' }}>|</span> <span style={{ color: '#E63946' }}>{mapData.summary?.prohibited_build_patches || 12} Hazard</span>
            </div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Geo-safety clearance</span>
          </div>
        </div>
      )}

      {/* Layer View Mode Switcher & Active Scope Summary */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
        {/* Layer Mode Toggle Buttons */}
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-card)', padding: '4px 6px', borderRadius: '8px', border: '1px solid rgba(82, 183, 136, 0.2)' }}>
          <button
            className={`btn btn-sm ${mapMode === 'health' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMapMode('health')}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            🌲 Forest Health
          </button>
          <button
            className={`btn btn-sm ${mapMode === 'landslide' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMapMode('landslide')}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            ⛰️ Landslide Hazard
          </button>
          <button
            className={`btn btn-sm ${mapMode === 'construction' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMapMode('construction')}
            style={{ fontSize: '11px', padding: '6px 12px', borderColor: mapMode === 'construction' ? 'var(--forest-500)' : '#FFB703', color: mapMode === 'construction' ? '#fff' : '#FFB703' }}
          >
            🏗️ Building Suitability (Can We Build?)
          </button>
        </div>

        {/* Legend for active layer */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '11px', color: 'var(--text-sec)', background: 'var(--bg-card)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span style={{ fontWeight: 600, color: '#fff' }}>
            {mapMode === 'construction' ? 'Building Legend:' : (mapMode === 'landslide' ? 'Landslide Legend:' : 'Health Legend:')}
          </span>
          {mapMode === 'construction' ? (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#52B788' }}></span> Safe to Build
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#FFB703' }}></span> Conditional Engineering
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#E63946' }}></span> Hazard: Do Not Build
              </span>
            </>
          ) : mapMode === 'landslide' ? (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#52B788' }}></span> Low Risk
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#FFB703' }}></span> Moderate
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#E63946' }}></span> High / Critical
              </span>
            </>
          ) : (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#52B788' }}></span> Healthy (&lt;0.20)
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#F4A261' }}></span> Degraded (0.20-0.45)
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#E63946' }}></span> Severe (&gt;0.45)
              </span>
            </>
          )}
        </div>
      </div>

      <div className="page-body map-layout-container">
        {/* Leaflet Map */}
        <div className="map-wrapper" style={{ height: '580px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(82, 183, 136, 0.2)' }}>
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
            <MapRecenter center={center} />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {mapData.patches.map(patch => {
              const bounds = getGeoBounds(patch);
              const color  = getPatchColor(patch);
              const patchKey = `${mapData.region_name || 'reg'}_${mapData.start_date || startDate}_${mapData.end_date || endDate}_${mapMode}_${patch.patch_id}_${color}`;
              
              return (
                <Rectangle
                  key={patchKey}
                  bounds={bounds}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: mapMode === 'construction' ? 0.45 : 0.38,
                    weight: 1.5
                  }}
                  eventHandlers={{
                    click: () => handlePatchClick(patch)
                  }}
                >
                  <Popup className="patch-popup" minWidth={360}>
                    <div className="popup-header">
                      <h3>Patch #{patch.patch_id} Details</h3>
                      {mapMode === 'construction' ? (
                        <span className="badge" style={{ background: color + '25', color: color, fontWeight: 700 }}>
                          {patch.construction_suitability?.badge || 'Building Check'}
                        </span>
                      ) : mapMode === 'landslide' ? (
                        <span className="badge" style={{ background: color + '25', color: color, fontWeight: 700 }}>
                          {patch.landslide?.risk_level || 'Moderate'} Risk
                        </span>
                      ) : (
                        <span className="badge" style={{ background: color + '25', color: color }}>
                          Score: {patch.degradation_score ? patch.degradation_score.toFixed(3) : '0.500'}
                        </span>
                      )}
                    </div>

                    <div className="popup-body">
                      <div className="meta-grid">
                        <div>
                          <strong>Grid Coordinate:</strong>
                          <span>Row {patch.grid_row}, Col {patch.grid_col}</span>
                        </div>
                        <div>
                          <strong>Health Status:</strong>
                          <span className={`badge badge-${patch.health_status === 'Healthy' ? 'healthy' : (patch.health_status === 'Degraded' ? 'degraded' : 'severe')}`}>
                            {patch.health_status}
                          </span>
                        </div>
                        {patch.slope_deg !== undefined && (
                          <div>
                            <strong>Slope Angle:</strong>
                            <span>{patch.slope_deg}°</span>
                          </div>
                        )}
                        {patch.rainfall_90d_mm !== undefined && (
                          <div>
                            <strong>90d Rainfall:</strong>
                            <span>{patch.rainfall_90d_mm} mm</span>
                          </div>
                        )}
                      </div>

                      {/* Prominent Action Buttons */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '10px' }}>
                        {/* 1. Building Suitability Button */}
                        <button
                          className="btn btn-secondary"
                          onClick={() => setActiveConstructionPatch(patch)}
                          style={{
                            width: '100%',
                            padding: '7px 10px',
                            fontSize: '11px',
                            fontWeight: 600,
                            color: '#52B788',
                            borderColor: 'rgba(82, 183, 136, 0.4)',
                            background: 'rgba(82, 183, 136, 0.1)',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                        >
                          <span>🏗️ Check Building Suitability & Safety Audit ({patch.construction_suitability?.safety_score || 70}%)</span>
                        </button>

                        {/* 2. Landslide Diagnostic Button */}
                        {patch.landslide && (
                          <button
                            className="btn btn-secondary"
                            onClick={() => setActiveDiagnosticPatch(patch)}
                            style={{
                              width: '100%',
                              padding: '7px 10px',
                              fontSize: '11px',
                              fontWeight: 600,
                              color: '#FFB703',
                              borderColor: 'rgba(255, 183, 3, 0.4)',
                              background: 'rgba(255, 183, 3, 0.1)',
                              display: 'flex',
                              justifyContent: 'center',
                              alignItems: 'center',
                              gap: '6px'
                            }}
                          >
                            <span>⛰️ View Landslide Diagnostic Report ({patch.landslide.probability_pct}%)</span>
                          </button>
                        )}
                      </div>

                      {/* NDVI Series Chart */}
                      {selectedPatch === patch.patch_id && patchSeries ? (
                        <div className="popup-chart-wrapper" style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <h4 className="section-title" style={{ margin: 0, fontSize: '11px' }}>📊 Monthly Vegetation Profile</h4>
                            {patchSeries.trend_status && (
                              <span className="badge" style={{ fontSize: '10px', background: patchSeries.trend_status === 'Greening' ? 'rgba(82, 183, 136, 0.2)' : (patchSeries.trend_status === 'Degrading' ? 'rgba(230, 57, 70, 0.2)' : 'rgba(255, 183, 3, 0.2)'), color: patchSeries.trend_status === 'Greening' ? '#52B788' : (patchSeries.trend_status === 'Degrading' ? '#E63946' : '#FFB703') }}>
                                {patchSeries.trend_icon} {patchSeries.trend_status} ({patchSeries.trend_pct > 0 ? `+${patchSeries.trend_pct}` : patchSeries.trend_pct}%)
                              </span>
                            )}
                          </div>

                          {/* Stat summary pills */}
                          <div style={{ display: 'flex', gap: '8px', fontSize: '9px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                            <span>Start NDVI: <strong style={{ color: '#fff' }}>{patchSeries.start_ndvi || (patchSeries.ndvi_series && patchSeries.ndvi_series[0]?.ndvi)}</strong></span>
                            <span>Latest NDVI: <strong style={{ color: '#fff' }}>{patchSeries.end_ndvi || (patchSeries.ndvi_series && patchSeries.ndvi_series[patchSeries.ndvi_series.length - 1]?.ndvi)}</strong></span>
                            {patchSeries.peak_greenness && (
                              <span>Peak: <strong style={{ color: 'var(--forest-400)' }}>{patchSeries.peak_greenness.month}</strong></span>
                            )}
                          </div>

                          <div style={{ width: '100%', height: '140px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={patchSeries.ndvi_series} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={9} />
                                <YAxis domain={[0, 1]} stroke="var(--text-muted)" fontSize={9} />
                                <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--forest-500)', color: '#fff' }} />
                                <Line type="monotone" dataKey="ndvi" stroke="var(--forest-500)" strokeWidth={1.8} dot={false} name="NDVI (Canopy)" />
                                <Line type="monotone" dataKey="evi" stroke="var(--alert-orange)" strokeWidth={1.2} dot={false} name="EVI (Greenness)" />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>

                          {/* Grad-CAM Heatmap overlay */}
                          {patchSeries.heatmap && (
                            <div className="heatmap-control-panel">
                              <button 
                                className={`btn btn-sm ${showHeatmap ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setShowHeatmap(!showHeatmap)}
                                style={{ marginTop: '8px', fontSize: '10px', padding: '4px 8px', width: '100%' }}
                              >
                                {showHeatmap ? 'Hide Explainability Heatmap' : '🔍 View Pixel Degradation Heatmap (Grad-CAM)'}
                              </button>
                              
                              {showHeatmap && (
                                <div className="heatmap-preview" style={{ marginTop: '8px', textAlign: 'center' }}>
                                  <h5 style={{ fontSize: '9px', color: 'var(--text-sec)', marginBottom: '4px', textTransform: 'uppercase' }}>
                                    Pixel-level Degradation Attention (Grad-CAM)
                                  </h5>
                                  <div style={{ display: 'inline-grid', gridTemplateColumns: 'repeat(16, 7px)', gap: '1px', background: '#000', padding: '3px', borderRadius: '4px' }}>
                                    {patchSeries.heatmap.map((row, rIdx) => 
                                      row.map((val, cIdx) => {
                                        const r = Math.floor(val * 255);
                                        const g = Math.floor((1 - val) * 200);
                                        const b = 40;
                                        return (
                                          <div 
                                            key={`${rIdx}-${cIdx}`} 
                                            style={{ width: '7px', height: '7px', background: `rgb(${r},${g},${b})` }}
                                            title={`Attention: ${val.toFixed(2)}`}
                                          />
                                        );
                                      })
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="popup-loading" style={{ marginTop: '8px', fontSize: '11px' }}>Loading chart...</div>
                      )}
                    </div>
                  </Popup>
                </Rectangle>
              );
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
