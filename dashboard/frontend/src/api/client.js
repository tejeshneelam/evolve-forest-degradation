const API_BASE = 'http://localhost:8000/api';

export const api = {
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

  // Reports
  exportPDF: (from, to) => {
    window.open(`${API_BASE}/export-pdf?date_from=${from}&date_to=${to}`, '_blank');
  },
};
