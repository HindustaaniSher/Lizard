# steg_audio.py
"""
LSB steganography for WAV PCM audio (16-bit samples)
We embed into the least significant bit of each sample.
Capacity: number_of_samples bits => bytes = floor(samples/8)
We preserve WAV container and return a BytesIO buffer with modified WAV.
"""

import wave
import io
import struct
import math

def wav_capacity_bytes(wav_bytes_io: io.BytesIO) -> int:
    wav_bytes_io.seek(0)
    wf = wave.open(wav_bytes_io, 'rb')
    n_frames = wf.getnframes()
    n_channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    # we only support 16-bit PCM (sampwidth == 2)
    if sampwidth != 2:
        wf.close()
        return 0
    total_samples = n_frames * n_channels
    wf.close()
    return total_samples // 8  # bits -> bytes

def _bytes_to_bits(data: bytes) -> str:
    return ''.join(f"{byte:08b}" for byte in data)

def _bits_to_bytes(bits: str) -> bytes:
    b = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            chunk = chunk.ljust(8, '0')
        b.append(int(chunk, 2))
    return bytes(b)

def embed_bytes_in_wav(wav_bytes_io: io.BytesIO, payload: bytes) -> io.BytesIO:
    wav_bytes_io.seek(0)
    wf = wave.open(wav_bytes_io, 'rb')
    params = wf.getparams()
    n_channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    n_frames = wf.getnframes()

    if sampwidth != 2:
        wf.close()
        raise ValueError("Only 16-bit WAV files are supported.")

    raw = wf.readframes(n_frames)
    wf.close()

    # unpack samples
    total_samples = n_frames * n_channels
    fmt = "<" + str(total_samples) + "h"
    samples = list(struct.unpack(fmt, raw))

    bits = _bytes_to_bits(payload)
    if len(bits) > total_samples:
        raise ValueError("Payload too large for this WAV file.")

    # embed bit per sample LSB
    for i, bit in enumerate(bits):
        sample = samples[i]
        if sample < 0:
            sample = sample + (1 << 16)  # unsigned view
        sample = (sample & ~1) | int(bit)
        if sample >= (1 << 15):
            sample = sample - (1 << 16)
        samples[i] = sample

    # pack samples back
    new_raw = struct.pack(fmt, *samples)
    out = io.BytesIO()
    wf_out = wave.open(out, 'wb')
    wf_out.setparams(params)
    wf_out.writeframes(new_raw)
    wf_out.close()
    out.seek(0)
    return out

def extract_bytes_from_wav(wav_bytes_io: io.BytesIO) -> bytes:
    wav_bytes_io.seek(0)
    wf = wave.open(wav_bytes_io, 'rb')
    sampwidth = wf.getsampwidth()
    if sampwidth != 2:
        wf.close()
        raise ValueError("Only 16-bit WAV files are supported.")
    n_frames = wf.getnframes()
    n_channels = wf.getnchannels()
    raw = wf.readframes(n_frames)
    wf.close()
    total_samples = n_frames * n_channels
    fmt = "<" + str(total_samples) + "h"
    samples = struct.unpack(fmt, raw)
    bits = []
    for s in samples:
        if s < 0:
            s = s + (1 << 16)
        bits.append(str(s & 1))
    bits_str = ''.join(bits)
    # First 32 bits header length
    if len(bits_str) < 32:
        raise ValueError("No data found.")
    header_len = int(bits_str[:32], 2)
    header_bits_len = header_len * 8
    total_header_bits = 32 + header_bits_len
    if len(bits_str) < total_header_bits:
        raise ValueError("Incomplete header.")
    header_bytes = _bits_to_bytes(bits_str[32:total_header_bits])
    import json
    try:
        header = json.loads(header_bytes.decode('utf-8'))
    except:
        raise ValueError("Corrupt header in WAV.")
    payload_len = header.get('payload_length')
    if payload_len is None:
        raise ValueError("Header missing payload length.")
    total_payload_bits = payload_len * 8
    total_needed = total_header_bits + total_payload_bits
    if len(bits_str) < total_needed:
        raise ValueError("Incomplete payload.")
    payload_bits = bits_str[total_header_bits:total_needed]
    payload = _bits_to_bytes(payload_bits)
    return (header_len.to_bytes(4, byteorder='big') + header_bytes + payload)
