"""
EvOLve — History Vault REST API Router (routes/history.py)
Exposes endpoints to query and persist satellite inspection queries, construction permit audits,
and system statistics from the embedded SQLite database.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from dashboard.backend.database import (
    get_query_history,
    insert_query_history,
    get_construction_permits,
    insert_construction_permit,
    get_history_stats
)

router = APIRouter()


class QueryLogCreate(BaseModel):
    region_name: str
    start_date: Optional[str] = "2024-01-01"
    end_date: Optional[str] = "2024-12-31"
    mean_ndvi: Optional[float] = 0.65
    degraded_fraction: Optional[float] = 0.12
    officer_id: Optional[str] = "OFFICER-01"


class PermitCreate(BaseModel):
    patch_id: int
    region_name: str
    slope_deg: Optional[float] = 12.5
    elevation_m: Optional[float] = 850.0
    suitability_score: Optional[float] = 78.5
    decision: str  # APPROVED, REJECTED, CONDITIONAL, etc.
    reviewer_notes: Optional[str] = ""


@router.get("/history/queries")
def fetch_query_history():
    """Retrieve the last 25 historical satellite scans ordered by timestamp."""
    try:
        queries = get_query_history(limit=25)
        return {"status": "success", "count": len(queries), "queries": queries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch query history: {str(e)}")


@router.post("/history/log-query")
def log_query(req: QueryLogCreate):
    """Persist a new satellite regional inspection scan into the database."""
    try:
        query_id = insert_query_history(
            region_name=req.region_name,
            start_date=req.start_date or "2024-01-01",
            end_date=req.end_date or "2024-12-31",
            mean_ndvi=req.mean_ndvi if req.mean_ndvi is not None else 0.65,
            degraded_fraction=req.degraded_fraction if req.degraded_fraction is not None else 0.12,
            officer_id=req.officer_id or "OFFICER-01"
        )
        return {"status": "success", "message": "Query logged successfully", "id": query_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log query: {str(e)}")


@router.get("/history/permits")
def fetch_permits():
    """List all construction suitability audits and decisions."""
    try:
        permits = get_construction_permits(limit=50)
        return {"status": "success", "count": len(permits), "permits": permits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch permit records: {str(e)}")


@router.post("/history/save-permit")
def save_permit(req: PermitCreate):
    """Save an officer decision on a construction permit."""
    try:
        permit_id = insert_construction_permit(
            patch_id=req.patch_id,
            region_name=req.region_name,
            slope_deg=req.slope_deg or 0.0,
            elevation_m=req.elevation_m or 0.0,
            suitability_score=req.suitability_score or 0.0,
            decision=req.decision.upper(),
            reviewer_notes=req.reviewer_notes or ""
        )
        return {"status": "success", "message": "Permit decision saved", "id": permit_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save permit decision: {str(e)}")


@router.get("/history/stats")
def fetch_history_stats():
    """Summary counts (total queries run, total hectares inspected, permits issued)."""
    try:
        stats = get_history_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history stats: {str(e)}")
