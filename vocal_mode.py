import asyncio
import logging
import random
import time
import winsound

import config
import tts
import stt
import llm
import memory
import action_engine
import wake_word
from actions.system import get_greeting
from stack_selector import select_stack

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("emma.vocal")

async def vocal_pipeline():
    """Pipeline principal declenche par le Wake Word."""
    from hardware import hw
    stack = config.current_stack # On utilise la stack choisie au depart
    
    # 1. Salutation intelligente
    greeting = get_greeting()
    print(f"\n  EMMA >> {greeting}")
    
    # Synthese et lecture
    wav_path = tts.synthesize(greeting, engine=stack['tts'])
    if wav_path:
        hw.set_state('S') # Mode Parole
        tts.play_local(wav_path)
    
    # 2. Ecoute de la commande intelligente (VAD)
    print("  [Micro] Je vous ecoute... Parlez !")
    hw.set_state('L') # Mode Ecoute
    winsound.Beep(1200, 150)
    
    # Appel de la detection de silence (utilisation des reglages Config)
    pcm_bytes = await stt.record_until_silence()
    
    hw.set_state('T') # Mode Reflexion (STT + LLM)
    print("  [Micro] Fin de l'ecoute. Analyse...")

    # 3. Transcription STT (On utilise 'small' pour plus de puissance)
    user_text = await stt.transcribe(pcm_bytes, engine='whisper_small')
    print(f"  Vous avez dit : '{user_text}'")

    if not user_text.strip():
        print("  EMMA >> Je n'ai rien entendu, Monsieur.")
        hw.set_state('N')
        return

    # 4. Reflexion LLM
    memory.short_term.add_user(user_text)
    history = memory.short_term.get()
    
    intent = await llm.think(user_text, history, engine=stack['llm'])
    action_name = intent.get("action", "none")
    response = intent.get("response", "Je m'en occupe, Monsieur.")
    
    # --- CONFIRMATION D'INTENTION (Vocal 1) ---
    print(f"  EMMA >> {response}")
    wav_path = tts.synthesize(response, engine=stack['tts'])
    if wav_path:
        hw.set_state('S') # Mode Parole
        tts.play_local(wav_path)
        hw.set_state('T') # Retour reflexion pour l'action

    # 5. Execution Action
    if action_name != "none":
        result = await action_engine.execute(intent)
        print(f"  [ACTION] {action_name} -> {result}")
        
        # --- CONFIRMATION DE RESULTAT (Vocal 2) ---
        vocal_final = result or "C'est fait, Monsieur."
        print(f"  EMMA >> {vocal_final}")
        wav_path_final = tts.synthesize(vocal_final, engine=stack['tts'])
        if wav_path_final:
            hw.set_state('S') # Mode Parole
            tts.play_local(wav_path_final)
        
        memory.short_term.add_assistant(vocal_final)
    else:
        memory.short_term.add_assistant(response)

    hw.set_state('N') # Retour au calme



def on_wake_detected():
    """Appele par le module wake_word."""
    # On utilise asyncio.run_coroutine_threadsafe car wake_word tourne dans son propre thread
    # Mais ici on va faire plus simple pour le test :
    asyncio.run(vocal_pipeline())

if __name__ == "__main__":
    print("\n" + "="*50)
    print("      E.M.M.A v2.0 - MODE VOCAL COMPLET")
    print("="*50)
    
    # Selection de la pile logicielle
    config.current_stack = select_stack()
    
    print("\n[Systeme] EMMA est en veille active...")
    print("[Systeme] Dites 'EMMA' ou 'HEY EMMA' pour me reveiller.\n")
    
    # Lance l'ecoute du mot clef (bloquant)
    try:
        wake_word.listen_for_wake_word(on_wake_detected)
    except KeyboardInterrupt:
        print("\n[Systeme] Arret d'EMMA. Au revoir Monsieur.")
