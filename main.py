"""
EMMA v2.0 — Orchestrateur Principal
Point d'entree unique. Charge les modeles, demarre le serveur WebSocket,
coordonne la boucle : wake_word → STT → LLM → Action → TTS → ESP32.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import os
import random
import signal

from config import EMMA_NAME, EMMA_VERSION, EMMA_CREATOR, WAKE_RESPONSES, EMMA_DATA_DIR
from stack_selector import select_stack
import stt
import tts
import llm
import memory
import action_engine
import websocket_server as ws_server

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("emma.main")

os.makedirs(EMMA_DATA_DIR, exist_ok=True)

# ─── ASCII Art ────────────────────────────────────────────────────────────────
BANNER = r"""
  ███████╗███╗   ███╗███╗   ███╗ █████╗
  ██╔════╝████╗ ████║████╗ ████║██╔══██╗
  █████╗  ██╔████╔██║██╔████╔██║███████║
  ██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║██╔══██║
  ███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║
  ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
  Embedded Modular Multi-purpose Assistant
  v{version} | Createur : {creator}
  Yaounde, Cameroun
"""

# ─── Etat global ──────────────────────────────────────────────────────────────
_stack: dict = {}
_audio_buffer: bytearray = bytearray()
_processing: bool = False


# ─── Callbacks WebSocket ──────────────────────────────────────────────────────

async def _on_wake_word(websocket):
    """Declenche la sequence d'ecoute apres detection du wake word."""
    global _audio_buffer, _processing
    if _processing:
        log.info("[Main] Deja en traitement, wake word ignore.")
        return

    log.info("[Main] Wake word recu ! Debut de l'ecoute...")
    _audio_buffer = bytearray()

    # Annoncer etat 'listening'
    await ws_server.broadcast_state("listening")

    # Repondre vocalement
    phrase = random.choice(WAKE_RESPONSES)
    wav    = await tts.speak(phrase, engine=_stack.get("tts", "piper"))
    if wav:
        await ws_server.broadcast_audio(wav)


async def _on_audio_chunk(chunk: bytes):
    """Accumule les chunks audio PCM."""
    _audio_buffer.extend(chunk)


async def _on_audio_end(websocket):
    """Traite l'audio complet : STT → LLM → Action → TTS → ESP32."""
    global _processing, _audio_buffer

    if not _audio_buffer:
        log.warning("[Main] Buffer audio vide, abandon.")
        return

    _processing = True
    pcm = bytes(_audio_buffer)
    _audio_buffer = bytearray()

    try:
        # 1. Etat : traitement
        await ws_server.broadcast_state("thinking")

        # 2. STT
        log.info(f"[Main] Transcription ({len(pcm)} bytes PCM)...")
        text = await stt.transcribe(pcm, engine=_stack.get("stt", "vosk"))

        if not text.strip():
            log.info("[Main] Rien transcrit, abandon.")
            await ws_server.broadcast_state("idle")
            return

        log.info(f"[Main] Texte transcrit : '{text}'")

        # 3. Sauvegarder dans memoire court terme
        memory.short_term.add_user(text)

        # 4. LLM
        history = memory.short_term.get()
        intent  = await llm.think(text, history, engine=_stack.get("llm", "tinyllama"))

        # 5. Action
        result = await action_engine.execute(intent)
        vocal_response = intent.get("response", result or "Action executee, Monsieur.")

        # 6. Journaliser
        memory.log_action(
            action=intent.get("action", "none"),
            params=intent.get("params", {}),
            result=result,
        )

        # 7. Sauvegarder reponse dans memoire
        memory.short_term.add_assistant(vocal_response)

        # 8. TTS
        log.info(f"[Main] TTS : '{vocal_response[:60]}'")
        await ws_server.broadcast_state("speaking")
        wav = await tts.speak(vocal_response, engine=_stack.get("tts", "piper"))
        if wav:
            await ws_server.broadcast_audio(wav)
        else:
            # Lecture locale si pas d'ESP32
            tts.play_local(tts.TTS_TEMP_FILE)

    except Exception as e:
        log.error(f"[Main] Erreur critique dans la boucle : {e}", exc_info=True)
        err_wav = await tts.speak(
            "Une erreur est survenue, Monsieur. Veuillez reessayer.",
            engine=_stack.get("tts", "piper")
        )
        if err_wav:
            await ws_server.broadcast_audio(err_wav)
    finally:
        _processing = False
        await ws_server.broadcast_state("idle")


# ─── Demarrage ────────────────────────────────────────────────────────────────

async def main():
    global _stack

    # Affichage banniere
    print(BANNER.format(version=EMMA_VERSION, creator=EMMA_CREATOR))

    # Selection automatique de la stack
    _stack = select_stack()
    print(f"  Stack active : {_stack['profile']}")
    print(f"  STT={_stack['stt']} | LLM={_stack['llm']} | TTS={_stack['tts']}")
    print("  " + "═" * 50)

    # Pre-chargement des modeles STT (bloquer en avance pour eviter latence)
    log.info("Pre-chargement du modele STT...")
    if _stack["stt"] == "vosk":
        await asyncio.get_event_loop().run_in_executor(None, stt.load_vosk)
    elif _stack["stt"].startswith("whisper"):
        size = _stack["stt"].split("_")[-1]
        await asyncio.get_event_loop().run_in_executor(None, stt.load_whisper, size)

    # Pre-chargement TinyLlama si mode offline
    if _stack["llm"] == "tinyllama":
        log.info("Pre-chargement TinyLlama (peut prendre 30s)...")
        await asyncio.get_event_loop().run_in_executor(None, llm._load_tinyllama)

    # Enregistrement des callbacks WebSocket
    ws_server.set_callbacks(_on_wake_word, _on_audio_chunk, _on_audio_end)

    # Demarrage serveur WebSocket + mDNS
    log.info("Demarrage du serveur WebSocket...")
    server, zc, info = await ws_server.start_server()

    print(f"\n  ✅ EMMA operationnelle. En attente de l'ESP32 sur le reseau local...")
    print(f"     Dites 'Hey EMMA' pour demarrer.\n")

    # Boucle indefinie (jusqu'a CTRL+C)
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        log.info("Arret d'EMMA en cours...")
        server.close()
        await server.wait_closed()
        await zc.async_unregister_service(info)
        await zc.async_close()
        print("\n  EMMA arretee. A bientot, Monsieur.")


# ─── Point d'entree ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
