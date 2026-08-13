"""EvOLve — dashboard/backend/routes/ga_log.py"""
import os, json
from fastapi import APIRouter, HTTPException
router = APIRouter()
RESULTS_DIR = "results"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path) as f: return json.load(f)

@router.get("/ga-results")
def get_ga_results():
    data = load_json(os.path.join(RESULTS_DIR, "ga_results.json"))
    if not data: raise HTTPException(404, "Run ga/run_ga.py first")
    return data

@router.get("/ga-thresholds")
def get_ga_thresholds():
    data = load_json(os.path.join(RESULTS_DIR, "best_thresholds.json"))
    if not data: raise HTTPException(404, "Run ga/run_ga.py first")
    return data

@router.get("/ga-history")
def get_ga_history():
    data = load_json(os.path.join(RESULTS_DIR, "ga_results.json"))
    if not data: raise HTTPException(404, "GA results not found")
    return {"history": data.get("history", [])}
