"""
EvOLve — dashboard/backend/routes/health.py
Forest health endpoints: patch scores, NDVI series, patch map.
"""

import os
import json
import numpy as np
from fastapi import APIRouter, HTTPException

router = APIRouter()

RESULTS_DIR    = "results"
PATCHES_DIR    = "data/patches"
INDEX_PATH     = "data/patches/patch_index.json"
LABELS_DIR     = "data/labels"


def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


@router.get("/patches")
def get_all_patches():
    """
    Returns all patches with their degradation scores, grid positions,
    health status and basic metadata. Used to render the main forest map.
    """
    index = load_json(INDEX_PATH)
    clf   = load_json(os.path.join(RESULTS_DIR, "classifier_results.json"))

    if not index:
        raise HTTPException(404, "Patch index not found. Run build_patches.py first.")

    patch_scores = clf["patch_scores"] if clf else {}

    patches = []
    for entry in index["patches"]:
        pid = entry["patch_id"]
        score_data = patch_scores.get(str(pid), {})
        deg_score  = score_data.get("degradation_score", 0.5)

        # Health status
        if deg_score < 0.20:   status = "Healthy"
        elif deg_score < 0.45: status = "Degraded"
        else:                  status = "Severely Degraded"

        patches.append({
            "patch_id":         pid,
            "grid_row":         entry["grid_row"],
            "grid_col":         entry["grid_col"],
            "pixel_bounds":     entry["pixel_bounds"],
            "valid_fraction":   entry["valid_fraction"],
            "n_months":         entry["n_months"],
            "degradation_score": round(deg_score, 4),
            "health_status":    status,
            "prediction":       score_data.get("prediction", -1),
            "ground_truth":     score_data.get("label", -1),
        })

    # AOI bounding box (Wayanad Muthanga range)
    aoi = {
        "min_lon": 76.325, "max_lon": 76.375,
        "min_lat": 11.625, "max_lat": 11.675,
        "center":  [11.650, 76.350],
    }

    return {
        "aoi":           aoi,
        "total_patches": len(patches),
        "months":        index["months"],
        "patches":       patches,
    }


@router.get("/patches/{patch_id}/ndvi-series")
def get_ndvi_series(patch_id: int):
    """
    Returns the monthly NDVI time series for a single patch.
    Used for the click-to-inspect chart on the map.
    """
    index = load_json(INDEX_PATH)
    if not index:
        raise HTTPException(404, "Patch index not found")

    # Find entry
    entry = next((e for e in index["patches"] if e["patch_id"] == patch_id), None)
    if entry is None:
        raise HTTPException(404, f"Patch {patch_id} not found")

    patch_path = os.path.join(PATCHES_DIR, f"patch_{patch_id:04d}.npy")
    if not os.path.exists(patch_path):
        raise HTTPException(404, f"Patch data file not found: {patch_path}")

    patch = np.load(patch_path).astype(np.float32)   # (T, 8, 64, 64)
    patch[patch == -9999] = np.nan

    months   = index["months"]
    ndvi_idx = 6
    evi_idx  = 7

    series = []
    for t, month in enumerate(months):
        if t >= patch.shape[0]:
            break
        ndvi_t  = float(np.nanmean(patch[t, ndvi_idx]))
        evi_t   = float(np.nanmean(patch[t, evi_idx]))
        swir1_t = float(np.nanmean(patch[t, 4]))
        nan_frac = float(np.isnan(patch[t, ndvi_idx]).mean())
        series.append({
            "month":     month,
            "ndvi":      round(ndvi_t,  4) if not np.isnan(ndvi_t)  else None,
            "evi":       round(evi_t,   4) if not np.isnan(evi_t)   else None,
            "swir1":     round(swir1_t, 4) if not np.isnan(swir1_t) else None,
            "nan_frac":  round(nan_frac, 3),
        })

    # Load heatmap if available
    heatmap_path = os.path.join(RESULTS_DIR, "heatmaps", f"heatmap_{patch_id:04d}.npy")
    heatmap = None
    if os.path.exists(heatmap_path):
        hm = np.load(heatmap_path)
        heatmap = hm.tolist()   # 64×64 list of lists

    # Label info
    labels_data = load_json(os.path.join(RESULTS_DIR, "patch_labels.json"))
    label_info  = labels_data["labels"].get(str(patch_id), {}) if labels_data else {}

    return {
        "patch_id":     patch_id,
        "grid_row":     entry["grid_row"],
        "grid_col":     entry["grid_col"],
        "n_months":     len(series),
        "ndvi_series":  series,
        "heatmap":      heatmap,
        "label":        label_info,
    }


@router.get("/summary")
def get_summary():
    """High-level project summary for the dashboard header."""
    clf  = load_json(os.path.join(RESULTS_DIR, "classifier_results.json"))
    carb = load_json(os.path.join(RESULTS_DIR, "carbon_stock.json"))
    corr = load_json(os.path.join(RESULTS_DIR, "corridor_analysis.json"))
    enc  = load_json(os.path.join(RESULTS_DIR, "encroachment_alerts.json"))

    total_patches   = 64
    degraded        = 0
    if clf:
        degraded = sum(1 for v in clf["patch_scores"].values() if v["prediction"] == 1)

    return {
        "study_area":          "Wayanad Wildlife Sanctuary (Muthanga Range)",
        "monitoring_period":   "2019–2025",
        "total_patches":       total_patches,
        "degraded_patches":    degraded,
        "healthy_patches":     total_patches - degraded,
        "degradation_pct":     round(degraded / total_patches * 100, 1),
        "total_carbon_tCO2":   carb["total_stock_tCO2"]        if carb else None,
        "annual_carbon_loss":  carb["total_annual_loss_tCO2"]  if carb else None,
        "corridors_broken":    corr["broken"]                  if corr else None,
        "encroachment_alerts": enc["total_alerts"]             if enc else None,
    }
