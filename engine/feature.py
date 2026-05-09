import google.generativeai as genai      # ✅ Gemini replaces OpenAI
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

# ✅ Gemini setup — paste your key from aistudio.google.com/app/apikey
genai.configure(api_key="PASTE_YOUR_GEMINI_KEY_HERE")
_gemini = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "You are APEX, an advanced AI personal assistant. "
        "Be sharp, concise and futuristic. "
        "Keep responses under 3 sentences unless asked for detail. "
        "Always address the user as Boss."
    )
)


@eel.expose
def playAssistantSound():
    music_dir = "front\\assets\\audio\\radio.mp3"
    playsound(music_dir)


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


def opencommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "").strip()
    query = query.lower()

    print('Trying to open: ' + query)

    if query != "":
        speak('Opening ' + query + ', Boss.')
        os.system('start ' + query)
    else:
        speak('Please tell me what to open, Boss.')


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
#   CHATBOT — Gemini 1.5 Flash
# ══════════════════════════════
def chatbot(query):
    try:
        response = _gemini.generate_content(query.strip())
        reply = response.text.strip()
        print("[APEX] " + reply)
        speak(reply)
        return reply
    except Exception as e:
        print("[APEX ERROR] " + str(e))
        error_msg = "Sorry Boss, I ran into an issue processing that."
        speak(error_msg)
        return error_msg