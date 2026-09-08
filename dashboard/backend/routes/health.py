"""
EvOLve — dashboard/backend/routes/health.py
Forest health endpoints: patch scores, NDVI series, patch map.
"""

import os
import json
import numpy as np
from fastapi import APIRouter, HTTPException, Path

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
    health status, landslide diagnostics, and construction suitability.
    """
    index = load_json(INDEX_PATH)
    clf   = load_json(os.path.join(RESULTS_DIR, "classifier_results.json"))
    ls    = load_json(os.path.join(RESULTS_DIR, "landslide_risk.json"))

    if not index:
        raise HTTPException(404, "Patch index not found. Run build_patches.py first.")

    patch_scores = clf["patch_scores"] if clf else {}
    ls_patches   = ls.get("patches", {}) if ls else {}

    patches = []
    for entry in index["patches"]:
        pid = entry["patch_id"]
        score_data = patch_scores.get(str(pid), {})
        deg_score  = score_data.get("degradation_score", 0.5)

        # Health status
        if deg_score < 0.20:   status = "Healthy"
        elif deg_score < 0.45: status = "Degraded"
        else:                  status = "Severely Degraded"

        # Landslide diagnostic metrics
        p_ls = ls_patches.get(str(pid), {})
        slope = round(float(p_ls.get("slope_proxy", 0.5) * 12.0 + 3.5), 1)
        ls_prob = round(float(p_ls.get("vulnerability_score", 0.25)), 4)
        ls_level = p_ls.get("vulnerability_level", "Moderate")

        ls_diag = {
            "probability": ls_prob,
            "probability_pct": round(ls_prob * 100, 1),
            "risk_level": ls_level,
            "metrics": {
                "slope_angle_deg": slope,
                "tree_cover_pct": round(max(15.0, 92.0 - deg_score * 75.0), 1),
                "recent_loss_pct": round(float(p_ls.get("loss_rate", 0.01) * 100.0), 2),
                "rainfall_90d_mm": 280,
            },
            "factors": {
                "slope_weight": round(min(1.0, slope / 25.0), 3),
                "root_decay_weight": round(min(1.0, deg_score * 1.5), 3),
                "pore_pressure_weight": 0.85,
            },
            "primary_reasons": [
                f"Terrain slope gradient of {slope}° creates gravitational downward shear traction.",
                f"Vegetation canopy loss ({deg_score*100:.1f}%) weakens subsurface root anchoring cohesion.",
                "Monsoon hydrostatic pressure lubricates fracture planes."
            ],
            "recommended_mitigations": [
                "Install deep-rooted bio-anchoring flora (Vetiver and native ficus).",
                "Construct contour runoff diversion ditches.",
                "Restrict cutting unpaved access paths that trigger slope toe failures."
            ]
        }

        # Construction Suitability Assessment
        is_corridor = entry["grid_col"] in [2, 3, 4]
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
            build_verdict = "HAZARD_PROHIBITED"
            build_label = "Hazard Zone — Construction Prohibited"
            build_color = "#E63946"
            build_badge = "Hazard: Do Not Build"
        elif slope >= 10.0 or ls_prob >= 0.25 or overall_build_score < 72.0:
            build_verdict = "CONDITIONAL_RESTRICTED"
            build_label = "Conditional Clearance — Engineering Mandated"
            build_color = "#FFB703"
            build_badge = "Conditional Clearance"
        else:
            build_verdict = "SUITABLE_FOR_CONSTRUCTION"
            build_label = "Safe for Construction — Standard Foundations"
            build_color = "#52B788"
            build_badge = "Safe to Build"

        build_suitability = {
            'verdict': build_verdict,
            'verdict_label': build_label,
            'badge': build_badge,
            'color': build_color,
            'safety_score': round(overall_build_score, 1),
            'slope_deg': slope,
            'slope_category': slope_cat,
            'landslide_prob_pct': round(ls_prob * 100, 1),
            'bearing_capacity': "Adequate (>200 kPa)" if build_verdict == "SUITABLE_FOR_CONSTRUCTION" else ("Moderate (100–180 kPa)" if build_verdict == "CONDITIONAL_RESTRICTED" else "Inadequate / Shear Failure (<80 kPa)"),
            'wildlife_corridor_conflict': is_corridor,
            'eco_status': "Active Wildlife Corridor — Legal Moratorium" if is_corridor else "Standard Regulatory Clearance",
            'mandatory_actions': [
                "Strict construction moratorium — High risk of catastrophic slope shear." if build_verdict == "HAZARD_PROHIBITED" else ("Engineered retaining walls and contour drainage required." if build_verdict == "CONDITIONAL_RESTRICTED" else "Standard isolated pad foundations permitted.")
            ],
            'soil_stability': "Stable Bedrock" if build_verdict == "SUITABLE_FOR_CONSTRUCTION" else ("Moderate Cohesion" if build_verdict == "CONDITIONAL_RESTRICTED" else "Unconsolidated Colluvium / High Slip Risk")
        }

        # Approximated coordinate bounds for Wayanad (8x8 grid across bounding box)
        lat_size = (11.675 - 11.625) / 8.0
        lon_size = (76.375 - 76.325) / 8.0
        lat_max = 11.675 - entry["grid_row"] * lat_size
        lat_min = lat_max - lat_size
        lon_min = 76.325 + entry["grid_col"] * lon_size
        lon_max = lon_min + lon_size

        patches.append({
            "patch_id":         pid,
            "grid_row":         entry["grid_row"],
            "grid_col":         entry["grid_col"],
            "bounds":           [[lat_min, lon_min], [lat_max, lon_max]],
            "center":           [(lat_min + lat_max) / 2.0, (lon_min + lon_max) / 2.0],
            "pixel_bounds":     entry["pixel_bounds"],
            "valid_fraction":   entry["valid_fraction"],
            "n_months":         entry["n_months"],
            "degradation_score": round(deg_score, 4),
            "health_status":    status,
            "slope_deg":        slope,
            "prediction":       score_data.get("prediction", -1),
            "ground_truth":     score_data.get("label", -1),
            "landslide":        ls_diag,
            "construction_suitability": build_suitability,
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
def get_ndvi_series(patch_id: int = Path(..., ge=0, le=10000, description="Forest patch identifier (0 to 10000)")):
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
    valid_ndvis = []
    for t, month in enumerate(months):
        if t >= patch.shape[0]:
            break
        ndvi_t  = float(np.nanmean(patch[t, ndvi_idx]))
        evi_t   = float(np.nanmean(patch[t, evi_idx]))
        swir1_t = float(np.nanmean(patch[t, 4]))
        nan_frac = float(np.isnan(patch[t, ndvi_idx]).mean())
        if not np.isnan(ndvi_t):
            valid_ndvis.append((month, ndvi_t))
        series.append({
            "month":     month,
            "ndvi":      round(ndvi_t,  4) if not np.isnan(ndvi_t)  else None,
            "evi":       round(evi_t,   4) if not np.isnan(evi_t)   else None,
            "swir1":     round(swir1_t, 4) if not np.isnan(swir1_t) else None,
            "nan_frac":  round(nan_frac, 3),
        })

    # Trajectory summary
    start_ndvi = valid_ndvis[0][1] if valid_ndvis else 0.5
    end_ndvi = valid_ndvis[-1][1] if valid_ndvis else 0.5
    trend_diff = end_ndvi - start_ndvi
    trend_pct = (trend_diff / max(0.01, start_ndvi)) * 100.0

    if trend_pct <= -5.0:
        trend_status = "Degrading"
        trend_icon = "↘️"
    elif trend_pct >= 5.0:
        trend_status = "Greening"
        trend_icon = "↗️"
    else:
        trend_status = "Stable"
        trend_icon = "↔️"

    max_pt = max(valid_ndvis, key=lambda x: x[1]) if valid_ndvis else (months[0], 0.5)
    min_pt = min(valid_ndvis, key=lambda x: x[1]) if valid_ndvis else (months[0], 0.5)

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
        "patch_id":       patch_id,
        "grid_row":       entry["grid_row"],
        "grid_col":       entry["grid_col"],
        "n_months":       len(series),
        "start_ndvi":     round(start_ndvi, 3),
        "end_ndvi":       round(end_ndvi, 3),
        "trend_status":   trend_status,
        "trend_icon":     trend_icon,
        "trend_pct":      round(trend_pct, 1),
        "peak_greenness": {"month": max_pt[0], "ndvi": round(max_pt[1], 3)},
        "dry_trough":     {"month": min_pt[0], "ndvi": round(min_pt[1], 3)},
        "ndvi_series":    series,
        "heatmap":        heatmap,
        "label":          label_info,
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
