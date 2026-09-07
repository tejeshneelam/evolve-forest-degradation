# 🏛️ EvOLve — System Architecture & Workflow Specification
### *Technical Design Document for Panel Review 1 (Application Project — Type 2)*

---

## 1. Application Overview & Scope
**EvOLve** is a distributed geospatial intelligence platform combining real-time planetary satellite data streams, machine learning inference, and heuristic optimization for forest conservation and disaster mitigation.

The application architecture is structured into a **three-tier decoupled design**:
1. **Presentation Layer**: React 18 single-page GIS dashboard using Leaflet, Chart.js, and Lucide icons.
2. **Application & Processing Layer**: FastAPI asynchronous REST services coordinating Earth Engine ingestion, raster slicing, inference pipelines, and optimization algorithms.
3. **Data & Persistence Layer**: Google Earth Engine cloud repositories for satellite raster data and embedded SQLite (`evolve_records.db`) for local query and permit audit logs.

---

## 2. End-to-End System Block Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PRESENTATION TIER                                    │
│  React 18 + Leaflet GIS Client (Single Page Application - Port 3000)                   │
│                                                                                        │
│  ┌───────────────────────┐  ┌────────────────────────┐  ┌───────────────────────────┐  │
│  │ Global Region & Date  │  │ Interactive Leaflet Map│  │ Construction Suitability  │  │
│  │ Range Filter Controls │  │ (Forest / Hazard / Buil│  │ Diagnostic Audit Modal    │  │
│  └───────────┬───────────┘  └───────────┬────────────┘  └─────────────┬─────────────┘  │
│              │                          │                             │                │
│  ┌───────────┴───────────┐  ┌───────────┴────────────┐  ┌─────────────┴─────────────┐  │
│  │ Multi-Threat Risk     │  │ Wildlife Migration     │  │ GA Real-Time Adaptation   │  │
│  │ Dashboard & Fuel Table│  │ Corridor Viewer        │  │ Convergence Animator      │  │
│  └───────────────────────┘  └────────────────────────┘  └───────────────────────────┘  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON (Axios Client)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION & INFERENCE TIER                              │
│  FastAPI Asynchronous Engine (Python 3.12 - Port 8000)                                 │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Middleware & Security Layer: SlowAPI Rate Limiter, Pydantic Coordinate Sanitizer │  │
│  └──────────────────────────────────────────┬───────────────────────────────────────┘  │
│                                             │                                          │
│  ┌───────────────────────────┐  ┌───────────┴────────────────┐  ┌────────────────────┐ │
│  │ GEE Ingestion Service     │  │ Inference Engine           │  │ Optimization Engine│ │
│  │ (gee_service.py)          │  │ (inference_service.py)     │  │ (ga_optimizer.py)  │ │
│  │ - Multi-sensor fetching   │  │ - Landslide Hazard Physics │  │ - Multi-objective  │ │
│  │ - In-memory grid slicing  │  │ - Construction Suitability │  │   fitness formula  │ │
│  │ - Trajectory synthesizer  │  │ - Corridor Least-Cost Path │  │ - Chromosome evolution│
│  └─────────────┬─────────────┘  └───────────┬────────────────┘  └────────────┬───────┘ │
└────────────────┼────────────────────────────┼────────────────────────────────┼─────────┘
                 │                            │                                │
                 ▼                            │                                ▼
┌──────────────────────────────────────┐      │                 ┌────────────────────────┐
│             EXTERNAL TIER            │      │                 │    PERSISTENCE TIER    │
│  Google Earth Engine (GEE) REST API  │      │                 │  SQLite (evolve_record)│
│  - Sentinel-2 Level-2A (Multi-spectr)│      │                 │                        │
│  - USGS SRTM DEM 30m (Topography)    │◄─────┘                 │  - query_history       │
│  - CHIRPS Daily (Antecedent Rainfall)│                        │  - construction_permits│
│  - Hansen GFC (Tree Cover & Deforest)│                        │  - ga_experiment_logs  │
└──────────────────────────────────────┘                        └────────────────────────┘
```

---

## 3. Data Flow & Sequence Diagram (Dynamic Region Query)

The sequence diagram below illustrates the exact control flow when a user selects a target forest region and custom date range on the dashboard:

```
User (Browser)          React Frontend           FastAPI Backend           Google Earth Engine API
      │                       │                         │                             │
      │── 1. Select Region ──▶│                         │                             │
      │   & Date Range        │                         │                             │
      │                       │                         │                             │
      │── 2. Click "Run" ────▶│── 3. POST /dynamic-region ──▶                         │
      │                       │   (coords, dates)       │                             │
      │                       │                         │── 4. Coordinate Sanitizer ──│
      │                       │                         │   (Validate [-90,90])       │
      │                       │                         │                             │
      │                       │                         │── 5. ee.Initialize() ──────▶│
      │                       │                         │── 6. Query S2, DEM, CHIRPS ─▶│
      │                       │                         │                             │
      │                       │                         │◀─ 7. Raw Geospatial Tensors ─│
      │                       │                         │                             │
      │                       │                         │── 8. 8x8 Spatial Grid Slicing
      │                       │                         │   (In-memory, 64 patches)   │
      │                       │                         │                             │
      │                       │                         │── 9. Compute Landslide &    │
      │                       │                         │   Construction Suitability  │
      │                       │                         │                             │
      │                       │◀─ 10. Unified JSON ─────│                             │
      │                       │   (64 patch objects)    │                             │
      │                       │                         │                             │
      │◀─ 11. Render Map ─────│                         │                             │
      │   & Heatmap Tiles     │                         │                             │
```

---

## 4. Database Schema (SQLite: `evolve_records.db`)

To ensure persistence of queries, decisions, and audit history, EvOLve employs an embedded SQLite database (`evolve_records.db`):

### Table: `query_history`
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique scan identifier |
| `region_name` | TEXT | NOT NULL | User-selected or custom region name |
| `start_date` | TEXT | NOT NULL | Analysis start month (`YYYY-MM`) |
| `end_date` | TEXT | NOT NULL | Analysis end month (`YYYY-MM`) |
| `min_lat` | REAL | NOT NULL | Bounding box minimum latitude |
| `min_lon` | REAL | NOT NULL | Bounding box minimum longitude |
| `max_lat` | REAL | NOT NULL | Bounding box maximum latitude |
| `max_lon` | REAL | NOT NULL | Bounding box maximum longitude |
| `mean_ndvi` | REAL | NOT NULL | Regional mean vegetation index |
| `degraded_fraction`| REAL | NOT NULL | Fraction of 64 patches under alert |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Query execution timestamp |

### Table: `construction_permits`
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique permit record identifier |
| `patch_id` | INTEGER | NOT NULL | Evaluated spatial grid patch index ($0 - 63$) |
| `region_name` | TEXT | NOT NULL | Name of forest reserve |
| `slope_deg` | REAL | NOT NULL | Hillside incline angle |
| `elevation_m` | REAL | NOT NULL | Surface height above sea level |
| `landslide_prob` | REAL | NOT NULL | Physics-derived landslide hazard |
| `suitability_score`| REAL | NOT NULL | Composite building safety index ($0 - 100$) |
| `decision` | TEXT | NOT NULL | `PERMITTED` / `CONDITIONAL` / `PROHIBITED` |
| `reviewer_notes` | TEXT | DEFAULT NULL | Civil engineer comments & conditions |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Review timestamp |

### Table: `ga_experiment_logs`
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique optimization experiment ID |
| `generations` | INTEGER | NOT NULL | Number of evolved generations |
| `population_size`| INTEGER | NOT NULL | Chromosomes evaluated per generation |
| `best_fitness` | REAL | NOT NULL | Peak multi-objective score achieved |
| `dry_thresh` | REAL | NOT NULL | Evolved dry-season NDVI threshold |
| `monsoon_thresh`| REAL | NOT NULL | Evolved monsoon-season NDVI threshold |
| `runtime_sec` | REAL | NOT NULL | Execution latency in seconds |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Run timestamp |

---

## 5. Technology Stack & Component Justification

| Layer | Component | Selected Technology | Technical Justification |
|---|---|---|---|
| **Frontend** | Framework | React 18.3 | Virtual DOM ensures fast re-rendering of 64 interactive spatial polygons without UI lockup. |
| **Frontend** | GIS Mapping | Leaflet + React-Leaflet | Open-source, lightweight, native GeoJSON/TileLayer support, zero vendor lock-in. |
| **Frontend** | Charts | Chart.js + Recharts | Responsive temporal time-series plotting of 72 monthly NDVI curves. |
| **Backend** | REST Server | FastAPI (Python 3.12) | Asynchronous non-blocking architecture, native OpenAPI documentation, standard typing via Pydantic. |
| **Backend** | Rate Limiter | SlowAPI | Protects downstream Earth Engine API quota from denial-of-service or burst attacks. |
| **Geospatial** | Satellite Engine | Google Earth Engine Python API | Cloud-native multi-petabyte raster access; avoids downloading gigabytes of raw Sentinel-2 granules locally. |
| **Persistence**| Database | SQLite 3 | Embedded zero-configuration ACID compliance; single-file storage easily backed up or deployed. |

---

## 6. Deployment Strategy

### Local Development / Panel Demonstration
- **Backend**: Managed via Python virtual environment:
  ```bash
  uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Frontend**: Served via Webpack dev server:
  ```bash
  npm start --prefix dashboard/frontend
  ```

### Production Cloud Deployment Plan (Phase 2 Target)
- **Containerization**: Multi-stage Docker container (`Dockerfile`) bundling FastAPI with Nginx serving static React build artifacts.
- **Hosting**: Cloud VM (e.g. AWS EC2 t3.medium or Google Cloud Run) with environment-injected GEE Service Account credentials (`GOOGLE_APPLICATION_CREDENTIALS`).
