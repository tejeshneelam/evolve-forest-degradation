const API_BASE = 'http://localhost:8000/api';

/**
 * Robust fetch response handler with security exception awareness (HTTP 429 Rate Limiting,
 * validation errors, and retry-after guidance).
 */
async function handleResponse(response, defaultErrorMsg) {
  if (response.status === 429) {
    const data = await response.json().catch(() => ({}));
    const retryAfter = response.headers.get('Retry-After') || data.retry_after_seconds || 60;
    throw new Error(
      `⚠️ Security Rate Limit Exceeded (HTTP 429): ${data.message || 'Too many requests'}. ` +
      `Throttled for defense. Please wait ${retryAfter} seconds before submitting more requests.`
    );
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    let detailMsg = defaultErrorMsg;
    if (err.detail) {
      if (Array.isArray(err.detail)) {
        detailMsg = err.detail.map(d => d.msg || JSON.stringify(d)).join(' | ');
      } else {
        detailMsg = err.detail;
      }
    } else if (err.message) {
      detailMsg = err.message;
    }
    throw new Error(detailMsg);
  }

  return response.json();
}

export const api = {
  // Dynamic GEE Region Analysis (Version 2.0 with Rate Limiting & Bounds Sanitization)
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
    }).then(r => handleResponse(r, 'Failed to process region on Earth Engine'));
  },

  getCurrentRegion: () => fetch(`${API_BASE}/current-region`).then(r => handleResponse(r, 'Failed to fetch current region')),

  getLandslideDiagnostic: (patchId) => {
    return fetch(`${API_BASE}/landslide-diagnostic/${patchId}`)
      .then(r => handleResponse(r, 'Landslide diagnostic not found'));
  },

  getConstructionDiagnostic: (patchId) => {
    return fetch(`${API_BASE}/construction-diagnostic/${patchId}`)
      .then(r => handleResponse(r, 'Construction diagnostic not found'));
  },

  // On-demand geotechnical construction suitability inference
  getConstructionSuitabilityInference: (data) => {
    return fetch(`${API_BASE}/inference/construction-suitability`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => handleResponse(r, 'Failed to assess construction suitability'));
  },

  // Security & Compliance Audit Logs
  getAuditLogs: (limit = 50) => {
    return fetch(`${API_BASE}/security/audit-logs?limit=${limit}`)
      .then(r => handleResponse(r, 'Failed to retrieve audit telemetry'));
  },

  // Health
  getSummary:      () => fetch(`${API_BASE}/summary`).then(r => handleResponse(r, 'Failed to load summary')),
  getPatches:      () => fetch(`${API_BASE}/patches`).then(r => handleResponse(r, 'Failed to load patches')),
  getNDVISeries:   (pid) => fetch(`${API_BASE}/patches/${pid}/ndvi-series`).then(r => handleResponse(r, 'Failed to load NDVI series')),

  // Wildlife
  getCorridors:    () => fetch(`${API_BASE}/corridors`).then(r => handleResponse(r, 'Failed to load corridors')),

  // Risk
  getFireRisk:     () => fetch(`${API_BASE}/fire-risk`).then(r => handleResponse(r, 'Failed to load fire risk')),
  getLandslide:    () => fetch(`${API_BASE}/landslide`).then(r => handleResponse(r, 'Failed to load landslide risk')),
  getEncroachment: () => fetch(`${API_BASE}/encroachment`).then(r => handleResponse(r, 'Failed to load encroachment alerts')),

  // Conservation
  getCarbon:          () => fetch(`${API_BASE}/carbon`).then(r => handleResponse(r, 'Failed to load carbon stock')),
  getReforestation:   () => fetch(`${API_BASE}/reforestation?top_n=15`).then(r => handleResponse(r, 'Failed to load reforestation priority')),
  getPatrolRoute:     (start, end) => fetch(`${API_BASE}/patrol-route?start=${start}&end=${end}`).then(r => handleResponse(r, 'Failed to calculate patrol route')),

  // GA
  getGAResults:    () => fetch(`${API_BASE}/ga-results`).then(r => handleResponse(r, 'Failed to load GA results')),
  getGAThresholds: () => fetch(`${API_BASE}/ga-thresholds`).then(r => handleResponse(r, 'Failed to load GA thresholds')),
  getGAHistory:    () => fetch(`${API_BASE}/ga-history`).then(r => handleResponse(r, 'Failed to load GA history')),
  runGAAdaptation: (targetObjective = "balanced", popSize = 30, mutationRate = 0.08) => {
    return fetch(`${API_BASE}/run-ga-adaptation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_objective: targetObjective,
        population_size: popSize,
        mutation_rate: mutationRate,
      })
    }).then(r => handleResponse(r, 'Failed to run GA adaptation'));
  },

  // Reports
  exportPDF: (from, to) => {
    window.open(`${API_BASE}/export-pdf?date_from=${from}&date_to=${to}`, '_blank');
  },
};
