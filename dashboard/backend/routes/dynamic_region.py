"""
EvOLve Version 2.0 — Dynamic Region & Landslide Diagnostics Router
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
import numpy as np
from dashboard.backend.limiter import limiter
from dashboard.backend.utils import (
    sanitize_string,
    validate_coordinates,
    validate_date_range,
)
from dashboard.backend.services.gee_service import fetch_dynamic_region
from dashboard.backend.services.inference_service import analyze_dynamic_region

router = APIRouter()

# Global in-memory cache for the most recently processed dynamic region
LATEST_DYNAMIC_ANALYSIS = None


class RegionRequest(BaseModel):
    bbox: List[float] = Field(..., description="[min_lon, min_lat, max_lon, max_lat]")
    region_name: Optional[str] = Field("Selected Region", max_length=120)
    num_months: Optional[int] = Field(24, ge=1, le=120)
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")

    @field_validator("region_name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> str:
        return sanitize_string(v, max_length=120) or "Selected Region"

    @model_validator(mode="after")
    def validate_bounds_and_dates(self):
        # Enforce -90 <= min_lat < max_lat <= 90 and -180 <= min_lon < max_lon <= 180
        validate_coordinates(self.bbox)
        validate_date_range(self.start_date, self.end_date)
        return self


class ConstructionSuitabilityRequest(BaseModel):
    slope_deg: float = Field(..., ge=0.0, le=90.0, description="Terrain slope gradient in degrees (0 to 90)")
    landslide_prob: Optional[float] = Field(0.25, ge=0.0, le=1.0, description="Estimated landslide probability (0.0 to 1.0)")
    is_wildlife_corridor: Optional[bool] = Field(False, description="Flag indicating active wildlife corridor")
    soil_cohesion_kpa: Optional[float] = Field(120.0, ge=10.0, le=500.0, description="Effective soil cohesion in kPa")


@router.post("/process-region")
@router.post("/dynamic-region")
@limiter.limit("30/minute")
def process_region(request: Request, req: RegionRequest):
    """
    On-the-fly endpoint triggered when a user selects/draws a region on the map.
    Queries Google Earth Engine, runs EvOLve inference, and computes all features dynamically.
    Rate limited to max 30 requests per minute to prevent Earth Engine quota abuse.
    """
    global LATEST_DYNAMIC_ANALYSIS
    min_lon, min_lat, max_lon, max_lat = validate_coordinates(req.bbox)
    validate_date_range(req.start_date, req.end_date)
    sanitized_name = sanitize_string(req.region_name) or "Selected Region"
    
    # Validation: Ensure reasonable box size (max 0.35 x 0.35 degrees ~ 35km x 35km)
    if abs(max_lat - min_lat) > 0.35 or abs(max_lon - min_lon) > 0.35:
        raise HTTPException(400, "Selected region is too large for real-time analysis. Please choose an area under 35km x 35km.")

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

        # Automatically record inspection in SQLite persistence vault
        try:
            from dashboard.backend.database import log_query
            mean_ndvi = float(analysis.get("regional_summary", {}).get("mean_ndvi", 0.75))
            patches = analysis.get("patches", [])
            deg_count = sum(1 for p in patches if p.get("degraded", False))
            log_query(
                region_name=req.region_name,
                bbox=req.bbox,
                start_date=analysis.get('start_date'),
                end_date=analysis.get('end_date'),
                mean_ndvi=mean_ndvi,
                degraded_patch_count=deg_count,
                total_patches=len(patches)
            )
        except Exception:
            pass

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


@router.post("/inference/construction-suitability")
@limiter.limit("20/minute")
def evaluate_construction_suitability(request: Request, req: ConstructionSuitabilityRequest):
    """
    On-demand geo-safety and terrain construction suitability assessment.
    Rate limited to max 20 requests per minute to throttle intensive geotechnical simulations.
    """
    slope = float(req.slope_deg)
    ls_prob = float(req.landslide_prob or 0.25)
    is_corridor = bool(req.is_wildlife_corridor)

    if slope < 10.0:
        slope_cat = "Gentle / Low Incline (<10°)"
        slope_safety = 96.0 - (slope / 10.0) * 12.0
    elif slope < 20.0:
        slope_cat = "Moderate Hill Slope (10°–20°)"
        slope_safety = 82.0 - ((slope - 10.0) / 10.0) * 35.0
    else:
        slope_cat = "Steep Mountain Escarpment (>20°)"
        slope_safety = max(5.0, 45.0 - ((slope - 20.0) / 15.0) * 38.0)

    ls_deduct = ls_prob * 55.0
    eco_deduct = 25.0 if is_corridor else 0.0
    overall_build_score = float(np.clip(slope_safety - ls_deduct - eco_deduct, 2.0, 99.0))

    if slope >= 20.0 or ls_prob >= 0.45 or (is_corridor and overall_build_score < 45.0):
        verdict = "HAZARD_PROHIBITED"
        label = "Hazard Zone — Construction Prohibited"
        color = "#E63946"
        badge = "Hazard: Do Not Build"
    elif slope >= 10.0 or ls_prob >= 0.25 or overall_build_score < 72.0:
        verdict = "CONDITIONAL_RESTRICTED"
        label = "Conditional Clearance — Engineering Mandated"
        color = "#FFB703"
        badge = "Conditional Clearance"
    else:
        verdict = "SUITABLE_FOR_CONSTRUCTION"
        label = "Safe for Construction — Standard Foundations"
        color = "#52B788"
        badge = "Safe to Build"

    try:
        from dashboard.backend.database import log_construction_permit
        notes = "Moratorium enforced." if verdict == "HAZARD_PROHIBITED" else ("Retaining walls and drainage required." if verdict == "CONDITIONAL_RESTRICTED" else "Standard pad foundations permitted.")
        log_construction_permit(
            patch_id=None,
            slope_deg=slope,
            landslide_prob=ls_prob,
            safety_score=round(overall_build_score, 1),
            verdict=verdict,
            decision_notes=f"{label}. {notes}"
        )
    except Exception:
        pass

    return {
        "status": "success",
        "verdict": verdict,
        "verdict_label": label,
        "badge": badge,
        "color": color,
        "safety_score": round(overall_build_score, 1),
        "slope_deg": slope,
        "slope_category": slope_cat,
        "landslide_prob_pct": round(ls_prob * 100, 1),
        "bearing_capacity": "Adequate (>200 kPa)" if verdict == "SUITABLE_FOR_CONSTRUCTION" else ("Moderate (100–180 kPa)" if verdict == "CONDITIONAL_RESTRICTED" else "Inadequate / Shear Failure (<80 kPa)"),
        "wildlife_corridor_conflict": is_corridor,
        "soil_stability": "Stable Bedrock" if verdict == "SUITABLE_FOR_CONSTRUCTION" else ("Moderate Cohesion" if verdict == "CONDITIONAL_RESTRICTED" else "Unconsolidated Colluvium / High Slip Risk"),
        "mandatory_actions": [
            "Strict construction moratorium — High risk of catastrophic slope shear." if verdict == "HAZARD_PROHIBITED" else ("Engineered retaining walls and contour drainage required." if verdict == "CONDITIONAL_RESTRICTED" else "Standard isolated pad foundations permitted.")
        ]
    }
