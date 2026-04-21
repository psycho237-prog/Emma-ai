"""
EMMA v2.0 — Module Musique
Lecture locale + stream YouTube via yt-dlp + mpv.
Memorisation des chansons favorites.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import os
import platform
import random
import subprocess
from pathlib import Path

from memory import get_preference, set_preference

log = logging.getLogger("emma.actions.music")
OS = platform.system()

# ─── Dossiers de musique scannables ───────────────────────────────────────────
MUSIC_DIRS = []
for candidate in ["Musique", "Music", "Downloads", "Telechargements"]:
    p = Path.home() / candidate
    if p.exists():
        MUSIC_DIRS.append(p)

AUDIO_EXTS = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac"}

# ─── Categories d'ambiance ────────────────────────────────────────────────────
AMBIANCE_KEYWORDS = {
    "lofi":      ["lofi", "lo-fi", "chill beats", "study"],
    "jazz":      ["jazz", "swing", "bossa nova", "blues"],
    "chill":     ["chill", "relax", "ambient", "calm"],
    "afrobeats": ["afro", "afrobeats", "afropop", "cameroun", "cameroon"],
    "focus":     ["focus", "concentration", "deep work", "productivity"],
    "classique": ["classique", "classical", "mozart", "beethoven", "piano"],
}

# Processus mpv actif
_mpv_process: subprocess.Popen | None = None
_mpv_socket = "/tmp/emma_mpv_socket"


async def execute(sub_action: str, params: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _dispatch, sub_action, params)


def _dispatch(sub_action: str, params: dict) -> str:
    handlers = {
        "play":          _play,
        "stop":          _stop,
        "volume":        _volume,
        "save_favorite": _save_favorite,
        "favorite":      _play_favorite,
    }
    fn = handlers.get(sub_action)
    return fn(params) if fn else f"Action musique '{sub_action}' inconnue, Monsieur."


# ─── Lecture ──────────────────────────────────────────────────────────────────

def _play(params: dict) -> str:
    genre   = params.get("genre", "").lower()
    query   = params.get("query", genre)
    offline = params.get("offline", False)

    # 1. Tente la musique locale
    local_file = _find_local(genre or query)
    if local_file:
        return _play_file(str(local_file))

    # 2. Fallback YouTube via yt-dlp si connexion dispo
    if not offline:
        return _play_youtube(query or "lofi chill music")

    return "Aucune musique locale trouvee et pas de connexion disponible, Monsieur."


def _find_local(query: str) -> Path | None:
    """Cherche un fichier audio local correspondant au genre/requete."""
    candidates = []
    for music_dir in MUSIC_DIRS:
        for f in music_dir.rglob("*"):
            if f.suffix.lower() in AUDIO_EXTS:
                if not query or query.lower() in f.name.lower() or query.lower() in str(f.parent).lower():
                    candidates.append(f)
    return random.choice(candidates) if candidates else None


def _find_vlc():
    """Trouve le binaire VLC sur Windows."""
    candidates = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "vlc"  # Tente dans le PATH si non trouve


def _play_file(path: str) -> str:
    global _mpv_process
    _stop_music()
    filename = Path(path).name
    try:
        # Essayer MPV
        cmd = ["mpv", "--no-video", f"--input-ipc-server={_mpv_socket}", path]
        _mpv_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info(f"[Music] Lecture locale (mpv) : {filename}")
        return f"Je lance '{filename}', Monsieur. Bonne ecoute."
    except Exception:
        # Fallback VLC
        vlc_bin = _find_vlc()
        try:
            # On enleve -I dummy pour voir la fenetre, et on garde vlc_bin
            cmd = [vlc_bin, "--play-and-exit", path]
            _mpv_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info(f"[Music] Lecture locale (vlc) : {filename}")
            return f"Je lance '{filename}' via VLC, Monsieur."
        except Exception:
            # Dernier recours
            if OS == "Windows":
                os.startfile(path)
            return f"Ouverture de '{filename}', Monsieur."


def _play_youtube(query: str) -> str:
    global _mpv_process
    _stop_music()
    
    # 1. Tentative MPV (directement supporte par ytdl)
    try:
        search_url = f"ytdl://ytsearch1:{query}"
        cmd = [
            "mpv", "--no-video",
            f"--input-ipc-server={_mpv_socket}",
            "--ytdl-format=bestaudio",
            search_url,
        ]
        _mpv_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info(f"[Music] Stream YouTube (mpv) : {query}")
        return f"Je lance '{query}' depuis YouTube, Monsieur. Un instant..."
    except Exception:
        # 2. Fallback VLC + yt-dlp manuel
        log.info("[Music] MPV absent, tentative VLC + yt-dlp...")
        try:
            # Extraire l'URL directe avec yt-dlp
            extract_cmd = ["yt-dlp", "-g", "--format", "bestaudio", f"ytsearch1:{query}"]
            res = subprocess.run(extract_cmd, capture_output=True, text=True, timeout=10)
            stream_url = res.stdout.strip()
            
            if not stream_url:
                return "Je n'ai pas pu trouver de flux audio pour cette recherche, Monsieur."

            vlc_bin = _find_vlc()
            # On enleve -I dummy et --no-video pour voir le lecteur
            cmd = [vlc_bin, "--play-and-exit", stream_url]
            _mpv_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Je lance '{query}' en streaming direct sur VLC, Monsieur."

        except Exception as e:
            log.error(f"[Music] Echec VLC/ytdlp : {e}")
            return "Impossible de lire la musique depuis YouTube sans MPV ou VLC configure, Monsieur."



# ─── Arret ────────────────────────────────────────────────────────────────────

# ─── Arret ────────────────────────────────────────────────────────────────────

def _stop_music():
    global _mpv_process
    if _mpv_process and _mpv_process.poll() is None:
        _mpv_process.terminate()
        try:
            _mpv_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _mpv_process.kill()
        
        # Sur Windows, on force parfois pour VLC
        if OS == "Windows":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(_mpv_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        _mpv_process = None


def _stop(params: dict) -> str:
    _stop_music()
    return "Musique arretee, Monsieur."



# ─── Volume ───────────────────────────────────────────────────────────────────

def _volume(params: dict) -> str:
    direction = params.get("direction", "down")
    amount    = params.get("amount", 10)

    try:
        import socket as sock
        s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
        s.connect(_mpv_socket)
        cmd = {"command": ["add", "volume", amount if direction == "up" else -amount]}
        import json
        s.sendall((json.dumps(cmd) + "\n").encode())
        s.close()
        return f"Volume musique {'augmente' if direction=='up' else 'diminue'}, Monsieur."
    except Exception:
        return "Impossible de modifier le volume de la musique, Monsieur."


# ─── Favoris ──────────────────────────────────────────────────────────────────

def _save_favorite(params: dict) -> str:
    song  = params.get("song", params.get("query", ""))
    genre = params.get("genre", "general")
    prefs = get_preference("music", {})
    if not isinstance(prefs, dict):
        prefs = {}
    prefs[genre] = song
    set_preference("music", prefs)
    return f"J'ai memorise '{song}' comme votre chanson favorite ({genre}), Monsieur."


def _play_favorite(params: dict) -> str:
    genre = params.get("genre", "general")
    prefs = get_preference("music", {})
    song  = prefs.get(genre) if isinstance(prefs, dict) else None
    if not song:
        return f"Vous n'avez pas encore de favori enregistre pour '{genre}', Monsieur."
    return _play({"query": song})
