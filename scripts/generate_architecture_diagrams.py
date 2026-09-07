import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

# Primary Color Palette matching Amrita PPT Template
COLOR_BG = '#FFFFFF'
COLOR_MAROON = '#A4123F'
COLOR_DARK_SLATE = '#1E293B'
COLOR_MUTED_SLATE = '#475569'
COLOR_LIGHT_BG = '#F8FAFC'
COLOR_CARD_BG = '#FFFFFF'
COLOR_BORDER = '#CBD5E1'
COLOR_ACCENT_BG = '#FFF5F7'

def draw_system_architecture():
    # 16:7.5 Aspect Ratio - Perfectly proportioned for Beamer slides and LaTeX report
    fig, ax = plt.subplots(figsize=(16, 7.5), dpi=300)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Header Title
    ax.text(8.0, 7.15, "EvOLve: Decoupled 4-Tier System Architecture", 
            fontsize=17, fontweight='bold', color=COLOR_MAROON, ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 6.85, "Presentation (React 18) · Security Gateway (FastAPI) · AI & Scientific Inference · Satellite Cloud & SQLite", 
            fontsize=10.5, color=COLOR_MUTED_SLATE, ha='center', va='center', fontfamily='sans-serif')

    def add_card(x, y, w, h, title, items, is_accent=False):
        border_col = COLOR_MAROON if is_accent else COLOR_BORDER
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.15",
                              facecolor=COLOR_CARD_BG, edgecolor=border_col, linewidth=1.5, zorder=2)
        ax.add_patch(card)
        
        # Title banner inside card
        banner_h = 0.32
        banner = FancyBboxPatch((x, y + h - banner_h), w, banner_h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                facecolor=COLOR_MAROON if is_accent else '#F1F5F9', edgecolor='none', zorder=3)
        ax.add_patch(banner)
        ax.text(x + w/2, y + h - banner_h/2, title, fontsize=9.5, fontweight='bold', 
                color='#FFFFFF' if is_accent else COLOR_DARK_SLATE, ha='center', va='center', zorder=4, fontfamily='sans-serif')
        
        # Item bullets
        start_y = y + h - banner_h - 0.22
        for i, item in enumerate(items):
            item_y = start_y - (i * 0.25)
            ax.text(x + 0.18, item_y, f"• {item}", fontsize=8.2, color=COLOR_DARK_SLATE, 
                    va='center', zorder=4, fontfamily='sans-serif')

    # -------------------------------------------------------------
    # TIER 1: PRESENTATION LAYER (y=4.80 to 6.60)
    # -------------------------------------------------------------
    t1_bg = FancyBboxPatch((0.5, 4.80), 15.0, 1.85, boxstyle="round,pad=0.08,rounding_size=0.2",
                           facecolor=COLOR_LIGHT_BG, edgecolor=COLOR_BORDER, linewidth=1.5, zorder=1)
    ax.add_patch(t1_bg)
    ax.text(0.8, 6.45, "TIER 1: PRESENTATION LAYER (React 18 + Leaflet GIS Single Page Application — Port 3000)", 
            fontsize=10.5, fontweight='bold', color=COLOR_MAROON, va='center', fontfamily='sans-serif')

    add_card(0.8, 4.92, 3.35, 1.35, "Interactive GIS Map", 
             ["64-Patch Raster Grid ($640m \\times 640m$)", "Dynamic Layer Switcher", "Forest Health (NDVI Vigor)", "Landslide Hazard & Suitability"])

    add_card(4.45, 4.92, 3.35, 1.35, "Region & Date Controls", 
             ["Presets: Wayanad, Silent Valley, Amazon", "Custom Lat/Lon Bounding Box Input", "Temporal Range: 2018 to 2025", "Monthly NDVI Trajectory Graphs"])

    add_card(8.1, 4.92, 3.35, 1.35, "Construction Safety Auditor", 
             ["Calculates Suitability Score (0-100)", "Slope & Landslide Risk Gating", "Enforces 500m Sanctuary Setback", "Civil Engineering Bio-Mitigations"])

    add_card(11.75, 4.92, 3.5, 1.35, "Risk & Wildlife Dashboards", 
             ["Fire Fuel Moisture Danger Table", "Dijkstra Least-Cost Migration Paths", "Asian Elephant & Bengal Tiger", "IPCC Carbon Stock Valuation ($11.8M)"])

    # -------------------------------------------------------------
    # TIER 2: SECURITY & MIDDLEWARE LAYER (y=3.85 to 4.50)
    # -------------------------------------------------------------
    sec_bg = FancyBboxPatch((0.5, 3.85), 15.0, 0.65, boxstyle="round,pad=0.06,rounding_size=0.15",
                            facecolor=COLOR_ACCENT_BG, edgecolor=COLOR_MAROON, linewidth=1.5, zorder=1)
    ax.add_patch(sec_bg)
    ax.text(8.0, 4.32, "TIER 2: API GATEWAY & SECURITY HARDENING (FastAPI Middleware — Port 8000)", 
            fontsize=10.5, fontweight='bold', color=COLOR_MAROON, ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 4.05, "SlowAPI Rate Limiting (5 req/min GA, 30 req/min GEE) · Pydantic Lat/Lon Sanitizer ([-90, 90]) · HTTP Security Headers (DENY Clickjacking)", 
            fontsize=8.8, color=COLOR_DARK_SLATE, ha='center', va='center', fontfamily='sans-serif')

    # Arrow T1 <-> T2
    ax.annotate("", xy=(8.0, 4.80), xytext=(8.0, 4.50),
                arrowprops=dict(arrowstyle="<->", color=COLOR_MAROON, lw=2.0, mutation_scale=14))

    # -------------------------------------------------------------
    # TIER 3: APPLICATION & INFERENCE ENGINE (y=1.90 to 3.55)
    # -------------------------------------------------------------
    t3_bg = FancyBboxPatch((0.5, 1.90), 15.0, 1.65, boxstyle="round,pad=0.08,rounding_size=0.2",
                           facecolor=COLOR_LIGHT_BG, edgecolor=COLOR_BORDER, linewidth=1.5, zorder=1)
    ax.add_patch(t3_bg)
    ax.text(0.8, 3.35, "TIER 3: APPLICATION & SCIENTIFIC INFERENCE ENGINES (Python 3.12 / PyTorch / NumPy / SciPy)", 
            fontsize=10.5, fontweight='bold', color=COLOR_MAROON, va='center', fontfamily='sans-serif')

    add_card(0.8, 2.02, 3.35, 1.15, "In-Memory GEE Slicing", 
             ["Zero-disk tensor raster in RAM", "In-memory 8x8 tiling (<12s)", "Extracts 72-Month NDVI history"], is_accent=True)

    add_card(4.45, 2.02, 3.35, 1.15, "Physics Landslide Engine", 
             ["Shear Stress: 0.45 * Slope Angle", "Root Tensile Loss: 0.35 * Cover", "Pore Pressure: 0.20 * CHIRPS Rain"])

    add_card(8.1, 2.02, 3.35, 1.15, "Fire Fuel Moisture Engine", 
             ["Sentinel-2 SWIR1/2 Biomass", "NDWI Moisture Deficit Index", "Peak Dry Season 1.5x Multiplier"])

    add_card(11.75, 2.02, 3.5, 1.15, "Adaptive GA Optimizer", 
             ["5-gene continuous chromosome", "Pareto tournament selection", "Runs in <4s with embedding cache"])

    # Arrow T2 <-> T3
    ax.annotate("", xy=(8.0, 3.85), xytext=(8.0, 3.55),
                arrowprops=dict(arrowstyle="<->", color=COLOR_MAROON, lw=2.0, mutation_scale=14))

    # -------------------------------------------------------------
    # TIER 4: CLOUD SATELLITE STREAM & PERSISTENCE (y=0.45 to 1.60)
    # -------------------------------------------------------------
    t4_bg = FancyBboxPatch((0.5, 0.45), 15.0, 1.15, boxstyle="round,pad=0.08,rounding_size=0.2",
                           facecolor=COLOR_LIGHT_BG, edgecolor=COLOR_BORDER, linewidth=1.5, zorder=1)
    ax.add_patch(t4_bg)
    ax.text(0.8, 1.42, "TIER 4: SATELLITE STREAMING & RELATIONAL PERSISTENCE LAYER", 
            fontsize=10.5, fontweight='bold', color=COLOR_MAROON, va='center', fontfamily='sans-serif')

    add_card(0.8, 0.55, 7.0, 0.75, "Google Earth Engine Planetary Platform (forest-502505)", 
             ["Sentinel-2 L2A Multi-Spectral (10m) · USGS SRTM DEM (30m) · CHIRPS Precipitation · Hansen Global Forest Change"])

    add_card(8.1, 0.55, 7.15, 0.75, "Embedded SQLite Database Vault (evolve_records.db)", 
             ["query_history (coordinates, dates, NDVI) · construction_permits (audit decisions) · ga_experiment_logs (Pareto metrics)"])

    # Arrow T3 <-> T4
    ax.annotate("", xy=(4.3, 1.90), xytext=(4.3, 1.60),
                arrowprops=dict(arrowstyle="<->", color=COLOR_MAROON, lw=2.0, mutation_scale=14))
    ax.annotate("", xy=(11.7, 1.90), xytext=(11.7, 1.60),
                arrowprops=dict(arrowstyle="<->", color=COLOR_MAROON, lw=2.0, mutation_scale=14))

    plt.tight_layout()
    plt.savefig('slides_assets/system_architecture.png', dpi=300, facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    print("✅ Successfully generated slides_assets/system_architecture.png (Clean White & Maroon)!")

def draw_data_flow_diagram():
    # 16:7.5 Aspect Ratio - Clean, Spacious, Zero Overlap
    fig, ax = plt.subplots(figsize=(16, 7.5), dpi=300)
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Header Title
    ax.text(8.0, 7.15, "EvOLve: End-to-End Execution Data Flow Pipeline", 
            fontsize=17, fontweight='bold', color=COLOR_MAROON, ha='center', va='center', fontfamily='sans-serif')
    ax.text(8.0, 6.85, "Execution Lifecycle: From Planetary Satellite Feeds to Actionable Disaster Audits in <12 Seconds", 
            fontsize=10.5, color=COLOR_MUTED_SLATE, ha='center', va='center', fontfamily='sans-serif')

    def add_step_card(x, y, w, h, step_num, title, details):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.2",
                              facecolor=COLOR_CARD_BG, edgecolor=COLOR_MAROON, linewidth=1.8, zorder=2)
        ax.add_patch(card)
        
        # Step badge (Maroon pill)
        badge = FancyBboxPatch((x + 0.25, y + h - 0.42), 1.15, 0.32, boxstyle="round,pad=0.03,rounding_size=0.1",
                               facecolor=COLOR_MAROON, edgecolor='none', zorder=3)
        ax.add_patch(badge)
        ax.text(x + 0.825, y + h - 0.26, f"STEP {step_num}", fontsize=8.8, fontweight='bold', 
                color='#FFFFFF', ha='center', va='center', zorder=4, fontfamily='sans-serif')
        
        # Step Title
        ax.text(x + 1.55, y + h - 0.26, title, fontsize=10.5, fontweight='bold', 
                color=COLOR_DARK_SLATE, va='center', zorder=4, fontfamily='sans-serif')
        
        # Divider line
        ax.plot([x + 0.2, x + w - 0.2], [y + h - 0.52, y + h - 0.52], color=COLOR_BORDER, lw=1.0, zorder=3)

        # Bullet details
        start_y = y + h - 0.78
        for i, d in enumerate(details):
            ax.text(x + 0.25, start_y - (i * 0.34), f"• {d}", fontsize=8.6, 
                    color=COLOR_DARK_SLATE, va='center', zorder=3, fontfamily='sans-serif')

    # ROW 1 (Steps 1, 2, 3: Left to Right)
    step1_items = [
        "User selects region preset or custom bounding box",
        "Sets dynamic time window (2018-01 to 2024-12)",
        "Leaflet GIS map validates bounding box coordinates",
        "Dispatches async query to FastAPI backend"
    ]
    add_step_card(0.6, 3.65, 4.6, 2.7, "1", "User Query on Leaflet UI", step1_items)

    step2_items = [
        "Pydantic validates bounds: -90 <= lat <= 90",
        "SlowAPI checks rate limits (30 req/min GEE)",
        "Sanitizes ISO date ranges against malformed regex",
        "Enforces HTTP security headers against injection"
    ]
    add_step_card(5.7, 3.65, 4.6, 2.7, "2", "API Validation & Security", step2_items)

    step3_items = [
        "FastAPI executes Google Earth Engine Python API",
        "Streams Sentinel-2 L2A optical granules (10m)",
        "Queries USGS SRTM DEM for slope gradient",
        "Pulls CHIRPS 90-day precipitation & Hansen canopy"
    ]
    add_step_card(10.8, 3.65, 4.6, 2.7, "3", "GEE Cloud Ingestion", step3_items)

    # Connecting arrows Row 1
    ax.annotate("", xy=(5.6, 5.0), xytext=(5.3, 5.0),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAROON, lw=2.5, mutation_scale=16))
    ax.annotate("", xy=(10.7, 5.0), xytext=(10.4, 5.0),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAROON, lw=2.5, mutation_scale=16))

    # Connecting arrow from Row 1 to Row 2
    ax.annotate("", xy=(13.1, 3.25), xytext=(13.1, 3.55),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAROON, lw=2.5, mutation_scale=16))

    # ROW 2 (Steps 4, 5, 6: Right to Left)
    step4_items = [
        "Bounding box partitioned into 8x8 spatial grid",
        "Creates 64 uniform patches (640m x 640m each)",
        "Executed 100% in RAM (zero disk I/O latency)",
        "Compiles 72-month NDVI trajectory series"
    ]
    add_step_card(10.8, 0.45, 4.6, 2.7, "4", "In-Memory Grid Slicing", step4_items)

    step5_items = [
        "Landslide Hazard: 0.45*Slope + 0.35*Root + 0.20*Rain",
        "Fire Fuel Flammability: SWIR1/2 + NDWI moisture deficit",
        "Mountain Suitability: 100 - Penalties (0 - 100 score)",
        "Dijkstra solves Elephant & Tiger migration corridors"
    ]
    add_step_card(5.7, 0.45, 4.6, 2.7, "5", "Multi-Engine AI Inference", step5_items)

    step6_items = [
        "Leaflet GIS displays 64 color-coded spatial patches",
        "Permit Status: PERMITTED / CONDITIONAL / PROHIBITED",
        "Explainable modal prescribes Vetiver / drainage orders",
        "Audit parameters persisted to SQLite Database"
    ]
    add_step_card(0.6, 0.45, 4.6, 2.7, "6", "Actionable Deliverables", step6_items)

    # Connecting arrows Row 2
    ax.annotate("", xy=(10.4, 1.8), xytext=(10.7, 1.8),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAROON, lw=2.5, mutation_scale=16))
    ax.annotate("", xy=(5.3, 1.8), xytext=(5.6, 1.8),
                arrowprops=dict(arrowstyle="->", color=COLOR_MAROON, lw=2.5, mutation_scale=16))

    plt.tight_layout()
    plt.savefig('slides_assets/data_flow.png', dpi=300, facecolor=COLOR_BG, edgecolor='none')
    plt.close()
    print("✅ Successfully generated slides_assets/data_flow.png (Clean White & Maroon)!")

if __name__ == '__main__':
    draw_system_architecture()
    draw_data_flow_diagram()
