# 🌲 EvOLve — Forest Cover Monitoring & Disaster Risk Mitigation Platform
### *An Evolutionary AI Framework & Geospatial Application Using Sentinel-2 Satellite Data*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2.0-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Google Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-API-4285F4.svg?logo=google-cloud&logoColor=white)](https://earthengine.google.com)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900.svg?logo=leaflet&logoColor=white)](https://leafletjs.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Executive Summary

**EvOLve** (**Ev**olutionary **O**ptimization, **L**earning, and **v**egetation **e**nvironmental adaptive systems) is a full-stack geospatial intelligence platform designed for forest rangers, civil planners, and disaster management authorities.

Traditional forest monitoring systems rely on periodic biennial reports (such as the *India State of Forest Report - ISFR*) or static satellite thresholds that fail during natural seasonal leaf-shedding. In the wake of catastrophic monsoon-triggered disasters—such as the **2024 Wayanad Landslides**—EvOLve integrates **Google Earth Engine (GEE)** live satellite streaming, self-supervised spatio-temporal representations, and **Genetic Algorithms (GA)** to deliver real-time environmental monitoring, early disaster warnings, and sustainable land-use intelligence.

---

## 👥 Project Team & Work Breakdown

**Amrita Vishwa Vidyapeetham | School of Computing | Department of Computer Science & Engineering**  
**Course**: `23CSE399` — Project Phase 2 (Application Project — Type 2)

| Student Name | Register Number | Role & Core Modules | GitHub Branch |
|:---|:---:|:---|:---:|
| **Neelam Tejesh** *(Lead)* | `CB.EN.U4CSE23042` | Spatio-Temporal Vision Transformer, Live GEE Pipeline, Land Construction Suitability Engine | `main` |
| **Kolla Girish** | `CB.EN.U4CSE23223` | Multi-Threat Risk Dashboard, Fuel Modeling & Officer RBAC | `feature/auth-rbac-ui` |
| **D Vasishta** | `CB.EN.U4CSE23016` | Wildlife Corridor Graph Analysis, Carbon Stock Accounting & SQLite Vault | `feature/sqlite-history-db` |
| **Ande Tarak** | `CB.EN.U4CSE23212` | Genetic Algorithm Multi-Objective Optimization & Cyber Security Hardening | `feature/security-rate-limiting` |

---

## 🌟 Core Application Capabilities

### 1. Dynamic Google Earth Engine (GEE) Ingestion
- **Global Coverage**: Query any forest bounding box on Earth (Wayanad, Silent Valley, Amazon Basin, Congo Basin, or custom coordinates).
- **Multi-Sensor Fusion**:
  - **Sentinel-2 L2A**: Multi-spectral imagery ($B2, B3, B4, B8, B11, B12$) + NDVI and EVI.
  - **USGS SRTM DEM (30m)**: Real-time terrain elevation and slope gradient calculations.
  - **CHIRPS Daily**: 90-day antecedent precipitation (soil moisture saturation).
  - **Hansen Global Forest Change**: Canopy cover density and historical loss tracking.
- **In-Memory $8 \times 8$ Grid Slicing**: Automatically partitions any target area into 64 spatial patches ($640\text{m} \times 640\text{m}$ each) within 10–15 seconds.

### 2. Dynamic Time Range Selector (2018–2025)
- Inspect monthly vegetation trajectories over custom historical periods.
- Distinguishes between natural dry-season phenological shedding and permanent canopy deforestation.

### 3. Mountain Construction Suitability Index & Safety Audit
- **Safety Formula**: Computes structural feasibility ($0 - 100$) based on slope stability, landslide hazard, tree cover protection, and eco-sensitive boundary buffers.
- **Audit Decision**: Categorizes patches as `PERMITTED`, `CONDITIONAL APPROVAL`, or `STRICTLY PROHIBITED`.
- **Diagnostic Modal**: Detailed engineering reports with civil mitigation recommendations (retaining walls, deep-root terracing, stormwater cutoffs).

### 4. Explainable Landslide Hazard Prediction
- Physics-informed hazard formulation:
  $$P_{\text{landslide}} = \text{clip}\left(0.45 \cdot S_f + 0.35 \cdot R_f + 0.20 \cdot P_f, 0.02, 0.98\right)$$
  *(where $S_f$ is downhill shear stress, $R_f$ is root decay depletion, and $P_f$ is pore-water pressure).*
