import speech_recognition as sr
import threading
import time
import pyttsx3
import eel

# ══════════════════════════════
#   WAKE WORDS
# ══════════════════════════════
WAKE_WORDS   = ['hey apex', 'wake up', 'apex wake up', 'hey a pex', 'apex']
DEVICE_INDEX = 0

_running = False

# ══════════════════════════════
#   FAST SPEAK — pre-initialized
# ══════════════════════════════
_engine = pyttsx3.init('sapi5')
_voices = _engine.getProperty('voices')
_engine.setProperty('voice',  _voices[1].id)
_engine.setProperty('rate',   175)
_engine.setProperty('volume', 1.0)

def _fast_speak(text):
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        print('[APEX] fast_speak error: ' + str(e))

# ══════════════════════════════
#   WAKE DETECTED
# ══════════════════════════════
def on_wake():
    print("[APEX] Wake word detected!")
    threading.Thread(
        target=_fast_speak,
        args=("I'm here Boss. What do you need?",),
        daemon=True
    ).start()
    try:
        eel.bringToFront()
    except Exception as e:
        print("[APEX] eel error: " + str(e))

# ══════════════════════════════
#   WAKE WORD LISTENER LOOP
# ══════════════════════════════
def _wake_loop():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold  = 0.5
    print("[APEX] Wake word detection active — say 'Hey APEX' to wake me up.")

    while _running:
        try:
            with sr.Microphone(device_index=DEVICE_INDEX) as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=4, phrase_time_limit=3)
            text = r.recognize_google(audio, language='en-in').lower()
            print('[APEX security] Heard: ' + text)
            if any(w in text for w in WAKE_WORDS):
                on_wake()
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print('[APEX] Wake loop error: ' + str(e))
            time.sleep(1)

# ══════════════════════════════
#   START / STOP
# ══════════════════════════════
def start_clap_detection():
    global _running
    if _running:
        return
    _running = True
    threading.Thread(target=_wake_loop, daemon=True).start()
    print("[APEX] Clap detection ready.")

def stop_clap_detection():
    global _running
    _running = False