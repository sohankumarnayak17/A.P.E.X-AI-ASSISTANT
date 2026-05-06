import hugchat
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


@eel.expose
def playAssistantSound():
    music_dir = "front\\assets\\audio\\radio.mp3"
    playsound(music_dir)


def speak(text):
    import pyttsx3
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    engine.say(text)
    engine.runAndWait()


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
    """
    Search contacts table for a name mentioned in the query.
    Returns (mobile_number, name) or (0, '')
    """
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

    # Encode message and build WhatsApp URL
    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Open WhatsApp Desktop with the contact
    subprocess.run(f"start {whatsapp_url}", shell=True)
    time.sleep(6)  # Wait for WhatsApp to open fully

    if flag == "message":
        autogui.hotkey("enter")               # message box is auto-focused via URL
    elif flag == "call":
        autogui.hotkey("ctrl", "shift", "p")  # WhatsApp Desktop voice call shortcut
    else:
        autogui.hotkey("ctrl", "shift", "v")  # WhatsApp Desktop video call shortcut

    speak(apex_message)


#chatbot feature 
# ✅ chatbot feature
def chatbot(query):
    user_input = query.lower()
    bot = hugchat.Chatbot(cookie_path="engine/cookies.json")  # ✅ renamed var: chatbot → bot (was shadowing function)
    id = bot.new_conversation()                                # ✅ fixed typo: new_Conversion → new_conversation
    bot.change_conversation(id)
    response = bot.chat(user_input)
    print(response)
    speak(response)
    return response