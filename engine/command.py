import contextlib
import re
import os
import json
import struct
import time
import hashlib
import threading
import datetime
import subprocess
import sqlite3
import webbrowser
import pyaudio
import pvporcupine
import pyautogui as autogui
import eel
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from playsound import playsound
from urllib.parse import quote
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term
from engine.db import searchDB

# ── Screen awareness deps ──────────────────────────────────
# pip install mss pillow pytesseract
try:
    import mss
    import pytesseract
    from PIL import Image
    import os as _os
    # Force tesseract path — bypasses PATH lookup entirely
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    _os.environ["PATH"] = _os.environ.get("PATH", "") + r";C:\Program Files\Tesseract-OCR"
    SCREEN_AWARE = True
except ImportError:
    SCREEN_AWARE = False
    print("[APEX] Screen awareness disabled — pip install mss pillow pytesseract to enable.")

# ── Force load .env from project root ─────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DB_PATH = r"C:\Users\KIIT\OneDrive\Desktop\APEX\APEX.db"


# ══════════════════════════════
#   GROQ SETUP
# ══════════════════════════════
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")   # ← store in .env, not here
_groq = Groq(api_key=GROQ_API_KEY)

_system_prompt = (
    "You are APEX, an advanced AI personal assistant. "
    "Speak naturally like FRIDAY from Iron Man — sharp, confident, slightly witty. "
    "Keep responses under 3 sentences unless asked for detail. "
    "Always address the user as Boss. "
    "NEVER use markdown, bullet points, asterisks, or any special formatting. "
    "Plain text only."
)

# Separate prompt used only for task decomposition calls
_decompose_prompt = (
    "You are a task planner for APEX, a desktop AI assistant. "
    "Given a complex user request, break it into a JSON array of simple atomic steps. "
    "Each step must be a plain English command APEX can execute on its own. "
    "Return ONLY a raw JSON array of strings — no preamble, no markdown, no extra text. "
    'Example input:  "Open YouTube then send Riya a WhatsApp saying I am studying" '
    'Example output: ["open youtube", "whatsapp message Riya I am studying"]'
)


# ══════════════════════════════
#   PYTTSX3 — init once only
# ══════════════════════════════
import pyttsx3 as _tts

_engine = _tts.init('sapi5')
_voices = _engine.getProperty('voices')
_engine.setProperty('voice',  _voices[1].id)   # Zira — FRIDAY-like
_engine.setProperty('rate',   165)
_engine.setProperty('volume', 1.0)


# ══════════════════════════════════════════════════════════
#   PHASE 2 ❶ — CONTEXT MEMORY
#   SQLite-backed conversation history.
#   Lighter than ChromaDB — no vector server, no extra deps.
# ══════════════════════════════════════════════════════════

