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

# Primary SQLite database location
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
    "forest_records.db"
)


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the SQLite database tables and seeds demo audit records if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Query History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            region_name TEXT NOT NULL,
            bbox TEXT DEFAULT '[]',
            start_date TEXT,
            end_date TEXT,
            mean_ndvi REAL,
            degraded_patch_count INTEGER DEFAULT 0,
            degraded_fraction REAL DEFAULT 0.0,
            total_patches INTEGER DEFAULT 64,
            officer_id TEXT DEFAULT 'OFFICER-DEFAULT',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Construction Permits Audit Vault
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS construction_permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            patch_id INTEGER NOT NULL,
            region_name TEXT DEFAULT 'Wayanad Sanctuary',
            slope_deg REAL NOT NULL,
            elevation_m REAL DEFAULT 850.0,
            landslide_prob REAL DEFAULT 0.0,
            safety_score REAL DEFAULT 0.0,
            suitability_score REAL DEFAULT 0.0,
            verdict TEXT,
            decision TEXT,
            decision_notes TEXT,
            reviewer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Genetic Algorithm Experiment Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ga_experiment_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            generations INTEGER NOT NULL,
            population_size INTEGER DEFAULT 30,
            mutation_rate REAL DEFAULT 0.08,
            target_climate TEXT DEFAULT 'balanced',
            best_fitness REAL NOT NULL,
            theta_dry REAL,
            theta_monsoon REAL,
            theta_retreat REAL,
            runtime_ms REAL DEFAULT 0.0,
            runtime_seconds REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial records if query_history is empty
    cursor.execute("SELECT COUNT(*) FROM query_history")
    if cursor.fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        cursor.executemany("""
            INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_fraction, degraded_patch_count, total_patches, officer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (now, "Wayanad Wildlife Sanctuary, India", "[76.325, 11.625, 76.375, 11.675]", "2022-01", "2024-12", 0.68, 0.12, 8, 64, "OFFICER-VASISHTA"),
            (now, "Silent Valley National Park, India", "[76.400, 11.050, 76.450, 11.100]", "2021-06", "2024-06", 0.74, 0.05, 3, 64, "OFFICER-TEJESH"),
            (now, "Amazon Rainforest, Peru", "[-69.350, -12.650, -69.300, -12.600]", "2020-01", "2024-01", 0.59, 0.24, 15, 64, "OFFICER-GIRISH"),
            (now, "Congo Basin, DRC", "[20.800, -2.150, 20.850, -2.100]", "2021-01", "2023-12", 0.71, 0.08, 5, 64, "OFFICER-TARAK"),
        ])

        # Seed construction permits
        cursor.executemany("""
            INSERT INTO construction_permits (timestamp, patch_id, region_name, slope_deg, elevation_m, landslide_prob, safety_score, suitability_score, verdict, decision, decision_notes, reviewer_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (now, 14, "Wayanad Wildlife Sanctuary, India", 28.5, 940.0, 0.42, 11.6, 32.0, "HAZARD_PROHIBITED", "STRICTLY PROHIBITED", "Steep mountain escarpment (>20°), high shear failure risk. Construction moratorium enforced.", "Excessive slope (>25°) and landslide hazard risk. High tree canopy density."),
            (now, 42, "Wayanad Wildlife Sanctuary, India", 11.2, 780.0, 0.12, 84.5, 84.5, "SUITABLE_FOR_CONSTRUCTION", "PERMITTED", "Stable valley floor with gentle gradient and low landslide susceptibility.", "Standard pad foundations permitted."),
            (now, 27, "Silent Valley National Park, India", 19.8, 1120.0, 0.28, 58.0, 58.0, "CONDITIONAL_RESTRICTED", "CONDITIONAL APPROVAL", "Approved subject to strict stormwater runoff retention and deep-root bio-mitigation.", "Retaining walls and weep holes required."),
        ])

        # Seed GA experiment log
        cursor.executemany("""
            INSERT INTO ga_experiment_logs (timestamp, generations, population_size, mutation_rate, target_climate, best_fitness, theta_dry, theta_monsoon, theta_retreat, runtime_ms, runtime_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (now, 50, 30, 0.08, "monsoon_priority", 0.9620, 0.333, 0.554, 0.441, 3840.5, 4.25),
            (now, 100, 50, 0.05, "balanced", 0.8920, 0.334, 0.558, 0.452, 8700.0, 8.70),
        ])

    conn.commit()
    conn.close()
    print(f"[SQLite DB] Database initialized at: {DB_PATH}")


# -------------------------------------------------------------
# Query History Operations
# -------------------------------------------------------------

def insert_query_history(
    region_name: str,
    start_date: str,
    end_date: str,
    mean_ndvi: float,
    degraded_fraction: float,
    officer_id: str = "OFFICER-01",
    bbox: Optional[str] = "[]"
) -> int:
    """Inserts a historical scan record."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_fraction, officer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, region_name, str(bbox), start_date, end_date, float(mean_ndvi), float(degraded_fraction), officer_id))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def log_query(
    region_name: str,
    bbox: List[float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mean_ndvi: float = 0.75,
    degraded_patch_count: int = 0,
    total_patches: int = 64,
    officer_id: str = "OFFICER-GEE"
) -> int:
    """Logs an on-the-fly regional GEE inspection query."""
    now = datetime.now(timezone.utc).isoformat()
    deg_frac = round(degraded_patch_count / max(1, total_patches), 4)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO query_history (timestamp, region_name, bbox, start_date, end_date, mean_ndvi, degraded_patch_count, degraded_fraction, total_patches, officer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, region_name, json.dumps(bbox), start_date, end_date, float(mean_ndvi), int(degraded_patch_count), deg_frac, int(total_patches), officer_id))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_query_history(limit: int = 25) -> List[Dict[str, Any]]:
    """Retrieves recent satellite inspection queries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM query_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------
# Construction Permits Operations
# -------------------------------------------------------------

def insert_construction_permit(
    patch_id: int,
    region_name: str,
    slope_deg: float,
    elevation_m: float,
    suitability_score: float,
    decision: str,
    reviewer_notes: str = ""
) -> int:
    """Inserts a permit audit decision."""
    now = datetime.now(timezone.utc).isoformat()
    verdict = "HAZARD_PROHIBITED" if "PROHIBIT" in decision.upper() or "REJECT" in decision.upper() else ("CONDITIONAL_RESTRICTED" if "COND" in decision.upper() else "SUITABLE_FOR_CONSTRUCTION")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO construction_permits (timestamp, patch_id, region_name, slope_deg, elevation_m, safety_score, suitability_score, verdict, decision, decision_notes, reviewer_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, patch_id, region_name, float(slope_deg), float(elevation_m), float(suitability_score), float(suitability_score), verdict, decision, reviewer_notes, reviewer_notes))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def log_construction_permit(
    patch_id: int,
    slope_deg: float,
    landslide_prob: float,
    safety_score: float,
    verdict: str,
    decision_notes: str,
    region_name: str = "Wayanad Sanctuary"
) -> int:
    """Logs a mountain construction suitability audit verdict."""
    now = datetime.now(timezone.utc).isoformat()
    decision = "STRICTLY PROHIBITED" if verdict == "HAZARD_PROHIBITED" else ("CONDITIONAL APPROVAL" if verdict == "CONDITIONAL_RESTRICTED" else "PERMITTED")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO construction_permits (timestamp, patch_id, region_name, slope_deg, landslide_prob, safety_score, suitability_score, verdict, decision, decision_notes, reviewer_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, patch_id, region_name, float(slope_deg), float(landslide_prob), float(safety_score), float(safety_score), verdict, decision, decision_notes, decision_notes))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_construction_permits(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves civil construction suitability audit records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM construction_permits ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------
# Genetic Algorithm Experiments Operations
# -------------------------------------------------------------

def insert_ga_log(
    generations: int,
    population_size: int,
    mutation_rate: float,
    best_fitness: float,
    runtime_seconds: float
) -> int:
    """Inserts a GA optimization record."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ga_experiment_logs (timestamp, generations, population_size, mutation_rate, best_fitness, runtime_ms, runtime_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now, int(generations), int(population_size), float(mutation_rate), float(best_fitness), float(runtime_seconds * 1000.0), float(runtime_seconds)))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ga_experiment_logs (timestamp, generations, target_climate, best_fitness, theta_dry, theta_monsoon, theta_retreat, runtime_ms, runtime_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, int(generations), target_climate, float(best_fitness), float(theta_dry), float(theta_monsoon), float(theta_retreat), float(runtime_ms), float(runtime_ms / 1000.0)))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_ga_experiment_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves historical Genetic Algorithm optimization runs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ga_experiment_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------
# History Statistics Operations
# -------------------------------------------------------------

def get_history_stats() -> Dict[str, Any]:
    """Summary counts (total queries run, total hectares inspected, permits issued)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM query_history")
    total_queries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM construction_permits")
    total_permits = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ga_experiment_logs")
    total_ga_runs = cursor.fetchone()[0]

    # Standard query covers 64 patches * 64 ha = ~4,096 hectares
    estimated_hectares = total_queries * 4096

    conn.close()
    return {
        "total_queries": total_queries,
        "total_permits": total_permits,
        "total_ga_runs": total_ga_runs,
        "estimated_hectares_inspected": estimated_hectares
    }
