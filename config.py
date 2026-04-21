"""
EMMA v2.0 — Configuration centrale
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import os
import platform

# ─── Identite ────────────────────────────────────────────────────────────────
EMMA_NAME    = "EMMA"
EMMA_VERSION = "2.0"
EMMA_CREATOR = "ONANA GREGOIRE LEGRAND"
EMMA_ORIGIN  = "Yaounde, Cameroun"

# ─── Reseau ───────────────────────────────────────────────────────────────────
WEBSOCKET_HOST = "0.0.0.0"
WEBSOCKET_PORT = 8765
MDNS_NAME      = "emma-pc"          # resolvable as emma-pc.local
MDNS_SERVICE   = "_emma._tcp.local."

# ─── API Cles (remplir avant utilisation) ─────────────────────────────────────
GEMINI_API_KEY      = "AIzaSyCR3fwooydM-462KubGRGZj9DgCl0S5Gt4"

ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = "claude-sonnet-4-5"

# ─── Chemins assets ───────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
VOICES_DIR  = os.path.join(ASSETS_DIR, "voices")
MODELS_DIR  = os.path.join(ASSETS_DIR, "models")

VOSK_MODEL_PATH      = os.path.join(MODELS_DIR, "vosk-fr")
TINYLLAMA_MODEL_PATH = os.path.join(MODELS_DIR, "tinyllama", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
PIPER_MODEL_PATH     = os.path.join(VOICES_DIR, "fr_FR-upmc-medium.onnx")
PIPER_CONFIG_PATH    = os.path.join(VOICES_DIR, "fr_FR-upmc-medium.onnx.json")



# ─── Preferences utilisateur ──────────────────────────────────────────────────
OS_TYPE        = platform.system()  # 'Linux' ou 'Windows'
EMMA_DATA_DIR  = os.path.join(os.path.expanduser("~"), ".emma")
PREFERENCES_FILE = os.path.join(EMMA_DATA_DIR, "preferences.json")

# ─── Audio ────────────────────────────────────────────────────────────────────
SAMPLE_RATE  = 16000
CHANNELS     = 1
SAMPLE_WIDTH = 2   # 16 bits

# ─── TTS temporaire ───────────────────────────────────────────────────────────
TTS_TEMP_FILE = os.path.join(EMMA_DATA_DIR, "tts_temp")

# ─── Phrases de reveil ────────────────────────────────────────────────────────
WAKE_WORDS = ["emma", "hey emma", "ok emma"]

WAKE_RESPONSES = [
    "Je vous ecoute, Monsieur.",
    "A vos ordres, Monsieur.",
    "Oui, Monsieur ? Je suis prete.",
    "Que puis-je faire pour vous, Monsieur ?",
    "Presente, Monsieur. Dites-moi tout.",
]

# ─── Projets actifs (contexte LLM) ───────────────────────────────────────────
ACTIVE_PROJECTS = ["AgriShield", "AKIBA", "stage-es-dirigeants"]

# Variable de session
current_stack = None


