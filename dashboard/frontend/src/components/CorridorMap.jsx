import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Polyline, CircleMarker, Popup } from 'react-leaflet';
import { api } from '../api/client';

export default function CorridorMap() {
  const [corridorsData, setCorridorsData] = useState(null);
  const [loading, setLoading]             = useState(true);
  const [showGuide, setShowGuide]         = useState(true);
  const [selectedCorridor, setSelectedCorridor] = useState(null);

  useEffect(() => {
    // Check if dynamic region exists, else fetch baseline corridors
    api.getCurrentRegion()
      .then(dyn => {
        if (dyn && dyn.corridors) {
          // Format dynamic corridors into standard shape
          const patchHealthMap = {};
          dyn.patches.forEach(p => {
            patchHealthMap[p.patch_id] = {
              grid_row: p.grid_row,
              grid_col: p.grid_col,
              status: p.health_status,
              degradation_score: p.degradation_score
            };
          });
          setCorridorsData({
            corridors: dyn.corridors,
            patch_health: patchHealthMap,
            broken: dyn.corridors.filter(c => c.status === 'Broken').length
          });
          setLoading(false);
        } else {
          return api.getCorridors().then(data => {
            setCorridorsData(data);
            setLoading(false);
          });
        }
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
        <span>Mapping Ecological Corridors & Wildlife Pathways...</span>
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

  // Build curved, naturalistic pathway coordinates (simulating valley & canopy contour tracking)
  const getNaturalCorridorCoords = (cId, patchesList) => {
    const points = [];
    patchesList.forEach((pid, idx) => {
      const cell = corridorsData.patch_health[pid];
      if (cell) {
        const [baseLat, baseLon] = getGeoCenter(cell.grid_row, cell.grid_col);
        // Natural gentle lateral deviation based on row and corridor ID
        const lonOffset = Math.sin((cell.grid_row * 1.3) + cId) * 0.0018;
        points.push([baseLat, baseLon + lonOffset]);
      }
    });
    return points;
  };

  const getStatusColor = (status) => {
    if (status === 'Intact') return '#52B788'; // green
    if (status === 'Weakened') return '#FFB703'; // yellow/amber
    return '#E63946'; // red
  };

  // Animal route archetypes for each corridor
  const CORRIDOR_SPECIES = [
    { name: "Elephant Northern Foraging Route", icon: "🐘", species: "Asian Elephant (Elephas maximus)" },
    { name: "Tiger Dispersal Riparian Valley", icon: "🐅", species: "Bengal Tiger (Panthera tigris)" },
    { name: "Elephant Central Muthanga Migration Conduit", icon: "🐘", species: "Asian Elephant (Elephas maximus)" },
    { name: "Deer & Herbivore Inter-Reserve Passage", icon: "🦌", species: "Spotted Deer & Sambar" },
    { name: "Southern Western Ghats Tiger Belt", icon: "🐅", species: "Bengal Tiger (Panthera tigris)" },
    { name: "Elephant Interstate Bandipur Connector", icon: "🐘", species: "Asian Elephant (Elephas maximus)" },
    { name: "Canopy Arboreal Corridor (Leopard/Civet)", icon: "🐆", species: "Indian Leopard (Panthera pardus)" },
    { name: "Eastern Buffer Wildlife Path", icon: "🐘", species: "Asian Elephant (Elephas maximus)" },
  ];

  return (
    <div className="corridor-page">
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              🐘 Wildlife Corridors & Human-Animal Conflict Protection
            </h2>
            <p className="page-subtitle">
              Continuous canopy pathways connecting Wayanad, Nagarhole, Bandipur, and Mudumalai. Predicts migration chokepoints where forest degradation forces wildlife into human villages.
            </p>
          </div>
          <button 
            className={`btn btn-sm ${showGuide ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => setShowGuide(!showGuide)}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            {showGuide ? 'Hide Guidance Guide' : '📖 How to Read This Map & Guide'}
          </button>
        </div>
      </div>

      {/* Educational & Ranger Guidance Card */}
      {showGuide && (
        <div className="guide-card card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, rgba(82,183,136,0.1) 0%, rgba(20,35,25,0.6) 100%)', border: '1px solid rgba(82,183,136,0.3)', padding: '16px 20px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h3 style={{ fontSize: '14px', color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'Space Grotesk, sans-serif' }}>
              📖 Understanding Wildlife Corridors in the Western Ghats
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--forest-400)', fontWeight: 600 }}>Project Elephant & Tiger Conservation Protocol</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '12px', fontSize: '12px' }}>
            <div>
              <strong style={{ color: 'var(--forest-300)', display: 'block', marginBottom: '4px' }}>1. What Are These Paths?</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                Large mammals (elephants & tigers) must migrate between wet-season and dry-season feeding grounds. The 8 conduits represent the natural terrain arteries across the 64 monitoring zones.
              </p>
            </div>

            <div>
              <strong style={{ color: 'var(--alert-orange)', display: 'block', marginBottom: '4px' }}>2. Why Degradation is Dangerous</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                If even <strong>one patch</strong> in a corridor is clear-cut or degraded, animals reach a dead end. They are deflected into farming settlements, causing crop raiding and human casualties.
              </p>
            </div>

            <div>
              <strong style={{ color: '#fff', display: 'block', marginBottom: '4px' }}>3. Pathway Health Status</strong>
              <p style={{ margin: 0, color: 'var(--text-sec)', lineHeight: 1.4 }}>
                <span style={{ color: '#52B788', fontWeight: 600 }}>🟢 Intact:</span> Safe migration • <span style={{ color: '#FFB703', fontWeight: 600 }}>🟡 Weakened:</span> High conflict tension • <span style={{ color: '#E63946', fontWeight: 600 }}>🔴 Broken:</span> Severed conduit requiring eco-bridges or emergency patrols.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="page-body grid-2">
        {/* Left: Interactive Map with Curved Swaths & Waypoints */}
        <div className="map-card card" style={{ padding: 0, height: '560px', overflow: 'hidden', borderRadius: '10px' }}>
          <MapContainer center={[11.65, 76.35]} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {/* Draw individual grid patch outlines with subtle health opacity */}
            {Object.entries(corridorsData.patch_health).map(([pid, cell]) => {
              const bounds = getGeoBounds(cell.grid_row, cell.grid_col);
              const color = getStatusColor(cell.status);
              return (
                <Rectangle
                  key={pid}
                  bounds={bounds}
                  pathOptions={{
                    color: 'rgba(255,255,255,0.06)',
                    fillColor: color,
                    fillOpacity: cell.status === 'Severely Degraded' || cell.status === 'Broken' ? 0.35 : 0.05,
                    weight: 0.6
                  }}
                />
              );
            })}

            {/* Draw curved ecological migration swaths */}
            {corridorsData.corridors.map(c => {
              const coords = getNaturalCorridorCoords(c.corridor_id, c.patches);
              const color  = getStatusColor(c.status);
              const info   = CORRIDOR_SPECIES[c.corridor_id % CORRIDOR_SPECIES.length];
              const isSelected = selectedCorridor === c.corridor_id;

              return (
                <React.Fragment key={c.corridor_id}>
                  {/* Wide Swath Underlay (Canopy belt) */}
                  <Polyline
                    positions={coords}
                    pathOptions={{
                      color: color,
                      weight: isSelected ? 18 : 12,
                      opacity: isSelected ? 0.40 : 0.22,
                      lineCap: 'round',
                      lineJoin: 'round'
                    }}
                  />

                  {/* Core Migration Path */}
                  <Polyline
                    positions={coords}
                    pathOptions={{
                      color: color,
                      weight: isSelected ? 5 : (c.status === 'Intact' ? 3.5 : 2.5),
                      dashArray: c.status === 'Broken' ? '6, 8' : 'none',
                      opacity: 0.95
                    }}
                    eventHandlers={{
                      click: () => setSelectedCorridor(c.corridor_id)
                    }}
                  >
                    <Popup>
                      <div style={{ padding: '4px', minWidth: '220px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontSize: '18px' }}>{info.icon}</span>
                          <div>
                            <h4 style={{ margin: 0, color: 'var(--text-prim)', fontSize: '13px' }}>
                              Corridor #{c.corridor_id}
                            </h4>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{info.name}</span>
                          </div>
                        </div>

                        <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px' }}>
                          <div><strong>Status:</strong> <span className={`badge badge-${c.status.toLowerCase()}`}>{c.status}</span></div>
                          <div><strong>Primary Species:</strong> {info.species}</div>
                          <div><strong>Length:</strong> {c.length_km} km</div>
                          <div><strong>Degradation Pressure:</strong> {c.mean_degradation}</div>
                          {c.break_points && c.break_points.length > 0 ? (
                            <div style={{ background: 'rgba(230,57,70,0.15)', color: 'var(--alert-red)', padding: '6px', borderRadius: '4px', marginTop: '4px' }}>
                              ⚠️ <strong>SEVERED CHOKEPOINT:</strong> Blocked at Patch {c.break_points.join(', ')}. Animals deflected towards farmland!
                            </div>
                          ) : (
                            <div style={{ color: '#52B788', marginTop: '4px' }}>
                              ✅ Migration corridor continuous and unobstructed.
                            </div>
                          )}
                        </div>
                      </div>
                    </Popup>
                  </Polyline>

                  {/* Highlight Chokepoint Break Points with Pulsing Warning Markers */}
                  {c.break_points && c.break_points.map(breakPid => {
                    const cell = corridorsData.patch_health[breakPid];
                    if (!cell) return null;
                    const center = getGeoCenter(cell.grid_row, cell.grid_col);
                    return (
                      <CircleMarker
                        key={`break-${breakPid}`}
                        center={center}
                        radius={9}
                        pathOptions={{
                          color: '#E63946',
                          fillColor: '#E63946',
                          fillOpacity: 0.85,
                          weight: 2
                        }}
                      >
                        <Popup>
                          <div style={{ padding: '2px', fontSize: '11px' }}>
                            <strong style={{ color: '#E63946' }}>🚨 CORRIDOR BREACH: Patch #{breakPid}</strong>
                            <p style={{ margin: '4px 0 0', color: 'var(--text-sec)' }}>
                              Canopy cover severed here. Priority site for eco-duct restoration and forest patrol squads.
                            </p>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </React.Fragment>
              );
            })}
          </MapContainer>
        </div>

        {/* Right: Detailed List with Species Archetypes & Chokepoint Action Callouts */}
        <div className="corridor-list-card card" style={{ height: '560px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 className="section-title" style={{ margin: 0 }}>🐘 Wildlife Conduit Ledger</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Click to highlight path</span>
          </div>

          <div className="corridor-items-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
            {corridorsData.corridors.map(c => {
              const color = getStatusColor(c.status);
              const info = CORRIDOR_SPECIES[c.corridor_id % CORRIDOR_SPECIES.length];
              const isSelected = selectedCorridor === c.corridor_id;

              return (
                <div 
                  key={c.corridor_id} 
                  className="corridor-item" 
                  onClick={() => setSelectedCorridor(c.corridor_id)}
                  style={{ 
                    borderLeft: `4px solid ${color}`, 
                    background: isSelected ? 'rgba(82,183,136,0.15)' : 'var(--bg-surface)', 
                    padding: '12px 14px', 
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    border: isSelected ? `1px solid ${color}` : '1px solid rgba(255,255,255,0.04)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '16px' }}>{info.icon}</span>
                      <h4 style={{ color: '#fff', fontSize: '13px', margin: 0 }}>{info.name}</h4>
                    </div>
                    <span className={`badge badge-${c.status.toLowerCase()}`} style={{ marginLeft: 'auto', fontSize: '10px' }}>{c.status}</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginTop: '6px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <div>📏 Length: <strong style={{ color: '#fff' }}>{c.length_km} km</strong></div>
                    <div>📉 Degradation: <strong style={{ color: '#fff' }}>{c.mean_degradation}</strong></div>
                  </div>

                  {c.break_points && c.break_points.length > 0 ? (
                    <div style={{ background: 'rgba(230,57,70,0.12)', color: 'var(--alert-red)', padding: '6px 10px', borderRadius: '4px', marginTop: '8px', fontSize: '11px', display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span>⛔</span>
                      <span><strong>Critical Chokepoint:</strong> Severed at patch #{c.break_points.join(', #')}</span>
                    </div>
                  ) : (
                    <div style={{ color: 'var(--forest-400)', fontSize: '11px', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span>✓</span> Pathway intact; safe seasonal passage confirmed.
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
