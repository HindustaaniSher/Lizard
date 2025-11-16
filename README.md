# 🦎 Lizard – Image & Audio Steganography Tool

[![Live demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://lizard-y893.onrender.com/)

A web-based steganography tool that hides text or files inside images or WAV audio.  
You can embed any file, protect it with a password, and extract it later by re-uploading the stego file.

🌐 **Live App**: https://lizard-y893.onrender.com/

---

## Features

- Hide text or any file inside PNG, BMP, or WAV.
- Extract hidden content anytime by uploading the stego file.
- Optional password protection with AES encryption.
- Clean, responsive GUI with Light–Dark mode toggle.
- Works on all modern browsers.
- Image and audio LSB-based steganography.
- Reliable metadata headers for accurate file recovery.

---

## How to Use?

- Open the **Live App** from the link above.  
- Upload a carrier file (PNG/BMP/WAV).  
- Enter text or upload the file you want to hide.  
- (Optional) Add a password for encryption.  
- Download the generated stego file.  
- Upload the stego file in the Extract section to recover the hidden data.

---

## Want to Use Locally?

```bash
git clone https://github.com/HindustaaniSher/Lizard.git
cd Lizard
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
