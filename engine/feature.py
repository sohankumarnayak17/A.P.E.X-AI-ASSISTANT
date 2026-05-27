import re
import threading
import subprocess
import webbrowser
import time
import eel
import pyttsx3
from groq import Groq
from playsound import playsound
from urllib.parse import quote

from engine.config import (
    ASSISTANT_NAME, GROQ_API_KEY, GROQ_MODEL,
    GROQ_MAX_TOKENS, GROQ_TEMP, SYSTEM_PROMPT,
    TTS_VOICE_INDEX, TTS_RATE, TTS_VOLUME, DB_PATH
)
from engine.helper import extract_yt_term

import sqlite3

# ══════════════════════════════
#   TTS ENGINE — thread-safe singleton
# ══════════════════════════════
_tts_lock   = threading.Lock()
_tts_engine = None

def _get_tts() -> pyttsx3.Engine:
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init("sapi5")
        voices = _tts_engine.getProperty("voices")
        if TTS_VOICE_INDEX < len(voices):
            _tts_engine.setProperty("voice",  voices[TTS_VOICE_INDEX].id)
        _tts_engine.setProperty("rate",   TTS_RATE)
        _tts_engine.setProperty("volume", TTS_VOLUME)
    return _tts_engine


def _clean_text(text: str) -> str:
    """Strip markdown and normalise whitespace for speech."""
    text = re.sub(r"\*+",  "", str(text))
    text = re.sub(r"#+\s?","", text)
    text = re.sub(r"`+",   "", text)
    text = re.sub(r"\n+",  " ", text)
    return text.strip()


def speak(text: str):
    """Non-blocking TTS — runs in a background daemon thread."""
    def _run():
        clean = _clean_text(text)
        if not clean:
            return
        print(f"[APEX] {clean}")
        with _tts_lock:
            try:
                engine = _get_tts()
                engine.say(clean)
                engine.runAndWait()
            except Exception as e:
                print(f"[APEX] TTS error: {e}")
    threading.Thread(target=_run, daemon=True).start()


def speak_wait(text: str):
    """Blocking TTS — waits until speech is complete."""
    clean = _clean_text(text)
    if not clean:
        return
    print(f"[APEX] {clean}")
    with _tts_lock:
        try:
            engine = _get_tts()
            engine.say(clean)
            engine.runAndWait()
        except Exception as e:
            print(f"[APEX] TTS error: {e}")


# ══════════════════════════════
#   GROQ CLIENT
# ══════════════════════════════
_groq_client = None
try:
    _groq_client = Groq(api_key=GROQ_API_KEY)
    print("[APEX] Groq connected.")
except Exception as e:
    print(f"[APEX] Groq init error: {e}")


# ══════════════════════════════
#   SOUND
# ══════════════════════════════
@eel.expose
def playAssistantSound():
    def _play():
        try:
            playsound(r"front\assets\audio\radio.mp3")
        except Exception as e:
            print(f"[APEX] Sound error: {e}")
    threading.Thread(target=_play, daemon=True).start()


# ══════════════════════════════
#   OPEN COMMAND
# ══════════════════════════════
def opencommand(query: str):
    from engine.db import searchDB
    target = (query
              .replace(ASSISTANT_NAME, "")
              .replace("open", "")
              .strip()
              .lower())
    if not target:
        speak("What would you like me to open, Boss?")
        return
    kind, value = searchDB(target)
    if kind == "web":
        speak(f"Opening {target}, Boss.")
        webbrowser.open(value)
    elif kind == "app":
        speak(f"Launching {target}, Boss.")
        try:
            subprocess.Popen(value)
        except Exception as e:
            speak("Could not launch that, Boss.")
            print(f"[APEX] Popen error: {e}")
    else:
        speak(f"Couldn't find {target}, Boss.")


# ══════════════════════════════
#   YOUTUBE
# ══════════════════════════════
def playyoutube(query: str):
    term = extract_yt_term(query)
    if not term:
        term = (query
                .replace("play", "")
                .replace("on youtube", "")
                .replace("youtube", "")
                .strip())
    if term:
        speak(f"Playing {term} on YouTube, Boss.")
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote(term))
    else:
        speak("What would you like me to play, Boss?")


# ══════════════════════════════
#   CONTACTS
# ══════════════════════════════
def findcontact(query: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            for row in conn.execute("SELECT name, mobile_number FROM contacts"):
                name, number = row
                if name.lower() in query.lower():
                    return (number, name)
    except Exception as e:
        print(f"[APEX] findcontact error: {e}")
    return (0, "")


# ══════════════════════════════
#   WHATSAPP
# ══════════════════════════════
def whatsapp(mobile_no: str, message: str, flag: str, name: str):
    import pyautogui as autogui
    if not mobile_no:
        speak("Couldn't find that contact, Boss.")
        return
    try:
        encoded = quote(message)
        url     = f"whatsapp://send?phone={mobile_no}&text={encoded}"
        subprocess.run(f"start {url}", shell=True)
        time.sleep(5)
        if flag == "message":
            autogui.hotkey("enter")
            speak(f"Message sent to {name}, Boss.")
        elif flag == "call":
            autogui.hotkey("ctrl", "shift", "p")
            speak(f"Calling {name}, Boss.")
        else:
            autogui.hotkey("ctrl", "shift", "v")
            speak(f"Video calling {name}, Boss.")
    except Exception as e:
        speak("WhatsApp action failed, Boss.")
        print(f"[APEX] WhatsApp error: {e}")


# ══════════════════════════════
#   CHATBOT — Groq
# ══════════════════════════════
def chatbot(query: str, context: list = None) -> str:
    """
    Send query to Groq LLM.
    Optionally pass recent context as list of {role, content} dicts.
    """
    if _groq_client is None:
        msg = "AI brain offline, Boss. Check the API key."
        speak(msg)
        return msg
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": query.strip()})

        resp  = _groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = messages,
            max_tokens  = GROQ_MAX_TOKENS,
            temperature = GROQ_TEMP,
        )
        reply = resp.choices[0].message.content.strip()
        reply = re.sub(r"[\*\#\`]+", "", reply)
        reply = re.sub(r"\n+",       " ", reply).strip()
        speak(reply)
        return reply
    except Exception as e:
        print(f"[APEX] Groq error: {e}")
        msg = "Sorry Boss, something went wrong."
        speak(msg)
        return msg


# ══════════════════════════════
#   WAKE WORD HOTKEY
# ══════════════════════════════
def hotkey():
    """Blocking wake-word listener — run in a daemon thread."""
    import speech_recognition as sr
    from engine.config import WAKE_WORDS, MIC_DEVICE
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold  = 0.5
    print("[APEX] Hotkey listener ready.")
    while True:
        try:
            with sr.Microphone(device_index=MIC_DEVICE) as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=4, phrase_time_limit=3)
            text = r.recognize_google(audio, language="en-in").lower()
            if any(w in text for w in WAKE_WORDS):
                speak("I'm here, Boss.")
                try:
                    eel.bringToFront()
                except Exception:
                    pass
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"[APEX] Hotkey error: {e}")
            time.sleep(1)