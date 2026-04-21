"""
EMMA v2.0 — Interface LLM
Supporte : TinyLlama (offline via llama-cpp-python) + Claude API (online)
Retourne toujours un JSON structure : { action, params, response, steps }
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import datetime
import json
import logging
import os
import platform
import socket

import psutil

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    EMMA_CREATOR,
    EMMA_NAME,
    EMMA_VERSION,
    TINYLLAMA_MODEL_PATH,
    ACTIVE_PROJECTS,
)

log = logging.getLogger("emma.llm")

# ─── Modele TinyLlama (charge une seule fois) ─────────────────────────────────
_llama_model = None


def _load_tinyllama():
    global _llama_model
    if _llama_model is None:
        # Windows Python 3.8+ : ajouter explicitement le repertoire DLL
        if platform.system() == "Windows":
            import importlib.util
            spec = importlib.util.find_spec("llama_cpp")
            if spec and spec.origin:
                lib_dir = os.path.join(os.path.dirname(spec.origin), "lib")
                if os.path.isdir(lib_dir):
                    os.add_dll_directory(lib_dir)
                    log.info(f"DLL directory ajoute : {lib_dir}")

        from llama_cpp import Llama
        log.info(f"Chargement TinyLlama : {TINYLLAMA_MODEL_PATH}")
        _llama_model = Llama(
            model_path=TINYLLAMA_MODEL_PATH,
            n_ctx=2048,
            n_threads=os.cpu_count() or 4,
            verbose=False,
        )
        log.info("TinyLlama charge.")
    return _llama_model


# ─── Contexte dynamique ────────────────────────────────────────────────────────

def _build_context() -> str:
    now      = datetime.datetime.now().strftime("%A %d %B %Y, %H:%M")
    os_type  = platform.system()
    ram_mb   = int(psutil.virtual_memory().available / (1024 ** 2))
    try:
        wifi_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        wifi_ip = "inconnu"

    return (
        f"Date/Heure : {now}\n"
        f"OS : {os_type}\n"
        f"IP PC : {wifi_ip}\n"
        f"RAM disponible : {ram_mb} MB\n"
        f"Projets actifs : {', '.join(ACTIVE_PROJECTS)}\n"
    )


# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Tu es EMMA (Embedded Modular Multi-purpose Assistant),
assistante personnelle vocale de Monsieur ONANA GREGOIRE LEGRAND,
developpee a Yaounde, au Cameroun.

IDENTITE (reponses hardcodees) :
- Ton nom : EMMA
- Ton createur : {EMMA_CREATOR}
- Ta version : {EMMA_VERSION}
- Tu communiques en francais, style formel, tu appelles l'utilisateur "Monsieur"
- Ta voix est feminine

COMPORTEMENT :
- Tu comprends le langage naturel SANS commandes predefinies
- Tu analyses l'INTENTION reelle, pas les mots exacts
- Tu tiens compte du CONTEXTE injecte (heure, OS, RAM, fichiers, projets)
- Pour les taches complexes, tu PLANIFIES avant d'agir
- Si ambigu, tu poses UNE seule question de clarification
- Tu confirmes les actions sensibles (suppression, arret PC, etc.)

ACTIONS DISPONIBLES (schemas JSON) :
  system    : volume, lock, shutdown, restart, screenshot, brightness, time
  apps      : open, close
  files     : scan, organize, find, rename, delete_duplicates, report
  web       : search, synthesize, news, weather, save
  documents : report, note, summary, journal, prospection
  terminal  : execute (3 niveaux de securite)
  music     : play, stop, volume, save_favorite

RETOURNE UNIQUEMENT un JSON valide :
{{
  "action": "nom_du_module.sous_action",
  "params": {{}},
  "response": "texte que tu vas prononcer vocalement, Monsieur",
  "steps": []
}}

Si tu ne peux pas agir, retourne action="none" avec une reponse vocale.
"""


# ─── Appel LLM ────────────────────────────────────────────────────────────────

