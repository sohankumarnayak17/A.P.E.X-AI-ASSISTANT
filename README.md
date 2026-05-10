<div align="center">

<br/>

```
░█████╗░██████╗░███████╗██╗░░██╗
██╔══██╗██╔══██╗██╔════╝╚██╗██╔╝
███████║██████╔╝█████╗░░░╚███╔╝░
██╔══██║██╔═══╝░██╔══╝░░░██╔██╗░
██║░░██║██║░░░░░███████╗██╔╝╚██╗
╚═╝░░╚═╝╚═╝░░░░░╚══════╝╚═╝░░╚═╝
```

**AI-powered voice assistant for your PC.**  
Talk to your computer. Control apps, browse the web, play music — all hands-free.

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Eel](https://img.shields.io/badge/Eel-UI-222222?style=for-the-badge&logo=google-chrome&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![HTML](https://img.shields.io/badge/HTML%2FCSS%2FJS-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-00A67E?style=for-the-badge&logo=lightning&logoColor=white)

> Inspired by JARVIS — built from scratch as a real, personal productivity assistant.

</div>

---

## What is APEX?

APEX (AI-Powered EXecutive) is a desktop voice assistant built entirely in Python. It listens to your voice, understands your commands, and takes action — launching apps, searching the web, sending WhatsApp messages, checking live weather, reading your daily agenda, and holding real conversations powered by Groq's LLaMA3.

It runs with a custom red-wine dark UI built on Eel and SiriWave.js, featuring an animated holographic orb, real-time waveform, chat history sidebar, and a HUD-style interface. Every session starts with a personalised greeting — APEX tells you the time, live weather, and your agenda for the day before you say a word.

All app and website commands are stored in a local SQLite database, making APEX easily extensible — add any app or site without touching the core code.

---

## Features

| Feature | Description |
|---|---|
| 🎙️ Voice Recognition | Real-time speech-to-text using SpeechRecognition |
| 🔊 Text-to-Speech | Natural voice responses via pyttsx3 |
| 🤖 LLM Chatbot | Conversational AI fallback powered by Groq LLaMA3 |
| 🌅 Startup Greeting | Greets you on launch with time, live weather & today's agenda |
| 🌤️ Live Weather | Real-time weather fetched from OpenWeatherMap API |
| 📅 Agenda / Tasks | Daily task tracker stored in SQLite, spoken on startup |
| 🌐 Open Websites | Voice-triggered browser navigation |
| 💻 Launch Applications | Open any app on your PC by name |
| 🎵 Play YouTube | Hands-free video playback via pywhatkit |
| 💬 WhatsApp Messaging | Send messages, make calls & video calls via WhatsApp |
| 🕘 Chat History | Full conversation log saved to SQLite, shown in sidebar |
| 💬 Text Fallback | Chat input when mic isn't available |
| 🗄️ SQLite Command Registry | Extensible database for apps, web commands & contacts |
| 🌊 SiriWave UI | Animated waveform interface in the browser |
| 🎨 HUD Interface | Red-wine dark theme with holographic orb & scanline effects |

---

## Tech Stack

```
Python              — Core assistant logic & command handling
Eel                 — Bridge between Python backend and web UI
Groq (LLaMA3)       — LLM fallback for conversational responses
SpeechRecognition   — Converts voice to text
pyttsx3             — Text-to-speech engine (offline)
pywhatkit           — YouTube playback & web utilities
requests            — Live weather from OpenWeatherMap API
SQLite              — Local database for commands, history & agenda
HTML / CSS / JS     — Frontend UI structure and styling
jQuery              — DOM manipulation & event handling
SiriWave.js         — Animated voice waveform visualisation
Bootstrap 5         — Layout, offcanvas chat history sidebar
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- A working microphone
- Chrome, Chromium, or Edge browser (Eel uses it for the UI)
- Free API keys for [Groq](https://console.groq.com) and [OpenWeatherMap](https://openweathermap.org/api)

### Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/sohankumarnayak17/APEX.git
cd APEX

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise the SQLite database
py db.py

# 4. Add your API keys in engine/command.py
WEATHER_API_KEY = "your_openweathermap_key"
CITY_NAME       = "your_city"

# and in engine/feature.py
_groq = Groq(api_key="your_groq_key")

# 5. Launch APEX
py main.py
```

> The UI will open automatically in your browser. Allow microphone access when prompted.

---

## How It Works

```
App launches  →  APEX greets you by name
              →  Speaks today's date
              →  Fetches & speaks live weather
              →  Reads out your agenda for the day

You speak     →  SpeechRecognition converts audio to text
              →  Python parses the command
              →  SQLite queried for matching app / website / contact
              →  Action executed (launch / open URL / WhatsApp / search)
              →  Unrecognised commands fall back to Groq LLaMA3 chatbot
              →  pyttsx3 speaks the response back
              →  SiriWave UI animates in sync
              →  Conversation saved to chat history DB & sidebar
```

---

## Chat History

Every conversation is saved to `APEX.db`. Click the chat icon in the toolbar to open the history sidebar — it loads your last 50 messages in real time, styled with the APEX red-wine dark theme.

---

## Agenda / Task Manager

Add tasks for the day directly via voice:

> *"Add task review project report"*  
> *"What's my agenda today?"*

Tasks are stored in SQLite and spoken aloud every time APEX starts up.

---

## Adding Custom Commands

APEX uses SQLite to store commands. Run `db.py` to set up the schema, then add rows directly:

```python
# Add a new app
INSERT INTO sys_command (name, path) VALUES ('notepad', 'notepad.exe');

# Add a new website
INSERT INTO web_command (name, url) VALUES ('linkedin', 'https://linkedin.com');

# Add a contact for WhatsApp
INSERT INTO contacts (name, mobile_number) VALUES ('John', '+911234567890');
```

No hardcoded commands — everything lives in the database.

---

## Roadmap

- [x] Voice recognition & TTS
- [x] App & website launching
- [x] YouTube playback
- [x] Text input fallback
- [x] SQLite command registry
- [x] SiriWave animated UI
- [x] Groq LLaMA3 conversational chatbot
- [x] Live weather on startup
- [x] Daily agenda & task tracker
- [x] Startup greeting sequence
- [x] WhatsApp messaging & calling
- [x] Chat history sidebar
- [x] HUD red-wine dark theme UI
- [ ] Wake word detection ("Hey APEX")
- [ ] Web search with spoken results
- [ ] System controls (volume, brightness, shutdown)
- [ ] Task scheduling & reminders
- [ ] Multi-language support

---

## Author

**Sohan Kumar Nayak**  
B.Tech CSE — KIIT University, Bhubaneswar  
[GitHub](https://github.com/sohankumarnayak17)

---

<div align="center">
  <sub>Built from scratch. No shortcuts. Just Python. 🐍</sub>
</div>