- Explains primary physical root causes and outputs bio-mitigation strategies (Vetiver grass stabilization, contour drainage).

### 5. Multi-Threat Risk Dashboard & Wildlife Corridors
- **Threat Matrices**: Real-time Fire Risk Index, Landslide Hazard, and Encroachment Vulnerability.
- **Species Migration Routing**: Least-cost path analysis for **Asian Elephants** (slope avoidance) and **Bengal Tigers** (canopy cover preference) with chokepoint breach detection.
- **Carbon Asset Economics**: IPCC 2019 allometric aboveground biomass calculations valued at $\$15/\text{ton } \text{CO}_2$.

### 6. Evolutionary GA Threshold Adaptation
- Genetic Algorithm dynamically adapts seasonal alert thresholds across Monsoon, Dry, and Retreat seasons, achieving **85.71% F1-score** and **96.88% accuracy**.

### 7. Cyber Security Hardening & Rate Limiting
- **SlowAPI Integration**: Protects compute-heavy endpoints (5 req/min on GA, 30 req/min on GEE).
- **Coordinate Boundary Sanitization**: Strict Pydantic validation preventing coordinate injection.
- **Security Headers**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │       React 18 + Leaflet GIS UI        │
                               │  - Interactive Satellite Heatmap        │
                               │  - Construction Suitability Auditor     │
                               │  - Multi-Threat Risk & Corridor Tabs    │
                               └────────────────────┬────────────────────┘
                                                    │ REST API (JSON)
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │           FastAPI Backend Engine        │
                               │  - SlowAPI Rate Limiter & Sanitizer     │
                               │  - In-Memory 8x8 Patch Grid Slicer      │
                               │  - Physics & Heuristic Inference Engine │
                               │  - Genetic Algorithm Adaptor            │
                               └───────┬─────────────────────────┬───────┘
                                       │                         │
                     Cloud Satellite APIs                        │ Embedded Storage
                                       ▼                         ▼
┌────────────────────────────────────────────────────────┐  ┌─────────────────────────┐
│              Google Earth Engine (GEE)                 │  │   SQLite Database       │
│  - Sentinel-2 MSI (Optical & Spectral Indices)         │  │   (evolve_records.db)   │
│  - USGS SRTM DEM (Terrain Slope & Elevation)           │  │  - Query History Vault  │
│  - CHIRPS Daily (90-Day Rainfall Saturation)           │  │  - Construction Permits │
│  - Hansen GFC (Canopy Cover & Historical Loss)         │  │  - GA Experiment Logs   │
└────────────────────────────────────────────────────────┘  └─────────────────────────┘
```

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description | Rate Limit |
|:---:|:---|:---|:---:|
| `POST` | `/api/dynamic-region` | Triggers live GEE multi-sensor ingestion for any bounding box & date range | 30 / min |
| `POST` | `/api/process-region` | Slices bounding box into 64 patches and computes baseline features | 30 / min |
| `POST` | `/api/inference/construction-suitability` | Evaluates mountain building safety score and civil recommendations | 20 / min |
| `GET` | `/api/landslide` | Returns physics-informed landslide hazard probabilities for all patches | 60 / min |
| `GET` | `/api/corridors` | Returns least-cost wildlife migration paths and chokepoints | 60 / min |
| `POST` | `/api/run-ga-adaptation` | Re-evolves seasonal detection thresholds using Genetic Algorithm | 5 / min |
| `GET` | `/api/current-region` | Retrieves active region telemetry, spatial bounds, and summary stats | 120 / min |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (Recommended: Python 3.12)
- Node.js 18+ and npm
- Google Earth Engine authenticated project (e.g. `forest-502505`)

### 1. Clone the Repository
```bash
git clone https://github.com/tejeshneelam/evolve-forest-degradation.git
cd evolve-forest-degradation
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
export PYTHONPATH=.
uvicorn dashboard.backend.main:app --reload --port 8000
```
*The FastAPI interactive Swagger docs will be live at `http://localhost:8000/docs`.*

### 3. Frontend Setup
```bash
# Open a new terminal window
cd dashboard/frontend

# Install dependencies
npm install

# Start React GIS dashboard
npm start
```
*The dashboard will automatically open at `http://localhost:3000`.*

---

## 📄 License & Academic Attribution
This project is developed for academic evaluation under **Amrita Vishwa Vidyapeetham, School of Computing**.  
Licensed under the [MIT License](LICENSE).
