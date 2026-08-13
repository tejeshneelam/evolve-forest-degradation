"""EvOLve — dashboard/backend/routes/wildlife.py"""
import os, json
from fastapi import APIRouter, HTTPException
router = APIRouter()
RESULTS_DIR = "results"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path) as f: return json.load(f)

@router.get("/corridors")
def get_corridors():
    data = load_json(os.path.join(RESULTS_DIR, "corridor_analysis.json"))
    if not data: raise HTTPException(404, "Run features/corridor.py first")
    return data

@router.get("/corridors/{corridor_id}")
def get_corridor(corridor_id: int):
    data = load_json(os.path.join(RESULTS_DIR, "corridor_analysis.json"))
    if not data: raise HTTPException(404, "Corridor data not found")
    c = next((c for c in data["corridors"] if c["corridor_id"] == corridor_id), None)
    if not c: raise HTTPException(404, f"Corridor {corridor_id} not found")
    return c
