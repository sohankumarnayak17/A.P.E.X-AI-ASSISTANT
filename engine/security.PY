import threading
import time
import numpy as np
import pyaudio
import speech_recognition as sr
import eel

from engine.config import (
    WAKE_WORDS, MIC_DEVICE,
    CLAP_THRESHOLD, CLAP_GAP, CLAP_COOLDOWN
)

# ══════════════════════════════
#   APEX — Security & Wake Detection
#   Two modes:
#     1. Double-clap  → wake APEX
#     2. "Hey APEX"   → wake APEX  (runs in feature.hotkey)
# ══════════════════════════════

_clap_running = False
_wake_running = False

# ─────────────────────────────
#   Shared wake action
# ─────────────────────────────
def _on_wake(source: str = ""):
    from engine.feature import speak
    print(f"[APEX SECURITY] Wake triggered by: {source}")
    threading.Thread(target=speak, args=("I'm here, Boss.",), daemon=True).start()
    try:
        eel.bringToFront()
    except Exception:
        pass


# ══════════════════════════════
#   CLAP DETECTION
# ══════════════════════════════
def _clap_loop():
    p      = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024
    )
    last_clap    = 0.0
    last_trigger = 0.0
    print("[APEX SECURITY] Clap detection active.")

    while _clap_running:
        try:
            data = stream.read(1024, exception_on_overflow=False)
            peak = np.abs(np.frombuffer(data, dtype=np.int16)).max()
            now  = time.time()

            if peak > CLAP_THRESHOLD:
                # Still in cooldown after last trigger
                if now - last_trigger < CLAP_COOLDOWN:
                    continue

                if now - last_clap < CLAP_GAP:
                    # ── Second clap: fire ──
                    print("[APEX SECURITY] Double-clap detected!")
                    last_trigger = now
                    last_clap    = 0.0
                    threading.Thread(
                        target=_on_wake, args=("double-clap",), daemon=True
                    ).start()
                else:
                    # ── First clap: start window ──
                    last_clap = now

        except Exception as e:
            print(f"[APEX SECURITY] Clap error: {e}")
            time.sleep(0.5)

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("[APEX SECURITY] Clap detection stopped.")


def start_clap_detection():
    global _clap_running
    if _clap_running:
        return
    _clap_running = True
    threading.Thread(target=_clap_loop, daemon=True).start()


def stop_clap_detection():
    global _clap_running
    _clap_running = False


# ══════════════════════════════
#   VOICE WAKE WORD DETECTION
#   Separate from feature.hotkey so both can run together
# ══════════════════════════════
def _wake_loop():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold  = 0.5
    print("[APEX SECURITY] Voice wake-word listener active.")

    while _wake_running:
        try:
            with sr.Microphone(device_index=MIC_DEVICE) as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=4, phrase_time_limit=3)
            text = r.recognize_google(audio, language="en-in").lower()
            print(f"[APEX SECURITY] Heard: {text}")
            if any(w in text for w in WAKE_WORDS):
                _on_wake("voice")
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"[APEX SECURITY] Wake loop error: {e}")
            time.sleep(1)

    print("[APEX SECURITY] Voice wake-word stopped.")


def start_wake_detection():
    global _wake_running
    if _wake_running:
        return
    _wake_running = True
    threading.Thread(target=_wake_loop, daemon=True).start()


def stop_wake_detection():
    global _wake_running
    _wake_running = False