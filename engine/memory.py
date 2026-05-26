import sqlite3
import datetime
import json
from typing import List, Dict, Optional
from engine.config import DB_PATH

# ══════════════════════════════
#   APEX — Memory & Learning System
# ══════════════════════════════

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_db():
    try:
        with _get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    query          TEXT NOT NULL,
                    response       TEXT NOT NULL,
                    success        INTEGER DEFAULT 1,
                    command_type   TEXT DEFAULT 'general',
                    timestamp      TEXT NOT NULL,
                    execution_time REAL DEFAULT 0.0,
                    context        TEXT
                );
                CREATE TABLE IF NOT EXISTS command_patterns (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    command      TEXT NOT NULL UNIQUE,
                    frequency    INTEGER DEFAULT 1,
                    last_used    TEXT NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    avg_time     REAL DEFAULT 0.0
                );
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    category   TEXT NOT NULL,
                    key        TEXT NOT NULL,
                    value      TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    learned_at TEXT NOT NULL,
                    UNIQUE(category, key)
                );
                CREATE TABLE IF NOT EXISTS task_metrics (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type      TEXT NOT NULL UNIQUE,
                    total_attempts INTEGER DEFAULT 0,
                    successes      INTEGER DEFAULT 0,
                    failures       INTEGER DEFAULT 0,
                    avg_duration   REAL DEFAULT 0.0
                );
            """)
            conn.commit()
        print("[APEX MEMORY] Initialized.")
    except Exception as e:
        print(f"[APEX MEMORY] Init error: {e}")


def record_interaction(
    query: str,
    response: str,
    success: bool = True,
    command_type: str = "general",
    execution_time: float = 0.0,
    context: dict = None
):
    """Record every interaction for learning and pattern detection."""
    try:
        ts           = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context_json = json.dumps(context) if context else None
        success_int  = 1 if success else 0
        success_float = 1.0 if success else 0.0

        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO interactions
                    (query, response, success, command_type, timestamp, execution_time, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query, response, success_int, command_type, ts, execution_time, context_json))

            conn.execute("""
                INSERT INTO command_patterns (command, frequency, last_used, success_rate)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(command) DO UPDATE SET
                    frequency    = frequency + 1,
                    last_used    = excluded.last_used,
                    success_rate = (success_rate * frequency + excluded.success_rate)
                                   / (frequency + 1)
            """, (command_type, ts, success_float))

            conn.execute("""
                INSERT INTO task_metrics (task_type, total_attempts, successes, failures, avg_duration)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(task_type) DO UPDATE SET
                    total_attempts = total_attempts + 1,
                    successes      = successes + excluded.successes,
                    failures       = failures  + excluded.failures,
                    avg_duration   = (avg_duration * total_attempts + excluded.avg_duration)
                                     / (total_attempts + 1)
            """, (command_type, success_int, 1 - success_int, execution_time))

            conn.commit()
    except Exception as e:
        print(f"[APEX MEMORY] record_interaction error: {e}")


def get_recent_context(limit: int = 5) -> List[Dict]:
    """Fetch recent interactions to pass as LLM context."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT query, response, command_type, timestamp
                FROM interactions
                ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
            return [
                {"query": r[0], "response": r[1], "type": r[2], "time": r[3]}
                for r in reversed(rows)
            ]
    except Exception as e:
        print(f"[APEX MEMORY] get_recent_context error: {e}")
        return []


def get_command_patterns(top_n: int = 10) -> List[Dict]:
    """Return most-used command types for proactive suggestions."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT command, frequency, last_used, success_rate
                FROM command_patterns
                ORDER BY frequency DESC LIMIT ?
            """, (top_n,)).fetchall()
            return [
                {"command": r[0], "frequency": r[1],
                 "last_used": r[2], "success_rate": r[3]}
                for r in rows
            ]
    except Exception as e:
        print(f"[APEX MEMORY] get_command_patterns error: {e}")
        return []


def learn_preference(category: str, key: str, value: str, confidence: float = 0.7):
    """Upsert a learned preference, incrementally raising confidence."""
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO user_preferences (category, key, value, confidence, learned_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(category, key) DO UPDATE SET
                    value      = excluded.value,
                    confidence = MIN(1.0, confidence + 0.1),
                    learned_at = excluded.learned_at
            """, (category, key, value, confidence, ts))
            conn.commit()
    except Exception as e:
        print(f"[APEX MEMORY] learn_preference error: {e}")


def get_preferences(category: Optional[str] = None) -> List[Dict]:
    """Retrieve all or category-filtered preferences."""
    try:
        with _get_conn() as conn:
            if category:
                rows = conn.execute("""
                    SELECT category, key, value, confidence
                    FROM user_preferences WHERE category = ?
                    ORDER BY confidence DESC
                """, (category,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT category, key, value, confidence
                    FROM user_preferences ORDER BY confidence DESC
                """).fetchall()
            return [
                {"category": r[0], "key": r[1],
                 "value": r[2], "confidence": r[3]}
                for r in rows
            ]
    except Exception as e:
        print(f"[APEX MEMORY] get_preferences error: {e}")
        return []


def analyze_user_behavior() -> Dict:
    """Return peak hour, most-used command, and daily average."""
    try:
        with _get_conn() as conn:
            peak = conn.execute("""
                SELECT strftime('%H', timestamp) as h, COUNT(*) as c
                FROM interactions GROUP BY h ORDER BY c DESC LIMIT 1
            """).fetchone()

            common = conn.execute("""
                SELECT command_type, COUNT(*) as c
                FROM interactions GROUP BY command_type ORDER BY c DESC LIMIT 1
            """).fetchone()

            freq = conn.execute("""
                SELECT COUNT(DISTINCT DATE(timestamp)), COUNT(*)
                FROM interactions
            """).fetchone()

        return {
            "peak_hour":             int(peak[0]) if peak else None,
            "most_common_command":   common[0]    if common else None,
            "daily_avg_interactions": round(freq[1] / max(freq[0], 1), 1) if freq else 0,
        }
    except Exception as e:
        print(f"[APEX MEMORY] analyze_user_behavior error: {e}")
        return {}


def get_task_metrics() -> List[Dict]:
    """Return success/failure stats per task type."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("""
                SELECT task_type, total_attempts, successes, failures, avg_duration
                FROM task_metrics ORDER BY total_attempts DESC
            """).fetchall()
            return [
                {
                    "task":         r[0],
                    "attempts":     r[1],
                    "successes":    r[2],
                    "failures":     r[3],
                    "avg_duration": round(r[4], 3),
                    "success_rate": round(r[2] / max(r[1], 1), 2),
                }
                for r in rows
            ]
    except Exception as e:
        print(f"[APEX MEMORY] get_task_metrics error: {e}")
        return []


# Auto-init on import
init_memory_db()