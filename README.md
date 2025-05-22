

# Emma - Linux AI Desktop Assistant

Emma is a futuristic smart assistant for Linux desktops, powered by ChatGPT. She responds to both voice and manual commands, features a smooth female voice, and presents an elegant interface with animations and a 3D avatar.

Developed by Onana Gregoire Legrand, 20-year-old IT student at University of Yaoundé 1.

---

## Features

- **Voice Commands (default mode)**  
- **Manual Command Entry**  
- **Interactive 3D Avatar**  
- **Vibrating Sphere Animation During Speech**  
- **Real-Time Responses via ChatGPT**  
- **Music Control (via Rhythmbox)**  
- **Configurable API Key Management**  
- **.deb Installer with Interactive Setup**

---

## Technologies Used

- Python 3
- gTTS (Google Text-to-Speech)
- SpeechRecognition
- Tkinter & Pyglet (for GUI & 3D)
- OpenAI ChatGPT API
- Rhythmbox
- Ubuntu 22.04.1+

---

## Installation

### 1. Install Dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk sox espeak ffmpeg portaudio19-dev
pip install -r requirements.txt

2. Install with .deb Package (Recommended)

sudo dpkg -i emma-assistant.deb

> The installer will guide you interactively, check for dependencies, and show slides about Emma's features.




---

Usage

Launch Emma from your applications menu or by running:

emma

Use voice commands by default.
Switch modes using the GUI buttons:

Send: manual command

Speak: voice input

Interface: switch to the 3D avatar view



---

API Key Setup

On first launch, Emma creates a ~/.emma_config.json.
You can update your ChatGPT API key inside that file.


---

Screenshots

Coming soon: Interface mockups, avatar previews, and animated demo.


---

Author

Onana Gregoire Legrand
20 y/o IT student — Yaoundé I State University

GitHub: psycho237-prog


---

License

This project is licensed under the MIT License.



