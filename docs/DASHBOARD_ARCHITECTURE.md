# EvOLve Dashboard Architecture & Navigation Guide

**Project**: EvOLve — Evolutionary-Optimized Forest Degradation Intelligence Framework  
**Branch**: `tarak`  
**Target Scope**: 6-Tab Clean Ecological UI with Backend-Enforced Cyber Security  

---

## 1. Executive Architectural Overview

The EvOLve dashboard interface is designed specifically for forest monitoring officers, ecologists, and conservation authorities. The frontend strictly separates **domain-specific ecological intelligence** from **infrastructure & cyber security controls**.

* **Frontend UI (React 19)**: Dedicated solely to ecological data visualization, dynamic satellite ingestion, AI inference diagnostics, and printable reporting across **6 core tabs**.
* **Backend Security Layer (FastAPI Middleware)**: Cyber security controls (SlowAPI rate limiting, geographic bounding box sanitization, OWASP HTTP response headers, CORS whitelisting, and forensic audit logging) are implemented and enforced natively at the server gateway layer.

---

## 2. Active Dashboard Tabs

| Tab # | Module Name | Primary React Component | Backend Endpoints | Key Capabilities |
| :---: | :--- | :--- | :--- | :--- |
| **1** | 🗺️ **Forest Health** | `ForestMap.jsx` | `POST /api/process-region`<br>`GET /api/current-region`<br>`GET /api/patches/:id/ndvi-series` | Global dynamic Sentinel-2 & Hansen GFC ingestion, multi-year temporal sliders, patch-level vegetation health profiles. |
| **2** | 🐘 **Wildlife Corridors** | `CorridorMap.jsx` | `GET /api/corridors` | Elephant and apex predator movement corridor mapping, resistance raster overlays, pinch-point threat analysis. |
| **3** | 🔥 **Risk Dashboard** | `RiskDashboard.jsx` | `GET /api/fire-risk`<br>`GET /api/landslide`<br>`GET /api/encroachment`<br>`GET /api/landslide-diagnostic/:id` | Multi-hazard early warning center, real-time fire fuel indices, explainable landslide diagnostics with SHAP attribution. |
| **4** | 🌱 **Conservation** | `ConservationTab.jsx` | `GET /api/carbon`<br>`GET /api/reforestation`<br>`GET /api/patrol-route` | Aboveground biomass & carbon stock quantification ($tCO_2$), optimal reforestation parcel rankings, Dijkstra ranger patrol routing. |
| **5** | 🧬 **GA Adaptation Log** | `GALog.jsx` | `GET /api/ga-results`<br>`GET /api/ga-thresholds`<br>`POST /api/run-ga-adaptation` | Evolutionary threshold self-adaptation across 30 generations, multi-objective Pareto optimization (balanced, fire precision, monsoon recall). |
| **6** | 📄 **Reports** | `ReportExport.jsx` | `GET /api/export-pdf` | Executive briefing generator, PDF compliance document generation, automated geospatial diagnostic exports. |

---

## 3. Cyber Security & Hardening Architecture

Rather than burdening domain end-users with raw administrative telemetry, cyber security controls operate unobtrusively in the background:

1. **SlowAPI Rate Limiting**:
   - `POST /api/run-ga-adaptation`: Enforces maximum **5 requests / minute**.
   - `POST /api/process-region`: Enforces maximum **30 requests / minute**.
   - Client interceptor (`client.js` `handleResponse`) automatically converts HTTP 429 into friendly, actionable retry notices.
2. **Geographic Coordinate Sanitization**:
   - Validates latitude bounds ($-90^\circ \le \text{lat} \le +90^\circ$) and longitude bounds ($-180^\circ \le \text{lon} \le +180^\circ$).
   - Limits real-time dynamic analysis to $\le 0.35^\circ \times 0.35^\circ$ ($\approx 35\text{km} \times 35\text{km}$).
3. **Response Security Headers**:
   - Middleware automatically injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`, and `Content-Security-Policy`.
4. **Forensic Audit Telemetry**:
   - All inbound requests are tracked in a 100-event ring buffer capturing client IP, endpoint, HTTP status, and latency ($ms$).

---

## 4. Local Execution Guide

### Backend Service (FastAPI)
```powershell
python -m uvicorn dashboard.backend.main:app --port 8000
```
- API Base: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### Frontend Application (React)
```powershell
cd dashboard/frontend
npm start
```
- Web Dashboard: `http://localhost:3000`
