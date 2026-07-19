"""Tests for MMSI handling."""

import pytest

from vhf_dsc.protocol.mmsi import MMSI, MMSIType


class TestMMSI:
    def test_valid_ship_mmsi(self):
        mmsi = MMSI("234567890")
        assert mmsi.is_valid
        assert mmsi.type == MMSIType.SHIP

    def test_valid_coast_mmsi(self):
        mmsi = MMSI("002241022")
        assert mmsi.is_valid
        assert mmsi.type == MMSIType.COAST

    def test_all_ships(self):
        mmsi = MMSI("000000000")
        assert mmsi.is_valid
        assert mmsi.type == MMSIType.ALL_SHIPS

    def test_invalid_too_short(self):
        assert not MMSI.is_valid("12345")

    def test_invalid_non_numeric(self):
        assert not MMSI.is_valid("abcdefghi")

    def test_mid_extraction(self):
        mmsi = MMSI("234567890")
        assert mmsi.mid == "234"

    def test_to_int(self):
        mmsi = MMSI("234567890")
        assert mmsi.to_int() == 234567890

    def test_from_int(self):
        mmsi = MMSI.from_int(234567890)
        assert mmsi.value == "234567890"

    def test_invalid_construction(self):
        with pytest.raises(ValueError):
            MMSI("invalid")
