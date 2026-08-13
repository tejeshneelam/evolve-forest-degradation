"""EvOLve — dashboard/backend/routes/conservation.py"""
import os, json
from fastapi import APIRouter, HTTPException, Query
router = APIRouter()
RESULTS_DIR = "results"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path) as f: return json.load(f)

@router.get("/carbon")
def get_carbon():
    data = load_json(os.path.join(RESULTS_DIR, "carbon_stock.json"))
    if not data: raise HTTPException(404, "Run features/carbon.py first")
    return data

@router.get("/reforestation")
def get_reforestation(top_n: int = Query(15, description="Number of top priority patches")):
    data = load_json(os.path.join(RESULTS_DIR, "reforestation_priority.json"))
    if not data: raise HTTPException(404, "Run features/reforestation.py first")
    data["top_candidates"] = data["top_candidates"][:top_n]
    return data

@router.get("/patrol-route")
def get_patrol_route(start: int = Query(...), end: int = Query(...)):
    """Find the safest ranger patrol route between two patches."""
    from features.patrol_route import find_patrol_route
    result = find_patrol_route(start, end)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result
