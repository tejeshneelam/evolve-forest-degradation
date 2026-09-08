import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import ForestMap from './components/ForestMap';
import CorridorMap from './components/CorridorMap';
import RiskDashboard from './components/RiskDashboard';
import ConservationTab from './components/ConservationTab';
import GALog from './components/GALog';
import HistoryVaultPage from './components/HistoryVaultPage';
import ReportExport from './components/ReportExport';
import './App.css';

const TABS = [
  { id: 'map',          label: '🗺️ Forest Health',    component: ForestMap },
  { id: 'wildlife',     label: '🐘 Wildlife Corridors',component: CorridorMap },
  { id: 'risk',         label: '🔥 Risk Dashboard',    component: RiskDashboard },
  { id: 'conservation', label: '🌱 Conservation',      component: ConservationTab },
  { id: 'ga',           label: '🧬 GA Adaptation Log', component: GALog },
  { id: 'history',      label: '📜 History Vault',     component: HistoryVaultPage },
  { id: 'reports',      label: '📄 Reports',           component: ReportExport },
];

export default function App() {
  const [activeTab, setActiveTab]         = useState('map');
  const [summary, setSummary]             = useState(null);
  const [apiConnected, setApiConnected]   = useState(null);
  const [reloadedSession, setReloadedSession] = useState(null);

  useEffect(() => {
    api.getSummary()
      .then(res => {
        setSummary(res);
        setApiConnected(true);
      })
      .catch(() => {
        setSummary(null);
        setApiConnected(false);
      });
  }, []);

  const handleReloadSession = (session) => {
    setReloadedSession({ ...session, _reloadTimestamp: Date.now() });
    setActiveTab('map');
  };

  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component;

  return (
    <div className="app">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">Ev<span>OL</span>ve</div>
          <div className="brand-sub">Forest Intelligence System</div>
          <div className="brand-area">🌿 Wayanad, Kerala</div>
        </div>

        <nav className="sidebar-nav">
          {TABS.map(tab => (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Stats panel */}
        {summary && (
          <div className="sidebar-stats">
            <div className="stat-item">
              <span className="stat-val">{summary.total_patches}</span>
              <span className="stat-label">Patches Monitored</span>
            </div>
            <div className="stat-item degraded">
              <span className="stat-val">{summary.degraded_patches}</span>
              <span className="stat-label">Degraded ({summary.degradation_pct}%)</span>
            </div>
            {summary.total_carbon_tCO2 && (
              <div className="stat-item carbon">
                <span className="stat-val">{(summary.total_carbon_tCO2 / 1000).toFixed(1)}K</span>
                <span className="stat-label">Tons CO₂ Stored</span>
              </div>
            )}
            {summary.encroachment_alerts !== null && (
              <div className="stat-item alert">
                <span className="stat-val">{summary.encroachment_alerts}</span>
                <span className="stat-label">Encroachment Alerts</span>
              </div>
            )}
          </div>
        )}

        <div className="sidebar-footer">
          <div className="api-status-pill">
            <span className={`status-dot ${apiConnected === true ? 'online' : apiConnected === false ? 'offline' : 'checking'}`}></span>
            <span className="status-text">
              {apiConnected === true ? 'FastAPI Active (8000)' : apiConnected === false ? 'API Offline' : 'Connecting...'}
            </span>
          </div>
          <div className="footer-text">BTech Final Year Project</div>
          <div className="footer-text">Amrita School of Computing</div>
          <div className="footer-badge">2019 – 2025</div>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────────────────── */}
      <main className="main-content">
        <div className="tab-content">
          {ActiveComponent && (
            <ActiveComponent
              reloadedSession={reloadedSession}
              onReloadSession={handleReloadSession}
              onClose={() => setActiveTab('map')}
            />
          )}
        </div>
      </main>
    </div>
  );
}
