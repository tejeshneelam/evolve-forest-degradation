"""EvOLve — dashboard/backend/routes/risk.py"""
import os, json
from fastapi import APIRouter, HTTPException, Query
router = APIRouter()
RESULTS_DIR = "results"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path) as f: return json.load(f)

@router.get("/fire-risk")
def get_fire_risk():
    data = load_json(os.path.join(RESULTS_DIR, "fire_risk.json"))
    if not data: raise HTTPException(404, "Run features/fire_risk.py first")
    return data

@router.get("/landslide")
def get_landslide():
    data = load_json(os.path.join(RESULTS_DIR, "landslide_risk.json"))
    if not data: raise HTTPException(404, "Run features/landslide.py first")
    return data

@router.get("/encroachment")
def get_encroachment(severity: str = Query(None, description="Filter by severity: High/Medium/Low")):
    data = load_json(os.path.join(RESULTS_DIR, "encroachment_alerts.json"))
    if not data: raise HTTPException(404, "Run features/encroachment.py first")
    if severity:
        data["alerts"] = [a for a in data["alerts"] if a["severity"] == severity]
    return data
