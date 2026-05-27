import datetime
import os
import subprocess
import time
import webbrowser
import sqlite3

import eel
import speech_recognition as sr
import pyaudio

from engine.config import DB_PATH, MIC_DEVICE
from engine.feature import speak, findcontact, whatsapp, chatbot, opencommand, playyoutube
from engine.memory  import record_interaction, get_recent_context

# ══════════════════════════════
#   APEX — Command Router
# ══════════════════════════════

# ─────────────────────────────
#   Chat history helpers
# ─────────────────────────────
def _init_chat_history():
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
        print(f"[APEX] chat_history init error: {e}")


def _save_message(sender: str, message: str):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO chat_history (sender, message, timestamp) VALUES (?,?,?)",
                (sender, message, ts)
            )
            conn.commit()
    except Exception as e:
        print(f"[APEX] save_message error: {e}")


# ─────────────────────────────
#   Microphone selection
# ─────────────────────────────
def _get_best_mic() -> int:
    """Pick the most suitable input device index."""
    try:
        p         = pyaudio.PyAudio()
        mic_names = sr.Microphone.list_microphone_names()
        skip = {"speaker", "output", "hap", "stereo mix",
                "headphones 1", "headphones 2", "pc speaker"}
        want = {"microphone", "mic in", "bluetooth", "headset", "array"}
        for i, name in enumerate(mic_names):
            nl = name.lower()
            if any(s in nl for s in skip):
                continue
            if any(w in nl for w in want):
                try:
                    if p.get_device_info_by_index(i).get("maxInputChannels", 0) > 0:
                        p.terminate()
                        return i
                except Exception:
                    continue
        p.terminate()
    except Exception as e:
        print(f"[APEX] Mic selection error: {e}")
    return MIC_DEVICE


# ──────────────────────────────────────────────────
#   eel-exposed: Chat history
# ──────────────────────────────────────────────────
@eel.expose
def getChatHistory(limit: int = 50):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT sender, message, timestamp FROM chat_history "
                "ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {"sender": r[0], "message": r[1], "timestamp": r[2]}
            for r in reversed(rows)
        ]
    except Exception as e:
        print(f"[APEX] getChatHistory error: {e}")
        return []


@eel.expose
def clearChatHistory():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM chat_history")
            conn.commit()
        return True
    except Exception as e:
        print(f"[APEX] clearChatHistory error: {e}")
        return False


# ──────────────────────────────────────────────────
#   eel-exposed: Voice input
# ──────────────────────────────────────────────────
@eel.expose
def takecommand() -> str:
    """Listen on the best mic and return recognised text (lowercase)."""
    r = sr.Recognizer()
    device_index = _get_best_mic()
    try:
        with sr.Microphone(device_index=device_index, sample_rate=44100) as source:
            print("[APEX] Listening...")
            r.energy_threshold = 300
            r.pause_threshold  = 0.6
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.listen(source, timeout=6, phrase_time_limit=7)
        query = r.recognize_google(audio, language="en-in")
        print(f"[APEX] Heard: {query}")
        return query.lower()
    except sr.WaitTimeoutError:
        speak("No speech detected, Boss.")
        return ""
    except sr.UnknownValueError:
        speak("Could not understand, Boss.")
        return ""
    except Exception as e:
        print(f"[APEX] takecommand error: {e}")
        return ""


