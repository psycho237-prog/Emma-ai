# emma.spec — Fichier de compilation PyInstaller pour EMMA v2.0
# Mode : --onedir (dossier dist/EMMA/)
# Avantages : demarrage instantane, modeles lus directement sans extraction
# Compatible Linux (dist/EMMA/EMMA) et Windows (dist/EMMA/EMMA.exe)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Voix Piper TTS (offline, feminine francais)
        ('assets/voices/*.onnx',            'assets/voices'),
        ('assets/voices/*.json',             'assets/voices'),
        # Modele STT Vosk francais (~60 MB)
        ('assets/models/vosk-fr/',           'assets/models/vosk-fr'),
        # Modele LLM TinyLlama Q4 (~700 MB)
        ('assets/models/tinyllama/',         'assets/models/tinyllama'),
        # Modules d'action Python
        ('actions/',                         'actions'),
    ],
    hiddenimports=[
        'vosk',
        'faster_whisper',
        'websockets',
        'zeroconf',
        'zeroconf.asyncio',
        'pyautogui',
        'psutil',
        'platform',
        'duckduckgo_search',
        'bs4',
        'docx',
        'reportlab',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'anthropic',
        'ollama',
        'llama_cpp',
        'llama_cpp.llama',
        'gtts',
        'yt_dlp',
        'yt_dlp.utils',
        'asyncio',
        'json',
        'hashlib',
        'wave',
        'io',
        'socket',
        'subprocess',
        'shutil',
        're',
        'random',
        'datetime',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',      # Pas de GUI tkinter pour EMMA
        'matplotlib',
        'numpy',        # Non requis (sauf si faster-whisper en GPU)
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── EXE (sans les datas — ceux-ci restent dans le dossier via COLLECT) ───────
exe = EXE(
    pyz,
    a.scripts,
    [],                         # Pas de binaries/datas ici (geres par COLLECT)
    exclude_binaries=True,      # CLE : les binaires vont dans COLLECT
    name='EMMA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python3*.dll',
    ],
    console=True,               # True = terminal visible (logs EMMA)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/emma_icon.ico',
)

# ─── COLLECT : assemble tout dans dist/EMMA/ ──────────────────────────────────
# Structure finale :
#   dist/EMMA/
#     EMMA.exe          (ou EMMA sur Linux)
#     assets/voices/    <- modeles Piper TTS directement accessibles
#     assets/models/    <- Vosk + TinyLlama directement accessibles
#     actions/          <- modules Python actions
#     *.dll / *.so      <- dependances natives
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EMMA',        # => dist/EMMA/
)
