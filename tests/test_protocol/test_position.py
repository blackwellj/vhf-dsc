"""Tests for position encoding (quadrant+degrees+minutes)."""

import pytest

from vhf_dsc.protocol.position import (
    encode_position, decode_position,
    encode_time_utc, decode_time_utc,
    Position,
)


class TestPosition:
    def test_encode_decode_northern(self):
        lat, lon = 51.5074, 0.1278
        digits = encode_position(lat, lon)
        assert len(digits) == 10
        pos = decode_position(digits)
        assert abs(pos.latitude - lat) < 1.0
        assert abs(pos.longitude - lon) < 1.0

    def test_encode_decode_southern(self):
        lat, lon = -33.8688, 18.4241
        digits = encode_position(lat, lon)
        pos = decode_position(digits)
        assert abs(pos.latitude - lat) < 1.0
        assert abs(pos.longitude - lon) < 1.0

    def test_quadrant_ne(self):
        digits = encode_position(10.0, 10.0)
        assert digits[0] == 0

    def test_quadrant_nw(self):
        digits = encode_position(10.0, -10.0)
        assert digits[0] == 1

    def test_quadrant_se(self):
        digits = encode_position(-10.0, 10.0)
        assert digits[0] == 2

    def test_quadrant_sw(self):
        digits = encode_position(-10.0, -10.0)
        assert digits[0] == 3

    def test_invalid_position(self):
        pos = Position()
        assert not pos.is_valid

    def test_valid_position(self):
        pos = Position(latitude=51.0, longitude=0.0)
        assert pos.is_valid


class TestTime:
    def test_encode_decode(self):
        digits = encode_time_utc("1230")
        assert digits == [1, 2, 3, 0]
        time_str = decode_time_utc(digits)
        assert time_str == "1230"

    def test_invalid_time(self):
        assert decode_time_utc([8, 8, 8, 8]) is None
