"""10-bit character encoding per ITU-R M.493-16 Table A1-1.

B = binary 0, Y = binary 1
Bit transmission order: bit 1 first (LSB)
Bits 1-7: information bits (symbol number)
Bits 8-10: binary count of B(0) elements in bits 1-7
  - Bit 8 = LSB (1s place)
  - Bit 9 = 2s place
  - Bit 10 = MSB (4s place)
"""

from __future__ import annotations


def _build_character_table() -> dict[int, int]:
    """Build the ITU-R M.493-16 Table A1-1 character encoding table."""
    table = {}
    for sym in range(128):
        info_bits = sym
        b_count = 7 - bin(info_bits).count("1")
        
        # Check bits: bit 8 = LSB, bit 9 = middle, bit 10 = MSB
        # In our storage (bit 1 at position 0):
        # bit 8 -> position 7, bit 9 -> position 8, bit 10 -> position 9
        b0 = b_count & 1         # LSB -> bit 8 -> position 7
        b1 = (b_count >> 1) & 1  # middle -> bit 9 -> position 8
        b2 = (b_count >> 2) & 1  # MSB -> bit 10 -> position 9
        
        check_stored = (b0 << 7) | (b1 << 8) | (b2 << 9)
        table[sym] = info_bits | check_stored
    
    return table


CHARACTER_TABLE: dict[int, int] = _build_character_table()
REVERSE_TABLE: dict[int, int] = {v: k for k, v in CHARACTER_TABLE.items()}


def encode_char(value: int) -> int:
    """Encode a 7-bit symbol number to a 10-bit DSC character."""
    if not 0 <= value <= 127:
        raise ValueError(f"Symbol number {value} out of range (0-127)")
    return CHARACTER_TABLE[value]


def decode_char(code: int) -> int:
    """Decode a 10-bit DSC character to a 7-bit symbol number."""
    if code in REVERSE_TABLE:
        return REVERSE_TABLE[code]

    best_match = -1
    best_distance = 11

    for code10, value7 in REVERSE_TABLE.items():
        distance = bin(code ^ code10).count("1")
        if distance < best_distance:
            best_distance = distance
            best_match = value7

    if best_distance <= 1:
        return best_match

    return -1


def hamming_distance(a: int, b: int) -> int:
    """Calculate Hamming distance between two 10-bit codes."""
    return bin(a ^ b).count("1")


def encode_bitstream(values: list[int]) -> list[int]:
    """Encode a list of 7-bit symbol numbers to 10-bit character codes."""
    return [encode_char(v) for v in values]


def decode_bitstream(codes: list[int]) -> tuple[list[int], int]:
    """Decode a list of 10-bit character codes to 7-bit symbol numbers."""
    decoded = []
    errors = 0
    for code in codes:
        value = decode_char(code)
        if value == -1:
            errors += 1
            decoded.append(0)
        else:
            decoded.append(value)
    return decoded, errors


def code_to_bits(code: int) -> list[int]:
    """Convert a 10-bit character code to a list of bits (bit 1 first = LSB)."""
    return [(code >> i) & 1 for i in range(10)]


def bits_to_code(bits: list[int]) -> int:
    """Convert a list of 10 bits (bit 1 first) to a character code."""
    code = 0
    for i, bit in enumerate(bits):
        code |= (bit << i)
    return code
