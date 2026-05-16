import pyaudio
import numpy as np
import threading
import time
import eel
from engine.command import speak

# ══════════════════════════════
#   CLAP DETECTION CONFIG
# ══════════════════════════════
CLAP_THRESHOLD   = 2500   # volume level to trigger — raise if too sensitive
CLAP_COOLDOWN    = 2.0    # seconds before next clap registers
SAMPLE_RATE      = 44100
CHUNK            = 1024

_last_clap_time  = 0
_clap_running    = False


# ══════════════════════════════
#   CLAP DETECTED — ACTION
# ══════════════════════════════
def on_clap():
    print("[APEX] Clap detected — waking up!")
    speak("Welcome back Boss. APEX is online and ready.")
    try:
        eel.bringToFront()   # brings Electron window to foreground
    except Exception as e:
        print("[APEX] eel.bringToFront error: " + str(e))


# ══════════════════════════════
#   CLAP LISTENER LOOP
# ══════════════════════════════
def _clap_loop():
    global _last_clap_time

    p      = pyaudio.PyAudio()
    stream = p.open(
        format            = pyaudio.paInt16,
        channels          = 1,
        rate              = SAMPLE_RATE,
        input             = True,
        frames_per_buffer = CHUNK
    )

    print("[APEX] Clap detection active — clap to wake me up Boss.")

    while _clap_running:
        try:
            data     = stream.read(CHUNK, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16)
            volume   = np.abs(audio_np).mean()

            if volume > CLAP_THRESHOLD:
                now = time.time()
                if now - _last_clap_time > CLAP_COOLDOWN:
                    _last_clap_time = now
                    on_clap()

        except Exception as e:
            print("[APEX] Clap loop error: " + str(e))
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("[APEX] Clap detection stopped.")


# ══════════════════════════════
#   START / STOP
# ══════════════════════════════
def start_clap_detection():
    global _clap_running
    if _clap_running:
        print("[APEX] Clap detection already running.")
        return
    _clap_running = True
    t = threading.Thread(target=_clap_loop, daemon=True)
    t.start()


def stop_clap_detection():
    global _clap_running
    _clap_running = False
    print("[APEX] Clap detection stopped.")