"""
EvOLve Version 2.0 — Dynamic Region & Landslide Diagnostics Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dashboard.backend.services.gee_service import fetch_dynamic_region
from dashboard.backend.services.inference_service import analyze_dynamic_region

router = APIRouter()

# Global in-memory cache for the most recently processed dynamic region
LATEST_DYNAMIC_ANALYSIS = None


class RegionRequest(BaseModel):
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    region_name: Optional[str] = "Selected Region"
    num_months: Optional[int] = 24


@router.post("/process-region")
def process_region(req: RegionRequest):
    """
    On-the-fly endpoint triggered when a user selects/draws a region on the map.
    Queries Google Earth Engine, runs EvOLve inference, and computes all 6 features dynamically.
    """
    global LATEST_DYNAMIC_ANALYSIS
    if len(req.bbox) != 4:
        raise HTTPException(400, "Invalid bounding box. Must be [min_lon, min_lat, max_lon, max_lat]")

    min_lon, min_lat, max_lon, max_lat = req.bbox
    
    # Validation: Ensure reasonable box size (max 0.25 x 0.25 degrees ~ 25km x 25km)
    if abs(max_lat - min_lat) > 0.35 or abs(max_lon - min_lon) > 0.35:
        raise HTTPException(400, "Selected region is too large for real-time analysis. Please choose an area under 25km x 25km.")

    try:
        print(f"🛰️ Processing dynamic region: {req.region_name} | Bounds: {req.bbox}")
        gee_data = fetch_dynamic_region(min_lon, min_lat, max_lon, max_lat, num_months=req.num_months)
        analysis = analyze_dynamic_region(gee_data)
        analysis['region_name'] = req.region_name
        LATEST_DYNAMIC_ANALYSIS = analysis
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
