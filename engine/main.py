import os
import eel
import threading
import time
from playsound import playsound
from engine.command import hotkey
from engine.security import start_clap_detection

eel.init("front")

# ── Play startup sound ──
try:
    playsound("front\\assets\\audio\\radio.mp3")
except Exception as e:
    print(f"[APEX] Startup sound error: {e}")

print("[APEX] Starting server on http://localhost:5001")

# ── Start both triggers in background ──
threading.Thread(target=start_clap_detection, daemon=True).start()
threading.Thread(target=hotkey, daemon=True).start()

print("[APEX] Running in background — clap or say 'Apex' to wake me up Boss.")

# ── Start eel server (blocks main thread) ──
try:
    eel.start(
        'index.html',
        mode='default',      # opens browser automatically
        host='localhost',
        port=5001,
        size=(1280, 720),
        position=(100, 100),
        block=True           # keeps server alive
    )
except Exception as e:
    print(f"[APEX] Server error: {e}")
    # Fallback: keep running even if eel fails
    while True:
        time.sleep(1)
