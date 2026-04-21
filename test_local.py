"""
EMMA v2.0 -- Mode Test Local (sans ESP32)
Tape tes commandes au clavier, EMMA repond vocalement sur le PC.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import os
import sys
import random

# Forcer UTF-8 sur Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ajouter le dossier courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import EMMA_NAME, EMMA_VERSION, EMMA_CREATOR, WAKE_RESPONSES, EMMA_DATA_DIR
from stack_selector import select_stack
import llm
import memory
import action_engine
import tts

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("emma.test")

os.makedirs(EMMA_DATA_DIR, exist_ok=True)

BANNER = """
  ======================================
  ||   E . M . M . A   v{version}        ||
  ||   Mode Test Local (sans ESP32)   ||
  ||   Createur : {creator}  ||
  ======================================

  Tapez vos commandes, EMMA repond.
  Tapez 'quit' ou 'exit' pour quitter.
"""


async def process_input(text: str, stack: dict):
    """Pipeline complet : texte -> LLM -> Action -> TTS."""

    print(f"\n  [EMMA] Reflexion en cours...")

    # 1. Memoire
    memory.short_term.add_user(text)
    history = memory.short_term.get()

    # 2. LLM
    try:
        intent = await llm.think(text, history, engine=stack.get("llm", "claude"))
    except Exception as e:
        log.error(f"Erreur LLM : {e}")
        intent = {
            "action": "none",
            "params": {},
            "response": f"Je n'ai pas pu traiter votre demande, Monsieur. Erreur : {str(e)[:100]}",
            "steps": [],
        }

    action_name = intent.get("action", "none")
    response    = intent.get("response", "")

    print(f"  [LLM] Action detectee : {action_name}")
    print(f"  [LLM] Reponse vocale  : {response}")

    # 3. Executer l'action
    if action_name and action_name != "none":
        try:
            result = await action_engine.execute(intent)
            print(f"  [ACTION] Resultat : {result}")
        except Exception as e:
            result = f"Erreur d'execution : {e}"
            print(f"  [ACTION] Erreur : {e}")
    else:
        result = response

    # 4. Journaliser
    memory.log_action(
        action=action_name,
        params=intent.get("params", {}),
        result=result or "",
    )

    # 5. Memoire assistant
    if action_name and action_name != "none":
        # Si une action a ete faite, on donne la priorite au resultat de l'action (qui contient l'info reelle)
        vocal = result or response or "Action executee, Monsieur."
    else:
        vocal = response or "Je vous ecoute, Monsieur."

    memory.short_term.add_assistant(vocal)

    # 6. TTS sur le PC
    print(f"\n  EMMA >> {vocal}\n")
    try:
        wav_path = tts.synthesize(vocal, engine=stack.get("tts", "piper"))
        if wav_path:
            tts.play_local(wav_path)
    except Exception as e:
        log.warning(f"TTS echoue (pas grave en test) : {e}")


async def main():
    print(BANNER.format(version=EMMA_VERSION, creator=EMMA_CREATOR))

    # Selection stack
    stack = select_stack()
    print(f"  Stack : {stack['profile']}")
    print(f"  STT={stack['stt']} | LLM={stack['llm']} | TTS={stack['tts']}")
    print(f"  {'='*50}\n")

    # Salutation
    greeting = random.choice(WAKE_RESPONSES)
    print(f"  EMMA >> {greeting}\n")

    while True:
        try:
            user_input = input("  Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n  EMMA >> Au revoir, Monsieur. A bientot.\n")
            break

        # Ajout du test micro
        if user_input.lower() == "/mic" or user_input.lower() == "m":
            try:
                import sounddevice as sd
                import numpy as np
                import stt
                
                print("  [Micro] Enregistrement en cours (5 secondes)... Parlez !")
                # Vosk attend du 16000Hz, mono, 16-bit
                audio_data = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='int16')
                sd.wait()  # Wait until recording is finished
                print("  [Micro] Fin de l'enregistrement. Transcription...")
                
                pcm_bytes = audio_data.tobytes()
                # Transcrire le son
                user_text = await stt.transcribe(pcm_bytes, engine=stack.get("stt", "vosk"))
                print(f"  Vous avez dit : '{user_text}'")
                
                if not user_text.strip():
                    print("  EMMA >> Je n'ai rien entendu, Monsieur.")
                    continue
                
                user_input = user_text
            except ImportError:
                print("  [Erreur] Le module 'sounddevice' (ou numpy) n'est pas installe. Tapez votre texte au clavier.")
                continue
            except Exception as e:
                print(f"  [Erreur Micro] {e}")
                continue

        # Questions d'identite -- reponses hardcodees (instantanees)
        lower = user_input.lower()
        identity_map = {
            "qui es-tu":      f"Je suis {EMMA_NAME}, Embedded Modular Multi-purpose Assistant, votre assistante personnelle.",
            "tu es qui":      f"Je suis {EMMA_NAME}, votre assistante, concue par Monsieur {EMMA_CREATOR}.",
            "qui t'a cree":   f"J'ai ete concue et developpee par Monsieur {EMMA_CREATOR}, a Yaounde, au Cameroun.",
            "ton createur":   f"Mon createur est Monsieur {EMMA_CREATOR}. C'est lui qui m'a donne vie.",
            "ton nom":        f"Je m'appelle {EMMA_NAME}, Embedded Modular Multi-purpose Assistant, pour vous servir, Monsieur.",
        }
        matched = False
        for key, resp in identity_map.items():
            if key in lower:
                print(f"\n  EMMA >> {resp}\n")
                memory.short_term.add_user(user_input)
                memory.short_term.add_assistant(resp)
                matched = True
                break
        if matched:
            continue

        await process_input(user_input, stack)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  EMMA arretee. A bientot, Monsieur.")
