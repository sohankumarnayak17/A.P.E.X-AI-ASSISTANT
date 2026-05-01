import sqlite3

conn = sqlite3.connect("APEX.db")
cursor = conn.cursor()

# ══════════════════════════════
#   SYSTEM APPS TABLE
# ══════════════════════════════
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_command (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE,
        path VARCHAR(500)
    )
""")

apps = [
    ('android studio',  r'C:\Program Files\Android\Android Studio\bin\studio64.exe'),
    ('vs code',         r'C:\Users\KIIT\AppData\Local\Programs\Microsoft VS Code\Code.exe'),
    ('notepad',         r'C:\Windows\System32\notepad.exe'),
    ('calculator',      r'C:\Windows\System32\calc.exe'),
    ('chrome',          r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
    ('file explorer',   r'C:\Windows\explorer.exe'),
    ('task manager',    r'C:\Windows\System32\Taskmgr.exe'),
    ('cmd',             r'C:\Windows\System32\cmd.exe'),
    ('spotify',         r'C:\Users\KIIT\AppData\Roaming\Spotify\Spotify.exe'),
    ('vlc',             r'C:\Program Files\VideoLAN\VLC\vlc.exe'),
    ('whatsapp',        r'C:\Users\KIIT\AppData\Local\WhatsApp\WhatsApp.exe'),
    ('discord',         r'C:\Users\KIIT\AppData\Local\Discord\Update.exe'),
    ('postman',         r'C:\Users\KIIT\AppData\Local\Postman\Postman.exe'),
    ('word',            r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE'),
    ('excel',           r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE'),
    ('powerpoint',      r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE'),
]

cursor.executemany(
    "INSERT OR IGNORE INTO sys_command (name, path) VALUES (?, ?)", apps
)

# ══════════════════════════════
#   WEB COMMANDS TABLE
# ══════════════════════════════
cursor.execute("""
    CREATE TABLE IF NOT EXISTS web_command (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE,
        url  VARCHAR(1000)
    )
""")

sites = [
    ('youtube',       'https://www.youtube.com'),
    ('google',        'https://www.google.com'),
    ('github',        'https://www.github.com'),
    ('gmail',         'https://mail.google.com'),
    ('instagram',     'https://www.instagram.com'),
    ('twitter',       'https://www.twitter.com'),
    ('whatsapp web',  'https://web.whatsapp.com'),
    ('netflix',       'https://www.netflix.com'),
    ('stackoverflow', 'https://www.stackoverflow.com'),
    ('chatgpt',       'https://www.chatgpt.com'),
    ('linkedin',      'https://www.linkedin.com'),
    ('reddit',        'https://www.reddit.com'),
    ('amazon',        'https://www.amazon.in'),
    ('maps',          'https://maps.google.com'),
    ('translate',     'https://translate.google.com'),
    ('leetcode',      'https://www.leetcode.com'),
]

cursor.executemany(
    "INSERT OR IGNORE INTO web_command (name, url) VALUES (?, ?)", sites
)

# ══════════════════════════════
#   CONTACTS TABLE
# ══════════════════════════════
cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          VARCHAR(100) UNIQUE,
        mobile_number VARCHAR(20),
        email         VARCHAR(225)
    )
""")

conn.commit()
conn.close()
print("[APEX] Database ready — sys_command, web_command and contacts tables loaded.")
