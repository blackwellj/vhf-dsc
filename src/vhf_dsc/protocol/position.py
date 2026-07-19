"""Position encoding per ITU-R M.493-16 Sections 8.1.2 and 8.1.3.

Distress coordinates (Section 8.1.2): 10 digits as 5 symbol-number characters
- Digit 1: quadrant (0=NE, 1=NW, 2=SE, 3=SW)
- Digits 2-3: latitude degrees (00-90)
- Digits 4-5: latitude minutes (00-59)
- Digits 6-8: longitude degrees (000-180)
- Digits 9-10: longitude minutes (00-59)

Per Table A1-2: digits are packed in pairs. Each character = symbol number = the
two-decimal figure it represents. Character 1 is transmitted LAST.

Time (Section 8.1.3): 4 digits as 2 symbol-number characters
- Digits 1-2: hours (00-23)
- Digits 3-4: minutes (00-59)

If position cannot be included: transmit 9999999999 (10 nines).
If time cannot be included: transmit 8888.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """Geographic position in DSC format."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    time_utc: Optional[str] = None
    quadrant: Optional[int] = None

    @property
    def is_valid(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def __str__(self) -> str:
        if not self.is_valid:
            return "No position"
        lat_dir = "N" if self.latitude >= 0 else "S"
        lon_dir = "E" if self.longitude >= 0 else "W"
        return f"{abs(self.latitude):.4f}{lat_dir} {abs(self.longitude):.4f}{lon_dir}"


def _lat_lon_to_quadrant(lat: float, lon: float) -> int:
    """Determine quadrant from lat/lon.
    0=NE, 1=NW, 2=SE, 3=SW
    """
    q = 0
    if lat < 0:
        q |= 2
    if lon < 0:
        q |= 1
    return q


def encode_position(lat: float, lon: float) -> list[int]:
    """Encode position to 10 DSC digits (5 symbol-number characters).

    Returns list of 10 individual digits (to be packed into 5 chars by serializer).
    """
    quadrant = _lat_lon_to_quadrant(lat, lon)
    abs_lat = abs(lat)
    abs_lon = abs(lon)

    lat_deg = int(abs_lat)
    lat_min = int(round((abs_lat - lat_deg) * 60))
    if lat_min >= 60:
        lat_deg += 1
        lat_min = 0

    lon_deg = int(abs_lon)
    lon_min = int(round((abs_lon - lon_deg) * 60))
    if lon_min >= 60:
        lon_deg += 1
        lon_min = 0

    digits = [
        quadrant,
        (lat_deg // 10) % 10,
        lat_deg % 10,
        (lat_min // 10) % 10,
        lat_min % 10,
        (lon_deg // 100) % 10,
        (lon_deg // 10) % 10,
        lon_deg % 10,
        (lon_min // 10) % 10,
        lon_min % 10,
    ]
    return digits


def decode_position(digits: list[int]) -> Position:
    """Decode 10 DSC digits to a Position."""
    if len(digits) < 10:
        return Position()

    if all(d == 9 for d in digits):
        return Position()

    quadrant = digits[0]
    lat_deg = digits[1] * 10 + digits[2]
    lat_min = digits[3] * 10 + digits[4]
    lon_deg = digits[5] * 100 + digits[6] * 10 + digits[7]
    lon_min = digits[8] * 10 + digits[9]

    lat = lat_deg + lat_min / 60.0
    lon = lon_deg + lon_min / 60.0

    if quadrant & 2:
        lat = -lat
    if quadrant & 1:
        lon = -lon

    return Position(latitude=lat, longitude=lon, quadrant=quadrant)


def encode_time_utc(time_str: str) -> list[int]:
    """Encode UTC time to 4 DSC digits.
    Format: HHMM
    """
    if len(time_str) < 4:
        return [8, 8, 8, 8]
    return [int(time_str[0]), int(time_str[1]), int(time_str[2]), int(time_str[3])]


def decode_time_utc(digits: list[int]) -> Optional[str]:
    """Decode 4 DSC digits to UTC time string."""
    if len(digits) < 4:
        return None
    if digits == [8, 8, 8, 8]:
        return None
    return f"{digits[0]}{digits[1]}{digits[2]}{digits[3]}"


def position_digits_to_chars(digits: list[int]) -> list[int]:
    """Pack position digits into symbol-number characters per Table A1-2.

    Each character = symbol number = the two-decimal figure.
    Character 1 is transmitted LAST.

    10 digits -> 5 characters:
    Char 5: digits[0:2] (quadrant + lat_deg_tens)
    Char 4: digits[2:4] (lat_deg_units + lat_min_tens)
    Char 3: digits[4:6] (lat_min_units + lon_deg_hundreds)
    Char 2: digits[6:8] (lon_deg_tens + lon_deg_units)
    Char 1: digits[8:10] (lon_min_tens + lon_min_units)
    """
    chars = []
    for i in range(0, 10, 2):
        val = digits[i] * 10 + digits[i + 1]
        chars.append(val)
    return chars


def time_digits_to_chars(digits: list[int]) -> list[int]:
    """Pack time digits into symbol-number characters per Table A1-2.

    4 digits -> 2 characters:
    Char 2: digits[0:2] (hours)
    Char 1: digits[2:4] (minutes)
    """
    return [digits[0] * 10 + digits[1], digits[2] * 10 + digits[3]]
