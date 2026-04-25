import pyttsx3
import speech_recognition as sr
import pyaudio
import eel

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
    skip_keywords = ['speaker', 'output', 'hap', 'stereo mix', 'headphones 1', 'headphones 2', 'pc speaker']
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
        speak(query)
        return query.lower()
    except sr.WaitTimeoutError:
        print('No speech detected.')
        speak('No speech detected. Try again Boss.')
        return ''
    except sr.UnknownValueError:
        print('Could not understand.')
        speak('Could not understand. Try again Boss.')
        return ''
    except Exception as e:
        print('Error: ' + str(e))
        return ''

print('Testing mic...')
text = takecommand()
print('Final query: ' + text)
