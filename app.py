# app.py
"""
Lizard - Steganography Webapp
Main Flask application
"""

import io
import json
import traceback
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from steg_image import embed_bytes_in_image, extract_bytes_from_image, image_capacity_bytes
from steg_audio import embed_bytes_in_wav, extract_bytes_from_wav, wav_capacity_bytes
from crypto_util import encrypt, decrypt

ALLOWED_IMAGE = {'png', 'bmp'}
ALLOWED_WAV = {'wav'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB upload cap

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"  # Replace before publishing

def allowed_ext(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE or ext in ALLOWED_WAV

@app.route('/')
def index():
    return render_template('index.html')

def build_payload_blob(filename: str, content_type: str, payload_bytes: bytes) -> bytes:
    """
    Build final payload: [4-byte header-length][JSON header][payload bytes]
    Header contains filename and content_type and payload_length.
    """
    header = {
        "filename": filename,
        "content_type": content_type,
        "payload_length": len(payload_bytes)
    }
    header_bytes = json.dumps(header).encode('utf-8')
    header_len = len(header_bytes).to_bytes(4, byteorder='big')
    return header_len + header_bytes + payload_bytes

def parse_payload_blob(blob: bytes):
    """
    Parse blob produced by build_payload_blob
    Returns (header_dict, payload_bytes)
    """
    if len(blob) < 4:
        raise ValueError("Blob too small to contain header.")
    header_len = int.from_bytes(blob[:4], byteorder='big')
    if len(blob) < 4 + header_len:
        raise ValueError("Incomplete header in blob.")
    header_bytes = blob[4:4+header_len]
    header = json.loads(header_bytes.decode('utf-8'))
    payload = blob[4+header_len:4+header_len+header.get('payload_length', 0)]
    return header, payload

@app.route('/embed', methods=['POST'])
def embed():
    try:
        # Validate carrier file
        carrier = request.files.get('carrier')
        if not carrier or carrier.filename == '':
            return jsonify({"error": "Carrier file is required."}), 400

        filename = secure_filename(carrier.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in ALLOWED_IMAGE and ext not in ALLOWED_WAV:
            return jsonify({"error": "Carrier must be PNG, BMP or WAV."}), 400

        # Read payload: either text or file
        payload_text = request.form.get('text_payload', '')
        payload_file = request.files.get('payload_file')
        if payload_file and payload_file.filename:
            p_filename = secure_filename(payload_file.filename)
            p_bytes = payload_file.read()
            p_type = payload_file.mimetype or 'application/octet-stream'
        elif payload_text and payload_text.strip() != '':
            p_filename = 'message.txt'
            p_bytes = payload_text.encode('utf-8')
            p_type = 'text/plain'
        else:
            return jsonify({"error": "Provide text or a payload file to embed."}), 400

        # Optional encryption
        password = request.form.get('password') or None
        if password:
            p_bytes = encrypt(p_bytes, password)
            # Mark content type as encrypted so extraction will attempt decryption if password provided
            p_type = 'application/octet-stream+encrypted'

        # Wrap with header
        payload_blob = build_payload_blob(p_filename, p_type, p_bytes)

        # Embed depending on carrier type
        carrier_bytes = carrier.read()
        if ext in ALLOWED_IMAGE:
            img = Image.open(io.BytesIO(carrier_bytes)).convert('RGB')
            # capacity check
            cap = image_capacity_bytes(img)
            if len(payload_blob) > cap:
                return jsonify({"error": f"Payload too large for this image. Capacity {cap} bytes."}), 400
            stego_img = embed_bytes_in_image(img, payload_blob)
            out_buf = io.BytesIO()
            stego_img.save(out_buf, format='PNG')
            out_buf.seek(0)
            return send_file(out_buf, as_attachment=True, download_name='lizard_stego.png', mimetype='image/png')

        else:  # WAV
            # capacity check
            cap = wav_capacity_bytes(io.BytesIO(carrier_bytes))
            if len(payload_blob) > cap:
                return jsonify({"error": f"Payload too large for this WAV. Capacity {cap} bytes."}), 400
            out_buf = embed_bytes_in_wav(io.BytesIO(carrier_bytes), payload_blob)
            out_buf.seek(0)
            return send_file(out_buf, as_attachment=True, download_name='lizard_stego.wav', mimetype='audio/wav')

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract():
    try:
        stego = request.files.get('stego')
        if not stego or stego.filename == '':
            return jsonify({"error": "Stego file is required."}), 400
        filename = secure_filename(stego.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in ALLOWED_IMAGE and ext not in ALLOWED_WAV:
            return jsonify({"error": "File must be PNG/BMP or WAV."}), 400
        password = request.form.get('password') or None

        stego_bytes = stego.read()

        if ext in ALLOWED_IMAGE:
            img = Image.open(io.BytesIO(stego_bytes)).convert('RGB')
            blob = extract_bytes_from_image(img)
        else:
            blob = extract_bytes_from_wav(io.BytesIO(stego_bytes))

        header, payload = parse_payload_blob(blob)

        # If encrypted, try to decrypt using provided password
        if header.get('content_type') == 'application/octet-stream+encrypted':
            if not password:
                return jsonify({"error": "This payload is encrypted. Provide password."}), 400
            try:
                payload = decrypt(payload, password)
            except Exception as e:
                return jsonify({"error": "Decryption failed. Wrong password or corrupted data."}), 400

        # Try return as text if content type is text
        if header.get('content_type', '').startswith('text/') and header.get('filename', '').endswith('.txt'):
            try:
                text = payload.decode('utf-8')
                return jsonify({"filename": header.get('filename'), "content_type": header.get('content_type'), "text": text})
            except:
                pass

        # Otherwise return file download
        out = io.BytesIO(payload)
        out.seek(0)
        return send_file(out, as_attachment=True, download_name=header.get('filename', 'extracted.bin'),
                         mimetype=header.get('content_type', 'application/octet-stream'))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
