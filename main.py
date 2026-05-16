import os
import eel
import threading
from playsound import playsound
from engine.feature import *
from engine.command import *
from engine.security import start_clap_detection

eel.init("front")

# ── Play startup sound ──
playsound("front\\assets\\audio\\radio.mp3")

# ── Start clap detection in background ──
threading.Thread(target=start_clap_detection, daemon=True).start()

# ── Launch APEX ──
eel.start('index.html', mode='edge', host='localhost', port=5001, block=True)