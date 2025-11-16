# steg_image.py
"""
LSB steganography for images (RGB)
Stores: [4-byte header-length][JSON header][payload bytes] as raw bytes
Uses 1 LSB per color channel => 3 bits per pixel => capacity = floor(width*height*3/8) bytes
"""

from PIL import Image
import math

def _int_to_bin(rgb):
    return tuple(f"{v:08b}" for v in rgb)

def _bin_to_int(binaries):
    return tuple(int(b, 2) for b in binaries)

def _data_to_bits(data: bytes) -> str:
    return ''.join(f"{byte:08b}" for byte in data)

def _bits_to_bytes(bits: str) -> bytes:
    b = bytearray()
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) < 8:
            byte = byte.ljust(8, '0')
        b.append(int(byte, 2))
    return bytes(b)

def image_capacity_bytes(img: Image.Image) -> int:
    width, height = img.size
    capacity_bits = width * height * 3
    return capacity_bits // 8

def embed_bytes_in_image(image: Image.Image, payload: bytes) -> Image.Image:
    bits = _data_to_bits(payload)
    n_bits = len(bits)
    img = image.copy().convert('RGB')
    width, height = img.size
    capacity = width * height * 3
    if n_bits > capacity:
        raise ValueError(f"Payload too large: needs {n_bits} bits, capacity {capacity} bits")
    pixels = img.load()
    bit_idx = 0
    for y in range(height):
        for x in range(width):
            if bit_idx >= n_bits:
                break
            r, g, b = pixels[x, y]
            rb, gb, bb = _int_to_bin((r, g, b))
            new_rb = rb[:-1] + bits[bit_idx] if bit_idx < n_bits else rb
            bit_idx += 1
            new_gb = gb[:-1] + bits[bit_idx] if bit_idx < n_bits else gb
            bit_idx += 1
            new_bb = bb[:-1] + bits[bit_idx] if bit_idx < n_bits else bb
            bit_idx += 1
            pixels[x, y] = _bin_to_int((new_rb, new_gb, new_bb))
        if bit_idx >= n_bits:
            break
    return img

def extract_bytes_from_image(image: Image.Image) -> bytes:
    img = image.convert('RGB')
    width, height = img.size
    bits = []
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            rb, gb, bb = _int_to_bin((r, g, b))
            bits.append(rb[-1])
            bits.append(gb[-1])
            bits.append(bb[-1])
    bits_str = ''.join(bits)
    # First 32 bits = header length in bytes
    if len(bits_str) < 32:
        raise ValueError("No data found.")
    header_len = int(bits_str[:32], 2)
    total_header_bits = 32 + header_len * 8
    if len(bits_str) < total_header_bits:
        raise ValueError("Incomplete header.")
    header_bytes = _bits_to_bytes(bits_str[32:total_header_bits])
    payload_len = None
    try:
        import json
        header = json.loads(header_bytes.decode('utf-8'))
        payload_len = header.get('payload_length')
    except:
        raise ValueError("Corrupt header.")
    total_payload_bits = payload_len * 8
    total_needed_bits = total_header_bits + total_payload_bits
    if len(bits_str) < total_needed_bits:
        raise ValueError("Incomplete payload.")
    payload_bits = bits_str[total_header_bits:total_needed_bits]
    payload = _bits_to_bytes(payload_bits)
    # Return complete blob: [4-byte header-len][header bytes][payload]
    # We reconstruct to the original blob format used by app
    from struct import pack
    return (header_len.to_bytes(4, byteorder='big') + header_bytes + payload)
