"""
EMMA v2.0 — Module Applications
Ouverture et fermeture d'applications. Cross-platform Linux + Windows.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import platform
import subprocess

log = logging.getLogger("emma.actions.apps")
OS = platform.system()

# ─── Equivalences app : nom naturel -> commande Linux / executable Windows ─────
APP_MAP = {
    # Editeurs / IDE
    "vscode":       {"linux": "code",               "windows": "code.exe"},
    "vs code":      {"linux": "code",               "windows": "code.exe"},
    "notepad":      {"linux": "gedit",              "windows": "notepad.exe"},
    "sublime":      {"linux": "subl",               "windows": "subl.exe"},
    # Navigateurs
    "chrome":       {"linux": "google-chrome",      "windows": "chrome.exe"},
    "firefox":      {"linux": "firefox",            "windows": "firefox.exe"},
    "edge":         {"linux": "microsoft-edge",     "windows": "msedge.exe"},
    # Fichiers
    "explorateur":  {"linux": "nautilus",           "windows": "explorer.exe"},
    "explorer":     {"linux": "nautilus",           "windows": "explorer.exe"},
    # Terminal
    "terminal":     {"linux": "gnome-terminal",     "windows": "cmd.exe"},
    "cmd":          {"linux": "gnome-terminal",     "windows": "cmd.exe"},
    "powershell":   {"linux": "bash",               "windows": "powershell.exe"},
    # Communication
    "discord":      {"linux": "discord",            "windows": "Discord.exe"},
    "whatsapp":     {"linux": "whatsapp-desktop",   "windows": "WhatsApp.exe"},
    # Media
    "vlc":          {"linux": "vlc",                "windows": "vlc.exe"},
    "spotify":      {"linux": "spotify",            "windows": "Spotify.exe"},
    # Bureautique
    "word":         {"linux": "libreoffice --writer", "windows": "WINWORD.EXE"},
    "excel":        {"linux": "libreoffice --calc",   "windows": "EXCEL.EXE"},
    # Autres
    "calculatrice": {"linux": "gnome-calculator",   "windows": "calc.exe"},
    "paint":        {"linux": "gimp",               "windows": "mspaint.exe"},
}


async def execute(sub_action: str, params: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _dispatch, sub_action, params)


def _dispatch(sub_action: str, params: dict) -> str:
    if sub_action == "open":
        return _open(params)
    elif sub_action == "close":
        return _close(params)
    return f"Action application '{sub_action}' inconnue, Monsieur."


def _open(params: dict) -> str:
    app_name = params.get("app", "").lower().strip()

    # Recherche dans la table d'equivalences
    entry = APP_MAP.get(app_name)
    if entry:
        cmd = entry.get("linux" if OS == "Linux" else "windows", app_name)
    else:
        cmd = app_name  # Tentative directe avec le nom donne

    try:
        if OS == "Linux":
            subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif OS == "Windows":
            subprocess.Popen(cmd, shell=True)
        log.info(f"[Apps] Ouverture : {cmd}")
        return f"J'ouvre {app_name} pour vous, Monsieur."
    except FileNotFoundError:
        return f"Je n'ai pas trouve l'application '{app_name}', Monsieur."
    except Exception as e:
        return f"Impossible d'ouvrir '{app_name}' : {e}, Monsieur."


def _close(params: dict) -> str:
    app_name = params.get("app", "").lower().strip()
    import psutil

    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        if app_name in proc.info["name"].lower():
            try:
                proc.terminate()
                killed.append(proc.info["name"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    if killed:
        return f"J'ai ferme : {', '.join(set(killed))}, Monsieur."
    return f"Aucun processus '{app_name}' trouve en cours d'execution, Monsieur."
