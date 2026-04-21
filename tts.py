"""
EMMA v2.0 — Module TTS (Text-to-Speech)
Supporte : Piper TTS (offline, voix feminine) + gTTS (online fallback)
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import os
import subprocess
import tempfile

from config import PIPER_MODEL_PATH, PIPER_CONFIG_PATH, TTS_TEMP_FILE, EMMA_DATA_DIR

log = logging.getLogger("emma.tts")

os.makedirs(EMMA_DATA_DIR, exist_ok=True)


# ─── Piper TTS (offline) ──────────────────────────────────────────────────────

def _synthesize_piper(text: str, out_path: str) -> bool:
    """Appelle le binaire piper local ou systeme."""
    import platform
    is_win = platform.system() == "Windows"

    from config import BASE_DIR
    # Securite : Verifier si les fichiers de voix existent
    if not os.path.exists(PIPER_MODEL_PATH) or not os.path.exists(PIPER_CONFIG_PATH):
        log.warning(f"[Piper] Fichiers de voix manquants dans assets/voices/. Fallback.")
        return False

    piper_bin = "piper" # Par defaut si dans le PATH
    
    # Verifier si le binaire est dans le dossier racine
    local_filename = "piper.exe" if is_win else "piper"
    local_piper = os.path.join(BASE_DIR, local_filename)
    if os.path.exists(local_piper):
        piper_bin = local_piper

    try:
        if is_win:
            # Sur Windows, on utilise shell=True pour gerer les chemins complexes avec espaces
            full_cmd = f'"{piper_bin}" --model "{PIPER_MODEL_PATH}" --config "{PIPER_CONFIG_PATH}" --output_file "{out_path}" --length_scale 1.15'
            proc = subprocess.run(
                full_cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                shell=True,
                timeout=15,
            )
        else:
            # Sur Linux, on utilise une liste de commande plus propre
            proc = subprocess.run(
                [
                    piper_bin,
                    "--model", PIPER_MODEL_PATH,
                    "--config", PIPER_CONFIG_PATH,
                    "--output_file", out_path,
                    "--length_scale", "1.15"
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=15,
            )

        if proc.returncode != 0:
            err_msg = proc.stderr.decode(errors="ignore").strip()
            log.error(f"[Piper] Erreur ({proc.returncode}) : {err_msg}")
            return False
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0

    except (FileNotFoundError, Exception) as e:
        log.warning(f"[Piper] Binaire indisponible ({e}). Fallback gTTS.")
        return False



def _synthesize_gtts(text: str, out_path: str) -> bool:
    """Synthese via Google TTS (necessite Internet)."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="fr", slow=False)
        tts.save(out_path)
        return True
    except Exception as e:
        log.error(f"[gTTS] Echec : {e}")
        return False


def synthesize(text: str, engine: str = "piper") -> str | None:
    """
    Synthetise le texte et retourne le chemin d'un fichier unique.
    """
    import time
    timestamp = int(time.time() * 1000)
    
    if engine == "piper":
        out_path = os.path.join(EMMA_DATA_DIR, f"tts_{timestamp}.wav")
        ok = _synthesize_piper(text, out_path)
        if not ok:
            log.warning("Piper a echoue, tentative gTTS...")
            out_path = os.path.join(EMMA_DATA_DIR, f"tts_{timestamp}.mp3")
            ok = _synthesize_gtts(text, out_path)
    else:
        out_path = os.path.join(EMMA_DATA_DIR, f"tts_{timestamp}.mp3")
        ok = _synthesize_gtts(text, out_path)

    # Nettoyage optionnel des anciens fichiers pour ne pas saturer le disque
    # (On pourrait le faire ici ou au démarrage)
    
    return out_path if ok else None



def read_wav_bytes(path: str) -> bytes:
    """Lit un fichier audio et retourne son contenu en bytes."""
    with open(path, "rb") as f:
        return f.read()


# ─── Wrapper asynchrone ───────────────────────────────────────────────────────

async def speak(text: str, engine: str = "piper") -> bytes | None:
    """
    Synthetise le texte de maniere asynchrone.
    """
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, synthesize, text, engine)
    if path is None:
        return None
    data = await loop.run_in_executor(None, read_wav_bytes, path)
    log.info(f"[TTS] '{text[:60]}...' — {len(data)} bytes generes.")
    return data


# ─── Lecture locale (PC sans ESP32) ───────────────────────────────────────────

def play_local(path: str):
    """Lecture du fichier audio sur le PC en attendant la fin de la lecture."""
    import platform
    import time
    os_type = platform.system()
    abs_path = os.path.abspath(path)
    
    try:
        if os_type == "Linux":
            # On utilise .run au lieu de .Popen pour bloquer
            subprocess.run(["ffplay", "-nodisp", "-autoexit", abs_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os_type == "Windows":
            # On utilise PowerShell pour detecter la fin de lecture
            ps_script = f"""
            $path = '{abs_path}'
            $shell = New-Object -ComObject Shell.Application
            $folder = $shell.Namespace((Split-Path $path))
            $file = $folder.ParseName((Split-Path $path -Leaf))
            $durationString = $folder.GetDetailsOf($file, 27) # Detaille 27 = Duree
            
            # Convertir la duree (00:00:05) en secondes
            if ($durationString -match '(\\d+):(\\d+):(\\d+)') {{
                $duration = [int]$matches[1]*3600 + [int]$matches[2]*60 + [int]$matches[3]
            }} else {{ $duration = 2 }}

            Add-Type -AssemblyName PresentationCore
            $player = New-Object System.Windows.Media.MediaPlayer
            $player.Open($path)
            $player.Play()
            Start-Sleep -Seconds ($duration + 1)
            $player.Close()
            """
            import base64
            encoded_script = base64.b64encode(ps_script.encode('utf-16-le')).decode()
            # On utilise .run pour attendre la fin du script PowerShell
            subprocess.run(["powershell", "-EncodedCommand", encoded_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    except Exception as e:
        log.warning(f"Lecture locale echouee : {e}")


