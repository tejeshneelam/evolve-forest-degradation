import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def draw_system_architecture():
    # 16:9 Aspect Ratio, High Resolution
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    fig.patch.set_facecolor('#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title Header
    ax.text(8.0, 8.55, "EvOLve: End-to-End Application Architecture", 
            fontsize=22, fontweight='bold', color='#ffffff', ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 8.18, "Decoupled 4-Tier Architecture: Presentation · Security · AI Inference & Physics · Cloud Satellite Stream", 
            fontsize=12, color='#94a3b8', ha='center', va='center', fontfamily='sans-serif')

    def add_card(x, y, w, h, bg, border, title, items, subtitle=None, icon=None):
        # Draw background card
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.2",
                              facecolor=bg, edgecolor=border, linewidth=1.8, zorder=2)
        ax.add_patch(card)
        
        # Header text
        header_text = title
        ax.text(x + w/2, y + h - 0.32, header_text, fontsize=11, fontweight='bold', 
                color='#ffffff', ha='center', va='center', zorder=3, fontfamily='sans-serif')
        
        if subtitle:
            ax.text(x + w/2, y + h - 0.58, subtitle, fontsize=8.5, color='#cbd5e1', 
                    ha='center', va='center', zorder=3, fontfamily='sans-serif')
            start_y = y + h - 0.90
        else:
            start_y = y + h - 0.65

        # Item bullets
        for i, item in enumerate(items):
            item_y = start_y - (i * 0.38)
            ax.text(x + 0.25, item_y, f"• {item}", fontsize=8.5, color='#e2e8f0', 
                    va='center', zorder=3, fontfamily='sans-serif')

    # -------------------------------------------------------------
    # TIER 1: PRESENTATION TIER (TOP)
    # -------------------------------------------------------------
    tier1_bg = FancyBboxPatch((0.5, 5.25), 15.0, 2.55, boxstyle="round,pad=0.1,rounding_size=0.3",
                              facecolor='#131b2e', edgecolor='#3b82f6', linewidth=2.0, linestyle='--', zorder=1)
    ax.add_patch(tier1_bg)
    ax.text(0.85, 7.55, "TIER 1: PRESENTATION LAYER (React 18 + Leaflet GIS Single Page Application — Port 3000)", 
            fontsize=11, fontweight='bold', color='#60a5fa', va='center', fontfamily='sans-serif')

    # Card 1: Interactive GIS Map
    add_card(0.8, 5.45, 3.4, 1.85, '#1e293b', '#3b82f6', "Interactive Leaflet Map", 
             ["64-Patch Spatial Grid ($640m \\times 640m$)", "Real-time Layer Switching:", "  - Forest Health (NDVI Colors)", "  - Landslide Hazard (Shear risk)", "  - Building Suitability (Civil Permits)"],
             subtitle="Map Visualization Component", icon="🗺️")

    # Card 2: Query Controls
    add_card(4.4, 5.45, 3.4, 1.85, '#1e293b', '#3b82f6', "Region & Date Selector", 
             ["Presets: Wayanad, Silent Valley, Amazon", "Custom Lat/Lon Bounding Box Input", "Dynamic Date Range: 2018 to 2025", "Monthly NDVI Trajectory Graphs"],
             subtitle="Temporal Filter Controller", icon="⏱️")

    # Card 3: Construction Safety Modal
    add_card(8.0, 5.45, 3.4, 1.85, '#1e293b', '#10b981', "Construction Safety Auditor", 
             ["Calculates Suitability Score (0 - 100)", "Slope & Landslide Risk Gating", "Enforces 500m Sanctuary Setback", "Civil Engineering Bio-Mitigations"],
             subtitle="Engineering Compliance Modal", icon="🏗️")

    # Card 4: Environmental Risk & Corridors
    add_card(11.6, 5.45, 3.6, 1.85, '#1e293b', '#f59e0b', "Risk & Wildlife Dashboards", 
             ["Tri-Threat Matrix: Fire, Landslide, Encroach", "Dijkstra Least-Cost Migration Paths", "Species: Asian Elephant & Bengal Tiger", "IPCC Allometric Carbon Valuation ($11.8M)"],
             subtitle="Ecological Decision Tabs", icon="🐘")

    # -------------------------------------------------------------
    # TIER 2: SECURITY & MIDDLEWARE LAYER (MIDDLE-TOP)
    # -------------------------------------------------------------
    sec_bg = FancyBboxPatch((0.5, 4.25), 15.0, 0.75, boxstyle="round,pad=0.08,rounding_size=0.2",
                            facecolor='#1e1e38', edgecolor='#a855f7', linewidth=1.5, zorder=1)
    ax.add_patch(sec_bg)
    ax.text(8.0, 4.62, "TIER 2: API GATEWAY & SECURITY HARDENING (FastAPI Middleware)", 
            fontsize=11, fontweight='bold', color='#c084fc', ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 4.38, "SlowAPI Rate Limiter (5 req/min GA, 30 req/min GEE) · Pydantic Lat/Lon Sanitizer ([-90,90]) · HTTP Security Headers (DENY Clickjacking)", 
            fontsize=9.0, color='#e2e8f0', ha='center', va='center', fontfamily='sans-serif')

    # -------------------------------------------------------------
    # TIER 3: APPLICATION & INFERENCE ENGINE (MIDDLE-BOTTOM)
    # -------------------------------------------------------------
    tier3_bg = FancyBboxPatch((0.5, 1.95), 15.0, 2.05, boxstyle="round,pad=0.1,rounding_size=0.3",
                              facecolor='#131b2e', edgecolor='#10b981', linewidth=2.0, linestyle='--', zorder=1)
    ax.add_patch(tier3_bg)
    ax.text(0.85, 3.75, "TIER 3: APPLICATION & AI INFERENCE LAYER (FastAPI Async Engine — Python 3.12 — Port 8000)", 
            fontsize=11, fontweight='bold', color='#34d399', va='center', fontfamily='sans-serif')

    # Card 5: GEE Slicing Service
    add_card(0.8, 2.10, 3.4, 1.45, '#1e293b', '#10b981', "GEE Ingestion Service", 
             ["Cloud Handshake: ee.Initialize()", "In-Memory 8x8 Grid Slicing (<12s)", "Zero-disk tensor raster extraction", "Synthesizes 72-Month NDVI series"],
             icon="🛰️")

    # Card 6: Physics Hazard Engine
    add_card(4.4, 2.10, 3.4, 1.45, '#1e293b', '#10b981', "Physics Hazard Engine", 
             ["Shear Stress: 0.45 * SRTM Slope", "Root Decay: 0.35 * Hansen Cover Loss", "Pore Pressure: 0.20 * CHIRPS Rain", "Predicts Landslide Early Warning"],
             icon="⛰️")

    # Card 7: Genetic Algorithm Adaptor
    add_card(8.0, 2.10, 3.4, 1.45, '#1e293b', '#ec4899', "Evolutionary GA Optimizer", 
             ["Chromosome: [lr, drop, dry, mon, ret]", "Multi-objective Fitness function", "In-Memory Embedding Cache (<4 sec)", "Evolves dry=0.333, monsoon=0.554"],
             icon="🧬")

    # Card 8: Ecological Graph Engine
    add_card(11.6, 2.10, 3.6, 1.45, '#1e293b', '#10b981', "Ecological Graph Router", 
             ["64-Node Resistance Matrix", "Elephant: Slope avoidance (>15 deg)", "Tiger: High tree cover affinity (>65%)", "Chokepoint breach detection alerts"],
             icon="🐅")

    # -------------------------------------------------------------
    # TIER 4: SATELLITE CLOUD & LOCAL PERSISTENCE (BOTTOM)
    # -------------------------------------------------------------
    # GEE Cloud (Left)
    add_card(0.8, 0.25, 6.9, 1.45, '#1a2333', '#0284c7', "Google Earth Engine Satellite Cloud (Planetary API)", 
             ["Sentinel-2 L2A (10m MSI optical bands B2, B3, B4, B8, B11, B12, NDVI, EVI)",
              "USGS SRTM Digital Elevation Model (30m terrain elevation & slope gradient)",
              "CHIRPS Daily Precipitation (90-day antecedent rainfall soil water saturation load)",
              "Hansen Global Forest Change (Canopy cover density & historical loss tracking)"],
             subtitle="External Cloud Ingestion Stream", icon="🌍")

    # SQLite Database (Right)
    add_card(8.1, 0.25, 7.1, 1.45, '#1a2333', '#eab308', "Embedded Persistence: SQLite Database (evolve_records.db)", 
             ["query_history Table: Stores scanned BBox, start/end dates, mean NDVI, degraded fraction",
              "construction_permits Table: Stores patch ID, slope, landslide risk, building score & officer notes",
              "ga_experiment_logs Table: Checkpoints evolved seasonal thresholds, generations & fitness scores",
              "1-Click Historical Inspection Recall Vault via React drawer"],
             subtitle="Local ACID Relational Storage", icon="💾")

    # -------------------------------------------------------------
    # CONNECTING ARROWS & LABELS
    # -------------------------------------------------------------
    # Arrow 1: Presentation <-> Security
    ax.annotate("", xy=(8.0, 4.95), xytext=(8.0, 5.35),
                arrowprops=dict(arrowstyle="<->", color="#60a5fa", lw=2.5, mutation_scale=15))
    ax.text(8.3, 5.10, "HTTP / JSON REST Requests", fontsize=8.5, color='#93c5fd', fontweight='bold', fontfamily='sans-serif')

    # Arrow 2: Security <-> AI Engine
    ax.annotate("", xy=(8.0, 3.98), xytext=(8.0, 4.25),
                arrowprops=dict(arrowstyle="<->", color="#34d399", lw=2.5, mutation_scale=15))
    ax.text(8.3, 4.10, "Sanitized Request Dispatches", fontsize=8.5, color='#6ee7b7', fontweight='bold', fontfamily='sans-serif')

    # Arrow 3: GEE Service <-> Google Earth Engine
    ax.annotate("", xy=(4.2, 1.70), xytext=(4.2, 2.05),
                arrowprops=dict(arrowstyle="<->", color="#38bdf8", lw=2.5, mutation_scale=15))
    ax.text(4.4, 1.85, "ee.Initialize() & Multi-Spectral Tensor Slices", fontsize=8.5, color='#7dd3fc', fontweight='bold', fontfamily='sans-serif')

    # Arrow 4: Inference Engine <-> SQLite DB
    ax.annotate("", xy=(11.6, 1.70), xytext=(11.6, 2.05),
                arrowprops=dict(arrowstyle="<->", color="#facc15", lw=2.5, mutation_scale=15))
    ax.text(11.8, 1.85, "ACID Query Logs & Audit Permits", fontsize=8.5, color='#fde047', fontweight='bold', fontfamily='sans-serif')

    plt.tight_layout()
    plt.savefig('slides_assets/system_architecture.png', dpi=300, facecolor='#0b0f19', edgecolor='none')
    plt.close()
    print("✅ Created slides_assets/system_architecture.png successfully!")

