"""MMSI handling per ITU-R M.493-16 Section 5.2 and ITU-R M.585.

MMSI is 9 digits, transmitted as 5 symbol-number character pairs:
(M,I)(D,X4)(X5,X6)(X7,X8)(X9,0)

Per Table A1-2: each pair of digits forms a symbol number (00-99).
X10 is always 0 unless equipment supports ITU-R M.1080 expansion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum


class MMSIType(IntEnum):
    SHIP = 0
    GROUP = 1
    COAST = 2
    SAR_AIRCRAFT = 3
    AID_TO_NAV = 4
    CRAFT_ASSOCIATED = 5
    ALL_SHIPS = 6


@dataclass(frozen=True)
class MMSI:
    value: str

    def __post_init__(self):
        if not self.is_valid(self.value):
            raise ValueError(f"Invalid MMSI: {self.value}")

    @staticmethod
    def is_valid(mmsi: str) -> bool:
        if not isinstance(mmsi, str):
            return False
        if not re.match(r"^\d{9}$", mmsi):
            return False
        if mmsi == "000000000":
            return True
        if mmsi.startswith("970"):
            return True
        if mmsi.startswith("00"):
            mid = int(mmsi[2:5])
            return mid != 0
        if mmsi.startswith("0"):
            return True
        mid = int(mmsi[:3])
        return mid != 0

    @property
    def type(self) -> MMSIType:
        if self.value == "000000000":
            return MMSIType.ALL_SHIPS
        if self.value.startswith("970"):
            return MMSIType.SAR_AIRCRAFT
        if self.value.startswith("00"):
            return MMSIType.COAST
        if self.value.startswith("98") or self.value.startswith("99"):
            return MMSIType.AID_TO_NAV
        if self.value.startswith("0"):
            return MMSIType.GROUP
        return MMSIType.SHIP

    @property
    def mid(self) -> str:
        if self.value.startswith("00"):
            return self.value[2:5]
        return self.value[:3]

    def to_digits(self) -> list[int]:
        """Convert MMSI to list of 9 digits."""
        return [int(d) for d in self.value]

    def to_symbol_chars(self) -> list[int]:
        """Convert MMSI to 5 symbol-number characters per Section 5.2.

        (M,I)(D,X4)(X5,X6)(X7,X8)(X9,0)
        Each pair = symbol number = two-digit decimal value.
        """
        digits = self.to_digits()
        return [
            digits[0] * 10 + digits[1],
            digits[2] * 10 + digits[3],
            digits[4] * 10 + digits[5],
            digits[6] * 10 + digits[7],
            digits[8] * 10 + 0,
        ]

    @classmethod
    def from_symbol_chars(cls, chars: list[int]) -> "MMSI":
        """Reconstruct MMSI from 5 symbol-number characters."""
        if len(chars) < 5:
            raise ValueError("Need 5 symbol characters")
        digits = []
        for ch in chars[:4]:
            digits.append((ch // 10) % 10)
            digits.append(ch % 10)
        digits.append(chars[4] // 10)
        return cls("".join(str(d) for d in digits))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"MMSI({self.value}, type={self.type.name})"

    def to_int(self) -> int:
        return int(self.value)

    @classmethod
    def from_int(cls, value: int) -> "MMSI":
        return cls(f"{value:09d}")
