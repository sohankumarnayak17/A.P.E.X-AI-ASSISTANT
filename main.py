import os
import eel
import threading
from playsound import playsound

# ✅ Import command module AFTER eel.init so decorators register
eel.init("front")

# Now import — this lets @eel.expose decorators work
from engine.command import processQuery, takecommand, allcommand, getChatHistory, clearChatHistory
from engine.feature import hotkey, playAssistantSound
from engine.security import start_clap_detection

# Startup sound
try:
    playsound("front\\assets\\audio\\radio.mp3")
except Exception as e:
    print(f"[APEX] Startup sound error: {e}")

print("[APEX] Server starting on http://localhost:5001")

# Background triggers
threading.Thread(target=start_clap_detection, daemon=True).start()
threading.Thread(target=hotkey, daemon=True).start()

print("[APEX] Background listening active — clap or say 'Hey APEX'.")

# Start eel server (blocks)
try:
    eel.start(
        'index.html',
        mode='default',
        host='localhost',
        port=5001,
        size=(1280, 720),
        block=True
    )
except KeyboardInterrupt:
    print("\n[APEX] Shutting down...")
except Exception as e:
    print(f"[APEX] Server error: {e}")
    import time
    while True:
        time.sleep(1)