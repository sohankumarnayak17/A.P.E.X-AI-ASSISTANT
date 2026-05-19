import pyaudio
import numpy as np
import threading
import time
import pyttsx3

# ══════════════════════════════
#   CLAP DETECTION CONFIG
# ══════════════════════════════
CLAP_THRESHOLD    = 2500
CLAP_COOLDOWN     = 1.5     # seconds before next clap registers
SAMPLE_RATE       = 44100
CHUNK             = 1024
DEVICE_INDEX      = 0

_last_clap_time   = 0
_clap_running     = False
_tts_lock         = threading.Lock()  # ← prevents "run loop already started"

# ══════════════════════════════
#   TTS — thread-safe wrapper
# ══════════════════════════════
_engine = None

def _init_tts():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init('sapi5')
        voices = _engine.getProperty('voices')
        _engine.setProperty('voice', voices[1].id)
        _engine.setProperty('rate', 175)
        _engine.setProperty('volume', 1.0)

def _fast_speak(text):
    with _tts_lock:  # ← only one thread speaks at a time
        try:
            _init_tts()
            _engine.say(text)
            _engine.runAndWait()
        except Exception as e:
            print('[APEX] fast_speak error: ' + str(e))

# ══════════════════════════════
#   CLAP DETECTED — OPEN UI
# ══════════════════════════════
def on_clap():
    print("[APEX] Clap detected! Opening UI...")
    threading.Thread(
        target=_fast_speak,
        args=("Yes Boss, APEX is online.",),
        daemon=True
    ).start()
    
    # Open browser to UI
    try:
        import webbrowser
        time.sleep(0.3)
        webbrowser.open("http://localhost:5001/index.html")
    except Exception as e:
        print("[APEX] UI open error: " + str(e))

# ══════════════════════════════
#   CLAP LISTENER LOOP
# ══════════════════════════════
def _clap_loop():
    global _last_clap_time

    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print("[APEX] Mic error: " + str(e))
        p.terminate()
        return

    print("[APEX] Clap detection ready.")

    while _clap_running:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_np).mean()
            now = time.time()

            if volume > CLAP_THRESHOLD and now - _last_clap_time > CLAP_COOLDOWN:
                _last_clap_time = now
                on_clap()

        except Exception as e:
            print("[APEX] Clap loop error: " + str(e))
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

# ══════════════════════════════
#   START
# ══════════════════════════════
def start_clap_detection():
    global _clap_running
    if _clap_running:
        return
    _clap_running = True
    threading.Thread(target=_clap_loop, daemon=True).start()

def stop_clap_detection():
    global _clap_running
    _clap_running = False
