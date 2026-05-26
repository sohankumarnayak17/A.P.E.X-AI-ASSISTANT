import os

# ══════════════════════════════
#   APEX — Central Configuration
# ══════════════════════════════

ASSISTANT_NAME = "apex"

# Resolve DB path relative to this file so it works on any machine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "APEX.db")

# Groq
GROQ_API_KEY   = "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"
GROQ_MODEL     = "llama-3.1-8b-instant"
GROQ_MAX_TOKENS = 120
GROQ_TEMP       = 0.6

SYSTEM_PROMPT = (
    "You are APEX, an elite AI assistant modelled after FRIDAY from Iron Man. "
    "Be sharp, witty, and extremely concise — 1 to 2 sentences maximum. "
    "Always address the user as Boss. "
    "Never use markdown, bullet points, or formatting. Plain spoken text only."
)

# TTS
TTS_VOICE_INDEX = 1     # 0 = male, 1 = female (SAPI5)
TTS_RATE        = 185
TTS_VOLUME      = 1.0

# Wake word
WAKE_WORDS   = ['hey apex', 'apex', 'wake up', 'apex wake up']
MIC_DEVICE   = 0        # override if your mic index differs

# Clap detection
CLAP_THRESHOLD = 2500   # peak amplitude; lower = more sensitive
CLAP_GAP       = 0.6    # seconds between two claps
CLAP_COOLDOWN  = 2.0    # seconds to ignore after a trigger

# Server
EEL_HOST = "localhost"
EEL_PORT = 5001