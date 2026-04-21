"""
EMMA v2.0 — Memoire conversationnelle
Court terme (RAM) + Long terme (preferences.json) + Journal de bord
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import datetime
import json
import logging
import os

from config import EMMA_DATA_DIR, PREFERENCES_FILE

log = logging.getLogger("emma.memory")

os.makedirs(EMMA_DATA_DIR, exist_ok=True)


# ─── Memoire court terme (session) ────────────────────────────────────────────

class ShortTermMemory:
    """Historique de la conversation en cours (perdu a la fermeture)."""

    def __init__(self, max_turns: int = 10):
        self._history: list[dict] = []
        self._max = max_turns

    def add_user(self, text: str):
        self._history.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str):
        self._history.append({"role": "assistant", "content": text})
        self._trim()

    def _trim(self):
        # Garde les derniers max_turns echanges
        if len(self._history) > self._max * 2:
            self._history = self._history[-(self._max * 2):]

    def get(self) -> list[dict]:
        return list(self._history)

    def clear(self):
        self._history.clear()
        log.info("[Memoire] Session effacee.")


# ─── Memoire long terme (preferences.json) ────────────────────────────────────

def load_preferences() -> dict:
    """Charge les preferences utilisateur depuis ~/.emma/preferences.json."""
    if not os.path.exists(PREFERENCES_FILE):
        return {}
    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"[Memoire] Erreur lecture preferences : {e}")
        return {}


def save_preferences(prefs: dict):
    """Sauvegarde les preferences utilisateur."""
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
        log.info("[Memoire] Preferences sauvegardees.")
    except IOError as e:
        log.error(f"[Memoire] Erreur ecriture preferences : {e}")


def get_preference(key: str, default=None):
    prefs = load_preferences()
    return prefs.get(key, default)


def set_preference(key: str, value):
    prefs = load_preferences()
    prefs[key] = value
    save_preferences(prefs)


# ─── Journal de bord ──────────────────────────────────────────────────────────

def _journal_path() -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(EMMA_DATA_DIR, f"journal_{today}.json")


def log_action(action: str, params: dict, result: str):
    """Enregistre une action dans le journal du jour."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action":    action,
        "params":    params,
        "result":    result,
    }
    path    = _journal_path()
    journal = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                journal = json.load(f)
        except Exception:
            journal = []

    journal.append(entry)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(journal, f, ensure_ascii=False, indent=2)
    except IOError as e:
        log.error(f"[Journal] Erreur ecriture : {e}")


def read_today_journal() -> list[dict]:
    """Retourne toutes les entrees du journal d'aujourd'hui."""
    path = _journal_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ─── Instance globale court terme ─────────────────────────────────────────────
short_term = ShortTermMemory(max_turns=10)
