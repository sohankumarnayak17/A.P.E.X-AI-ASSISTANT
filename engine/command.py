import pyttsx3
import speech_recognition as sr

def speak(text):
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    engine.say(text)
    engine.runAndWait()

def takecommand():
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=1, sample_rate=44100) as source:
            print('Listening...')
            r.energy_threshold = 4000
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=10, phrase_time_limit=6)
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
        speak(f"You said: {query}")
        return query.lower()
    except sr.WaitTimeoutError:
        print("No speech detected. Try again.")
        speak("No speech detected. Try again Boss.")
        return ""
    except sr.UnknownValueError:
        print("Could not understand. Try again.")
        speak("Could not understand. Try again Boss.")
        return ""
    except Exception as e:
        print(f"Error: {e}")
        return ""

text = takecommand()
print(f"Final query: {text}")
