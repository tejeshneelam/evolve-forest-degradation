import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Popup } from 'react-leaflet';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { api } from '../api/client';

export default function ForestMap() {
  const [mapData, setMapData]         = useState(null);
  const [selectedPatch, setSelectedPatch] = useState(null);
  const [patchSeries, setPatchSeries]     = useState(null);
  const [showHeatmap, setShowHeatmap]     = useState(false);
  const [loading, setLoading]             = useState(true);

  useEffect(() => {
    api.getPatches()
      .then(data => {
        setMapData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading patches:", err);
        setLoading(false);
      });
  }, []);

  const handlePatchClick = (patchId) => {
    setSelectedPatch(patchId);
    setPatchSeries(null);
    setShowHeatmap(false);
    api.getNDVISeries(patchId)
      .then(data => {
        setPatchSeries(data);
      })
      .catch(err => console.error("Error loading series:", err));
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Loading Forest Health Map...</span>
      </div>
    );
  }

  if (!mapData) {
    return <div className="error-state text-center pad-lg">No map data available. Make sure the backend is running.</div>;
  }

  // Wayanad Center Coordinates
  const center = mapData.aoi?.center || [11.65, 76.35];

  // Helper to get color based on degradation score
  const getPatchColor = (score) => {
    if (score < 0.20) return '#52B788'; // Green
    if (score < 0.45) return '#F4A261'; // Orange
    return '#E63946'; // Red
  };

  // Convert pixel bounds to geographic coordinates (approximation for grid mapping)
  // Muthanga bounding box: lat 11.625 to 11.675, lon 76.325 to 76.375
  const getGeoBounds = (gridRow, gridCol) => {
    const latSize = (11.675 - 11.625) / 8;
    const lonSize = (76.375 - 76.325) / 8;
    
    // Top-left is (0,0) in grid row
    const latMax = 11.675 - gridRow * latSize;
    const latMin = latMax - latSize;
    const lonMin = 76.325 + gridCol * lonSize;
    const lonMax = lonMin + lonSize;
    
    return [
      [latMin, lonMin],
      [latMax, lonMax]
    ];
  };

  return (
    <div className="forest-map-page">
      <div className="page-header">
        <h2 className="page-title">🗺️ Forest Health Map</h2>
        <p className="page-subtitle">Wayanad Muthanga Range. Click any patch on the grid to inspect monthly NDVI trends and Grad-CAM pixel heatmaps.</p>
      </div>

      <div className="page-body map-layout-container">
        {/* Leaflet Map */}
        <div className="map-wrapper" style={{ height: '580px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(82, 183, 136, 0.2)' }}>
          <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
            {/* Dark Premium Basemap */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {/* Grid of patches */}
            {mapData.patches.map(patch => {
              const bounds = getGeoBounds(patch.grid_row, patch.grid_col);
              const color  = getPatchColor(patch.degradation_score);
              
              return (
                <Rectangle
                  key={patch.patch_id}
                  bounds={bounds}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.35,
                    weight: 1.5
                  }}
                  eventHandlers={{
                    click: () => handlePatchClick(patch.patch_id)
                  }}
                >
                  <Popup className="patch-popup" minWidth={350}>
                    <div className="popup-header">
                      <h3>Patch {patch.patch_id} Details</h3>
                      <span className="badge" style={{ background: color + '20', color: color }}>
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
                          <strong>Status:</strong>
                          <span className={`badge badge-${patch.health_status === 'Healthy' ? 'healthy' : (patch.health_status === 'Degraded' ? 'degraded' : 'severe')}`}>
                            {patch.health_status}
                          </span>
                        </div>
                      </div>

                      {/* NDVI Series Chart */}
                      {selectedPatch === patch.patch_id && patchSeries ? (
                        <div className="popup-chart-wrapper">
                          <h4 className="section-title">📊 6-Year NDVI Trend</h4>
                          <div style={{ width: '100%', height: '150px' }}>
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

                          {/* Heatmap overlay option */}
                          {patchSeries.heatmap && (
                            <div className="heatmap-control-panel">
                              <button 
                                className={`btn btn-sm ${showHeatmap ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setShowHeatmap(!showHeatmap)}
                                style={{ marginTop: '10px', fontSize: '11px', padding: '5px 10px', width: '100%' }}
                              >
                                {showHeatmap ? 'hide explainability heatmap' : '🔍 view pixel degradation heatmap (Grad-CAM)'}
                              </button>
                              
                              {showHeatmap && (
                                <div className="heatmap-preview" style={{ marginTop: '10px', textAlign: 'center' }}>
                                  <h5 style={{ fontSize: '10px', color: 'var(--text-sec)', marginBottom: '5px', textTransform: 'uppercase' }}>
                                    Pixel-level attention (Grad-CAM)
                                  </h5>
                                  <div style={{ display: 'inline-grid', gridTemplateColumns: 'repeat(16, 8px)', gap: '1px', background: '#000', padding: '4px', borderRadius: '4px' }}>
                                    {/* Subsample 64x64 down to 16x16 to fit inside the popup */}
                                    {patchSeries.heatmap.filter((_, idx) => idx % 4 === 0).map((row, rIdx) => 
                                      row.filter((_, cIdx) => cIdx % 4 === 0).map((val, cIdx) => {
                                        // Color map: yellow (healthy) -> red (degraded)
                                        const r = Math.floor(val * 255);
                                        const g = Math.floor((1 - val) * 200);
                                        const b = 50;
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
                                  <p style={{ fontSize: '9px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                    Red zones indicate pixels with highest degradation gradients.
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="popup-loading">Loading chart...</div>
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
