import json
import logging
import queue
import time

try:
    import sounddevice as sd
except ImportError:
    sd = None

from config import WAKE_WORDS, SAMPLE_RATE
from stt import load_vosk
from vosk import KaldiRecognizer

log = logging.getLogger("emma.wakeword")

def listen_for_wake_word(callback):
    """
    Ecoute en continu via le microphone pour detecter un wake word.
    Quand un wake word est repere, declenche le callback.
    """
    if sd is None:
        log.error("Le module sounddevice n'est pas installe. Impossible d'activer le Wake Word.")
        return

    q = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        """Place l'audio capture dans la queue."""
        if status:
            log.warning(f"Statut audio: {status}")
        q.put(bytes(indata))

    log.info("Chargement du modele Vosk pour le Wake Word...")
    model = load_vosk()
    
    # On optimise Vosk : on lui dit de n'ecouter QUE les mots cles (plus de precision, moins de CPU)
    # On ajoute des mots courants pour eviter que Vosk force les syllabes aleatoires sur "emma"
    grammar = '["emma", "hey", "ok", "bonjour", "salut", "stop", "[unk]"]'
    rec = KaldiRecognizer(model, SAMPLE_RATE, grammar)

    log.info(f"Ecoute en arriere-plan activee. Mots cles : {WAKE_WORDS}")
    print("\n  [Wake Word] Le micro ecoute en arriere-plan... Dites 'Emma' ou 'Hey Emma'.")

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=None, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            try:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    
                    # Check si un de nos Wake Words est present
                    for ww in WAKE_WORDS:
                        if ww in text:
                            log.info(f"Wake Word detecte : '{ww}' (Texte brut: '{text}')")
                            # On vide la file d'attente pour ne pas avoir un ancien son
                            with q.mutex:
                                q.queue.clear()
                                
                            # Executer la fonction suite au reveil !
                            callback()
                            
                            # Reinitialiser le recognizer pour la prochaine ecoute continue
                            rec.Reset()
                            break
            except KeyboardInterrupt:
                print("\n  [Wake Word] Arret de l'ecoute en arriere-plan.")
                break

if __name__ == "__main__":
    # Test autonome du wake word
    logging.basicConfig(level=logging.INFO)
    def on_wake():
        import winsound
        print("  !!! EMMA S'EST REVEILLEE !!!")
        winsound.Beep(1000, 300)
        
    listen_for_wake_word(on_wake)
