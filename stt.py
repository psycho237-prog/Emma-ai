"""
EMMA v2.0 — Module STT (Speech-to-Text)
Supporte : Vosk (offline), faster-whisper (offline ameliore)
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import io
import logging
import wave
from config import VOSK_MODEL_PATH, SAMPLE_RATE

log = logging.getLogger("emma.stt")

# ─── Chargement paresseux des modeles ─────────────────────────────────────────
_vosk_model = None
_whisper_model = None


def load_vosk():
    """Charge le modele Vosk fr une seule fois."""
    global _vosk_model
    if _vosk_model is None:
        from vosk import Model
        log.info(f"Chargement modele Vosk depuis : {VOSK_MODEL_PATH}")
        _vosk_model = Model(VOSK_MODEL_PATH)
        log.info("Vosk charge avec succes.")
    return _vosk_model


def load_whisper(size: str = "tiny"):
    """Charge le modele Whisper une seule fois en mode local uniquement."""
    global _whisper_model
    if _whisper_model is None:
        import platform, os
        if platform.system() == "Windows":
            import importlib.util
            spec = importlib.util.find_spec("ctranslate2")
            if spec and spec.origin:
                lib_dir = os.path.dirname(spec.origin)
                if os.path.isdir(lib_dir):
                    os.add_dll_directory(lib_dir)
                    log.info(f"DLL directory ajoute pour ctranslate2 : {lib_dir}")
                    
        from faster_whisper import WhisperModel
        log.info(f"Chargement Whisper '{size}' (Mode Local Rapide)...")
        # On tente de charger localement pour eviter les requetes HTTP lentes
        try:
            _whisper_model = WhisperModel(size, device="cpu", compute_type="int8", local_files_only=True)
        except Exception:
            # Si le modele n'est pas encore telecharge, on autorise une derniere fois internet
            log.info("Modele non detecte localement, telechargement initial...")
            _whisper_model = WhisperModel(size, device="cpu", compute_type="int8", local_files_only=False)
            
        log.info("Whisper charge avec succes.")
    return _whisper_model



# ─── Transcription ─────────────────────────────────────────────────────────────

def transcribe_vosk(pcm_bytes: bytes) -> str:
    """
    Transcrit un buffer PCM 16bit 16kHz en texte via Vosk.
    Retourne la chaine transcrite ou '' si incomprehensible.
    """
    import json
    from vosk import KaldiRecognizer

    model = load_vosk()
    rec   = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(False)

    # Vosk attend des chunks; on envoie tout d'un coup
    rec.AcceptWaveform(pcm_bytes)
    result = json.loads(rec.FinalResult())
    text   = result.get("text", "").strip()
    log.info(f"[Vosk] Transcription : '{text}'")
    return text


def transcribe_whisper(pcm_bytes: bytes, size: str = "tiny") -> str:
    """
    Transcrit un buffer PCM via Whisper.
    Convertit d'abord en WAV en memoire.
    """
    model = load_whisper(size)

    # Emballer PCM brut dans un WAV en memoire
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
    buf.seek(0)

    segments, _ = model.transcribe(buf, language="fr", beam_size=1)
    text = " ".join(seg.text for seg in segments).strip()
    log.info(f"[Whisper] Transcription : '{text}'")
    return text


async def record_until_silence(threshold: int = 400, silence_duration: float = 2.5, timeout: float = 12.0) -> bytes:
    """
    Enregistre l'audio depuis le micro et s'arrete automatiquement 
    apres 'silence_duration' secondes de silence.
    Plus patient (2.5s).
    """

    import sounddevice as sd
    import numpy as np
    import time

    log.info("Debut de l'enregistrement intelligent (VAD)...")
    
    audio_chunks = []
    start_time = time.time()
    last_voice_time = time.time()
    is_speaking = False

    def callback(indata, frames, time_info, status):
        nonlocal last_voice_time, is_speaking
        if status:
            log.warning(str(status))
        
        # Calculer la puissance du son (RMS)
        rms = np.sqrt(np.mean(indata.astype(float)**2))
        audio_chunks.append(indata.copy())
        
        if rms > threshold:
            last_voice_time = time.time()
            is_speaking = True

    # Ouvrir le flux
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', callback=callback):
        while True:
            await asyncio.sleep(0.1)
            now = time.time()
            
            # 1. Securite : Temps maximum ecoule
            if now - start_time > timeout:
                log.info("Timeout d'enregistrement atteint.")
                break
            
            # 2. Silence detecte apres une parole
            if is_speaking and (now - last_voice_time > silence_duration):
                log.info(f"Silence detecte ({silence_duration}s). Arret.")
                break
                
            # 3. Rien n'a ete dit du tout pendant 4s
            if not is_speaking and (now - start_time > 4.0):
                log.info("Aucune voix detectee.")
                break

    return b"".join(audio_chunks)


async def transcribe(pcm_bytes: bytes, engine: str = "vosk") -> str:

    """
    Point d'entree asynchrone. Deliegue vers le bon moteur STT.
    engine : 'vosk' | 'whisper_tiny' | 'whisper_base'
    """
    loop = asyncio.get_event_loop()
    if engine == "vosk":
        return await loop.run_in_executor(None, transcribe_vosk, pcm_bytes)
    elif engine.startswith("whisper"):
        size = engine.split("_")[-1]   # tiny | base
        try:
            return await loop.run_in_executor(None, transcribe_whisper, pcm_bytes, size)
        except Exception as e:
            log.warning(f"Whisper a echoue ({e}), fallback Vosk...")
            return await loop.run_in_executor(None, transcribe_vosk, pcm_bytes)
    else:
        log.warning(f"Moteur STT inconnu : {engine}. Fallback Vosk.")
        return await loop.run_in_executor(None, transcribe_vosk, pcm_bytes)
