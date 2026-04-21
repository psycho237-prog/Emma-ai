"""
EMMA v2.0 — Module Recherche Web & Synthese
Utilise DuckDuckGo (sans cle API) + BeautifulSoup pour scraping.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("emma.actions.web")


async def execute(sub_action: str, params: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _dispatch, sub_action, params)


def _dispatch(sub_action: str, params: dict) -> str:
    handlers = {
        "search":    _search,
        "synthesize": _synthesize,
        "news":      _news,
        "weather":   _weather,
        "save":      _save,
    }
    fn = handlers.get(sub_action)
    return fn(params) if fn else f"Action web '{sub_action}' inconnue, Monsieur."


# ─── Recherche rapide ─────────────────────────────────────────────────────────

def _search(params: dict) -> str:
    query = params.get("query", "")
    if not query:
        return "Veuillez preciser votre requete, Monsieur."

    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(query, max_results=3))
        if not results:
            return f"Aucun resultat pour '{query}', Monsieur."

        summary = results[0].get("body", "Pas de description disponible.")
        return f"Voici ce que j'ai trouve pour '{query}', Monsieur : {summary[:300]}"
    except Exception as e:
        log.error(f"[Web] Recherche echouee : {e}")
        return f"Impossible d'effectuer la recherche pour le moment, Monsieur."


# ─── Synthese multi-sources ────────────────────────────────────────────────────

def _synthesize(params: dict) -> str:
    entity = params.get("entity", params.get("query", ""))
    if not entity:
        return "Preciser l'entite a analyser, Monsieur."

    try:
        from duckduckgo_search import DDGS
        results  = list(DDGS().text(f"{entity} site web entreprise informations", max_results=5))
        snippets = [r.get("body", "") for r in results if r.get("body")]
        combined = " ".join(snippets)[:1500]

        if not combined:
            return f"Pas assez d'informations trouvees sur '{entity}', Monsieur."

        # Resume simple (sans LLM additionnel)
        sentences = combined.split(". ")[:4]
        resume    = ". ".join(sentences)
        return f"Synthese sur '{entity}', Monsieur : {resume}."
    except Exception as e:
        log.error(f"[Web] Synthese echouee : {e}")
        return "Impossible de synthetiser les informations pour le moment, Monsieur."


# ─── Actualites ───────────────────────────────────────────────────────────────

def _news(params: dict) -> str:
    topic = params.get("topic", "actualites")
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().news(topic, max_results=3))
        if not results:
            return f"Aucune actualite sur '{topic}' trouvee, Monsieur."

        items = [f"— {r['title']} ({r.get('source', '')})" for r in results[:3]]
        return f"Dernieres actualites sur '{topic}', Monsieur :\n" + "\n".join(items)
    except Exception as e:
        log.error(f"[Web] Actualites echouees : {e}")
        return "Impossible de recuperer les actualites pour le moment, Monsieur."


# ─── Meteo ────────────────────────────────────────────────────────────────────

def _weather(params: dict) -> str:
    city = params.get("city", "Yaounde")
    try:
        import urllib.request
        url  = f"https://wttr.in/{city}?format=3"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read().decode("utf-8").strip()
        return f"Meteo a {city}, Monsieur : {data}."
    except Exception as e:
        log.error(f"[Web] Meteo echouee : {e}")
        return f"Impossible de recuperer la meteo de {city} pour le moment, Monsieur."


# ─── Sauvegarde resultat ──────────────────────────────────────────────────────

def _save(params: dict) -> str:
    content  = params.get("content", "")
    filename = params.get("filename", f"recherche_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    path     = Path.home() / "Documents" / filename

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Resultat sauvegarde dans '{path}', Monsieur."
    except Exception as e:
        return f"Erreur lors de la sauvegarde : {e}, Monsieur."
