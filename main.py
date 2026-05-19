import os
import eel
import threading
import time
from playsound import playsound
from engine.feature import *
from engine.command import *
from engine.security import start_clap_detection

eel.init("front")

# ── Play startup sound ──
try:
    playsound("front\\assets\\audio\\radio.mp3")
except Exception as e:
    print(f"[APEX] Startup sound error: {e}")

# ── Start eel server silently (no browser on startup) ──
threading.Thread(
    target=lambda: eel.start(
        'index.html',
        mode=None,
        host='localhost',
        port=5001,
        block=False
    ),
    daemon=True
).start()

# ── Start both triggers ──
threading.Thread(target=start_clap_detection, daemon=True).start()  # trigger 1: clap
threading.Thread(target=hotkey, daemon=True).start()                 # trigger 2: say "Apex"

print("[APEX] Running in background — clap or say Apex to wake me up Boss.")
while True:
    time.sleep(1)