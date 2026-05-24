import os
import eel
import threading
import time

eel.init("front")

# ── Import engine modules ──
try:
    from engine.feature import hotkey
    from engine.security import start_clap_detection
    import engine.command  # registers all @eel.expose functions
    print("[APEX] Engine loaded successfully.")
except Exception as e:
    print(f"[APEX] Engine load error: {e}")
    print("[APEX] Check your API key and imports.")

# ── Play startup sound ──
try:
    from playsound import playsound
    playsound("front\\assets\\audio\\radio.mp3")
except Exception as e:
    print(f"[APEX] Startup sound error: {e}")

print("[APEX] Starting server on http://localhost:5001")

# ── Start wake word + hotkey in background ──
try:
    threading.Thread(target=start_clap_detection, daemon=True).start()
    threading.Thread(target=hotkey, daemon=True).start()
except Exception as e:
    print(f"[APEX] Background thread error: {e}")

print("[APEX] Running in background — say 'Hey APEX' to wake me up Boss.")

# ── Start eel server ──
try:
    eel.start(
        'index.html',
        mode     = 'edge',
        host     = 'localhost',
        port     = 5001,
        size     = (1280, 720),
        position = (100, 100),
        block    = True
    )
except OSError as e:
    print(f"[APEX] Port 5001 in use. Try killing it:")
    print(f"       netstat -ano | findstr :5001")
    print(f"       taskkill /PID <number> /F")
    while True:
        time.sleep(1)
except Exception as e:
    print(f"[APEX] Server error: {e}")
    while True:
        time.sleep(1)