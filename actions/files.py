"""
EMMA v2.0 — Module Fichiers & Rangement
Scan, organisation intelligente, recherche, renommage, doublons.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import hashlib
import logging
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path

log = logging.getLogger("emma.actions.files")
OS  = platform.system()

# Dossier par defaut selon OS
DEFAULT_DIR = (
    Path.home() / "Bureau" if OS == "Linux"
    else Path.home() / "Desktop"
)


async def execute(sub_action: str, params: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _dispatch, sub_action, params)


def _dispatch(sub_action: str, params: dict) -> str:
    handlers = {
        "scan":              _scan,
        "organize":          _organize,
        "find":              _find,
        "rename":            _rename,
        "delete_duplicates": _delete_duplicates,
        "report":            _report,
        "create_folder":     _create_folder,
        "create_file":       _create_file,
        "delete_folder":     _delete_folder,
        "delete_file":       _delete_file,
    }
    fn = handlers.get(sub_action)
    return fn(params) if fn else f"Action fichier '{sub_action}' inconnue, Monsieur."


# ─── Creation ─────────────────────────────────────────────────────────────────

def _create_folder(params: dict) -> str:
    name = params.get("name", "Nouveau_Dossier")
    path = Path(params.get("path", str(DEFAULT_DIR))) / name
    try:
        path.mkdir(parents=True, exist_ok=True)
        return f"Le dossier '{name}' a ete cree avec succes sur votre bureau, Monsieur."
    except Exception as e:
        return f"Impossible de creer le dossier, Monsieur. Erreur : {e}"


def _create_file(params: dict) -> str:
    name    = params.get("name", "nouveau_fichier.txt")
    content = params.get("content", "Fichier cree par EMMA v2.0")
    folder  = Path(params.get("path", str(DEFAULT_DIR)))
    
    # Si un nom de dossier est specifie dans params (cas de la demande utilisateur)
    if "folder" in params:
        folder = folder / params["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        
    path = folder / name
    try:
        path.write_text(content, encoding="utf-8")
        return f"Le fichier '{name}' a ete cree dans le dossier '{folder.name}', Monsieur."
    except Exception as e:
        return f"Erreur lors de la creation du fichier, Monsieur : {e}"


# ─── Suppression ──────────────────────────────────────────────────────────────

def _delete_folder(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Veuillez preciser le nom du dossier a supprimer, Monsieur."
    path = Path(params.get("path", str(DEFAULT_DIR))) / name
    
    if not path.exists():
        return f"Le dossier '{name}' n'existe pas, Monsieur."
    
    try:
        shutil.rmtree(path)
        return f"Le dossier '{name}' a ete supprime avec succes, Monsieur."
    except Exception as e:
        return f"Impossible de supprimer le dossier '{name}', Monsieur. Erreur : {e}"


def _delete_file(params: dict) -> str:
    name = params.get("name", "")
    if not name:
        return "Veuillez preciser le nom du fichier a supprimer, Monsieur."
    path = Path(params.get("path", str(DEFAULT_DIR))) / name
    
    if not path.exists():
        return f"Le fichier '{name}' n'existe pas, Monsieur."
        
    try:
        path.unlink()
        return f"Le fichier '{name}' a ete supprime, Monsieur."
    except Exception as e:
        return f"Impossible de supprimer le fichier '{name}', Monsieur. Erreur : {e}"



# ─── Scan ──────────────────────────────────────────────────────────────────────

def _scan(params: dict) -> str:
    target = Path(params.get("path", str(DEFAULT_DIR)))
    if not target.exists():
        return f"Le dossier '{target}' n'existe pas, Monsieur."

    files = list(target.rglob("*"))
    total = len([f for f in files if f.is_file()])
    size  = sum(f.stat().st_size for f in files if f.is_file())
    log.info(f"[Files] Scan de '{target}' : {total} fichiers, {size/1024/1024:.1f} MB")
    return (
        f"Scan termine, Monsieur. '{target.name}' contient {total} fichiers "
        f"pour un total de {size / 1024 / 1024:.1f} megaoctets."
    )


# ─── Rangement intelligent ────────────────────────────────────────────────────

# Mapping extension -> dossier cible
EXT_CATEGORIES = {
    ".pdf":  "Documents/PDF",
    ".docx": "Documents/Word",
    ".doc":  "Documents/Word",
    ".xlsx": "Documents/Excel",
    ".xls":  "Documents/Excel",
    ".pptx": "Documents/Presentations",
    ".txt":  "Documents/Textes",
    ".md":   "Documents/Markdown",
    ".jpg":  "Images",
    ".jpeg": "Images",
    ".png":  "Images",
    ".gif":  "Images",
    ".bmp":  "Images",
    ".mp3":  "Musique",
    ".flac": "Musique",
    ".ogg":  "Musique",
    ".wav":  "Musique",
    ".m4a":  "Musique",
    ".mp4":  "Videos",
    ".mkv":  "Videos",
    ".avi":  "Videos",
    ".mov":  "Videos",
    ".py":   "Code/Python",
    ".js":   "Code/JavaScript",
    ".ts":   "Code/TypeScript",
    ".html": "Code/Web",
    ".css":  "Code/Web",
    ".zip":  "Archives",
    ".rar":  "Archives",
    ".7z":   "Archives",
    ".tar":  "Archives",
    ".gz":   "Archives",
    ".exe":  "Executables",
    ".sh":   "Scripts",
    ".bat":  "Scripts",
}


def _organize(params: dict) -> str:
    target = Path(params.get("path", str(DEFAULT_DIR)))
    dry_run = params.get("dry_run", True)  # Simulation par defaut (securite)

    if not target.exists():
        return f"Le dossier '{target}' n'existe pas, Monsieur."

    moved   = 0
    skipped = 0
    for f in target.iterdir():
        if not f.is_file():
            continue
        category = EXT_CATEGORIES.get(f.suffix.lower(), "Divers")
        dest_dir  = target / category
        dest_file = dest_dir / f.name

        if dry_run:
            log.info(f"[Dry-run] {f.name} → {category}/")
            moved += 1
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            if not dest_file.exists():
                shutil.move(str(f), str(dest_file))
                moved += 1
            else:
                skipped += 1

    mode = "simule" if dry_run else "effectue"
    return (
        f"Rangement {mode}, Monsieur. {moved} fichiers deplaces, {skipped} ignorés (doublons)."
        + (" Validez pour appliquer les changements." if dry_run else "")
    )


# ─── Recherche ────────────────────────────────────────────────────────────────

def _find(params: dict) -> str:
    query   = params.get("query", "").lower()
    root    = Path(params.get("path", str(Path.home())))
    results = []

    for f in root.rglob("*"):
        if query in f.name.lower():
            results.append(str(f))
        if len(results) >= 10:
            break

    if not results:
        return f"Aucun fichier correspondant a '{query}' trouve, Monsieur."
    listed = "\n".join(results[:5])
    return f"J'ai trouve {len(results)} fichier(s) correspondant a '{query}', Monsieur :\n{listed}"


# ─── Renommage en masse ────────────────────────────────────────────────────────

def _rename(params: dict) -> str:
    folder  = Path(params.get("path", str(DEFAULT_DIR)))
    prefix  = params.get("prefix", "fichier")
    ext     = params.get("ext", None)

    files = [f for f in folder.iterdir() if f.is_file() and (ext is None or f.suffix == ext)]
    for i, f in enumerate(sorted(files)):
        new_name = f"{prefix}_{i+1:03d}{f.suffix}"
        f.rename(folder / new_name)

    return f"{len(files)} fichiers renommes avec le prefixe '{prefix}', Monsieur."


# ─── Suppression doublons ─────────────────────────────────────────────────────

def _delete_duplicates(params: dict) -> str:
    folder = Path(params.get("path", str(DEFAULT_DIR)))
    hashes: dict[str, Path] = {}
    deleted = 0

    for f in folder.rglob("*"):
        if not f.is_file():
            continue
        h = hashlib.md5(f.read_bytes()).hexdigest()
        if h in hashes:
            log.info(f"[Files] Doublon supprime : {f.name}")
            f.unlink()
            deleted += 1
        else:
            hashes[h] = f

    return f"{deleted} doublon(s) supprime(s) dans '{folder.name}', Monsieur."


# ─── Rapport ──────────────────────────────────────────────────────────────────

def _report(params: dict) -> str:
    folder = Path(params.get("path", str(DEFAULT_DIR)))
    files  = sorted(folder.rglob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
    recent = [f for f in files if f.is_file()][:10]
    names  = ", ".join(f.name for f in recent)
    return f"Les 10 derniers fichiers modifies dans '{folder.name}' sont : {names}, Monsieur."
