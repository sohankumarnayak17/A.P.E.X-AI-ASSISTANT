import pyttsx3
import speech_recognition as sr
import pyaudio
import eel
import datetime
import webbrowser
import os

def speak(text):
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    engine.say(text)
    engine.runAndWait()

def get_best_mic():
    p = pyaudio.PyAudio()
    mic_names = sr.Microphone.list_microphone_names()
    input_keywords = ['microphone', 'mic in', 'bluetooth', 'headset', 'array']
    skip_keywords  = ['speaker', 'output', 'hap', 'stereo mix', 'headphones 1',
                      'headphones 2', 'pc speaker']
    for i, name in enumerate(mic_names):
        name_lower = name.lower()
        if any(skip in name_lower for skip in skip_keywords):
            continue
        if any(kw in name_lower for kw in input_keywords):
            try:
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    print('Using mic ' + str(i) + ': ' + name)
                    p.terminate()
                    return i
            except:
                continue
    p.terminate()
    print('Falling back to mic index 1')
    return 1

@eel.expose
def takecommand():
    r = sr.Recognizer()
    device_index = get_best_mic()
    try:
        with sr.Microphone(device_index=device_index, sample_rate=44100) as source:
            print('Listening...')
            r.energy_threshold = 300
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=10, phrase_time_limit=6)
        print('Recognizing...')
        query = r.recognize_google(audio, language='en-in')
        print('You said: ' + query)
        return query.lower()
    except sr.WaitTimeoutError:
        speak('No speech detected. Try again Boss.')
        return ''
    except sr.UnknownValueError:
        speak('Could not understand. Try again Boss.')
        return ''
    except Exception as e:
        print('Error: ' + str(e))
        return ''

@eel.expose
def processQuery(query):
    query = query.lower().strip()
    print('Processing: ' + query)

    if 'open' in query:
        app = query.replace('open', '').strip()
        if app:
            speak('Opening ' + app + ', Boss.')
            os.system('start ' + app)
            return 'Opening ' + app + ', Boss.'
        else:
            response = 'What would you like me to open, Boss?'
            speak(response)
            return response

    elif 'time' in query:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        response = 'The time is ' + now + ', Boss.'

    elif 'date' in query or 'today' in query:
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        response = 'Today is ' + today + ', Boss.'

    elif 'your name' in query or 'who are you' in query:
        response = 'I am APEX, your personal AI assistant, Boss.'

    elif 'hello' in query or 'hi' in query or 'hey' in query:
        response = 'Hello Boss. How can I assist you today?'

    elif 'search' in query or 'look up' in query:
        search_query = query.replace('search', '').replace('look up', '').strip()
        webbrowser.open('https://www.google.com/search?q=' + search_query)
        response = 'Searching for ' + search_query + ', Boss.'

    elif 'youtube' in query:
        search_query = query.replace('youtube', '').replace('play', '').replace('search', '').strip()
        if search_query:
            webbrowser.open('https://www.youtube.com/results?search_query=' + search_query)
            response = 'Searching YouTube for ' + search_query + ', Boss.'
        else:
            webbrowser.open('https://www.youtube.com')
            response = 'Opening YouTube, Boss.'

    elif 'shutdown' in query or 'exit' in query or 'quit' in query or 'bye' in query:
        response = 'Shutting down. Goodbye Boss.'
        speak(response)
        os._exit(0)

    else:
        response = 'I did not understand that, Boss. Please try again.'

    speak(response)
    return response

@eel.expose
def allcommand():
    query = takecommand()
    print('Query: ' + query)
    if query and query.strip() != '':
        return processQuery(query)
    return ''