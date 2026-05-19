import re
import os
import struct
import time
import subprocess
import sqlite3
import webbrowser
import pyaudio
import pvporcupine
import pyautogui as autogui
import eel
from groq import Groq
from playsound import playsound
from urllib.parse import quote
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term

DB_PATH = r"C:\Users\KIIT\OneDrive\Desktop\APEX\APEX.db"

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   GROQ SETUP
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
_groq = Groq(api_key="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")

_system_prompt = (
    "You are APEX, an advanced AI personal assistant. "
    "Speak naturally like FRIDAY from Iron Man â€” sharp, confident, slightly witty. "
    "Keep responses under 3 sentences unless asked for detail. "
    "Always address the user as Boss. "
    "NEVER use markdown, bullet points, asterisks, or any special formatting. "
    "Plain text only."
)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   PYTTSX3 â€” init once
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
import pyttsx3 as _tts
_engine = _tts.init('sapi5')
_voices = _engine.getProperty('voices')
_engine.setProperty('voice',  _voices[1].id)  # Zira
_engine.setProperty('rate',   165)
_engine.setProperty('volume', 1.0)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   PLAY SOUND
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
@eel.expose
def playAssistantSound():
    try:
        playsound("front\\assets\\audio\\radio.mp3")
    except Exception as e:
        print('[APEX] sound error: ' + str(e))

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   SPEAK
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   OPEN COMMAND
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def opencommand(query):
    from engine.db import searchDB
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "").strip().lower()
    print('[APEX] Trying to open: ' + query)
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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   PLAY YOUTUBE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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
        speak("Sorry Boss, I couldn't figure out what to play.")

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   HOTKEY â€” wake word
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def hotkey():
    porcupine    = None
    paud         = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis"])
        paud      = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate              = porcupine.sample_rate,
            channels          = 1,
            format            = pyaudio.paInt16,
            input             = True,
            frames_per_buffer = porcupine.frame_length
        )
        print('[APEX] Wake word listening...')
        while True:
            keyword       = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            keyword       = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)
            if keyword_index >= 0:
                print("[APEX] Wake word detected!")
                speak("Yes Boss, I'm listening.")
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
    except Exception as e:
        print("[APEX] Hotkey error: " + str(e))
    finally:
        try:
            if porcupine    is not None: porcupine.delete()
            if audio_stream is not None: audio_stream.close()
            if paud         is not None: paud.terminate()
        except: pass

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   FIND CONTACT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   WHATSAPP
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#   CHATBOT â€” Groq
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
def chatbot(query):
    try:
        response = _groq.chat.completions.create(
            model       = "llama-3.1-8b-instant",
            messages    = [
                {"role": "system", "content": _system_prompt},
                {"role": "user",   "content": query.strip()}
            ],
            max_tokens  = 300,
            temperature = 0.7,
        )
        reply = response.choices[0].message.content.strip()
        reply = re.sub(r'\*+', '', reply)
        reply = re.sub(r'#+\s?', '', reply)
        reply = re.sub(r'`+',   '', reply)
        reply = re.sub(r'\n+',  ' ', reply).strip()
        print("[APEX] " + reply)
        speak(reply)
        return reply
    except Exception as e:
        print("[APEX ERROR] " + str(e))
        error_msg = "Sorry Boss, I ran into an issue processing that."
        speak(error_msg)
        return error_msg
