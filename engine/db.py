import os
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
    """Create all tables and seed defaults."""
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
        _seed_web(conn)
        _seed_apps(conn)


# ─────────────────────────────
#   WEB DEFAULTS
# ─────────────────────────────
def _seed_web(conn):
    if conn.execute("SELECT COUNT(*) FROM web_command").fetchone()[0] > 0:
        return
    defaults = [
        ("youtube",       "https://www.youtube.com"),
        ("google",        "https://www.google.com"),
        ("github",        "https://www.github.com"),
        ("gmail",         "https://mail.google.com"),
        ("maps",          "https://maps.google.com"),
        ("reddit",        "https://www.reddit.com"),
        ("twitter",       "https://www.twitter.com"),
        ("instagram",     "https://www.instagram.com"),
        ("linkedin",      "https://www.linkedin.com"),
        ("whatsapp",      "https://web.whatsapp.com"),
        ("netflix",       "https://www.netflix.com"),
        ("spotify web",   "https://open.spotify.com"),
        ("wikipedia",     "https://www.wikipedia.org"),
        ("stackoverflow", "https://stackoverflow.com"),
        ("chatgpt",       "https://chat.openai.com"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO web_command (name, url) VALUES (?, ?)", defaults
    )
    conn.commit()
    print("[APEX DB] Web commands seeded.")


# ─────────────────────────────
#   APP DEFAULTS — auto-resolve real paths
# ─────────────────────────────
_APP_CANDIDATES = {
    # name : list of possible paths (first found wins)
    "spotify": [
        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe"),
        r"C:\Program Files\WindowsApps\SpotifyAB.SpotifyMusic_*\Spotify.exe",  # UWP glob
    ],
    "discord": [
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-*\Discord.exe"),
    ],
    "vscode": [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "notepad": [r"C:\Windows\System32\notepad.exe"],
    "calculator": [r"C:\Windows\System32\calc.exe"],
    "paint": [r"C:\Windows\System32\mspaint.exe"],
    "cmd": [r"C:\Windows\System32\cmd.exe"],
    "explorer": [r"C:\Windows\explorer.exe"],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
    ],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "task manager": [r"C:\Windows\System32\Taskmgr.exe"],
    "settings":     ["ms-settings:"],           # Windows Settings (URI)
    "whatsapp":     [
        os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\WhatsApp.exe"),
    ],
    "telegram": [
        os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Telegram Desktop\Telegram.exe"),
    ],
    "zoom": [
        os.path.expandvars(r"%APPDATA%\Zoom\bin\Zoom.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Zoom\bin\Zoom.exe"),
    ],
    "obs": [
        r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
        r"C:\Program Files (x86)\obs-studio\bin\32bit\obs32.exe",
    ],
}


def _resolve_path(candidates: list) -> str | None:
    """Return the first candidate path that actually exists on disk."""
    import glob
    for p in candidates:
        # Handle glob patterns (e.g. UWP apps with version in folder name)
        if "*" in p:
            matches = glob.glob(p)
            if matches:
                return matches[0]
        elif os.path.exists(p):
            return p
    return None


def _seed_apps(conn):
    if conn.execute("SELECT COUNT(*) FROM sys_command").fetchone()[0] > 0:
        return
    seeded = 0
    for name, candidates in _APP_CANDIDATES.items():
        path = _resolve_path(candidates)
        if path:
            conn.execute(
                "INSERT OR IGNORE INTO sys_command (name, path) VALUES (?, ?)",
                (name, path)
            )
            seeded += 1
    conn.commit()
    print(f"[APEX DB] {seeded} app(s) auto-detected and seeded.")


# ─────────────────────────────
#   SEARCH
# ─────────────────────────────
def searchDB(query: str):
    """
    Returns ('web', url) | ('app', path) | (None, None).
    Exact match first, then fuzzy LIKE.
    """
    query = query.strip().lower()
    if not query:
        return (None, None)
    try:
        with _get_conn() as conn:
            c = conn.cursor()

            # Exact
            c.execute("SELECT url  FROM web_command WHERE LOWER(name) = ?", (query,))
            row = c.fetchone()
            if row: return ("web", row[0])

            c.execute("SELECT path FROM sys_command WHERE LOWER(name) = ?", (query,))
            row = c.fetchone()
            if row: return ("app", row[0])

            # Fuzzy
            like = f"%{query}%"
            c.execute("SELECT url  FROM web_command WHERE LOWER(name) LIKE ?", (like,))
            row = c.fetchone()
            if row: return ("web", row[0])

            c.execute("SELECT path FROM sys_command WHERE LOWER(name) LIKE ?", (like,))
            row = c.fetchone()
            if row: return ("app", row[0])

    except Exception as e:
        print(f"[APEX DB] searchDB error: {e}")

    return (None, None)


# ─────────────────────────────
#   HELPERS — add at runtime
# ─────────────────────────────
def add_web_command(name: str, url: str) -> bool:
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


def list_apps() -> list:
    """Return all registered app commands — useful for debugging."""
    try:
        with _get_conn() as conn:
            rows = conn.execute("SELECT name, path FROM sys_command ORDER BY name").fetchall()
            return [{"name": r[0], "path": r[1]} for r in rows]
    except Exception as e:
        print(f"[APEX DB] list_apps error: {e}")
        return []


# Auto-init
init_db()