def _call_tinyllama(user_text: str, history: list[dict]) -> dict:
    """Appelle TinyLlama localement avec un prompt simplifie pour sa taille."""
    model = _load_tinyllama()

    # Prompt minimal pour eviter que TinyLlama s'egare
    # On lui donne juste l'essentiel : Action + Reponse en francais
    prompt = (
        f"<|im_start|>system\nTu es EMMA, une assistante vocale en francais. "
        "Tu reponds TOUJOURS en JSON valide. "
        "Format: {\"action\": \"module.action\", \"params\": {}, \"response\": \"Ta reponse vocale ici, Monsieur\"}\n"
        f"CONTEXTE: {datetime.datetime.now().strftime('%H:%M')}\n<|im_end|>\n"
        f"<|im_start|>user\n{user_text}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    output = model(prompt, max_tokens=150, stop=["<|im_end|>", "User:"], echo=False)
    raw    = output["choices"][0]["text"].strip()

    return _parse_llm_output(raw)



def _call_claude(user_text: str, history: list[dict]) -> dict:
    """Appelle l'API Claude Anthropic."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_with_context = SYSTEM_PROMPT + "\n\nCONTEXTE ACTUEL:\n" + _build_context()

    messages = []
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_text})

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=system_with_context,
        messages=messages,
    )
    raw = response.content[0].text.strip()
    return _parse_llm_output(raw)


def _parse_llm_output(raw: str) -> dict:
    """Parse la sortie JSON du LLM. Fallback robuste si invalide."""
    try:
        # Extraire JSON si entoure de texte parasite
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass

    log.warning(f"[LLM] Sortie non-JSON : '{raw[:100]}'")
    return {
        "action":   "none",
        "params":   {},
        "response": raw if raw else "Je n'ai pas compris votre demande, Monsieur.",
        "steps":    [],
    }


async def think(user_text: str, history: list[dict], engine: str = "tinyllama") -> dict:
    """
    Point d'entree asynchrone avec priorite aux actions rapides.
    Ordre : Mock -> Gemini (si dispo) -> TinyLlama
    """
    loop = asyncio.get_event_loop()
    user_text_low = user_text.lower()

    # 1. PRIORITE ABSOLUE : Mode Mock (Regles rapides)
    quick_keywords = ["musique", "joue", "mets", "met ", "mettre", "mais", "heure", "temp", "meteo", "cherche", "google", "dossier", "rapport", "verrouille", "lock", "ouvre", "lance", "ferme", "youtube", "navigateur", "redemarre", "restart", "eteindre"]
    if any(kw in user_text_low for kw in quick_keywords):
        log.info("[LLM] Commande rapide detectee (Mock bypass)")
        return _call_mock(user_text)

    # 2. Moteur Intelligent (Cascade)
    from config import GEMINI_API_KEY, ANTHROPIC_API_KEY

    # On priorise Gemini car c'est gratuit
    if GEMINI_API_KEY:
        try:
            return await loop.run_in_executor(None, _call_gemini, user_text, history)
        except Exception as e:
            log.warning(f"[LLM] Gemini echoue : {e}")

    if engine == "claude" or ANTHROPIC_API_KEY:
        try:
            return await loop.run_in_executor(None, _call_claude, user_text, history)
        except Exception: pass

    # IA Locale
    try:
        return await loop.run_in_executor(None, _call_tinyllama, user_text, history)
    except Exception: pass

    # 3. Ultime recours : Mode Mock (Regles simples)
    log.info("[LLM] Fallback -> Mode Mock (Simule)")
    return _call_mock(user_text)


def _call_gemini(user_text: str, history: list[dict]) -> dict:
    """Appelle l'API Google Gemini (Gratuit)."""
    import requests
    from config import GEMINI_API_KEY, SYSTEM_PROMPT
    
    # Utilisation du modele valide par test_gemini.py
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"


    
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXTE:\n{_build_context()}\n\nHISTORIQUE:\n"
    for msg in history[-5:]:
        prompt += f"{msg['role']}: {msg['content']}\n"
    prompt += f"user: {user_text}\nassistant:"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "topP": 0.8}
    }
    
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    try:
        raw = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return _parse_llm_output(raw)
    except Exception:
        log.error(f"[Gemini] Reponse malformee : {data}")
        raise ValueError("Reponse Gemini invalide")




