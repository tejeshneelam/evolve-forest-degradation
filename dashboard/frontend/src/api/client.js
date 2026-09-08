const API_BASE = 'http://localhost:8000/api';

export const api = {
  // Dynamic GEE Region Analysis (Version 2.0)
  processRegion: (bbox, regionName = "Custom Region", numMonths = 24, startDate = null, endDate = null) => {
    return fetch(`${API_BASE}/process-region`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bbox: bbox,
        region_name: regionName,
        num_months: numMonths,
        start_date: startDate,
        end_date: endDate,
      })
    }).then(async r => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to process region on Earth Engine');
      }
      return r.json();
    });
  },

  getCurrentRegion: () => fetch(`${API_BASE}/current-region`).then(r => r.json()),

  getLandslideDiagnostic: (patchId) => {
    return fetch(`${API_BASE}/landslide-diagnostic/${patchId}`).then(async r => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'Landslide diagnostic not found');
      }
      return r.json();
    });
  },

  getConstructionDiagnostic: (patchId) => {
    return fetch(`${API_BASE}/construction-diagnostic/${patchId}`).then(async r => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'Construction diagnostic not found');
      }
      return r.json();
    });
  },

  // Health
  getSummary:      () => fetch(`${API_BASE}/summary`).then(r => r.json()),
  getPatches:      () => fetch(`${API_BASE}/patches`).then(r => r.json()),
  getNDVISeries:   (pid) => fetch(`${API_BASE}/patches/${pid}/ndvi-series`).then(r => r.json()),

  // Wildlife
  getCorridors:    () => fetch(`${API_BASE}/corridors`).then(r => r.json()),

  // Risk
  getFireRisk:     () => fetch(`${API_BASE}/fire-risk`).then(r => r.json()),
  getLandslide:    () => fetch(`${API_BASE}/landslide`).then(r => r.json()),
  getEncroachment: () => fetch(`${API_BASE}/encroachment`).then(r => r.json()),

  // Conservation
  getCarbon:          () => fetch(`${API_BASE}/carbon`).then(r => r.json()),
  getReforestation:   () => fetch(`${API_BASE}/reforestation?top_n=15`).then(r => r.json()),
  getPatrolRoute:     (start, end) => fetch(`${API_BASE}/patrol-route?start=${start}&end=${end}`).then(r => r.json()),

  // GA
  getGAResults:    () => fetch(`${API_BASE}/ga-results`).then(r => r.json()),
  getGAThresholds: () => fetch(`${API_BASE}/ga-thresholds`).then(r => r.json()),
  getGAHistory:    () => fetch(`${API_BASE}/ga-history`).then(r => r.json()),
  runGAAdaptation: (targetObjective = "balanced", popSize = 30, mutationRate = 0.08) => {
    return fetch(`${API_BASE}/run-ga-adaptation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_objective: targetObjective,
        population_size: popSize,
        mutation_rate: mutationRate,
      })
    }).then(async r => {
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to run GA adaptation');
      }
      return r.json();
    });
  },

  // Reports
  exportPDF: (from, to) => {
    window.open(`${API_BASE}/export-pdf?date_from=${from}&date_to=${to}`, '_blank');
  },

  // History Vault (SQLite DB)
  getQueryHistory: () => fetch(`${API_BASE}/history/queries`).then(r => r.json()),
  logQuery: (queryData) => {
    return fetch(`${API_BASE}/history/log-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(queryData)
    }).then(r => r.json());
  },
  getPermits: () => fetch(`${API_BASE}/history/permits`).then(r => r.json()),
  savePermit: (permitData) => {
    return fetch(`${API_BASE}/history/save-permit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(permitData)
    }).then(r => r.json());
  },
  getHistoryStats: () => fetch(`${API_BASE}/history/stats`).then(r => r.json()),
};
