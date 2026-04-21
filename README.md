# EMMA v2.0 — Assistant Vocal Autonome & Matériel

EMMA (**E**lectronic **M**ultimodal **M**anagement **A**ssistant) est un assistant vocal "Local-First", conçu pour fonctionner sans cloud, avec une interface physique basée sur un **ESP32**.

## 🚀 Fonctionnalités
- **Reconnaissance Vocale (STT)** : Faster-Whisper (Modèle Small) — 100% Offline.
- **Cerveau (LLM)** : Google Gemini 1.5 (Cloud gratuit) ou TinyLlama (Local).
- **Synthèse Vocale (TTS)** : Piper (Voix UPMC de haute qualité) — 100% Offline.
- **Actions Système** : Gestion de la musique, des fichiers (création/suppression), redémarrage, point d'accès WiFi, etc.
- **Interface ESP32** : Yeux animés sur écran OLED, micro et haut-parleurs via I2S.

## 🛠 Architecture Matérielle (Hardware)
- **Cœur** : PC (Windows ou Linux) pour le traitement lourd (IA).
- **Visage & Audio** : ESP32 (DevKit V1).
- **Affichage** : Écran OLED I2C (SSD1306 128x64).
- **Audio In** : Microphone I2S (INMP441).
- **Audio Out** : Amplificateur I2S (MAX98357A) + Haut-parleur.

## 📁 Structure du Projet
- `/emma` : Code source Python (le moteur).
- `/firmware` : Code C++ pour l'ESP32 (Animations OLED + Flux Audio).
- `/assets` : Modèles IA (Whisper, Vosk, TinyLlama) et voix Piper.
- `vocal_mode.py` : Point d'entrée principal.

## 🔧 Installation Rapide
1. **Python** : `pip install -r requirements.txt`
2. **Modèles** : Télécharger les modèles dans `assets/models/`.
3. **Firmware** : Téléverser `firmware/emma_esp32.ino` sur l'ESP32 via Arduino IDE.
4. **Lancement** : `python vocal_mode.py`

## 🐧 Compatibilité
EMMA est compatible **Windows** (via PowerShell) et **Linux** (via nmcli/ffplay). Le binaire `piper` est inclus pour les deux systèmes.

---
*Créé par ONANA GREGOIRE LEGRAND | Yaoundé, Cameroun*
