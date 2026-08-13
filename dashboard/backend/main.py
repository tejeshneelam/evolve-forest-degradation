"""
EvOLve — dashboard/backend/main.py
FastAPI backend serving all EvOLve analysis results to the React dashboard.

Start with:
    cd evolve-forest-degradation
    source venv/bin/activate
    uvicorn dashboard.backend.main:app --reload --port 8000
"""

import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard.backend.routes import (
    health, wildlife, risk, conservation, reports, ga_log
)

app = FastAPI(
    title="EvOLve Forest Intelligence API",
    description=(
        "Evolutionary-Optimized Adaptive Self-Supervised Framework "
        "for Forest Degradation Detection — Wayanad Wildlife Sanctuary"
    ),
    version="1.0.0",
)

# Allow React dev server (port 3000) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(health.router,       prefix="/api",        tags=["Forest Health"])
app.include_router(wildlife.router,     prefix="/api",        tags=["Wildlife"])
app.include_router(risk.router,         prefix="/api",        tags=["Risk"])
app.include_router(conservation.router, prefix="/api",        tags=["Conservation"])
app.include_router(ga_log.router,       prefix="/api",        tags=["GA Log"])
app.include_router(reports.router,      prefix="/api",        tags=["Reports"])


@app.get("/")
def root():
    return {
        "project": "EvOLve",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/api/status")
def status():
    """Check which result files are available."""
    results_dir = "results"
    files = [
        "classifier_results.json",
        "corridor_analysis.json",
        "fire_risk.json",
        "landslide_risk.json",
        "encroachment_alerts.json",
        "carbon_stock.json",
        "reforestation_priority.json",
        "ga_results.json",
        "best_thresholds.json",
        "patch_labels.json",
    ]
    available = {}
    for f in files:
        path = os.path.join(results_dir, f)
        available[f] = {
            "exists": os.path.exists(path),
            "size_kb": round(os.path.getsize(path) / 1024, 1) if os.path.exists(path) else 0,
        }
    return {"results_available": available}
