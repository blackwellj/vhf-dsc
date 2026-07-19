"""Tests for protocol character encoding (ITU Table A1-1)."""

import pytest

from vhf_dsc.protocol.characters import (
    encode_char, decode_char, encode_bitstream, decode_bitstream,
    code_to_bits, bits_to_code, hamming_distance, CHARACTER_TABLE,
)


class TestCharacterEncoding:
    def test_encode_all_values(self):
        for val in range(128):
            code = encode_char(val)
            assert 0 <= code < 1024

    def test_decode_roundtrip(self):
        for val in range(128):
            code = encode_char(val)
            decoded = decode_char(code)
            assert decoded == val

    def test_encode_invalid(self):
        with pytest.raises(ValueError):
            encode_char(-1)
        with pytest.raises(ValueError):
            encode_char(128)

    def test_hamming_distance(self):
        for i in range(128):
            for j in range(i + 1, 128):
                d = hamming_distance(CHARACTER_TABLE[i], CHARACTER_TABLE[j])
                assert d >= 2

    def test_code_to_bits(self):
        code = encode_char(42)
        bits = code_to_bits(code)
        assert len(bits) == 10

    def test_bits_to_code(self):
        code = encode_char(42)
        bits = code_to_bits(code)
        reconstructed = bits_to_code(bits)
        assert reconstructed == code

    def test_encode_bitstream(self):
        values = [1, 2, 3, 4, 5]
        codes = encode_bitstream(values)
        assert len(codes) == 5

    def test_decode_bitstream(self):
        values = [1, 2, 3, 4, 5]
        codes = encode_bitstream(values)
        decoded, errors = decode_bitstream(codes)
        assert decoded == values
        assert errors == 0

    def test_table_size(self):
        assert len(CHARACTER_TABLE) == 128

    def test_check_bits_correct(self):
        for sym, code in CHARACTER_TABLE.items():
            info_bits = code & 0x7F
            b_count = 7 - bin(info_bits).count("1")
            bit8 = (code >> 7) & 1  # LSB
            bit9 = (code >> 8) & 1  # middle
            bit10 = (code >> 9) & 1  # MSB
            check_bits = bit10 * 4 + bit9 * 2 + bit8
            assert check_bits == b_count, f"Symbol {sym}: expected {b_count} B-count, got {check_bits}"
