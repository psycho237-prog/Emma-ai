"""
EMMA v2.0 — Action Engine (Router)
Dispatch les intentions LLM vers les modules d'action correspondants.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import logging

log = logging.getLogger("emma.action_engine")


async def execute(intent: dict) -> str:
    """
    Recoit un dictionnaire LLM :
      { "action": "module.sous_action", "params": {...}, "response": "...", "steps": [] }
    Retourne un message de resultat (str).
    """
    action = intent.get("action", "none")
    params = intent.get("params", {})

    if action == "none" or not action:
        return intent.get("response", "")

    module_name, _, sub_action = action.partition(".")
    module_name = module_name.strip().lower()

    log.info(f"[ActionEngine] Module : {module_name} | Sous-action : {sub_action} | Params : {params}")

    try:
        if module_name == "system":
            from actions import system as mod
            return await mod.execute(sub_action, params)

        elif module_name == "apps":
            from actions import apps as mod
            return await mod.execute(sub_action, params)

        elif module_name == "files":
            from actions import files as mod
            return await mod.execute(sub_action, params)

        elif module_name == "web":
            from actions import web as mod
            return await mod.execute(sub_action, params)

        elif module_name == "documents":
            from actions import documents as mod
            return await mod.execute(sub_action, params)

        elif module_name == "terminal":
            from actions import terminal as mod
            return await mod.execute(sub_action, params)

        elif module_name == "music":
            from actions import music as mod
            return await mod.execute(sub_action, params)

        else:
            log.warning(f"[ActionEngine] Module inconnu : {module_name}")
            return intent.get("response", f"Je ne sais pas executer l'action '{action}', Monsieur.")

    except Exception as e:
        log.error(f"[ActionEngine] Erreur lors de l'execution de '{action}' : {e}", exc_info=True)
        return f"Une erreur est survenue lors de l'execution, Monsieur : {str(e)}"
