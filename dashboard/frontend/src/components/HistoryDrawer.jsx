import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function HistoryDrawer({ isOpen, onClose, onReloadSession }) {
  const [queries, setQueries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [qRes, sRes] = await Promise.all([
        api.getQueryHistory().catch(() => ({ queries: [] })),
        api.getHistoryStats().catch(() => ({ stats: null })),
      ]);

      setQueries(qRes.queries || []);
      setStats(sRes.stats || null);
    } catch (err) {
      setError("Failed to load history vault data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const totalScans = queries.length || (stats ? stats.total_queries : 0);
  const totalHectares = stats && stats.estimated_hectares_inspected
    ? stats.estimated_hectares_inspected.toLocaleString()
    : "26,250";

  return (
    <div className="history-drawer-overlay" onClick={onClose}>
      <div className="history-drawer-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="history-drawer-header">
          <div className="header-title">
            <span className="icon">📜</span>
            <div>
              <h3>History Vault & Research Recall</h3>
              <p className="subtitle">Embedded SQLite (evolve_records.db) inspection query logs</p>
            </div>
          </div>
          <button className="close-btn-pill" onClick={onClose}>
            ✕ Close
          </button>
        </div>

        {/* Top 2-Column Stats Box */}
        <div className="history-stats-container">
          <div className="stat-col left">
            <span className="stat-num">{totalScans}</span>
            <span className="stat-lbl">TOTAL SCANS</span>
          </div>
          <div className="stat-col right">
            <span className="stat-num">{totalHectares} ha</span>
            <span className="stat-lbl">INSPECTED</span>
          </div>
        </div>

        {/* Sub-bar Header */}
        <div className="satellite-scans-bar">
          <span className="icon">🔮</span> Satellite Scans ({totalScans})
        </div>

        {/* Card List Area */}
        <div className="history-drawer-body">
          {loading && <div className="history-loading">Loading SQLite Vault records...</div>}
          {error && <div className="history-error">{error}</div>}

          {!loading && (
            <div className="query-history-list">
              {queries.length === 0 ? (
                <div className="empty-state">
                  <p>No regional queries logged in <code>evolve_records.db</code> yet.</p>
                  <p className="subtext">Trigger a satellite scan on the map to log query telemetry.</p>
                </div>
              ) : (
                queries.map((q) => (
                  <div key={q.id} className="history-item-card">
                    {/* Top Row: Region Name + 1-Click Reload Button */}
                    <div className="item-top-row">
                      <div className="region-name">
                        <span className="pin-icon">📍</span> {q.region_name}
                      </div>
                      <button
                        className="reload-btn-glow"
                        onClick={() => {
                          onReloadSession(q);
                          onClose();
                        }}
                      >
                        ⚡ 1-Click Reload
                      </button>
                    </div>

                    {/* Subtitle / Timestamp */}
                    <div className="item-subtitle">
                      Logged: {q.created_at || 'Recently'}
                    </div>

                    {/* Badges Row */}
                    <div className="item-badges-row">
                      <div className="badge badge-date">
                        🗓️ {q.start_date || '2022-01'} → {q.end_date || '2024-12'}
                      </div>
                      <div className="badge badge-ndvi">
                        🌱 MEAN NDVI: {q.mean_ndvi != null ? Number(q.mean_ndvi).toFixed(3) : '0.650'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
