"""Error correction per ITU-R M.493-16 Section 10.

ECC (Error Check Character) = even vertical parity of all information characters.
Section 10.2: "The seven information bits of the ECC shall be equal to the least
significant bit of the modulo-2 sums of the corresponding bits of all information
characters (i.e. even vertical parity)."

Format specifier and EOS characters ARE information characters.
Phasing characters and RX (retransmission) characters are NOT information characters.
Only ONE format specifier and ONE EOS character are used in ECC construction.
"""

from __future__ import annotations


def compute_ecc(info_symbols: list[int]) -> int:
    """Compute ECC as even vertical parity of information symbol numbers.

    Args:
        info_symbols: List of 7-bit symbol numbers (NOT 10-bit codes)

    Returns:
        7-bit ECC symbol number
    """
    ecc = 0
    for sym in info_symbols:
        ecc ^= (sym & 0x7F)
    return ecc & 0x7F


def verify_ecc(info_symbols: list[int], expected_ecc: int) -> bool:
    """Verify ECC of information symbols.

    Args:
        info_symbols: List of 7-bit symbol numbers
        expected_ecc: Expected ECC value

    Returns:
        True if ECC matches
    """
    return compute_ecc(info_symbols) == (expected_ecc & 0x7F)


def extract_info_symbols(dx_symbols: list[int]) -> list[int]:
    """Extract information symbols from a DX-only symbol stream.

    Removes phasing characters (125, 111-104) and keeps format specifier,
    address, messages, and EOS. Only one format specifier and one EOS counted.

    Args:
        dx_symbols: DX position symbols (not including RX duplicates)

    Returns:
        List of information symbol numbers for ECC computation
    """
    PHASING_SYMBOLS = {125, 111, 110, 109, 108, 107, 106, 105, 104}

    info = []
    format_seen = False
    eos_seen = False

    for sym in dx_symbols:
        if sym in PHASING_SYMBOLS:
            continue
        if sym in (112, 116, 114, 120, 102, 123):
            if format_seen:
                continue
            format_seen = True
        if sym in (117, 122, 127):
            if eos_seen:
                continue
            eos_seen = True
        info.append(sym)

    return info


def repeat_time_diversity(symbols: list[int]) -> list[int]:
    """Apply time diversity: each char transmitted twice with 4 chars between.

    Per Section 1.2.1: first transmission (DX) followed by 4 other characters
    before re-transmission (RX).

    For a sequence [A, B, C, D, E, F, G, H, I, J]:
    DX stream: A, B, C, D, E, F, G, H, I, J
    RX stream: A, B, C, D, E, F, G, H, I, J (interleaved 4 chars later)

    Transmitted order: A, B, C, D, E, A, F, B, G, C, H, D, I, E, J, F, ...

    For short messages, we use a simpler approach:
    DX symbols first, then RX symbols.
    """
    if len(symbols) <= 4:
        return symbols + symbols

    result = list(symbols)
    for i, sym in enumerate(symbols):
        result.append(sym)

    return result


def deinterleave_time_diversity(symbols: list[int]) -> tuple[list[int], list[int]]:
    """De-interleave time-diversity stream into DX and RX streams.

    Per Section 1.2.1, RX chars appear 4 positions after their DX counterparts.

    Args:
        symbols: Received symbol stream (with time diversity)

    Returns:
        Tuple of (dx_symbols, rx_symbols)
    """
    n = len(symbols)
    if n < 10:
        return symbols, []

    dx = []
    rx = []

    for i in range(n):
        if i < 5:
            dx.append(symbols[i])
        else:
            rx_pos = i - 5
            if rx_pos < len(dx):
                rx.append(symbols[i])
            else:
                dx.append(symbols[i])

    return dx, rx
