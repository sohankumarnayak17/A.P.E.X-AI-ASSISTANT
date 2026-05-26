import re
import os
import time
import subprocess
import sqlite3
import webbrowser
import threading
import pyautogui as autogui
import eel
import pyttsx3
from groq import Groq
from playsound import playsound
from urllib.parse import quote
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term

DB_PATH = r"C:\Users\KIIT\OneDrive\Desktop\APEX\APEX.db"

# ------------------------------
#   SINGLE PYTTSX3 ENGINE
#   Thread-safe, non-blocking
# ------------------------------
_tts_lock   = threading.Lock()
_tts_engine = None

def _get_tts():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init('sapi5')
        voices = _tts_engine.getProperty('voices')
        _tts_engine.setProperty('voice',  voices[1].id)
        _tts_engine.setProperty('rate',   185)   # faster rate
        _tts_engine.setProperty('volume', 1.0)
    return _tts_engine

def speak(text):
    """Non-blocking speak — runs in background thread"""
    def _speak():
        try:
            text_clean = re.sub(r'\*+', '', str(text))
            text_clean = re.sub(r'#+\s?', '', text_clean)
            text_clean = re.sub(r'`+',   '', text_clean)
            text_clean = re.sub(r'\n+',  ' ', text_clean).strip()
            if not text_clean:
                return
            print('[APEX speaks] ' + text_clean)
            with _tts_lock:
                engine = _get_tts()
                engine.say(text_clean)
                engine.runAndWait()
        except Exception as e:
            print('[APEX] speak error: ' + str(e))
    threading.Thread(target=_speak, daemon=True).start()

def speak_wait(text):
    """Blocking speak — use when you need to wait"""
    try:
        text_clean = re.sub(r'\*+', '', str(text))
        text_clean = re.sub(r'#+\s?', '', text_clean)
        text_clean = re.sub(r'`+',   '', text_clean)
        text_clean = re.sub(r'\n+',  ' ', text_clean).strip()
        if not text_clean:
            return
        print('[APEX speaks] ' + text_clean)
        with _tts_lock:
            engine = _get_tts()
            engine.say(text_clean)
            engine.runAndWait()
    except Exception as e:
        print('[APEX] speak error: ' + str(e))

# ------------------------------
#   GROQ — fast setup
# ------------------------------
_groq = None
try:
    _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("[APEX] Groq connected.")
except Exception as e:
    print(f"[APEX] Groq error: {e}")

_system_prompt = (
    "You are APEX, an advanced AI assistant like FRIDAY from Iron Man. "
    "Be sharp and concise. Max 1-2 sentences. "
    "Call the user Boss. No markdown, no formatting. Plain text only."
)

# ------------------------------
#   PLAY SOUND
# ------------------------------
@eel.expose
def playAssistantSound():
    try:
        threading.Thread(
            target=playsound,
            args=("front\\assets\\audio\\radio.mp3",),
            daemon=True
        ).start()
    except Exception as e:
        print('[APEX] sound error: ' + str(e))

# ------------------------------
#   OPEN COMMAND
# ------------------------------
def opencommand(query):
    from engine.db import searchDB
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").strip().lower()
    if not query:
        speak('What would you like me to open, Boss?')
        return
    kind, value = searchDB(query)
    if kind == 'web':
        speak('Opening ' + query + ', Boss.')
        webbrowser.open(value)
    elif kind == 'app':
        speak('Launching ' + query + ', Boss.')
        subprocess.Popen(value)
    else:
        speak("Couldn't find " + query + " Boss.")

# ------------------------------
#   PLAY YOUTUBE
# ------------------------------
def playyoutube(query):
    search_term = extract_yt_term(query)
    if not search_term:
        search_term = (query
                       .replace("play", "")
                       .replace("on youtube", "")
                       .replace("youtube", "")
                       .strip())
    if search_term:
        speak("Playing " + search_term + " on YouTube, Boss.")
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote(search_term))
    else:
        speak("Sorry Boss, what should I play?")

# ------------------------------
#   HOTKEY — speech wake word
# ------------------------------
def hotkey():
    import speech_recognition as sr
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold  = 0.5
    print('[APEX] Wake word listening — say "hey apex"...')
    while True:
        try:
            with sr.Microphone(device_index=0) as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
            text = r.recognize_google(audio, language='en-in').lower()
            print('[APEX] Heard: ' + text)
            if any(w in text for w in ['hey apex', 'wake up', 'apex wake', 'apex']):
                print('[APEX] Wake word detected!')
                speak("I'm here Boss.")
                try:
                    eel.bringToFront()
                except:
                    pass
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print('[APEX] Hotkey error: ' + str(e))
            time.sleep(1)

# ------------------------------
#   FIND CONTACT
# ------------------------------
def findcontact(query: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT name, mobile_number FROM contacts")
            rows = c.fetchall()
            for name, mobile_number in rows:
                if name.lower() in query.lower():
                    return (mobile_number, name)
    except Exception as e:
        print("[APEX] findcontact error: " + str(e))
    return (0, '')

# ------------------------------
#   WHATSAPP
# ------------------------------
def whatsapp(mobile_no, message, flag, name):
    if not mobile_no:
        speak("Couldn't find that contact, Boss.")
        return
    if flag == "message":
        apex_message = "Message sent, Boss."
    elif flag == "call":
        message      = ""
        apex_message = "Calling " + name + ", Boss."
    else:
        message      = ""
        apex_message = "Video calling " + name + ", Boss."
    try:
        encoded = quote(message)
        url     = f"whatsapp://send?phone={mobile_no}&text={encoded}"
        subprocess.run(f"start {url}", shell=True)
        time.sleep(5)
        if flag == "message":
            autogui.hotkey("enter")
        elif flag == "call":
            autogui.hotkey("ctrl", "shift", "p")
        else:
            autogui.hotkey("ctrl", "shift", "v")
        speak(apex_message)
    except Exception as e:
        print("[APEX] WhatsApp error: " + str(e))
        speak("WhatsApp failed Boss.")

# ------------------------------
#   CHATBOT — Groq fast
# ------------------------------
def chatbot(query):
    if _groq is None:
        msg = "AI brain offline Boss. Check the API key."
        speak(msg)
        return msg
    try:
        response = _groq.chat.completions.create(
            model       = "llama-3.1-8b-instant",
            messages    = [
                {"role": "system", "content": _system_prompt},
                {"role": "user",   "content": query.strip()}
            ],
            max_tokens  = 100,   # faster — shorter responses
            temperature = 0.6,
        )
        reply = response.choices[0].message.content.strip()
        reply = re.sub(r'[\*\#\`]+', '', reply)
        reply = re.sub(r'\n+', ' ', reply).strip()
        print("[APEX] " + reply)
        speak(reply)
        return reply
    except Exception as e:
        print("[APEX ERROR] " + str(e))
        msg = "Sorry Boss, something went wrong."
        speak(msg)
        return msg
