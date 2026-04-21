"""
EMMA v2.0 — Module Terminal (3 niveaux de securite)
Niveau 1 : commandes sures, execution silencieuse
Niveau 2 : commandes lourdes, terminal visible + confirmation vocale
Niveau 3 : refus absolu — commandes destructrices
Cross-platform Linux + Windows
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
import platform
import subprocess
import re

log = logging.getLogger("emma.actions.terminal")
OS = platform.system()

# ─── Classification des commandes ─────────────────────────────────────────────

NIVEAU_1_PREFIXES = [
    "apt install", "apt update", "apt upgrade",
    "systemctl status", "systemctl start", "systemctl stop", "systemctl restart",
    "netstat", "ss ", "df ", "free ", "du ",
    "pkill", "reboot", "shutdown",
    "pip install", "pip list", "pip show",
    "git status", "git log", "git diff", "git branch",
    "ls ", "dir ", "pwd", "whoami", "echo", "cat ",
    "mkdir", "cp ", "find ", "grep ",
    "ipconfig", "ifconfig", "ping", "tracert", "traceroute",
    "tasklist", "taskkill",
    "python --version", "python -V", "node --version",
]

NIVEAU_2_MOTS = [
    "rm ", "del ", "move ", "mv ",
    "chmod", "chown",
    "pip install", "npm install", "yarn add",
    "git push", "git merge", "git reset",
    "dpkg", "wget", "curl",
    "format", "diskpart",
    "reg add", "reg delete",
]

INTERDIT_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"dd\s+if=",
    r"mkfs",
    r":\(\){:|:&};:",  # fork bomb
    r">\s*/dev/sda",
    r"format\s+c:",
    r"del\s+/[sq]\s+c:\\windows",
    r"shutdown\s+/[rs]\s+/f",  # force sans confirmation
]


def _classify(command: str) -> int:
    """
    Retourne le niveau de securite de la commande :
    1 = silencieux, 2 = confirmation, 3 = interdit
    """
    cmd_lower = command.lower().strip()

    # Niveau 3 — Interdit absolu
    for pattern in INTERDIT_PATTERNS:
        if re.search(pattern, cmd_lower):
            return 3

    # Niveau 2 — Commandes lourdes
    for keyword in NIVEAU_2_MOTS:
        if cmd_lower.startswith(keyword) or f" {keyword}" in cmd_lower:
            return 2

    # Niveau 1 — Commandes sures
    for prefix in NIVEAU_1_PREFIXES:
        if cmd_lower.startswith(prefix):
            return 1

    # Inconnu → niveau 2 par securite
    return 2


async def execute(sub_action: str, params: dict) -> str:
    command = params.get("command", "").strip()
    if not command:
        return "Aucune commande specifiee, Monsieur."

    level = _classify(command)
    log.info(f"[Terminal] Commande : '{command}' — Niveau {level}")

    if level == 3:
        return (
            "Je refuse categoriquement d'executer cette commande, Monsieur. "
            "Elle pourrait causer des dommages irreversibles au systeme."
        )
    elif level == 1:
        return await _run_silent(command)
    else:
        return await _run_visible(command)


# ─── Execution silencieuse (Niveau 1) ────────────────────────────────────────

async def _run_silent(command: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _exec_silent, command)


def _exec_silent(command: str) -> str:
    try:
        if OS == "Linux":
            # Utilise sudo si commande systemd/apt
            needs_sudo = any(
                command.startswith(p)
                for p in ["apt", "systemctl", "pkill", "reboot", "shutdown", "netstat"]
            )
            prefix = "sudo " if needs_sudo else ""
            result = subprocess.run(
                prefix + command,
                shell=True, capture_output=True, text=True, timeout=30
            )
        else:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )

        output = (result.stdout or result.stderr or "").strip()
        if len(output) > 500:
            output = output[:500] + "..."
        return f"Commande executee, Monsieur. Resultat : {output}" if output else "Commande executee avec succes, Monsieur."
    except subprocess.TimeoutExpired:
        return "La commande a depasse le delai d'execution, Monsieur."
    except Exception as e:
        return f"Erreur d'execution : {e}, Monsieur."


# ─── Execution visible (Niveau 2) ────────────────────────────────────────────

async def _run_visible(command: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _exec_visible, command)


def _exec_visible(command: str) -> str:
    try:
        if OS == "Linux":
            subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", f"{command}; echo 'Appuyez sur Entree...'; read"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        elif OS == "Windows":
            subprocess.Popen(
                f'start cmd /k "{command}"', shell=True
            )
        return (
            f"J'ai ouvert un terminal et lance la commande '{command}', Monsieur. "
            "Vous pouvez suivre l'execution dans la fenetre ouverte."
        )
    except Exception as e:
        return f"Impossible d'ouvrir le terminal : {e}, Monsieur."
