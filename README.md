# 🦎 Lizard – Image & Audio Steganography Tool

A web-based steganography tool that hides text or files inside images or WAV audio.  
You can embed any file, protect it with a password, and extract it later by re-uploading the stego file.

🌐 [Live App](https://lizard-y893.onrender.com/)

---

## Features

- Hide text or any file inside PNG, BMP, or WAV.
- Extract hidden content anytime by uploading the stego file.
- Optional password protection with AES encryption.
- Clean, responsive GUI.
- Image and audio LSB-based steganography.
- Reliable metadata headers for accurate file recovery.

---

## How to Use?

- Open the [Live App](https://lizard-y893.onrender.com/)
in your browser.
- Upload a carrier file (PNG/BMP/WAV).  
- Enter text or upload the file you want to hide.  
- (Optional) Add a password for encryption.  
- Download the generated stego file.  
- Upload the stego file in the Extract section to recover the hidden data.

---

## How it works?

Lizard uses **LSB Steganography**, a method that hides data in the least significant bits of image or audio files.  
These tiny bit changes are invisible to the human eye and impossible to notice by listening.

For images:  
The tool takes the binary data of the file you want to hide, breaks it into bits, and stores those bits in the pixel values of PNG or BMP files.  
Your hidden content becomes part of the image itself.

For audio:  
The same technique is applied to WAV samples. The least significant bits of each audio sample are modified to store data without altering the sound.

If you choose to set a password:  
Your data is encrypted using **AES-GCM**, a secure encryption method. Even if someone extracts bits manually, they cannot read the hidden content.

When you upload the stego file again:  
Lizard reads the embedded metadata header, reconstructs the hidden bits, decrypts the content if needed, and returns the original text or file.

---

## Encryption

If you enter a password, Lizard encrypts the payload using:
- **Scrypt** (for key derivation)  
- **AES-GCM** (authenticated encryption)

Without the password, extraction won’t work.

---

## Want to Use Locally?

```bash
git clone https://github.com/HindustaaniSher/Lizard.git
cd Lizard
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```
Now, open the app at `http://127.0.0.1:5000`
