import os
import sys
import threading
import time

# ── eel must be initialised before importing any @eel.expose modules ──
import eel
eel.init("front")

# ── Engine imports (decorators register after eel.init) ───────────────
from engine.command  import processQuery, takecommand, allcommand, getChatHistory, clearChatHistory
from engine.feature  import speak, playAssistantSound
from engine.security import start_clap_detection, start_wake_detection
from engine.config   import EEL_HOST, EEL_PORT

# ══════════════════════════════
#   STARTUP HELPERS
# ══════════════════════════════
def _play_startup_sound():
    try:
        from playsound import playsound
        playsound(os.path.join("front", "assets", "audio", "radio.mp3"))
    except Exception as e:
        print(f"[APEX] Startup sound error: {e}")


def _greet():
    hour = time.localtime().tm_hour
    if   hour < 12: msg = "Good morning Boss, APEX is online and ready."
    elif hour < 17: msg = "Good afternoon Boss, APEX is at your service."
    else:           msg = "Good evening Boss, APEX is ready when you are."
    speak(msg)


# ══════════════════════════════
#   DESKTOP WINDOW SELECTOR
#   Priority: Chrome app-mode → Edge app-mode → fallback browser tab
# ══════════════════════════════
def _get_mode():
    """
    Return (mode, cmdline_args) that opens a borderless desktop window.
    eel supports 'chrome', 'edge', 'chromium', 'custom', or 'default'.
    """
    import shutil

    # Chrome — preferred (app mode = no address bar, looks native)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in chrome_paths:
        if os.path.exists(p):
            print("[APEX] Using Chrome desktop window.")
            return "chrome", []

    # Edge — fallback app-mode window
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in edge_paths:
        if os.path.exists(p):
            print("[APEX] Using Edge desktop window.")
            return "edge", []

    # Nothing found — open in default browser (visible tab)
    print("[APEX] No Chrome/Edge found — opening in default browser.")
    return "default", []


# ══════════════════════════════
#   MAIN
# ══════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print("  APEX — Advanced Personal EXecutive Assistant")
    print(f"  Running on http://{EEL_HOST}:{EEL_PORT}")
    print("=" * 50)

    # Background threads
    threading.Thread(target=_play_startup_sound, daemon=True).start()
    threading.Thread(target=_greet,              daemon=True).start()
    threading.Thread(target=start_clap_detection, daemon=True).start()
    threading.Thread(target=start_wake_detection, daemon=True).start()

    print("[APEX] Background listeners active — double-clap or say 'Hey APEX'.")

    mode, _ = _get_mode()

    try:
        eel.start(
            "index.html",
            mode    = mode,
            host    = EEL_HOST,
            port    = EEL_PORT,
            size    = (1280, 720),
            position= (100, 50),       # where the window appears on screen
            block   = True,
        )
    except KeyboardInterrupt:
        print("\n[APEX] Shutting down.")
        sys.exit(0)
    except Exception as e:
        print(f"[APEX] Window error: {e}")
        print("[APEX] Headless mode active. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)