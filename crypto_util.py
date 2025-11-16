# crypto_util.py
"""
Password-based encryption using Scrypt + AES-GCM
Outputs: salt(16) + nonce(12) + ciphertext
"""

import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_key(password: str, salt: bytes):
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    key = kdf.derive(password.encode('utf-8'))
    return key

def encrypt(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return salt + nonce + ct

def decrypt(blob: bytes, password: str) -> bytes:
    if len(blob) < 28:
        raise ValueError("Encrypted blob too small.")
    salt = blob[:16]
    nonce = blob[16:28]
    ct = blob[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)
