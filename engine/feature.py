from playsound import playsound
import eel
import os
import pywhatkit as kit
from engine.config import ASSISTANT_NAME

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
    search_term = query.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
    speak("Playing " + search_term + " on YouTube, Boss.")
    kit.playonyt(search_term)