"""
EvOLve — SQLite Database Layer (evolve_records.db)
Provides embedded storage for regional inspection queries, land construction suitability permits,
and Genetic Algorithm optimization logs using Python's standard sqlite3 engine.
"""

import os
import sqlite3
from typing import List, Dict, Any

# DB File path inside dashboard/backend directory
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "evolve_records.db")


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with dict row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: query_history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            mean_ndvi REAL,
            degraded_fraction REAL,
            officer_id TEXT DEFAULT 'OFFICER-DEFAULT',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: construction_permits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS construction_permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patch_id INTEGER NOT NULL,
            region_name TEXT NOT NULL,
            slope_deg REAL,
            elevation_m REAL,
            suitability_score REAL,
            decision TEXT CHECK(decision IN ('APPROVED', 'REJECTED', 'CONDITIONAL', 'PERMITTED', 'STRICTLY PROHIBITED', 'CONDITIONAL APPROVAL')),
            reviewer_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: ga_experiment_logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ga_experiment_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generations INTEGER,
            population_size INTEGER,
            mutation_rate REAL,
            best_fitness REAL,
            runtime_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed initial demo queries if table is empty
    cursor.execute("SELECT COUNT(*) FROM query_history")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO query_history (region_name, start_date, end_date, mean_ndvi, degraded_fraction, officer_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("Wayanad Wildlife Sanctuary, India", "2022-01", "2024-12", 0.68, 0.12, "OFFICER-VASISHTA"),
            ("Silent Valley National Park, India", "2021-06", "2024-06", 0.74, 0.05, "OFFICER-TEJESH"),
            ("Amazon Rainforest, Peru", "2020-01", "2024-01", 0.59, 0.24, "OFFICER-GIRISH"),
            ("Congo Basin, DRC", "2021-01", "2023-12", 0.71, 0.08, "OFFICER-TARAK"),
        ])

    # Seed initial permit records if empty
    cursor.execute("SELECT COUNT(*) FROM construction_permits")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO construction_permits (patch_id, region_name, slope_deg, elevation_m, suitability_score, decision, reviewer_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (14, "Wayanad Wildlife Sanctuary, India", 28.5, 940.0, 32.0, "STRICTLY PROHIBITED", "Excessive slope (>25°) and landslide hazard risk. High tree canopy density."),
            (42, "Wayanad Wildlife Sanctuary, India", 11.2, 780.0, 84.5, "PERMITTED", "Stable valley floor with gentle gradient and low landslide susceptibility."),
            (27, "Silent Valley National Park, India", 19.8, 1120.0, 58.0, "CONDITIONAL APPROVAL", "Approved subject to strict stormwater runoff retention and deep-root bio-mitigation."),
        ])

    # Seed initial GA experiment log if empty
    cursor.execute("SELECT COUNT(*) FROM ga_experiment_logs")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO ga_experiment_logs (generations, population_size, mutation_rate, best_fitness, runtime_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (50, 30, 0.08, 0.8571, 4.25),
            (100, 50, 0.05, 0.8920, 8.70),
        ])

    conn.commit()
    conn.close()
    print(f"[SQLite DB] Database initialized at: {DB_PATH}")


# Helper functions for database operations

def insert_query_history(region_name: str, start_date: str, end_date: str, mean_ndvi: float, degraded_fraction: float, officer_id: str = "OFFICER-01") -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO query_history (region_name, start_date, end_date, mean_ndvi, degraded_fraction, officer_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (region_name, start_date, end_date, mean_ndvi, degraded_fraction, officer_id))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_query_history(limit: int = 25) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM query_history ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def insert_construction_permit(patch_id: int, region_name: str, slope_deg: float, elevation_m: float, suitability_score: float, decision: str, reviewer_notes: str = "") -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO construction_permits (patch_id, region_name, slope_deg, elevation_m, suitability_score, decision, reviewer_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (patch_id, region_name, slope_deg, elevation_m, suitability_score, decision, reviewer_notes))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_construction_permits(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM construction_permits ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def insert_ga_log(generations: int, population_size: int, mutation_rate: float, best_fitness: float, runtime_seconds: float) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ga_experiment_logs (generations, population_size, mutation_rate, best_fitness, runtime_seconds)
        VALUES (?, ?, ?, ?, ?)
    """, (generations, population_size, mutation_rate, best_fitness, runtime_seconds))
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def get_history_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM query_history")
    total_queries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM construction_permits")
    total_permits = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ga_experiment_logs")
    total_ga_runs = cursor.fetchone()[0]

    # Calculate estimated inspected area: each patch is 64 hectares (8x8 grid = 64 patches * 64 ha ~ 4096 ha per query)
    # Standard query covers 64 patches * 64 ha = ~4,096 hectares
    estimated_hectares = total_queries * 4096

    conn.close()
    return {
        "total_queries": total_queries,
        "total_permits": total_permits,
        "total_ga_runs": total_ga_runs,
        "estimated_hectares_inspected": estimated_hectares
    }
