import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Polyline, Popup } from 'react-leaflet';
import { api } from '../api/client';

export default function CorridorMap() {
  const [corridorsData, setCorridorsData] = useState(null);
  const [loading, setLoading]             = useState(true);

  useEffect(() => {
    api.getCorridors()
      .then(data => {
        setCorridorsData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading corridors:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <span>Loading Corridor Analysis...</span>
      </div>
    );
  }

  if (!corridorsData) {
    return <div className="error-state text-center pad-lg">No corridor data available.</div>;
  }

  // Geographic calculations for mapping grid cells
  const getGeoCenter = (gridRow, gridCol) => {
    const latSize = (11.675 - 11.625) / 8;
    const lonSize = (76.375 - 76.325) / 8;
    const lat = 11.675 - gridRow * latSize - latSize / 2;
    const lon = 76.325 + gridCol * lonSize + lonSize / 2;
    return [lat, lon];
  };

  const getGeoBounds = (gridRow, gridCol) => {
    const latSize = (11.675 - 11.625) / 8;
    const lonSize = (76.375 - 76.325) / 8;
    const latMax = 11.675 - gridRow * latSize;
    const latMin = latMax - latSize;
    const lonMin = 76.325 + gridCol * lonSize;
    const lonMax = lonMin + lonSize;
    return [[latMin, lonMin], [latMax, lonMax]];
  };

  // Build the coordinates path for each corridor (runs N-S)
  const getCorridorLineCoords = (patchesList) => {
    return patchesList.map(pid => {
      const cellMeta = corridorsData.patch_health[pid];
      if (cellMeta) {
        return getGeoCenter(cellMeta.grid_row, cellMeta.grid_col);
      }
      return [11.65, 76.35]; // fallback
    });
  };

  const getStatusColor = (status) => {
    if (status === 'Intact') return '#52B788'; // green
    if (status === 'Weakened') return '#E9C46A'; // yellow
    return '#E63946'; // red
  };

  return (
    <div className="corridor-page">
      <div className="page-header">
        <h2 className="page-title">🐘 Wildlife Corridor Health</h2>
        <p className="page-subtitle">North-South elephant and tiger pathways mapped across Wayanad Muthanga Range. Alerts are automatically raised if degradation breaks corridor connectivity.</p>
      </div>

      <div className="page-body grid-2">
        {/* Left: Interactive Map */}
        <div className="map-card card" style={{ padding: 0, height: '520px', overflow: 'hidden' }}>
          <MapContainer center={[11.65, 76.35]} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {/* Draw individual grid patch outlines */}
            {Object.entries(corridorsData.patch_health).map(([pid, cell]) => {
              const bounds = getGeoBounds(cell.grid_row, cell.grid_col);
              const color = getStatusColor(cell.status);
              return (
                <Rectangle
                  key={pid}
                  bounds={bounds}
                  pathOptions={{
                    color: 'rgba(255,255,255,0.04)',
                    fillColor: color,
                    fillOpacity: cell.status !== 'Healthy' ? 0.25 : 0.02,
                    weight: 0.5
                  }}
                />
              );
            })}

            {/* Draw corridor flow lines */}
            {corridorsData.corridors.map(c => {
              const coords = getCorridorLineCoords(c.patches);
              const color  = getStatusColor(c.status);
              
              return (
                <Polyline
                  key={c.corridor_id}
                  positions={coords}
                  pathOptions={{
                    color: color,
                    weight: c.status === 'Intact' ? 6 : 4,
                    dashArray: c.status === 'Broken' ? '5, 10' : 'none',
                    opacity: 0.8
                  }}
                >
                  <Popup>
                    <div style={{ padding: '4px' }}>
                      <h4 style={{ margin: 0, color: 'var(--text-prim)' }}>Corridor {c.corridor_id}</h4>
                      <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '12px' }}>
                        <div><strong>Status:</strong> <span className={`badge badge-${c.status.toLowerCase()}`}>{c.status}</span></div>
                        <div><strong>Length:</strong> {c.length_km} km</div>
                        <div><strong>Avg Degradation:</strong> {c.mean_degradation}</div>
                        {c.break_points.length > 0 && (
                          <div style={{ color: 'var(--alert-red)', fontWeight: 600 }}>
                            ⚠️ Blocked at Patch: {c.break_points.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  </Popup>
                </Polyline>
              );
            })}
          </MapContainer>
        </div>

        {/* Right: Detailed list with statuses */}
        <div className="corridor-list-card card">
          <h3 className="section-title">🐘 Corridor Pathway Assessment</h3>
          <div className="corridor-items-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '450px', overflowY: 'auto' }}>
            {corridorsData.corridors.map(c => {
              const color = getStatusColor(c.status);
              return (
                <div key={c.corridor_id} className="corridor-item" style={{ borderLeft: `4px solid ${color}`, background: 'var(--bg-surface)', padding: '12px 16px', borderRadius: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                    <h4 style={{ color: '#fff', fontSize: '14px', margin: 0 }}>Corridor {c.corridor_id} (Col {c.corridor_id})</h4>
                    <span className={`badge badge-${c.status.toLowerCase()}`} style={{ marginLeft: 'auto' }}>{c.status}</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <div>📏 Length: <strong>{c.length_km} km</strong></div>
                    <div>📉 Avg Degradation: <strong>{c.mean_degradation}</strong></div>
                  </div>
                  {c.break_points.length > 0 ? (
                    <div style={{ background: 'rgba(230,57,70,0.1)', color: 'var(--alert-red)', padding: '6px 10px', borderRadius: '4px', marginTop: '8px', fontSize: '11px', display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span>🚨</span>
                      <span><strong>Warning:</strong> Degradation bottleneck detected at patch(es): {c.break_points.join(', ')}</span>
                    </div>
                  ) : (
                    <div style={{ color: 'var(--forest-500)', fontSize: '11px', marginTop: '6px' }}>
                      ✅ Pathway remains open and safe for wildlife migration.
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