def _call_mock(text: str) -> dict:
    """Reponses pre-definies pour tester les actions sans LLM."""
    text = text.lower().replace(".", "").replace("!", "").replace("?", "").strip()
    
    # --- HEURE ---
    if "heure" in text or "temps" in text:
        return {"action": "system.time", "params": {}, "response": "Je regarde...", "steps": []}

        
    # --- MUSIQUE ---
    if any(kw in text for kw in ["musique", "joue", "mets", "met ", "mettre", "mais"]):
        q = text
        # On nettoie les verbes en amont avec des espaces pour eviter de couper les mots
        for word in ["joue du", "joue de la", "joue", "mettre du", "mettez du", "mets du", "mets de la", "mets", "met de la", "met ", "mettre", "mais de la", "mais du", "mais", "la musique de", "la musique"]:
            if q.startswith(word):
                q = q[len(word):].strip()
                break

        
        query = q.replace("sur youtube", "").strip()
        if not query or len(query) < 2: 
            query = "Juice WRLD"
            
        return {
            "action": "music.play", 
            "params": {"query": query}, 
            "response": f"Tout de suite Monsieur, je lance {query} sur YouTube.", 
            "steps": ["recherche youtube", "streaming vlc"]
        }

    # --- APPLICATIONS & YOUTUBE ---
    if any(kw in text for kw in ["ouvre", "lance", "youtube", "navigateur"]):
        target = "youtube" if "youtube" in text else ("navigateur" if "navigateur" in text else "google chrome")
        return {
            "action": "apps.open",
            "params": {"app": target},
            "response": f"J'ouvre {target} pour vous, Monsieur.",
            "steps": ["recherche application", "lancement"]
        }

    if "verrouille" in text or "lock" in text:
        return {"action": "system.lock", "params": {}, "response": "Je verrouille votre session, Monsieur.", "steps": []}
        
    if "redemarre" in text or "restart" in text:
        return {"action": "system.restart", "params": {}, "response": "Très bien Monsieur, je redémarre le système. À tout de suite.", "steps": []}

    if "eteindre" in text or "éteins" in text or "stop pc" in text or "shutdown" in text:
        return {"action": "system.shutdown", "params": {"delay": 0}, "response": "À vos ordres Monsieur, j'éteins l'ordinateur. Au revoir.", "steps": []}

    if "point d'acces" in text or "point d'accès" in text or "hotspot" in text:
        state = "off" if "désactive" in text or "coupe" in text or "arrête" in text else "on"
        return {"action": "system.hotspot", "params": {"state": state}, "response": f"Tout de suite Monsieur, je {'lance' if state == 'on' else 'coupe'} le point d'accès.", "steps": []}

    if "cherche" in text or "google" in text:


        return {"action": "web.search", "params": {"query": text.replace("cherche", "").replace("google", "").strip()}, "response": "Je lance une recherche.", "steps": []}
        
    if "dossier" in text or "rapport" in text:
        if "supprime" in text:
            return {"action": "files.delete_folder", "params": {"name": "LEO RAPPORT"}, "response": "Je supprime le dossier de votre bureau.", "steps": []}
        return {"action": "files.create_file", "params": {"folder": "LEO RAPPORT", "name": "RAPPORT.TXT", "content": "Rapport Genere par EMMA"}, "response": "Je cree le dossier LEO RAPPORT, Monsieur.", "steps": []}

    return {
        "action": "none",
        "params": {},
        "response": "Je n'ai pas pu reflechir avec mon cerveau IA, mais je suis la. Posez-moi une question sur l'heure ou la musique pour tester mes actions.",
        "steps": []
    }




def _call_ollama(user_text: str, history: list[dict], model_key: str) -> dict:
    """Appelle Ollama local."""
    import ollama

    model_map = {
        "ollama_phi3":    "phi3:mini",
        "ollama_mistral": "mistral:7b",
    }
    model_name = model_map.get(model_key, "phi3:mini")

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nCONTEXTE:\n" + _build_context()}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_text})

    response = ollama.chat(model=model_name, messages=messages)
    raw      = response["message"]["content"].strip()
    return _parse_llm_output(raw)
