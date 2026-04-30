from playsound import playsound
import eel
import os
import pywhatkit as kit
import pyaudio
import pvporcupine
import struct
import time
import pyautogui as autogui
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


def hotkey():                                               # ✅ proper def with colon
    porcupine = None
    paud = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(keywords=["alexa"])  # ✅ pvporcupine.create, free keyword
        paud = pyaudio.PyAudio()                            # ✅ PyAudio() capital A
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,                         # ✅ dot not comma
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            keyword = audio_stream.read(porcupine.frame_length)               # ✅ frame_length
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)  # ✅ "h" * n

            keyword_index = porcupine.process(keyword)
            if keyword_index >= 0:                          # ✅ colon not semicolon
                print("Hotword detected")
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")

    except Exception as e:                                  # ✅ except at same level as try
        print("[APEX] Hotkey error: " + str(e))

    finally:                                                # ✅ finally for guaranteed cleanup
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()