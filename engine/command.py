import pyttsx3
import speech_recognition as sr
import pyaudio

def speak(text):
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    engine.say(text)
    engine.runAndWait()

def get_best_mic():
    """Only pick INPUT devices, skip output devices like speakers/headphones."""
    p = pyaudio.PyAudio()
    mic_names = sr.Microphone.list_microphone_names()

    # Keywords that are INPUT devices only
    input_keywords = ['microphone', 'mic in', 'bluetooth', 'headset', 'array']
    # Keywords to skip — these are OUTPUT devices
    skip_keywords  = ['speaker', 'output', 'hap', 'stereo mix', 'headphones 1',
                      'headphones 2', 'pc speaker']

    for i, name in enumerate(mic_names):
        name_lower = name.lower()
        # Skip output devices
        if any(skip in name_lower for skip in skip_keywords):
            continue
        # Pick first valid input device
        if any(kw in name_lower for kw in input_keywords):
            # Verify it has input channels
            try:
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    print(f"Using mic [{i}]: {name}")
                    p.terminate()
                    return i
            except:
                continue

    p.terminate()
    print("Falling back to mic index 18 (Microphone Array)")
    return 18

def takecommand():
    r = sr.Recognizer()
    device_index = get_best_mic()
    try:
        with sr.Microphone(device_index=device_index) as source:
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