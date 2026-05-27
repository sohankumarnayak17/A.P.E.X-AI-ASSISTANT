import os
import sys
import threading
import time

# ── eel must be initialised before importing any @eel.expose modules ──
import eel
eel.init("front")

# ── Engine imports (decorators register after eel.init) ──────────────
from engine.command  import processQuery, takecommand, allcommand, getChatHistory, clearChatHistory
from engine.feature  import speak, playAssistantSound
from engine.security import start_clap_detection, start_wake_detection
from engine.config   import EEL_HOST, EEL_PORT

# ══════════════════════════════
#   STARTUP
# ══════════════════════════════
def _play_startup_sound():
    try:
        from playsound import playsound
        playsound(os.path.join("front", "assets", "audio", "radio.mp3"))
    except Exception as e:
        print(f"[APEX] Startup sound error: {e}")


def _greet():
    """Time-aware startup greeting."""
    hour = time.localtime().tm_hour
    if hour < 12:
        greeting = "Good morning, Boss. APEX is online and ready."
    elif hour < 17:
        greeting = "Good afternoon, Boss. APEX is at your service."
    else:
        greeting = "Good evening, Boss. APEX is ready when you are."
    speak(greeting)


# ══════════════════════════════
#   MAIN
# ══════════════════════════════
if __name__ == "__main__":
    print("=" * 48)
    print("  APEX — Advanced Personal EXecutive Assistant")
    print(f"  http://{EEL_HOST}:{EEL_PORT}")
    print("=" * 48)

    # Startup sound + greeting
    threading.Thread(target=_play_startup_sound, daemon=True).start()
    threading.Thread(target=_greet,              daemon=True).start()

    # Background listeners
    threading.Thread(target=start_clap_detection, daemon=True).start()
    threading.Thread(target=start_wake_detection, daemon=True).start()

    print("[APEX] Background listeners started — double-clap or say 'Hey APEX'.")

    # Launch eel (blocks until window is closed)
    try:
        eel.start(
            "index.html",
            mode    = "default",      # opens system default browser
            host    = EEL_HOST,
            port    = EEL_PORT,
            size    = (1280, 720),
            block   = True,
        )
    except KeyboardInterrupt:
        print("\n[APEX] KeyboardInterrupt — shutting down.")
        sys.exit(0)
    except Exception as e:
        print(f"[APEX] Server error: {e}")
        # Keep alive so background threads can still respond
        print("[APEX] Running in headless mode. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)