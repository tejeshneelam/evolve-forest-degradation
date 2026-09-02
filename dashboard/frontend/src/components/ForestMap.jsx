import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Popup, useMap } from 'react-leaflet';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { api } from '../api/client';
import LandslideReportModal from './LandslideReportModal';

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
  
  // Dynamic Region selection states
  const [selectedPreset, setSelectedPreset]   = useState(0);
  const [customBBox, setCustomBBox]           = useState("76.325, 11.625, 76.375, 11.675");
  const [isProcessingGEE, setIsProcessingGEE] = useState(false);
  const [geeStatusMsg, setGeeStatusMsg]       = useState('');
  const [activeDiagnosticPatch, setActiveDiagnosticPatch] = useState(null);

  useEffect(() => {
    // Check if an existing dynamic region is loaded, otherwise load baseline patches
    api.getCurrentRegion()
      .then(dyn => {
        if (dyn && dyn.patches) {
          setMapData(dyn);
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
    if (patch.ndvi_series) {
      setPatchSeries(patch);
    } else {
      setPatchSeries(null);
      api.getNDVISeries(patch.patch_id)
        .then(data => setPatchSeries(data))
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
    setGeeStatusMsg("🛰️ Querying Google Earth Engine (Sentinel-2, SRTM Slope, CHIRPS Rainfall)...");

    api.processRegion(bbox, name, 24)
      .then(res => {
        setMapData(res);
        setIsProcessingGEE(false);
        setGeeStatusMsg('');
        setSelectedPatch(null);
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

  const getPatchColor = (score) => {
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

      {/* Header & Global Earth Engine Controls */}
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              🌍 Global Forest Health Map <span className="badge" style={{ background: 'rgba(82, 183, 136, 0.2)', color: 'var(--forest-300)', fontSize: '11px' }}>v2.0 GEE Live</span>
            </h2>
            <p className="page-subtitle">
              Select any forest region on Earth. Google Earth Engine dynamically crops Sentinel-2 imagery, runs EvOLve AI inference, and evaluates landslide hazards in real time.
            </p>
          </div>

          {/* Earth Engine Selector Toolbar */}
          <form onSubmit={handleTriggerGEE} style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--bg-card)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(82, 183, 136, 0.2)' }}>
            <div>
              <label style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>TARGET FOREST REGION</label>
              <select 
                value={selectedPreset} 
                onChange={(e) => setSelectedPreset(parseInt(e.target.value))}
                style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '12px' }}
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
                  style={{ background: 'var(--bg-surface)', border: '1px solid rgba(82, 183, 136, 0.3)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '11px', width: '220px' }}
                  disabled={isProcessingGEE}
                />
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={isProcessingGEE}
              style={{ marginTop: '16px', padding: '7px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {isProcessingGEE ? (
                <>
                  <div className="spinner" style={{ width: '12px', height: '12px', borderWidth: '2px' }}></div>
                  <span>Querying GEE...</span>
                </>
              ) : (
                <span>⚡ Run GEE Analysis</span>
              )}
            </button>
          </form>
        </div>

        {/* Live GEE Telemetry banner */}
        {isProcessingGEE && (
          <div style={{ marginTop: '12px', padding: '10px 14px', background: 'rgba(233, 196, 106, 0.1)', border: '1px solid var(--alert-orange)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }}></div>
            <span>{geeStatusMsg} (Takes ~10–15 seconds to stream all 64 patches from cloud)</span>
          </div>
        )}
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
              const color  = getPatchColor(patch.degradation_score);
              
              return (
                <Rectangle
                  key={patch.patch_id}
                  bounds={bounds}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.38,
                    weight: 1.5
                  }}
                  eventHandlers={{
                    click: () => handlePatchClick(patch)
                  }}
                >
                  <Popup className="patch-popup" minWidth={350}>
                    <div className="popup-header">
                      <h3>Patch {patch.patch_id} Details</h3>
                      <span className="badge" style={{ background: color + '25', color: color }}>
                        Score: {patch.degradation_score.toFixed(3)}
                      </span>
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
                            <strong>Slope (SRTM):</strong>
                            <span>{patch.slope_deg}°</span>
                          </div>
                        )}
                        {patch.rainfall_90d_mm !== undefined && (
                          <div>
                            <strong>90d Rain:</strong>
                            <span>{patch.rainfall_90d_mm} mm</span>
                          </div>
                        )}
                      </div>

                      {/* Prominent Landslide Diagnostic Button */}
                      {patch.landslide && (
                        <button
                          className="btn btn-secondary"
                          onClick={() => setActiveDiagnosticPatch(patch)}
                          style={{
                            width: '100%',
                            marginTop: '10px',
                            padding: '8px',
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

                      {/* NDVI Series Chart */}
                      {selectedPatch === patch.patch_id && patchSeries ? (
                        <div className="popup-chart-wrapper" style={{ marginTop: '12px' }}>
                          <h4 className="section-title">📊 Monthly Vegetation Profile</h4>
                          <div style={{ width: '100%', height: '140px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={patchSeries.ndvi_series} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={9} />
                                <YAxis domain={[0, 1]} stroke="var(--text-muted)" fontSize={9} />
                                <Tooltip contentStyle={{ background: 'var(--bg-card)', borderColor: 'var(--forest-500)', color: '#fff' }} />
                                <Line type="monotone" dataKey="ndvi" stroke="var(--forest-500)" strokeWidth={1.5} dot={false} name="NDVI" />
                                <Line type="monotone" dataKey="evi" stroke="var(--alert-orange)" strokeWidth={1} dot={false} name="EVI" />
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
