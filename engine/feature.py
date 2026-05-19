import re
from groq import Groq                     # ✅ pip install groq
from playsound import playsound
import eel
import os
import pywhatkit as kit
import pyaudio
import pvporcupine
import struct
import time
import subprocess
import sqlite3
import pyautogui as autogui
from urllib.parse import quote
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term

DB_PATH = "APEX.db"

# ══════════════════════════════
#   GROQ SETUP
#   Get free key at console.groq.com → API Keys → Create
# ══════════════════════════════
_groq = Groq(api_key="PASTE_GROQ_KEY_HERE")

_system_prompt = (
    "You are APEX, an advanced AI personal assistant. "
    "Be sharp, concise and futuristic. "
    "Keep responses under 3 sentences unless asked for detail. "
    "Always address the user as Boss. "
    "NEVER use markdown, bullet points, asterisks, or any special formatting. "
    "Plain text only."
)


# ══════════════════════════════
#   PLAY SOUND
# ══════════════════════════════
@eel.expose
def playAssistantSound():
    music_dir = "front\\assets\\audio\\radio.mp3"
    playsound(music_dir)


# ══════════════════════════════
#   SPEAK
# ══════════════════════════════
def speak(text):
    import pyttsx3
    try:
        text = str(text)
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.setProperty('rate', 174)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print('[APEX] speak error: ' + str(e))


# ══════════════════════════════
#   OPEN COMMAND
# ══════════════════════════════
def opencommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "").strip().lower()
    print('Trying to open: ' + query)
    if query:
        speak('Opening ' + query + ', Boss.')
        os.system('start ' + query)
    else:
        speak('Please tell me what to open, Boss.')


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
        speak("Playing " + search_term + " on YouTube, Boss.")
        kit.playonyt(search_term)
    else:
        speak("Sorry Boss, I couldn't figure out what to play.")


# ══════════════════════════════
#   HOTKEY
# ══════════════════════════════
def hotkey():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(keywords=["alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)
            if keyword_index >= 0:
                print("Hotword detected")
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
    except Exception as e:
        print("[APEX] Hotkey error: " + str(e))
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()


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
    if flag == "message":
        apex_message = "Message sent successfully, Boss."
    elif flag == "call":
        message = ""
        apex_message = "Calling " + name + ", Boss."
    else:
        message = ""
        apex_message = "Starting video call with " + name + ", Boss."

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    subprocess.run(f"start {whatsapp_url}", shell=True)
    time.sleep(6)

    if flag == "message":
        autogui.hotkey("enter")
    elif flag == "call":
        autogui.hotkey("ctrl", "shift", "p")
    else:
        autogui.hotkey("ctrl", "shift", "v")

    speak(apex_message)


# ══════════════════════════════
#   CHATBOT — Groq LLaMA3
# ══════════════════════════════
def chatbot(query):
    try:
        response = _groq.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": _system_prompt},
                {"role": "user",   "content": query.strip()}
            ],
            max_tokens=300,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        # strip any leftover markdown
        reply = re.sub(r'\*+', '', reply)
        reply = re.sub(r'#+\s?', '', reply)
        reply = re.sub(r'`+',   '', reply)
        reply = re.sub(r'\n+',  ' ', reply)
        reply = reply.strip()

        print("[APEX] " + reply)
        speak(reply)
        return reply

    except Exception as e:
        print("[APEX ERROR] " + str(e))
        error_msg = "Sorry Boss, I ran into an issue processing that."
        speak(error_msg)
        return error_msg
