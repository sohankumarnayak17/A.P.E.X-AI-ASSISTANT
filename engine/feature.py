from playsound import playsound
import eel
import os
import pywhatkit as kit
import pyaudio
import pvporcupine
import struct
import time
import subprocess
import pyautogui as autogui
from urllib.parse import quote                              # ✅ import quote for URL encoding
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term


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


def whatsapp(mobile_no, message, flag, name):              # ✅ closing ) and colon
    if flag == "message":                                  # ✅ proper if with == and colon
        target_tab = 12
        apex_message = "Message sent successfully."

    elif flag == "call":                                   # ✅ elif with colon
        target_tab = 7
        message = ""
        apex_message = "Calling " + name + ", Boss."

    else:                                                  # ✅ else with colon
        target_tab = 6
        message = ""
        apex_message = "Starting video call with " + name + ", Boss."

    # Encode the message for URL
    encoded_message = quote(message)                       # ✅ quote not quote(message) typo

    # Construct the WhatsApp URL
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"  # ✅ f"..." no space, correct var name

    full_command = f"start {whatsapp_url}"                 # ✅ proper f-string

    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)

    autogui.hotkey("ctrl", "f")                           # ✅ autogui not pyauntogui, "f" as string

    for i in range(1, target_tab):                        # ✅ proper for loop
        autogui.hotkey("tab")                             # ✅ autogui not pyautogui,

    autogui.hotkey("enter")                               # ✅ proper indentation

    speak(apex_message)                                    # ✅ apex_message not apexmessage