import pyaudio
import numpy as np
import threading
import time
import pyttsx3
import eel

# ══════════════════════════════
#   CLAP DETECTION CONFIG
# ══════════════════════════════
CLAP_THRESHOLD  = 50      # tuned for your mic
CLAP_COOLDOWN   = 2.0     # seconds before next clap registers
SAMPLE_RATE     = 44100
CHUNK           = 1024
DEVICE_INDEX    = 0       # Microsoft Sound Mapper — your working mic

_last_clap_time = 0
_clap_running   = False

# ══════════════════════════════
#   PRE-INIT TTS — instant speak
#   No delay on clap response
# ══════════════════════════════
_engine = pyttsx3.init('sapi5')
_voices = _engine.getProperty('voices')
_engine.setProperty('voice',  _voices[1].id)  # Zira
_engine.setProperty('rate',   175)             # slightly faster
_engine.setProperty('volume', 1.0)

def _fast_speak(text):
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        print('[APEX] fast_speak error: ' + str(e))

# ══════════════════════════════
#   CLAP DETECTED — ACTION
# ══════════════════════════════
def on_clap():
    print("[APEX] Clap detected!")
    threading.Thread(
        target=_fast_speak,
        args=("Welcome back Boss. APEX is online and ready.",),
        daemon=True
    ).start()
    try:
        eel.bringToFront()
    except Exception as e:
        print("[APEX] eel error: " + str(e))

# ══════════════════════════════
#   CLAP LISTENER LOOP
# ══════════════════════════════
def _clap_loop():
    global _last_clap_time

    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format             = pyaudio.paInt16,
            channels           = 1,
            rate               = SAMPLE_RATE,
            input              = True,
            input_device_index = DEVICE_INDEX,
            frames_per_buffer  = CHUNK
        )
    except Exception as e:
        print("[APEX] Mic open error: " + str(e))
        p.terminate()
        return

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
    threading.Thread(target=_clap_loop, daemon=True).start()

def stop_clap_detection():
    global _clap_running
    _clap_running = False
    print("[APEX] Clap detection stopped.")