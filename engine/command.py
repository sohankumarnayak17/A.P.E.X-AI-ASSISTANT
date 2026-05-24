import speech_recognition as sr
import pyaudio
import eel
import datetime
import webbrowser
import os
import subprocess
import sqlite3
import time
from engine.feature import (
    speak, findcontact, whatsapp, chatbot,
    opencommand, playyoutube, hotkey
)

DB_PATH = r"C:\Users\KIIT\OneDrive\Desktop\APEX\APEX.db"

# ══════════════════════════════
#   CHAT HISTORY DB
# ══════════════════════════════
def init_chat_history_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender    TEXT NOT NULL CHECK(sender IN ('user','apex')),
                    message   TEXT NOT NULL,
                    timestamp TEXT NOT NULL
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
                "INSERT INTO chat_history (sender,message,timestamp) VALUES (?,?,?)",
                (sender, message, ts)
            )
            conn.commit()
    except Exception as e:
        print('[APEX] save_message error: ' + str(e))

# ══════════════════════════════
#   MIC SELECTION
# ══════════════════════════════
def get_best_mic():
    p         = pyaudio.PyAudio()
    mic_names = sr.Microphone.list_microphone_names()
    skip      = ['speaker','output','hap','stereo mix','headphones 1','headphones 2','pc speaker']
    want      = ['microphone','mic in','bluetooth','headset','array']
    for i, name in enumerate(mic_names):
        nl = name.lower()
        if any(s in nl for s in skip): continue
        if any(w in nl for w in want):
            try:
                if p.get_device_info_by_index(i).get('maxInputChannels',0) > 0:
                    p.terminate()
                    return i
            except: continue
    p.terminate()
    return 0

# ══════════════════════════════
#   DATABASE LOOKUP
# ══════════════════════════════
def db_lookup(name: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            for table, col in [('web_command','url'), ('sys_command','path')]:
                c.execute(f"SELECT {col} FROM {table} WHERE LOWER(name)=?", (name,))
                row = c.fetchone()
                if row:
                    return ('web' if col=='url' else 'app', row[0])
            for table, col in [('web_command','url'), ('sys_command','path')]:
                c.execute(f"SELECT {col} FROM {table} WHERE LOWER(name) LIKE ?", (f'%{name}%',))
                row = c.fetchone()
                if row:
                    return ('web' if col=='url' else 'app', row[0])
    except Exception as e:
        print('[APEX] DB error: ' + str(e))
    return (None, None)

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
        try:
            subprocess.Popen(value)
        except Exception as e:
            print('[APEX] openApp error: ' + str(e))
        return True
    speak("Couldn't find " + name + " Boss.")
    return False

# ══════════════════════════════
#   CHAT HISTORY
# ══════════════════════════════
@eel.expose
def getChatHistory(limit: int = 50):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT sender,message,timestamp FROM chat_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = list(reversed(c.fetchall()))
            return [{"sender":r[0],"message":r[1],"timestamp":r[2]} for r in rows]
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
#   VOICE INPUT
# ══════════════════════════════
@eel.expose
def takecommand():
    r            = sr.Recognizer()
    device_index = get_best_mic()
    try:
        with sr.Microphone(device_index=device_index, sample_rate=44100) as source:
            print('Listening...')
            r.energy_threshold = 300
            r.pause_threshold  = 0.6
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.listen(source, timeout=6, phrase_time_limit=6)
        query = r.recognize_google(audio, language='en-in')
        print('You said: ' + query)
        return query.lower()
    except sr.WaitTimeoutError:
        speak('No speech detected Boss.')
        return ''
    except sr.UnknownValueError:
        speak('Could not understand Boss.')
        return ''
    except Exception as e:
        print('Error: ' + str(e))
        return ''

# ══════════════════════════════
#   PROCESS QUERY — fast routing
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
        # ── OPEN ──
        if 'open ' in query:
            target = query.replace('open', '').strip()
            if target:
                response = 'Opening ' + target + ', Boss.'
                speak(response)
                openApp(target)
            else:
                response = 'What would you like me to open, Boss?'
                speak(response)

        # ── YOUTUBE ──
        elif 'youtube' in query:
            sq = query.replace('youtube','').replace('play','').replace('search','').strip()
            if sq:
                webbrowser.open('https://www.youtube.com/results?search_query=' + sq)
                response = 'Searching YouTube for ' + sq + ', Boss.'
            else:
                webbrowser.open('https://www.youtube.com')
                response = 'Opening YouTube, Boss.'
            speak(response)

        # ── SEARCH ──
        elif 'search' in query or 'look up' in query:
            sq = query.replace('search','').replace('look up','').strip()
            webbrowser.open('https://www.google.com/search?q=' + sq)
            response = 'Searching for ' + sq + ', Boss.'
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
        elif any(g in query for g in ('hello','hi','hey')):
            response = 'Hello Boss. How can I assist you?'
            speak(response)

        # ── WHATSAPP ──
        elif any(w in query for w in ('send message','phone call','video call')):
            contact_no, name = findcontact(query)
            if contact_no != 0:
                if 'send message' in query:
                    flag = 'message'
                    speak('What message, Boss?')
                    message = takecommand()
                elif 'phone call' in query:
                    flag = 'call'; message = ''
                else:
                    flag = 'videocall'; message = ''
                whatsapp(contact_no, message, flag, name)
                response = 'Done, Boss.'
            else:
                response = 'Could not find the contact, Boss.'
                speak(response)

        # ── EXIT ──
        elif any(w in query for w in ('shutdown','exit','quit','bye')):
            response = 'Shutting down. Goodbye Boss.'
            speak(response)
            save_message('apex', response)
            time.sleep(1)
            os._exit(0)

        # ── FALLBACK → CHATBOT ──
        else:
            response = chatbot(query)
            if not response:
                response = 'Sorry Boss, could not process that.'
                speak(response)

    except Exception as e:
        print('[APEX] processQuery error: ' + str(e))
        response = 'Something went wrong Boss.'
        speak(response)

    if response:
        save_message('apex', response)

    return response

# ══════════════════════════════
#   ALL COMMAND
# ══════════════════════════════
@eel.expose
def allcommand() -> str:
    query = takecommand()
    if query and query.strip():
        return processQuery(query)
    return ''

# ══════════════════════════════
#   INIT
# ══════════════════════════════
init_chat_history_db()