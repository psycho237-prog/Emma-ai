@echo off
REM EMMA v2.0 — Script de compilation Windows
REM Mode : --onedir → genere dist\EMMA\ (dossier complet)
REM Avantage : demarrage instantane, modeles non extraits au runtime
REM Createur : ONANA GREGOIRE LEGRAND

echo.
echo  ============================================================
echo   EMMA v2.0 — Build Windows
echo   Createur : ONANA GREGOIRE LEGRAND
echo  ============================================================
echo.

REM Verification Python
python --version 2>NUL
if errorlevel 1 (
    echo  [ERREUR] Python n'est pas installe ou non dans le PATH.
    echo  Telechargez Python 3.10+ depuis https://python.org
    pause
    exit /b 1
)

REM Installation des dependances
echo  [1/4] Installation des dependances...
pip install -r requirements.txt
if errorlevel 1 (
    echo  [ERREUR] Echec de pip install. Verifiez votre connexion.
    pause
    exit /b 1
)

REM Verification des modeles
echo  [2/4] Verification des modeles...

if not exist "assets\models\vosk-fr\" (
    echo  Telechargement du modele Vosk fr...
    python -c "import urllib.request; urllib.request.urlretrieve('https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip', 'vosk-fr.zip')"
    powershell -Command "Expand-Archive vosk-fr.zip assets\models\" 
    move "assets\models\vosk-model-fr-0.22" "assets\models\vosk-fr"
    del vosk-fr.zip
)

if not exist "assets\voices\fr_FR-siwis-medium.onnx" (
    echo  Telechargement de la voix Piper fr_FR-siwis-medium...
    python -c "import urllib.request; urllib.request.urlretrieve('https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx', 'assets/voices/fr_FR-siwis-medium.onnx')"
    python -c "import urllib.request; urllib.request.urlretrieve('https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json', 'assets/voices/fr_FR-siwis-medium.onnx.json')"
)

REM Compilation PyInstaller
echo  [3/4] Compilation avec PyInstaller (mode --onedir)...
pyinstaller emma.spec --clean
if errorlevel 1 (
    echo  [ERREUR] Echec de la compilation PyInstaller.
    pause
    exit /b 1
)

echo  [4/4] Compilation terminee !
echo.
echo  ============================================================
echo   Dossier genere     : dist\EMMA\
echo   Executable         : dist\EMMA\EMMA.exe
echo   Lancement          : dist\EMMA\EMMA.exe
echo.
echo   Pour distribuer EMMA : copiez le dossier dist\EMMA\ entier
echo   (EMMA.exe + les modeles IA sont dans ce meme dossier)
echo  ============================================================
echo.
pause
