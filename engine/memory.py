import sqlite3
import datetime
import json
from typing import List, Dict, Optional

DB_PATH = "APEX.db"


# ══════════════════════════════════════════════════
#   MEMORY SYSTEM — Long-term learning & context
# ══════════════════════════════════════════════════

def init_memory_db():
    """Initialize advanced memory tables."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Interaction memory with embeddings preparation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    query       TEXT NOT NULL,
                    response    TEXT NOT NULL,
                    success     INTEGER DEFAULT 1,
                    command_type TEXT,
                    timestamp   TEXT NOT NULL,
                    execution_time REAL,
                    context     TEXT
                )
            """)
            
            # Command patterns - tracks what user does most
            conn.execute("""
                CREATE TABLE IF NOT EXISTS command_patterns (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    command     TEXT NOT NULL UNIQUE,
                    frequency   INTEGER DEFAULT 1,
                    last_used   TEXT NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    avg_time    REAL DEFAULT 0.0
                )
            """)
            
            # User preferences learned over time
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    category    TEXT NOT NULL,
                    key         TEXT NOT NULL,
                    value       TEXT NOT NULL,
                    confidence  REAL DEFAULT 0.5,
                    learned_at  TEXT NOT NULL,
                    UNIQUE(category, key)
                )
            """)
            
            # Task success metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_metrics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type   TEXT NOT NULL,
                    total_attempts INTEGER DEFAULT 0,
                    successes   INTEGER DEFAULT 0,
                    failures    INTEGER DEFAULT 0,
                    avg_duration REAL DEFAULT 0.0
                )
            """)
            
            conn.commit()
            print("[APEX MEMORY] Memory database initialized")
    except Exception as e:
        print(f'[APEX MEMORY] Init error: {e}')


def record_interaction(query: str, response: str, success: bool = True, 
                       command_type: str = "general", execution_time: float = 0.0,
                       context: dict = None):
    """Record an interaction for learning."""
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context_json = json.dumps(context) if context else None
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO interactions 
                (query, response, success, command_type, timestamp, execution_time, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query, response, 1 if success else 0, command_type, ts, execution_time, context_json))
            
            # Update command patterns
            conn.execute("""
                INSERT INTO command_patterns (command, frequency, last_used, success_rate)
                VALUES (?, 1, ?, 1.0)
                ON CONFLICT(command) DO UPDATE SET
                    frequency = frequency + 1,
                    last_used = ?,
                    success_rate = (success_rate * frequency + ?) / (frequency + 1)
            """, (command_type, ts, ts, 1.0 if success else 0.0))
            
            conn.commit()
    except Exception as e:
        print(f'[APEX MEMORY] Record error: {e}')


def get_recent_context(limit: int = 5) -> List[Dict]:
    """Get recent interactions as context for the LLM."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT query, response, command_type, timestamp
                FROM interactions
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
            return [
                {
                    "query": r[0],
                    "response": r[1],
                    "type": r[2],
                    "time": r[3]
                }
                for r in reversed(rows)
            ]
    except Exception as e:
        print(f'[APEX MEMORY] Context retrieval error: {e}')
        return []


def get_command_patterns(top_n: int = 10) -> List[Dict]:
    """Get most frequent commands for proactive suggestions."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT command, frequency, last_used, success_rate
                FROM command_patterns
                ORDER BY frequency DESC
                LIMIT ?
            """, (top_n,))
            rows = c.fetchall()
            return [
                {
                    "command": r[0],
                    "frequency": r[1],
                    "last_used": r[2],
                    "success_rate": r[3]
                }
                for r in rows
            ]
    except Exception as e:
        print(f'[APEX MEMORY] Pattern retrieval error: {e}')
        return []


def learn_preference(category: str, key: str, value: str, confidence: float = 0.7):
    """Learn a user preference over time."""
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO user_preferences (category, key, value, confidence, learned_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(category, key) DO UPDATE SET
                    value = ?,
                    confidence = MIN(1.0, confidence + 0.1),
                    learned_at = ?
            """, (category, key, value, confidence, ts, value, ts))
            conn.commit()
    except Exception as e:
        print(f'[APEX MEMORY] Preference learning error: {e}')


def get_preferences(category: Optional[str] = None) -> List[Dict]:
    """Retrieve learned preferences."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            if category:
                c.execute("""
                    SELECT category, key, value, confidence
                    FROM user_preferences
                    WHERE category = ?
                    ORDER BY confidence DESC
                """, (category,))
            else:
                c.execute("""
                    SELECT category, key, value, confidence
                    FROM user_preferences
                    ORDER BY confidence DESC
                """)
            rows = c.fetchall()
            return [
                {
                    "category": r[0],
                    "key": r[1],
                    "value": r[2],
                    "confidence": r[3]
                }
                for r in rows
            ]
    except Exception as e:
        print(f'[APEX MEMORY] Preference retrieval error: {e}')
        return []


def analyze_user_behavior() -> Dict:
    """Analyze user behavior patterns for proactive intelligence."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            
            # Most active hour
            c.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM interactions
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 1
            """)
            peak_hour = c.fetchone()
            
            # Most common command type
            c.execute("""
                SELECT command_type, COUNT(*) as count
                FROM interactions
                GROUP BY command_type
                ORDER BY count DESC
                LIMIT 1
            """)
            common_cmd = c.fetchone()
            
            # Average interaction frequency per day
            c.execute("""
                SELECT COUNT(DISTINCT DATE(timestamp)) as days,
                       COUNT(*) as total
                FROM interactions
            """)
            freq = c.fetchone()
            
            return {
                "peak_hour": int(peak_hour[0]) if peak_hour else None,
                "most_common_command": common_cmd[0] if common_cmd else None,
                "daily_avg_interactions": round(freq[1] / max(freq[0], 1), 1) if freq else 0
            }
    except Exception as e:
        print(f'[APEX MEMORY] Behavior analysis error: {e}')
        return {}


# Initialize on import
init_memory_db()
