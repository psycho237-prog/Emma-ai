#!/usr/bin/env bash
# EMMA v2.0 — Script de compilation Linux
# Mode : --onedir → genere dist/EMMA/ (dossier complet)
# Avantage : demarrage instantane, modeles non extraits au runtime
# Createur : ONANA GREGOIRE LEGRAND

set -e

echo ""
echo " ============================================================"
echo "  EMMA v2.0 — Build Linux"
echo "  Createur : ONANA GREGOIRE LEGRAND"
echo " ============================================================"
echo ""

# Verification Python >= 3.10
PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo " [ERREUR] Python >= 3.10 requis. Version detectee : $PY_VER"
    exit 1
fi
echo " [OK] Python $PY_VER detecte."

# Installation des dependances
echo " [1/4] Installation des dependances..."
pip install -r requirements.txt

# Telechargement modeles manquants
echo " [2/4] Verification/Telechargement des modeles..."

mkdir -p assets/models assets/voices

if [ ! -d "assets/models/vosk-fr" ]; then
    echo " Telechargement modele Vosk fr..."
    wget -q "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip" -O vosk-fr.zip
    unzip -q vosk-fr.zip -d assets/models/
    mv "assets/models/vosk-model-fr-0.22" "assets/models/vosk-fr"
    rm vosk-fr.zip
    echo " [OK] Vosk fr installe."
fi

if [ ! -f "assets/voices/fr_FR-siwis-medium.onnx" ]; then
    echo " Telechargement voix Piper siwis..."
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium"
    wget -q "$BASE_URL/fr_FR-siwis-medium.onnx" -O "assets/voices/fr_FR-siwis-medium.onnx"
    wget -q "$BASE_URL/fr_FR-siwis-medium.onnx.json" -O "assets/voices/fr_FR-siwis-medium.onnx.json"
    echo " [OK] Voix Piper installee."
fi

if [ ! -f "assets/models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo " Telechargement TinyLlama Q4 (~700MB)..."
    mkdir -p assets/models/tinyllama
    wget -q \
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
        -O "assets/models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo " [OK] TinyLlama installe."
fi

# Compilation PyInstaller (--onedir par defaut via COLLECT dans le spec)
echo " [3/4] Compilation avec PyInstaller (mode --onedir)..."
pyinstaller emma.spec --clean

echo " [4/4] Compilation terminee !"
echo ""
echo " ============================================================"
echo "  Dossier genere : dist/EMMA/"
echo "  Executable     : dist/EMMA/EMMA"
echo "  Lancement      : ./dist/EMMA/EMMA"
echo ""
echo "  Pour distribuer EMMA : copier le dossier dist/EMMA/ entier"
echo "  (EMMA + les modeles IA sont dans ce meme dossier)"
echo " ============================================================"
echo ""
