"""
Automated Forest Monitoring — dashboard/backend/database.py
Embedded SQLite persistence vault (forest_records.db).

Maintains historical audit trail for:
1. query_history: Region coordinates, dates, mean NDVI, degraded fraction
2. construction_permits: Geotechnical audit verdicts, slope, landslide risk, safety score
3. ga_experiment_logs: Optimization runs, generation count, best fitness, optimal thresholds
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
    "forest_records.db"
)


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the SQLite database tables and seeds demo audit records if empty."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Query History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                region_name TEXT NOT NULL,
                bbox TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                mean_ndvi REAL,
                degraded_patch_count INTEGER DEFAULT 0,
                total_patches INTEGER DEFAULT 64
            )
        """)

        # 2. Construction Permits Audit Vault
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS construction_permits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                patch_id INTEGER,
                slope_deg REAL NOT NULL,
                landslide_prob REAL NOT NULL,
                safety_score REAL NOT NULL,
                verdict TEXT NOT NULL,
                decision_notes TEXT
            )
        """)

        # 3. Genetic Algorithm Experiment Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ga_experiment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                generations INTEGER NOT NULL,
                target_climate TEXT NOT NULL,
                best_fitness REAL NOT NULL,
                theta_dry REAL,
                theta_monsoon REAL,
                theta_retreat REAL,
                runtime_ms REAL
            )
        """)

        # Seed initial records if query_history is empty
        cursor.execute("SELECT COUNT(*) FROM query_history")
        if cursor.fetchone()[0] == 0:
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_patch_count, total_patches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, "Wayanad Wildlife Sanctuary", "[76.325, 11.625, 76.375, 11.675]", "2019-01", "2025-12", 0.742, 14, 64))

            cursor.execute("""
                INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_patch_count, total_patches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, "Silent Valley Buffer Zone", "[76.400, 11.050, 76.450, 11.100]", "2020-01", "2024-12", 0.812, 6, 64))

            # Seed construction permit
            cursor.execute("""
                INSERT INTO construction_permits (timestamp, patch_id, slope_deg, landslide_prob, safety_score, verdict, decision_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, 24, 24.5, 0.40, 11.6, "HAZARD_PROHIBITED", "Steep mountain escarpment (>20°), high shear failure risk. Construction moratorium enforced."))

            cursor.execute("""
                INSERT INTO construction_permits (timestamp, patch_id, slope_deg, landslide_prob, safety_score, verdict, decision_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, 12, 8.5, 0.12, 88.4, "SUITABLE_FOR_CONSTRUCTION", "Gentle slope (<10°), low pore pressure. Standard pad foundations approved."))

            # Seed GA experiment log
            cursor.execute("""
                INSERT INTO ga_experiment_logs (timestamp, generations, target_climate, best_fitness, theta_dry, theta_monsoon, theta_retreat, runtime_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (now, 30, "monsoon_priority", 0.962, 0.333, 0.554, 0.441, 3840.5))

        conn.commit()


def log_query(
    region_name: str,
    bbox: List[float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mean_ndvi: float = 0.75,
    degraded_patch_count: int = 0,
    total_patches: int = 64
) -> int:
    """Logs an on-the-fly regional GEE inspection query."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_patch_count, total_patches)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, region_name, json.dumps(bbox), start_date, end_date, float(mean_ndvi), int(degraded_patch_count), int(total_patches)))
        conn.commit()
        return cursor.lastrowid


def log_construction_permit(
    patch_id: int,
    slope_deg: float,
    landslide_prob: float,
    safety_score: float,
    verdict: str,
    decision_notes: str
) -> int:
    """Logs a mountain construction suitability audit verdict."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO construction_permits (timestamp, patch_id, slope_deg, landslide_prob, safety_score, verdict, decision_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now, patch_id, float(slope_deg), float(landslide_prob), float(safety_score), verdict, decision_notes))
        conn.commit()
        return cursor.lastrowid


def log_ga_experiment(
    generations: int,
    target_climate: str,
    best_fitness: float,
    theta_dry: float,
    theta_monsoon: float,
    theta_retreat: float,
    runtime_ms: float
) -> int:
    """Logs a live Genetic Algorithm convergence experiment."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ga_experiment_logs (timestamp, generations, target_climate, best_fitness, theta_dry, theta_monsoon, theta_retreat, runtime_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, int(generations), target_climate, float(best_fitness), float(theta_dry), float(theta_monsoon), float(theta_retreat), float(runtime_ms)))
        conn.commit()
        return cursor.lastrowid


def get_query_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent satellite inspection queries."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM query_history ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_construction_permits(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves civil construction suitability audit records."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM construction_permits ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_ga_experiment_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves historical Genetic Algorithm optimization runs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ga_experiment_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]
