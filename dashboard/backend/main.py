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

from dashboard.backend.middleware import SecurityHeadersMiddleware, AuditLoggingMiddleware, AUDIT_LOG_BUFFER
from dashboard.backend.routes import (
    health, wildlife, risk, conservation, reports, ga_log, dynamic_region
)

app = FastAPI(
    title="EvOLve Forest Intelligence API",
    description=(
        "Evolutionary-Optimized Adaptive Self-Supervised Framework "
        "for Forest Degradation Detection — Global & Wayanad"
    ),
    version="2.0.0",
)

# 1. Custom Security Response Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Audit & Request Logger Middleware (captures IP, method, route, status, latency_ms)
app.add_middleware(AuditLoggingMiddleware)

# 2. Strict CORS Configuration - restricted to authorized local dashboard origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Register all route groups
app.include_router(dynamic_region.router,prefix="/api",        tags=["Dynamic GEE Ingestion"])
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
    

@app.get("/api/security/audit-logs", tags=["Security & Compliance"])
def get_audit_logs(limit: int = 50):
    """Retrieve recent structured audit logs for compliance monitoring."""
    logs = list(AUDIT_LOG_BUFFER)
    return {
        "total_buffered": len(logs),
        "audit_logs": logs[-max(1, min(100, limit)):]
    }