def draw_data_flow_diagram():
    # 16:9 Aspect Ratio, High Resolution
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    fig.patch.set_facecolor('#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title Header
    ax.text(8.0, 8.55, "EvOLve: End-to-End Execution Data Flow Pipeline", 
            fontsize=22, fontweight='bold', color='#ffffff', ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 8.18, "From Satellite Raw Granules to Actionable Forest Disaster & Building Safety Audits in <12 Seconds", 
            fontsize=12, color='#94a3b8', ha='center', va='center', fontfamily='sans-serif')

    def add_step_card(x, y, w, h, step_num, title, details, color_theme):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.25",
                              facecolor='#1e293b', edgecolor=color_theme, linewidth=2.0, zorder=2)
        ax.add_patch(card)
        
        # Step badge
        badge = FancyBboxPatch((x + 0.2, y + h - 0.45), 1.2, 0.35, boxstyle="round,pad=0.04,rounding_size=0.1",
                               facecolor=color_theme, edgecolor='none', zorder=3)
        ax.add_patch(badge)
        ax.text(x + 0.8, y + h - 0.28, f"STEP {step_num}", fontsize=8.5, fontweight='bold', 
                color='#ffffff', ha='center', va='center', zorder=4, fontfamily='sans-serif')
        
        # Title
        ax.text(x + 1.55, y + h - 0.28, title, fontsize=11, fontweight='bold', 
                color='#ffffff', va='center', zorder=4, fontfamily='sans-serif')

        # Details
        for i, d in enumerate(details):
            ax.text(x + 0.3, y + h - 0.70 - (i * 0.35), f"• {d}", fontsize=8.5, 
                    color='#e2e8f0', va='center', zorder=3, fontfamily='sans-serif')

    # 6 Steps in 2 Rows of 3 Cards each for maximum clarity and zero crowding!
    # ROW 1 (Steps 1, 2, 3)
    step1_items = [
        "User selects region (e.g. Wayanad / Silent Valley)",
        "User selects historical dates (2018-01 to 2024-12)",
        "Leaflet GIS sets bounding box coordinates",
        "Triggers 'Run GEE Analysis' button"
    ]
    add_step_card(0.8, 4.4, 4.5, 3.2, "1", "User Query on UI", step1_items, "#3b82f6")

    step2_items = [
        "Coordinates validated: -90 <= lat <= 90",
        "SlowAPI checks rate limit (30 req/min)",
        "Pydantic models sanitize date regex",
        "Prevents SQL/Script injection attacks"
    ]
    add_step_card(5.75, 4.4, 4.5, 3.2, "2", "API Validation & Security", step2_items, "#a855f7")

    step3_items = [
        "FastAPI executes Google Earth Engine Python API",
        "Streams Sentinel-2 optical bands (10m resolution)",
        "Queries USGS SRTM DEM for slope gradient",
        "Pulls CHIRPS 90-day precipitation & Hansen cover"
    ]
    add_step_card(10.7, 4.4, 4.5, 3.2, "3", "GEE Cloud Ingestion", step3_items, "#0284c7")

    # Connect Row 1
    ax.annotate("", xy=(5.65, 6.0), xytext=(5.35, 6.0),
                arrowprops=dict(arrowstyle="->", color="#60a5fa", lw=3.0, mutation_scale=20))
    ax.annotate("", xy=(10.6, 6.0), xytext=(10.3, 6.0),
                arrowprops=dict(arrowstyle="->", color="#c084fc", lw=3.0, mutation_scale=20))

    # Turn arrow from Row 1 Step 3 to Row 2 Step 4
    ax.annotate("", xy=(13.0, 4.0), xytext=(13.0, 4.35),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=3.0, mutation_scale=20))

    # ROW 2 (Steps 4, 5, 6)
    step4_items = [
        "Bounding box partitioned into 8x8 spatial grid",
        "Creates 64 uniform patches (640m x 640m each)",
        "Executed 100% in RAM (zero disk I/O latency)",
        "Compiles 72-month NDVI trajectory series"
    ]
    add_step_card(10.7, 0.6, 4.5, 3.2, "4", "In-Memory Grid Slicing", step4_items, "#10b981")

    step5_items = [
        "Physics Landslide: 0.45*Slope + 0.35*Root + 0.20*Rain",
        "Mountain Suitability: 100 - Penalties (0 - 100 score)",
        "GA seasonal adaptation: dry=0.333, monsoon=0.554",
        "Dijkstra solves Elephant & Tiger migration corridors"
    ]
    add_step_card(5.75, 0.6, 4.5, 3.2, "5", "Multi-Engine AI Inference", step5_items, "#f59e0b")

    step6_items = [
        "Interactive 64-patch color map rendered in Leaflet",
        "Permit status: PERMITTED / CONDITIONAL / PROHIBITED",
        "Civil engineering diagnostic modal with mitigations",
        "Query parameters persisted to SQLite Database"
    ]
    add_step_card(0.8, 0.6, 4.5, 3.2, "6", "Actionable Deliverables", step6_items, "#ec4899")

    # Connect Row 2 (Right to Left)
    ax.annotate("", xy=(10.3, 2.2), xytext=(10.65, 2.2),
                arrowprops=dict(arrowstyle="->", color="#34d399", lw=3.0, mutation_scale=20))
    ax.annotate("", xy=(5.35, 2.2), xytext=(5.7, 2.2),
                arrowprops=dict(arrowstyle="->", color="#fbbf24", lw=3.0, mutation_scale=20))

    plt.tight_layout()
    plt.savefig('slides_assets/data_flow.png', dpi=300, facecolor='#0b0f19', edgecolor='none')
    plt.close()
    print("✅ Created slides_assets/data_flow.png successfully!")

if __name__ == "__main__":
    draw_system_architecture()
    draw_data_flow_diagram()
