"""
EvOLve Version 2.0 — Dynamic Region & Landslide Diagnostics Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dashboard.backend.services.gee_service import fetch_dynamic_region
from dashboard.backend.services.inference_service import analyze_dynamic_region
from dashboard.backend.database import insert_query_history

router = APIRouter()

# Global in-memory cache for the most recently processed dynamic region
LATEST_DYNAMIC_ANALYSIS = None
# Cache map of processed regions to make reloads instantaneous
REGION_CACHE = {}


class RegionRequest(BaseModel):
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    region_name: Optional[str] = "Selected Region"
    num_months: Optional[int] = 24
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.post("/process-region")
def process_region(req: RegionRequest):
    """
    On-the-fly endpoint triggered when a user selects/draws a region on the map.
    Queries Google Earth Engine, runs EvOLve inference, and computes all features dynamically.
    """
    global LATEST_DYNAMIC_ANALYSIS, REGION_CACHE
    if len(req.bbox) != 4:
        raise HTTPException(400, "Invalid bounding box. Must be [min_lon, min_lat, max_lon, max_lat]")

    min_lon, min_lat, max_lon, max_lat = req.bbox
    
    # Validation: Ensure reasonable box size (max 0.35 x 0.35 degrees ~ 35km x 35km)
    if abs(max_lat - min_lat) > 0.35 or abs(max_lon - min_lon) > 0.35:
        raise HTTPException(400, "Selected region is too large for real-time analysis. Please choose an area under 35km x 35km.")

    cache_key = f"{req.region_name}_{min_lon:.3f}_{min_lat:.3f}_{max_lon:.3f}_{max_lat:.3f}_{req.start_date}_{req.end_date}"
    if cache_key in REGION_CACHE:
        print(f"⚡ Instant Cache Hit for: {req.region_name}")
        LATEST_DYNAMIC_ANALYSIS = REGION_CACHE[cache_key]
        return LATEST_DYNAMIC_ANALYSIS

    try:
        print(f"🛰️ Processing dynamic region: {req.region_name} | Bounds: {req.bbox} | Dates: {req.start_date} to {req.end_date}")
        gee_data = fetch_dynamic_region(
            min_lon, min_lat, max_lon, max_lat,
            num_months=req.num_months,
            start_date=req.start_date,
            end_date=req.end_date
        )
        analysis = analyze_dynamic_region(gee_data)
        analysis['region_name'] = req.region_name
        analysis['start_date'] = gee_data.get('start_date')
        analysis['end_date'] = gee_data.get('end_date')
        LATEST_DYNAMIC_ANALYSIS = analysis
        REGION_CACHE[cache_key] = analysis

        # Auto-log query history into SQLite vault
        try:
            mean_ndvi = analysis.get('stats', {}).get('mean_ndvi', 0.65)
            deg_pct = analysis.get('stats', {}).get('degradation_pct', 12.0)
            insert_query_history(
                region_name=req.region_name or "Selected Region",
                start_date=gee_data.get('start_date') or "2024-01-01",
                end_date=gee_data.get('end_date') or "2024-12-31",
                mean_ndvi=round(float(mean_ndvi), 3),
                degraded_fraction=round(float(deg_pct) / 100.0, 3),
                officer_id="OFFICER-GEE"
            )
        except Exception as db_err:
            print(f"⚠️ Auto-log to SQLite failed: {db_err}")

        return analysis
    except Exception as e:
        print(f"❌ Error during dynamic processing: {e}")
        raise HTTPException(500, f"Error processing satellite region: {str(e)}")


@router.get("/current-region")
def get_current_region():
    """Returns the currently active region analysis, or null if none processed."""
    return LATEST_DYNAMIC_ANALYSIS


@router.get("/landslide-diagnostic/{patch_id}")
def get_landslide_diagnostic(patch_id: int):
    """
    Dedicated diagnostic report for landslide probability, exact physical causes,
    and recommended engineering mitigations for a specific patch.
    """
    if not LATEST_DYNAMIC_ANALYSIS:
        raise HTTPException(404, "No active region loaded. Please select a region first.")

    patch = next((p for p in LATEST_DYNAMIC_ANALYSIS['patches'] if p['patch_id'] == patch_id), None)
    if not patch:
        raise HTTPException(404, f"Patch {patch_id} not found in active region.")

    return {
        'patch_id': patch_id,
        'grid_row': patch['grid_row'],
        'grid_col': patch['grid_col'],
        'center': patch['center'],
        'diagnostic': patch['landslide']
    }


@router.get("/construction-diagnostic/{patch_id}")
def get_construction_diagnostic(patch_id: int):
    """
    Dedicated geo-safety and terrain construction suitability diagnostic report for a specific patch.
    """
    if not LATEST_DYNAMIC_ANALYSIS:
        raise HTTPException(404, "No active region loaded. Please select a region first.")

    patch = next((p for p in LATEST_DYNAMIC_ANALYSIS['patches'] if p['patch_id'] == patch_id), None)
    if not patch:
        raise HTTPException(404, f"Patch {patch_id} not found in active region.")

    return {
        'patch_id': patch_id,
        'grid_row': patch['grid_row'],
        'grid_col': patch['grid_col'],
        'center': patch['center'],
        'bounds': patch['bounds'],
        'slope_deg': patch['slope_deg'],
        'construction': patch.get('construction_suitability', {})
    }
