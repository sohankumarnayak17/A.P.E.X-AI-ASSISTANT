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

> Inspired by JARVIS — built from scratch as a real, personal productivity assistant.

</div>

---

## What is APEX?

APEX (AI-Powered EXecutive) is a desktop voice assistant built entirely in Python. It listens to your voice, understands your commands, and takes action — launching apps, searching the web, playing YouTube videos, and more. It runs with a clean web-based UI powered by Eel and SiriWave.js, giving it a visual waveform interface that responds to your voice in real time.

All app and website commands are stored in a local SQLite database, making APEX easily extensible — add any app or site without touching the core code.

---

## Features

| Feature | Description |
|---|---|
| 🎙️ Voice Recognition | Real-time speech-to-text using SpeechRecognition |
| 🔊 Text-to-Speech | Natural voice responses via pyttsx3 |
| 🌐 Open Websites | Voice-triggered browser navigation |
| 💻 Launch Applications | Open any app on your PC by name |
| 🎵 Play YouTube | Hands-free video playback via pywhatkit |
| 💬 Text Fallback | Chat input when mic isn't available |
| 🗄️ SQLite Command Registry | Extensible database for apps & web commands |
| 🌊 SiriWave UI | Animated waveform interface in the browser |

---

## Tech Stack

```
Python              — Core assistant logic & command handling
Eel                 — Bridge between Python backend and web UI
SpeechRecognition   — Converts voice to text
pyttsx3             — Text-to-speech engine (offline)
pywhatkit           — YouTube playback & web utilities
SQLite              — Local database for command registry
HTML / CSS / JS     — Frontend UI structure and styling
jQuery              — DOM manipulation & event handling
SiriWave.js         — Animated voice waveform visualisation
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- A working microphone
- Chrome or Chromium browser (Eel uses it for the UI)

### Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/sohankumarnayak17/APEX.git
cd APEX

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise the SQLite database
py db.py

# 4. Launch APEX
py main.py
```

> The UI will open automatically in your browser. Allow microphone access when prompted.

---

## How It Works

```
You speak  →  SpeechRecognition converts audio to text
           →  Python parses the command
           →  SQLite is queried for matching app/website
           →  Action is executed (launch app / open URL / play video)
           →  pyttsx3 speaks the response back
           →  SiriWave UI animates in sync
```

The modular architecture means each capability (web, apps, YouTube, TTS) is its own independent module — easy to extend, easy to debug.

---

## Adding Custom Commands

APEX uses SQLite to store commands. Run `db.py` to set up the schema, then add rows directly:

```python
# Example: Add a new app
INSERT INTO apps (name, path) VALUES ('notepad', 'notepad.exe');

# Example: Add a new website
INSERT INTO websites (name, url) VALUES ('linkedin', 'https://linkedin.com');
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
- [ ] Wake word detection ("Hey APEX")
- [ ] Web search with spoken results
- [ ] System controls (volume, brightness, shutdown)
- [ ] GPT/LLM integration for conversational responses
- [ ] Task automation & scheduling

---

## Author

**Sohan Kumar Nayak**  
B.Tech CSE — KIIT University, Bhubaneswar  
[GitHub](https://github.com/sohankumarnayak17)

---

<div align="center">
  <sub>Built from scratch. No SDKs. No shortcuts. Just Python. 🐍</sub>
</div>
