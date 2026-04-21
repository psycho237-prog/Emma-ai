"""
EMMA v2.0 — Module Systeme & Applications
Controle volume, verrouillage, capture ecran, shutdown, etc.
Cross-platform : Linux + Windows
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import datetime
import logging
import platform
import subprocess

import pyautogui
import psutil

log = logging.getLogger("emma.actions.system")
OS = platform.system()


async def execute(sub_action: str, params: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _dispatch, sub_action, params)


def _dispatch(sub_action: str, params: dict) -> str:
    handlers = {
        "volume":      _volume,
        "mute":        _mute,
        "lock":        _lock,
        "shutdown":    _shutdown,
        "restart":     _restart,
        "screenshot":  _screenshot,
        "brightness":  _brightness,
        "time":        _time,
        "hotspot":     _hotspot,
    }
    fn = handlers.get(sub_action)
    if fn:
        return fn(params)
    return f"Action systeme '{sub_action}' inconnue, Monsieur."


# ─── Reseau / Hotspot ─────────────────────────────────────────────────────────

def _hotspot(params: dict) -> str:
    state = params.get("state", "on") # on | off
    if OS == "Windows":
        # Script PowerShell pour activer le hotspot mobile Windows
        ps_script = f"""
        $connectionProfile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
        $tetheringManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($connectionProfile)
        if ('{state}' -eq 'on') {{ $tetheringManager.StartTetheringAsync() }} else {{ $tetheringManager.StopTetheringAsync() }}
        """
        try:
            import base64
            encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode()
            subprocess.run(["powershell", "-EncodedCommand", encoded], capture_output=True)
            return f"Point d'acces sans fil {'active' if state=='on' else 'desactive'}, Monsieur."
        except Exception as e:
            return f"Erreur lors de la gestion du hotspot Windows : {e}"
    else:
        # Linux (Utilise NetworkManager / nmcli)
        try:
            # On suppose qu'un profil "Hotspot" existe ou on tente de lever l'interface
            cmd = ["nmcli", "con", "up" if state == "on" else "down", "Hotspot"]
            subprocess.run(cmd, capture_output=True)
            return f"Point d'acces {'active' if state=='on' else 'desactive'} via NetworkManager, Monsieur."
        except Exception:
            return "Action hotspot non supportee sur ce Linux (nmcli manquant ou profil 'Hotspot' absent)."
    return "Action hotspot non supportee sur cet OS, Monsieur."




# ─── Volume ────────────────────────────────────────────────────────────────────

def _volume(params: dict) -> str:
    direction = params.get("direction", "up")   # up | down | set
    value     = params.get("value", 10)

    if OS == "Linux":
        sign = "+" if direction == "up" else ("-" if direction == "down" else "")
        if direction == "set":
            cmd = f"pactl set-sink-volume @DEFAULT_SINK@ {value}%"
        else:
            cmd = f"pactl set-sink-volume @DEFAULT_SINK@ {sign}{value}%"
        subprocess.run(cmd, shell=True)
    elif OS == "Windows":
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        iface   = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume  = cast(iface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        if direction == "up":
            volume.SetMasterVolumeLevelScalar(min(1.0, current + value / 100), None)
        elif direction == "down":
            volume.SetMasterVolumeLevelScalar(max(0.0, current - value / 100), None)
        else:
            volume.SetMasterVolumeLevelScalar(value / 100, None)

    return f"Volume {'augmente' if direction=='up' else 'reduit'}, Monsieur."


def _mute(params: dict) -> str:
    if OS == "Linux":
        subprocess.run("pactl set-sink-mute @DEFAULT_SINK@ toggle", shell=True)
    elif OS == "Windows":
        pyautogui.press("volumemute")
    return "Son coupe, Monsieur."


# ─── Securite ─────────────────────────────────────────────────────────────────

def _lock(params: dict) -> str:
    if OS == "Linux":
        subprocess.Popen(["gnome-screensaver-command", "--lock"])
    elif OS == "Windows":
        import ctypes
        ctypes.windll.user32.LockWorkStation()
    return "Station de travail verrouillee, Monsieur."


def _shutdown(params: dict) -> str:
    delay = params.get("delay", 0)
    if OS == "Linux":
        subprocess.run(f"sudo shutdown -h +{delay}", shell=True)
    elif OS == "Windows":
        subprocess.run(f"shutdown /s /t {delay * 60}", shell=True)
    return "Extinction du systeme en cours, Monsieur. A bientot."


def _restart(params: dict) -> str:
    if OS == "Linux":
        subprocess.run("sudo reboot", shell=True)
    elif OS == "Windows":
        subprocess.run("shutdown /r /t 5", shell=True)
    return "Redemarrage du systeme, Monsieur."


# ─── Capture ecran ────────────────────────────────────────────────────────────

def _screenshot(params: dict) -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path      = params.get("path", f"capture_{timestamp}.png")
    img       = pyautogui.screenshot()
    img.save(path)
    return f"Capture ecran sauvegardee : {path}, Monsieur."


# ─── Luminosite ──────────────────────────────────────────────────────────────

def _brightness(params: dict) -> str:
    direction = params.get("direction", "down")
    value     = params.get("value", 20)
    if OS == "Linux":
        try:
            import subprocess as sp
            result  = sp.run(
                "cat /sys/class/backlight/*/brightness",
                shell=True, capture_output=True, text=True
            )
            current = int(result.stdout.strip() or 100)
            new_val = max(10, min(100, current + (value if direction == "up" else -value)))
            sp.run(f"echo {new_val} | sudo tee /sys/class/backlight/*/brightness", shell=True)
        except Exception:
            pass
    elif OS == "Windows":
        try:
            import wmi
            c = wmi.WMI(namespace="wmi")
            methods = c.WmiMonitorBrightnessMethods()[0]
            methods.WmiSetBrightness(value, 0)
        except Exception:
            pass
    return f"Luminosite {'augmentee' if direction=='up' else 'reduite'}, Monsieur."


# ─── Heure / Date ─────────────────────────────────────────────────────────────

def _time(params: dict) -> str:
    now = datetime.datetime.now()
    return f"Il est exactement {now.strftime('%H heures %M')}, Monsieur."



# Stockage interne pour le cooldown (en secondes)
_LAST_GREETING_TIME = 0

def get_greeting() -> str:
    """Retourne une salutation polie basee sur l'heure, avec cooldown de 5 mins."""
    import random
    import time
    from config import WAKE_RESPONSES
    global _LAST_GREETING_TIME
    
    now_ts = time.time()
    
    # Si on l'a salue il y a moins de 5 minutes (300 secondes)
    if (now_ts - _LAST_GREETING_TIME) < 300:
        short_responses = ["Oui ?", "Je vous écoute.", "Oui Monsieur ?", "Je suis là.", "Présente."]
        return random.choice(short_responses)
    
    # Sinon, on fait la salutation complète
    _LAST_GREETING_TIME = now_ts
    
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        prefix = "Bonjour Monsieur."
    elif 12 <= hour < 18:
        prefix = "Bon apres-midi Monsieur."
    else:
        prefix = "Bonsoir Monsieur."
        
    response = random.choice(WAKE_RESPONSES)
    return f"{prefix} {response}"


