import sqlite3
from engine.config import DB_PATH

# ══════════════════════════════
#   APEX — Database Layer
# ══════════════════════════════

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables and seed default commands if empty."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS web_command (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                url   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sys_command (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT NOT NULL UNIQUE,
                path  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contacts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                mobile_number TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                sender    TEXT NOT NULL CHECK(sender IN ('user','apex')),
                message   TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
        """)
        conn.commit()
        _seed_defaults(conn)


def _seed_defaults(conn):
    """Insert default web commands if the table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM web_command").fetchone()[0]
    if count > 0:
        return
    defaults = [
        ("youtube",   "https://www.youtube.com"),
        ("google",    "https://www.google.com"),
        ("github",    "https://www.github.com"),
        ("gmail",     "https://mail.google.com"),
        ("maps",      "https://maps.google.com"),
        ("reddit",    "https://www.reddit.com"),
        ("twitter",   "https://www.twitter.com"),
        ("instagram", "https://www.instagram.com"),
        ("linkedin",  "https://www.linkedin.com"),
        ("whatsapp",  "https://web.whatsapp.com"),
        ("netflix",   "https://www.netflix.com"),
        ("spotify",   "https://open.spotify.com"),
        ("wikipedia", "https://www.wikipedia.org"),
        ("stackoverflow", "https://stackoverflow.com"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO web_command (name, url) VALUES (?, ?)", defaults
    )
    conn.commit()
    print("[APEX DB] Default web commands seeded.")


def searchDB(query: str):
    """
    Search web_command then sys_command.
    Returns ('web', url) | ('app', path) | (None, None)
    Tries exact match first, then fuzzy LIKE.
    """
    query = query.strip().lower()
    if not query:
        return (None, None)

    try:
        with _get_conn() as conn:
            c = conn.cursor()
            # Exact match
            c.execute("SELECT url FROM web_command WHERE LOWER(name) = ?", (query,))
            row = c.fetchone()
            if row:
                return ("web", row[0])

            c.execute("SELECT path FROM sys_command WHERE LOWER(name) = ?", (query,))
            row = c.fetchone()
            if row:
                return ("app", row[0])

            # Fuzzy match
            like = f"%{query}%"
            c.execute("SELECT url FROM web_command WHERE LOWER(name) LIKE ?", (like,))
            row = c.fetchone()
            if row:
                return ("web", row[0])

            c.execute("SELECT path FROM sys_command WHERE LOWER(name) LIKE ?", (like,))
            row = c.fetchone()
            if row:
                return ("app", row[0])

    except Exception as e:
        print(f"[APEX DB] searchDB error: {e}")

    return (None, None)


def add_web_command(name: str, url: str) -> bool:
    """Add or update a web command."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO web_command (name, url) VALUES (?, ?)",
                (name.lower().strip(), url.strip())
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[APEX DB] add_web_command error: {e}")
        return False


def add_sys_command(name: str, path: str) -> bool:
    """Add or update a system command."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sys_command (name, path) VALUES (?, ?)",
                (name.lower().strip(), path.strip())
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[APEX DB] add_sys_command error: {e}")
        return False


# Auto-init on import
init_db()