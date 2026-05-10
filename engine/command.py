import pyttsx3
import speech_recognition as sr
import pyaudio
import eel
import datetime
import webbrowser
import os
import subprocess
import sqlite3
import requests
import threading
from engine.helper import remove_words
from engine.feature import findcontact, whatsapp, chatbot

DB_PATH = "APEX.db"

# ══════════════════════════════
#   WEATHER CONFIG
#   Get a free key at openweathermap.org → API keys
# ══════════════════════════════
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"   # ← replace this
CITY_NAME       = "Mumbai"                         # ← replace with your city


# ══════════════════════════════
#   CHAT HISTORY DB SETUP
# ══════════════════════════════
def init_chat_history_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender    TEXT NOT NULL CHECK(sender IN ('user', 'apex')),
                    message   TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # agenda table — stores tasks for today
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agenda (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    task      TEXT NOT NULL,
                    due_date  TEXT NOT NULL
                )
            """)
            conn.commit()
    except Exception as e:
        print('[APEX] chat_history init error: ' + str(e))


def save_message(sender: str, message: str):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO chat_history (sender, message, timestamp) VALUES (?, ?, ?)",
                (sender, message, ts)
            )
            conn.commit()
    except Exception as e:
        print('[APEX] save_message error: ' + str(e))


# ══════════════════════════════
#   SPEECH
# ══════════════════════════════
def speak(text):
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


# ══════════════════════════════
#   WEATHER FETCH
# ══════════════════════════════
def get_weather() -> str:
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric"
        )
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code == 200:
            desc  = data['weather'][0]['description'].capitalize()
            temp  = round(data['main']['temp'])
            feels = round(data['main']['feels_like'])
            return (
                f"Currently in {CITY_NAME} it is {desc}, "
                f"{temp} degrees Celsius, feels like {feels}."
            )
        else:
            return "Weather data unavailable at the moment."
    except Exception as e:
        print('[APEX] weather error: ' + str(e))
        return "I could not fetch weather data, Boss."


# ══════════════════════════════
#   AGENDA FETCH
# ══════════════════════════════
def get_today_agenda() -> str:
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT task FROM agenda WHERE due_date = ? ORDER BY id ASC",
                (today,)
            )
            rows = c.fetchall()
        if rows:
            tasks = [r[0] for r in rows]
            if len(tasks) == 1:
                return f"You have 1 task today: {tasks[0]}."
            joined = ", ".join(tasks[:-1]) + " and " + tasks[-1]
            return f"You have {len(tasks)} tasks today: {joined}."
        return "Your agenda is clear today, Boss. A great day to take on something new."
    except Exception as e:
        print('[APEX] agenda error: ' + str(e))
        return "I could not load your agenda."


# ══════════════════════════════
#   GREETING — time-aware
# ══════════════════════════════
def get_greeting() -> str:
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# ══════════════════════════════
#   STARTUP SEQUENCE
#   Called once when APEX boots
# ══════════════════════════════
def startup_sequence():
    """Runs in a background thread so the UI loads first."""
    import time
    time.sleep(2)   # wait for UI to fully render

    greeting = get_greeting()
    today    = datetime.datetime.now().strftime("%A, %d %B %Y")
    weather  = get_weather()
    agenda   = get_today_agenda()

    lines = [
        f"{greeting}, Boss. APEX is online and fully operational.",
        f"Today is {today}.",
        weather,
        agenda,
        "I am ready for your commands.",
    ]

    for line in lines:
        print("[APEX STARTUP] " + line)
        speak(line)
        save_message('apex', line)
        try:
            now_time = datetime.datetime.now().strftime("%H:%M")
            eel.appendHistoryItem('apex', line, now_time)()
        except Exception:
            pass


@eel.expose
def runStartupSequence():
    """Called from main.js after the page loads."""
    thread = threading.Thread(target=startup_sequence, daemon=True)
    thread.start()


# ══════════════════════════════
#   MIC SELECTION
# ══════════════════════════════
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
            except Exception:
                continue
    p.terminate()
    print('Falling back to mic index 1')
    return 1


# ══════════════════════════════
#   DATABASE LOOKUP
# ══════════════════════════════
def db_lookup(name: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT url FROM web_command WHERE name = ?", (name,))
            row = c.fetchone()
            if row:
                return ('web', row[0])
            c.execute("SELECT path FROM sys_command WHERE name = ?", (name,))
            row = c.fetchone()
            if row:
                return ('app', row[0])
    except Exception as e:
        print('[APEX] DB error: ' + str(e))
    return (None, None)


# ══════════════════════════════
#   CONTACT LOOKUP
# ══════════════════════════════
def contact_lookup(name: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT mobile_number FROM contacts WHERE name LIKE ?",
                ('%' + name + '%',)
            )
            row = c.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print('[APEX] Contact lookup error: ' + str(e))
    return None


# ══════════════════════════════
#   OPEN APP / SITE
# ══════════════════════════════
def openApp(name: str) -> bool:
    name = name.lower().strip()
    kind, value = db_lookup(name)
    if kind == 'web':
        webbrowser.open(value)
        return True
    if kind == 'app':
        if 'discord' in name:
            subprocess.Popen([value, '--processStart', 'Discord.exe'])
        else:
            subprocess.Popen(value)
        return True
    speak(f"Sorry Boss, I couldn't find {name} in my database.")
    return False


# ══════════════════════════════
#   CHAT HISTORY — EEL EXPOSED
# ══════════════════════════════
@eel.expose
def getChatHistory(limit: int = 50):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT sender, message, timestamp
                FROM chat_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
            rows = list(reversed(rows))
            return [
                {"sender": r[0], "message": r[1], "timestamp": r[2]}
                for r in rows
            ]
    except Exception as e:
        print('[APEX] getChatHistory error: ' + str(e))
        return []


@eel.expose
def clearChatHistory():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM chat_history")
            conn.commit()
        return True
    except Exception as e:
        print('[APEX] clearChatHistory error: ' + str(e))
        return False


# ══════════════════════════════
#   AGENDA — EEL EXPOSED
# ══════════════════════════════
@eel.expose
def addAgendaTask(task: str, due_date: str = None) -> bool:
    """Add a task. due_date format: YYYY-MM-DD. Defaults to today."""
    try:
        if not due_date:
            due_date = datetime.datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO agenda (task, due_date) VALUES (?, ?)",
                (task, due_date)
            )
            conn.commit()
        return True
    except Exception as e:
        print('[APEX] addAgendaTask error: ' + str(e))
        return False


@eel.expose
def getAgendaTasks(due_date: str = None):
    """Return tasks for a given date (defaults to today)."""
    try:
        if not due_date:
            due_date = datetime.datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, task, due_date FROM agenda WHERE due_date = ? ORDER BY id ASC",
                (due_date,)
            )
            rows = c.fetchall()
            return [{"id": r[0], "task": r[1], "due_date": r[2]} for r in rows]
    except Exception as e:
        print('[APEX] getAgendaTasks error: ' + str(e))
        return []


# ══════════════════════════════
#   VOICE INPUT
# ══════════════════════════════
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


# ══════════════════════════════
#   QUERY PROCESSING
# ══════════════════════════════
@eel.expose
def processQuery(query: str) -> str:
    query = query.lower().strip()
    if not query:
        return ''

    print('Processing: ' + query)
    response = ''
    save_message('user', query)

    try:
        # ── WEATHER ──
        if any(word in query for word in ('weather', 'temperature', 'forecast', 'climate')):
            response = get_weather()
            speak(response)

        # ── AGENDA ──
        elif any(word in query for word in ('agenda', 'schedule', 'tasks', 'plan for today', 'what do i have')):
            response = get_today_agenda()
            speak(response)

        # ── ADD TASK ──
        elif any(phrase in query for phrase in ('add task', 'add to agenda', 'remind me to', 'add reminder')):
            task = (query
                    .replace('add task', '')
                    .replace('add to agenda', '')
                    .replace('remind me to', '')
                    .replace('add reminder', '')
                    .strip())
            if task:
                addAgendaTask(task)
                response = f"Task added to your agenda: {task}. Got it, Boss."
            else:
                response = "What task would you like me to add, Boss?"
            speak(response)

        # ── OPEN ──
        elif query.startswith('open '):
            target = query[5:].strip()
            if target:
                response = 'Opening ' + target + ', Boss.'
                speak(response)
                openApp(target)
            else:
                response = 'What would you like me to open, Boss?'
                speak(response)

        # ── WHATSAPP CALL / VIDEO CALL / SEND MESSAGE ──
        elif any(word in query for word in ('send message', 'phone call', 'video call')):
            contact_no, name = findcontact(query)
            if contact_no != 0:
                if 'send message' in query:
                    flag = 'message'
                    speak('What message would you like to send, Boss?')
                    message = takecommand()
                elif 'phone call' in query:
                    flag = 'call'
                    message = ''
                else:
                    flag = 'videocall'
                    message = ''
                whatsapp(contact_no, message, flag, name)
                response = 'Done, Boss.'
            else:
                response = 'Sorry Boss, I could not find the contact.'
                speak(response)

        # ── TEXT / MESSAGE / WHATSAPP ──
        elif any(word in query for word in ('text', 'message', 'whatsapp')):
            words_to_remove = ['make', 'a', 'an', 'send', 'text', 'message',
                               'whatsapp', 'to', 'on', 'call', 'phone']
            contact_name = remove_words(query, words_to_remove).strip()
            if contact_name:
                number = contact_lookup(contact_name)
                if number:
                    response = f'Opening WhatsApp to message {contact_name}, Boss.'
                    speak(response)
                    webbrowser.open(f'https://wa.me/{number}')
                else:
                    response = f'Sorry Boss, I could not find {contact_name} in your contacts.'
                    speak(response)
            else:
                response = 'Who would you like to message, Boss?'
                speak(response)

        # ── TIME ──
        elif 'time' in query:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            response = 'The time is ' + now + ', Boss.'
            speak(response)

        # ── DATE ──
        elif 'date' in query or 'today' in query:
            today = datetime.datetime.now().strftime("%A, %d %B %Y")
            response = 'Today is ' + today + ', Boss.'
            speak(response)

        # ── IDENTITY ──
        elif 'your name' in query or 'who are you' in query:
            response = 'I am APEX, your personal AI assistant, Boss.'
            speak(response)

        # ── GREET ──
        elif any(greet in query for greet in ('hello', 'hi', 'hey')):
            response = 'Hello Boss. How can I assist you today?'
            speak(response)

        # ── SEARCH ──
        elif 'search' in query or 'look up' in query:
            search_query = query.replace('search', '').replace('look up', '').strip()
            webbrowser.open('https://www.google.com/search?q=' + search_query)
            response = 'Searching for ' + search_query + ', Boss.'
            speak(response)

        # ── YOUTUBE ──
        elif 'youtube' in query:
            search_query = (query
                            .replace('youtube', '')
                            .replace('play', '')
                            .replace('search', '')
                            .strip())
            if search_query:
                webbrowser.open('https://www.youtube.com/results?search_query=' + search_query)
                response = 'Searching YouTube for ' + search_query + ', Boss.'
            else:
                webbrowser.open('https://www.youtube.com')
                response = 'Opening YouTube, Boss.'
            speak(response)

        # ── EXIT ──
        elif any(word in query for word in ('shutdown', 'exit', 'quit', 'bye')):
            response = 'Shutting down. Goodbye Boss.'
            speak(response)
            save_message('apex', response)
            os._exit(0)

        # ── FALLBACK → CHATBOT ──
        else:
            print('[APEX] Falling back to chatbot for: ' + query)
            response = chatbot(query)
            if not response or not response.strip():
                response = 'Sorry Boss, I could not process that. Please try again.'
                speak(response)

    except Exception as e:
        print('[APEX] processQuery error: ' + str(e))
        response = 'Sorry Boss, something went wrong.'
        speak(response)

    if response:
        save_message('apex', response)

    try:
        now_time = datetime.datetime.now().strftime("%H:%M")
        eel.appendHistoryItem('user', query, now_time)()
        eel.appendHistoryItem('apex', response, now_time)()
    except Exception as e:
        print('[APEX] eel.appendHistoryItem error: ' + str(e))

    return response


# ══════════════════════════════
#   COMBINED VOICE COMMAND
# ══════════════════════════════
@eel.expose
def allcommand() -> str:
    query = takecommand()
    print('Query: ' + query)
    if query and query.strip():
        return processQuery(query)
    return ''


# ══════════════════════════════
#   INIT ON IMPORT
# ══════════════════════════════
init_chat_history_db()