# ──────────────────────────────────────────────────
#   eel-exposed: Main query router
# ──────────────────────────────────────────────────
@eel.expose
def processQuery(query: str) -> str:
    query = query.lower().strip()
    if not query:
        return ""

    print(f"[APEX] Processing: {query}")
    _save_message("user", query)
    response  = ""
    cmd_type  = "general"
    success   = True
    t_start   = time.time()

    try:
        # ── OPEN ─────────────────────────────────────
        if query.startswith("open ") or " open " in query:
            cmd_type = "open"
            target   = query.replace("open", "").strip()
            if target:
                response = f"Opening {target}, Boss."
                speak(response)
                opencommand(target)
            else:
                response = "What would you like me to open, Boss?"
                speak(response)

        # ── YOUTUBE ──────────────────────────────────
        elif "youtube" in query:
            cmd_type = "youtube"
            sq = (query
                  .replace("youtube", "")
                  .replace("play", "")
                  .replace("search", "")
                  .strip())
            if sq:
                webbrowser.open(
                    "https://www.youtube.com/results?search_query=" + sq
                )
                response = f"Searching YouTube for {sq}, Boss."
            else:
                webbrowser.open("https://www.youtube.com")
                response = "Opening YouTube, Boss."
            speak(response)

        # ── GOOGLE SEARCH ─────────────────────────────
        elif "search" in query or "look up" in query or "google" in query:
            cmd_type = "search"
            sq = (query
                  .replace("search", "")
                  .replace("look up", "")
                  .replace("google", "")
                  .strip())
            webbrowser.open("https://www.google.com/search?q=" + sq)
            response = f"Searching for {sq}, Boss."
            speak(response)

        # ── TIME ─────────────────────────────────────
        elif "time" in query:
            cmd_type = "time"
            now      = datetime.datetime.now().strftime("%I:%M %p")
            response = f"It's {now}, Boss."
            speak(response)

        # ── DATE ─────────────────────────────────────
        elif "date" in query or "today" in query:
            cmd_type = "date"
            today    = datetime.datetime.now().strftime("%A, %d %B %Y")
            response = f"Today is {today}, Boss."
            speak(response)

        # ── IDENTITY ─────────────────────────────────
        elif "your name" in query or "who are you" in query:
            cmd_type = "identity"
            response = "I am APEX, your personal AI assistant, Boss."
            speak(response)

        # ── GREET ────────────────────────────────────
        elif any(g in query for g in ("hello", "hi ", "hey")):
            cmd_type = "greet"
            hour     = datetime.datetime.now().hour
            greeting = (
                "Good morning" if hour < 12 else
                "Good afternoon" if hour < 17 else
                "Good evening"
            )
            response = f"{greeting}, Boss. How can I assist you?"
            speak(response)

        # ── WHATSAPP ─────────────────────────────────
        elif any(w in query for w in ("send message", "phone call", "video call")):
            cmd_type   = "whatsapp"
            contact_no, name = findcontact(query)
            if contact_no and contact_no != 0:
                if "send message" in query:
                    speak("What should I say, Boss?")
                    message = takecommand()
                    flag    = "message"
                elif "phone call" in query:
                    message, flag = "", "call"
                else:
                    message, flag = "", "videocall"
                whatsapp(contact_no, message, flag, name)
                response = "Done, Boss."
            else:
                response = "Could not find that contact, Boss."
                speak(response)
                success  = False

        # ── VOLUME ───────────────────────────────────
        elif "volume up" in query:
            cmd_type = "system"
            import pyautogui
            for _ in range(5):
                pyautogui.press("volumeup")
            response = "Volume increased, Boss."
            speak(response)

        elif "volume down" in query:
            cmd_type = "system"
            import pyautogui
            for _ in range(5):
                pyautogui.press("volumedown")
            response = "Volume decreased, Boss."
            speak(response)

        elif "mute" in query:
            cmd_type = "system"
            import pyautogui
            pyautogui.press("volumemute")
            response = "Muted, Boss."
            speak(response)

        # ── SCREENSHOT ───────────────────────────────
        elif "screenshot" in query or "screen shot" in query:
            cmd_type = "system"
            import pyautogui
            path = os.path.join(
                os.path.expanduser("~"), "Desktop",
                f"apex_screenshot_{int(time.time())}.png"
            )
            pyautogui.screenshot(path)
            response = f"Screenshot saved to Desktop, Boss."
            speak(response)

        # ── SHUTDOWN / EXIT ──────────────────────────
        elif any(w in query for w in ("shutdown", "exit", "quit", "bye", "goodbye")):
            cmd_type = "exit"
            response = "Shutting down. Goodbye, Boss."
            speak(response)
            _save_message("apex", response)
            record_interaction(query, response, True, cmd_type,
                               time.time() - t_start)
            time.sleep(1.5)
            os._exit(0)

        # ── FALLBACK → LLM ───────────────────────────
        else:
            cmd_type = "chatbot"
            # Pass last 3 turns as context
            ctx = [
                {"role": "user" if m["sender"] == "user" else "assistant",
                 "content": m["message"]}
                for m in get_recent_context(3)
            ]
            response = chatbot(query, context=ctx)
            if not response:
                response = "Sorry Boss, I could not process that."
                speak(response)
                success  = False

    except Exception as e:
        print(f"[APEX] processQuery error: {e}")
        response = "Something went wrong, Boss."
        speak(response)
        success  = False

    if response:
        _save_message("apex", response)

    record_interaction(
        query, response, success, cmd_type,
        round(time.time() - t_start, 3)
    )
    return response


# ──────────────────────────────────────────────────
#   eel-exposed: One-shot voice → process
# ──────────────────────────────────────────────────
@eel.expose
def allcommand() -> str:
    query = takecommand()
    if query.strip():
        return processQuery(query)
    return ""


# ──────────────────────────────────────────────────
#   Init on import
# ──────────────────────────────────────────────────
_init_chat_history()