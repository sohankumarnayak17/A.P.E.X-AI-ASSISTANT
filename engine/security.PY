import pyaudio
import numpy as np
import threading
import time
import pyttsx3
import eel

# ══════════════════════════════
#   CLAP DETECTION CONFIG
# ══════════════════════════════
CLAP_THRESHOLD    = 2500    # raised — filters out ambient noise & breathing
CLAP_COOLDOWN     = 2.0     # seconds before next clap registers
DOUBLE_CLAP_GAP   = 0.6     # max seconds between two claps to count as double
SAMPLE_RATE       = 44100
CHUNK             = 1024
DEVICE_INDEX      = 0       # Microsoft Sound Mapper

_last_clap_time   = 0
_pending_clap     = False   # waiting to see if a second clap follows
_clap_running     = False

# ══════════════════════════════
#   PRE-INIT TTS — instant speak
# ══════════════════════════════
_engine = pyttsx3.init('sapi5')
_voices = _engine.getProperty('voices')
_engine.setProperty('voice',  _voices[1].id)  # Zira
_engine.setProperty('rate',   175)
_engine.setProperty('volume', 1.0)

def _fast_speak(text):
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        print('[APEX] fast_speak error: ' + str(e))

# ══════════════════════════════
#   CLAP DETECTED — ACTION
#   Only fires on a confirmed double-clap
# ══════════════════════════════
def on_clap():
    print("[APEX] Double clap confirmed!")
    threading.Thread(
        target=_fast_speak,
        args=("Yes Boss, APEX is online and ready.",),
        daemon=True
    ).start()
    try:
        # Open the UI window on clap
        import subprocess
        subprocess.Popen(
            ["cmd", "/c", "start", "msedge", "http://localhost:5001/index.html"],
            shell=False
        )
    except Exception as e:
        print("[APEX] open UI error: " + str(e))

# ══════════════════════════════
#   CLAP LISTENER LOOP
# ══════════════════════════════
def _clap_loop():
    global _last_clap_time, _pending_clap

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

    print("[APEX] Clap detection active — double clap to wake me up Boss.")

    while _clap_running:
        try:
            data     = stream.read(CHUNK, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16)
            volume   = np.abs(audio_np).mean()

            now = time.time()

            if volume > CLAP_THRESHOLD:
                if now - _last_clap_time > CLAP_COOLDOWN:
                    # First clap — start waiting for second
                    if not _pending_clap:
                        _pending_clap   = True
                        _last_clap_time = now
                        print("[APEX] First clap — waiting for second...")
                    # Second clap within gap window — fire!
                    elif now - _last_clap_time <= DOUBLE_CLAP_GAP:
                        _pending_clap   = False
                        _last_clap_time = now
                        on_clap()

            # Pending clap timed out — reset
            if _pending_clap and (now - _last_clap_time > DOUBLE_CLAP_GAP):
                _pending_clap = False

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