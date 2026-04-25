import pyttsx3
import speech_recognition as sr
import sounddevice

def speak(text):
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    engine.say(text)
    engine.runAndWait()

def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening...')
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source, 10, 6)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
        speak(f"You said: {query}")
    except Exception as e:
        print("Could not understand. Try again.")
        speak("Could not understand. Try again.")
        return ""
    return query.lower()

text = takecommand()
print(f"Final query: {text}")