def _init_memory_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                role      TEXT    NOT NULL,
                content   TEXT    NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS screen_context (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT    NOT NULL,
                ocr_text  TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_patterns (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                hour   INTEGER NOT NULL,
                action TEXT    NOT NULL,
                count  INTEGER DEFAULT 1,
                UNIQUE(hour, action)
            )
        """)
        conn.commit()

_init_memory_db()

MEMORY_WINDOW = 10   # how many past turns to send to the LLM

def save_turn(role: str, content: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO conversation_history (role, content) VALUES (?, ?)",
            (role, content.strip())
        )
        conn.commit()

def load_recent_turns(n: int = MEMORY_WINDOW) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversation_history "
            "ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def clear_memory():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM conversation_history")
        conn.commit()
    speak("Memory cleared, Boss. Fresh start.")


# ══════════════════════════════════════════════════════════
#   PHASE 2 ❷ — TASK DECOMPOSITION
#   Multi-step command planning via a second Groq call.
#   Faster + simpler than LangChain agents.
# ══════════════════════════════════════════════════════════

# Words that signal a multi-step intent
_MULTI_STEP_MARKERS = [
    "then", "after that", "also", "and then",
    "followed by", "next", "afterwards", "finally", "lastly"
]

def is_complex_query(query: str) -> bool:
    q = query.lower()
    return any(m in q for m in _MULTI_STEP_MARKERS)

def decompose_task(query: str) -> list[str]:
    """
    Ask Groq to split a complex query into atomic steps.
    Returns a list of step strings, or [query] on failure.
    """
    try:
        response = _groq.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _decompose_prompt},
                {"role": "user",   "content": query.strip()}
            ],
            max_tokens=300,
            temperature=0.2,    # low = deterministic plan
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```[a-z]*", "", raw).replace("```", "").strip()
        steps = json.loads(raw)
        if isinstance(steps, list) and steps:
            print(f"[APEX] Decomposed → {steps}")
            return [str(s).strip() for s in steps]
    except Exception as e:
        print(f"[APEX] decompose_task error: {e}")
    return [query]


# ══════════════════════════════════════════════════════════
#   PHASE 2 ❸ — SCREEN AWARENESS
#   Screenshot + OCR every 5 s, hash-based change detection.
#   Only writes to DB when screen content actually changes.
# ══════════════════════════════════════════════════════════

_last_screen_hash: str = ""
_screen_ocr_text:  str = ""     # injected into chatbot calls

def _capture_screen() -> str:
    if not SCREEN_AWARE:
        return ""
    try:
        with mss.mss() as sct:
            raw = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        return pytesseract.image_to_string(img, config="--psm 3").strip()
    except Exception as e:
        print(f"[APEX] screen capture error: {e}")
        return ""

def _screen_watcher():
    global _last_screen_hash, _screen_ocr_text
    while True:
        time.sleep(5)
        text = _capture_screen()
        if not text:
            continue
        h = hashlib.md5(text.encode()).hexdigest()
        if h != _last_screen_hash:
            _last_screen_hash = h
            _screen_ocr_text  = text
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO screen_context (text_hash, ocr_text) VALUES (?, ?)",
                    (h, text[:2000])
                )
                conn.commit()

if SCREEN_AWARE:
    threading.Thread(target=_screen_watcher, daemon=True).start()
    print("[APEX] Screen awareness active.")


# ══════════════════════════════════════════════════════════
#   PHASE 2 ❹ — PROACTIVE SUGGESTIONS
#   Time-of-day heuristics + learned usage patterns.
#   No TRIBE framework needed — simple count-based scoring.
# ══════════════════════════════════════════════════════════

_DEFAULT_SUGGESTIONS = {
    range(6,  10): "Good morning Boss. Want me to pull up the news and your calendar?",
    range(12, 14): "Lunchtime Boss. Want some lo-fi to go with that?",
    range(17, 20): "Evening wind-down Boss. Music or a productivity recap?",
    range(22, 24): "Late night Boss. Anything you need before you wrap up?",
}

def _log_usage(action: str):
    hour = datetime.datetime.now().hour
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO usage_patterns (hour, action, count) VALUES (?, ?, 1) "
            "ON CONFLICT(hour, action) DO UPDATE SET count = count + 1",
            (hour, action)
        )
        conn.commit()

def get_proactive_suggestion() -> str:
    hour = datetime.datetime.now().hour
    # Learned pattern wins if seen ≥ 3 times at this hour
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT action, count FROM usage_patterns "
            "WHERE hour = ? ORDER BY count DESC LIMIT 1", (hour,)
        ).fetchone()
    if row and row[1] >= 3:
        return f"Based on your habits Boss, want me to {row[0]}?"
    # Fall back to time-of-day defaults
    for time_range, msg in _DEFAULT_SUGGESTIONS.items():
        if hour in time_range:
            return msg
    return ""

def maybe_suggest():
    suggestion = get_proactive_suggestion()
    if suggestion:
        speak(suggestion)


# ══════════════════════════════
#   PLAY SOUND
# ══════════════════════════════
def playAssistantSound():
    music_dir = "front\\assets\\audio\\radio.mp3"
    playsound(music_dir)


# ══════════════════════════════
#   SPEAK
# ══════════════════════════════
def speak(text):
    try:
        text = re.sub(r'\*+', '', str(text))
        text = re.sub(r'#+\s?', '', text)
        text = re.sub(r'`+',   '', text)
        text = re.sub(r'\n+',  ' ', text).strip()
        print('[APEX speaks] ' + text)
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        print('[APEX] speak error: ' + str(e))


# ══════════════════════════════
#   OPEN COMMAND
# ══════════════════════════════
def opencommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "").strip().lower()
    print('[APEX] Trying to open: ' + query)
    _log_usage(f"open {query}")                 # ← track usage pattern

    if not query:
        speak('What would you like me to open, Boss?')
        return

    kind, value = searchDB(query)
    if kind == 'web':
        speak('Opening ' + query + ', Boss.')
        webbrowser.open(value)
    elif kind == 'app':
        speak('Launching ' + query + ' for you, Boss.')
        subprocess.Popen(value)
    else:
        speak("I couldn't find " + query + " in my database, Boss.")


# ══════════════════════════════
#   PLAY YOUTUBE
# ══════════════════════════════
def playyoutube(query):
    search_term = extract_yt_term(query)
    if not search_term:
        search_term = (query
                       .replace("play", "")
                       .replace("on youtube", "")
                       .replace("youtube", "")
                       .strip())
    if search_term:
        _log_usage("play music")                # ← track usage pattern
        speak("Playing " + search_term + " on YouTube, Boss.")
        url = "https://www.youtube.com/results?search_query=" + quote(search_term)
        webbrowser.open(url)
    else:
        speak("Sorry Boss, I couldn't figure out what to play.")


# ══════════════════════════════
#   HOTKEY — Wake word
#   SpeechRecognition-based — detects "apex", "hey apex", "wake up apex"
#   pip install SpeechRecognition
# ══════════════════════════════
def hotkey():
    try:
        import speech_recognition as sr
    except ImportError:
        print("[APEX] Install SpeechRecognition: pip install SpeechRecognition")
        return

    r = sr.Recognizer()
    r.energy_threshold = 2000
    r.dynamic_energy_threshold = True
    mic = sr.Microphone(device_index=1)

    print("[APEX] Wake word listening for apex...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)

    while True:
        try:
            with mic as source:
                audio = r.listen(source, timeout=5, phrase_time_limit=4)
            text = r.recognize_google(audio).lower().strip()
            print("[APEX] Heard: " + text)
            triggers = ["apex", "hey apex", "wake up apex", "wake apex"]
            if any(w in text for w in triggers):
                print("[APEX] Wake word detected!")
                maybe_suggest()
                speak("Yes Boss, I am listening.")
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print("[APEX] STT error: " + str(e))
            time.sleep(2)
        except Exception as e:
            print("[APEX] Hotkey error: " + str(e))
            time.sleep(1)
# ══════════════════════════════
#   FIND CONTACT
# ══════════════════════════════
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


# ══════════════════════════════
#   WHATSAPP
# ══════════════════════════════
def whatsapp(mobile_no, message, flag, name):
    if not mobile_no:
        speak("I couldn't find that contact, Boss.")
        return

    if flag == "message":
        apex_message = "Message sent successfully, Boss."
    elif flag == "call":
        message      = ""
        apex_message = "Calling " + name + ", Boss."
    else:
        message      = ""
        apex_message = "Starting video call with " + name + ", Boss."

    encoded_message = quote(message)
    whatsapp_url    = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    try:
        subprocess.run(f"start {whatsapp_url}", shell=True)
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
        speak("Something went wrong with WhatsApp, Boss.")


# ══════════════════════════════════════════════════════════
#   CHATBOT — Groq LLaMA3  (Phase 2 upgraded)
#   Injects: conversation history + live screen context
# ══════════════════════════════════════════════════════════

def chatbot(query: str) -> str:
    try:
        messages = [{"role": "system", "content": _system_prompt}]

        # Inject screen context if there's something on screen worth noting
        if _screen_ocr_text:
            messages.append({
                "role": "system",
                "content": "Current screen content (for context only): " + _screen_ocr_text[:500]
            })

        # Inject last N conversation turns
        messages.extend(load_recent_turns())

        # Current query
        messages.append({"role": "user", "content": query.strip()})

        response = _groq.chat.completions.create(
            model       = "llama-3.1-8b-instant",
            messages    = messages,
            max_tokens  = 300,
            temperature = 0.7,
        )
        reply = response.choices[0].message.content.strip()
        reply = re.sub(r'\*+', '', reply)
        reply = re.sub(r'#+\s?', '', reply)
        reply = re.sub(r'`+',   '', reply)
        reply = re.sub(r'\n+',  ' ', reply).strip()

        # Persist both turns to memory
        save_turn("user",      query)
        save_turn("assistant", reply)

        print("[APEX] " + reply)
        speak(reply)
        return reply

    except Exception as e:
        print("[APEX ERROR] " + str(e))
        error_msg = "Sorry Boss, I ran into an issue processing that."
        speak(error_msg)
        return error_msg


# ══════════════════════════════════════════════════════════
#   EXECUTE PLAN  — wires decomposition into your main loop
#
#   In your main.py / dispatcher, replace:
#       chatbot(query)
#   with:
#       if is_complex_query(query):
#           execute_plan(query)
#       else:
#           chatbot(query)   # or your normal routing
# ══════════════════════════════════════════════════════════

def execute_plan(query: str):
    steps = decompose_task(query)
    if len(steps) == 1:
        chatbot(query)
        return

    speak(f"Breaking that into {len(steps)} steps, Boss.")
    for i, step in enumerate(steps, 1):
        print(f"[APEX] Step {i}/{len(steps)}: {step}")
        _dispatch(step)
        time.sleep(0.8)

def _dispatch(query: str):
    """
    Minimal internal router for execute_plan steps.
    Mirrors the logic in your main.py so each decomposed
    step goes through the right handler.
    """
    q = query.lower().strip()
    if q.startswith("open "):
        opencommand(query)
    elif "youtube" in q or q.startswith("play "):
        playyoutube(query)
    elif "whatsapp" in q:
        # Format: "whatsapp message <name> <text>"
        parts  = q.replace("whatsapp", "").strip().split(" ", 2)
        flag   = parts[0] if parts else "message"
        name_q = parts[1] if len(parts) > 1 else ""
        msg    = parts[2] if len(parts) > 2 else ""
        mobile, name = findcontact(name_q)
        whatsapp(mobile, msg, flag, name)
    else:
        chatbot(query)