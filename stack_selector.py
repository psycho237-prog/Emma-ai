"""
EMMA v2.0 — Selecteur de stack automatique
Choisit STT / LLM / TTS selon RAM disponible et connexion WiFi.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import psutil
import socket
import logging

log = logging.getLogger("emma.stack")


def _has_wifi() -> bool:
    """Verifie la connectivite reseau en tentant une connexion rapide."""
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


def select_stack() -> dict:
    """
    Retourne le profil de stack optimal pour cette machine.

    Profils :
      - minimal_offline  : <4 GB RAM sans WiFi
      - minimal_online   : <4 GB RAM avec WiFi
      - balanced         : 4-8 GB RAM
      - full             : >=8 GB RAM
    """
    ram_gb  = psutil.virtual_memory().total / (1024 ** 3)
    wifi_ok = _has_wifi()

    log.info(f"RAM detectee : {ram_gb:.1f} GB | WiFi : {wifi_ok}")

    if ram_gb < 4 and not wifi_ok:
        profile = "minimal_offline"
        stack = {
            "stt":     "vosk",
            "llm":     "tinyllama",
            "tts":     "piper",
            "profile": profile,
        }
    elif ram_gb < 4 and wifi_ok:
        profile = "minimal_online"
        stack = {
            "stt":     "vosk",
            "llm":     "claude",
            "tts":     "gtts",
            "profile": profile,
        }
    elif ram_gb < 8:
        profile = "balanced"
        stack = {
            "stt":     "whisper_tiny",
            "llm":     "ollama_phi3",
            "tts":     "piper",
            "profile": profile,
        }
    else:
        profile = "full"
        stack = {
            "stt":     "whisper_base",
            "llm":     "ollama_mistral",
            "tts":     "piper",
            "profile": profile,
        }

    log.info(f"Stack selectionnee : {profile} | {stack}")
    return stack
