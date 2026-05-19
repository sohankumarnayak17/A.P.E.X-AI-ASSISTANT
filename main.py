import os
import eel
import threading
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

# ── Start background threads ──
threading.Thread(target=start_clap_detection, daemon=True).start()
threading.Thread(target=hotkey, daemon=True).start()   # wake word listener

# ── Launch APEX UI ──
try:
    eel.start('index.html', mode='edge', host='localhost', port=5001, block=True)
except Exception as e:
    print(f"[APEX] eel.start error: {e}")