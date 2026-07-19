"""Tests for error correction (even vertical parity)."""

import pytest

from vhf_dsc.protocol.error_correction import (
    compute_ecc, verify_ecc, extract_info_symbols,
)


class TestECC:
    def test_compute_and_verify(self):
        data = [100, 101, 102, 103, 104]
        ecc = compute_ecc(data)
        assert verify_ecc(data, ecc)

    def test_verify_invalid(self):
        data = [100, 101, 102]
        assert not verify_ecc(data, 0x7F)

    def test_ecc_is_7bit(self):
        data = list(range(128))
        ecc = compute_ecc(data)
        assert 0 <= ecc <= 127

    def test_ecc_deterministic(self):
        data = [112, 100, 105, 126]
        ecc1 = compute_ecc(data)
        ecc2 = compute_ecc(data)
        assert ecc1 == ecc2

    def test_extract_info_symbols(self):
        symbols = [112, 23, 45, 67, 89, 100, 105, 126, 127, 127]
        info = extract_info_symbols(symbols)
        assert len(info) > 0

    def test_ecc_xor_property(self):
        data = [0, 0, 0]
        ecc = compute_ecc(data)
        assert ecc == 0

        data = [1, 0, 0]
        ecc = compute_ecc(data)
        assert ecc == 1

        data = [1, 1, 0]
        ecc = compute_ecc(data)
        assert ecc == 0
