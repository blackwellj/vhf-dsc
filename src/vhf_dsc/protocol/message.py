"""DSC message structure per ITU-R M.493-16."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .symbols import (
    FormatSpecifier, CategoryOfCall, NatureOfDistress,
    FirstTelecommand, SecondTelecommand,
)
from .position import Position


@dataclass
class DSCMessage:
    """Complete DSC message structure."""
    format_specifier: Optional[int] = None
    category: Optional[int] = None
    address: Optional[str] = None
    telecommand_1: Optional[int] = None
    telecommand_2: Optional[int] = None
    position: Optional[Position] = None
    nature_of_distress: Optional[int] = None
    time_utc: Optional[str] = None
    channel: Optional[int] = None
    frequency: Optional[float] = None
    eos: Optional[int] = None
    ecc: Optional[int] = None
    mmsi_self: Optional[str] = None
    mmsi_dest: Optional[str] = None
    distress_id: Optional[str] = None
    raw_symbols: list[int] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    frequency_rx: Optional[float] = None
    status: str = ""

    @property
    def is_distress(self) -> bool:
        return self.format_specifier == 112

    @property
    def is_valid(self) -> bool:
        if self.ecc is None:
            return False
        if self.format_specifier is None:
            return False
        return True

    def format_summary(self) -> str:
        from .symbols import FormatSpecifier as FS, CategoryOfCall as CC
        from .symbols import FirstTelecommand as TC1, SecondTelecommand as TC2
        from .symbols import EndOfSequence as EOS, NatureOfDistress as ND

        parts = []
        if self.format_specifier is not None:
            try:
                parts.append(f"FMT: {FS(self.format_specifier).name}")
            except ValueError:
                parts.append(f"FMT: {self.format_specifier}")
        if self.category is not None:
            try:
                parts.append(f"CAT: {CC(self.category).name}")
            except ValueError:
                parts.append(f"CAT: {self.category}")
        if self.mmsi_dest:
            parts.append(f"TO: {self.mmsi_dest}")
        if self.mmsi_self:
            parts.append(f"FROM: {self.mmsi_self}")
        if self.telecommand_1 is not None:
            try:
                parts.append(f"TC1: {TC1(self.telecommand_1).name}")
            except ValueError:
                parts.append(f"TC1: {self.telecommand_1}")
        if self.telecommand_2 is not None:
            try:
                parts.append(f"TC2: {TC2(self.telecommand_2).name}")
            except ValueError:
                parts.append(f"TC2: {self.telecommand_2}")
        if self.nature_of_distress is not None:
            try:
                parts.append(f"NATURE: {ND(self.nature_of_distress).name}")
            except ValueError:
                parts.append(f"NATURE: {self.nature_of_distress}")
        if self.position and self.position.is_valid:
            parts.append(f"POS: {self.position}")
        if self.eos is not None:
            try:
                parts.append(f"EOS: {EOS(self.eos).name}")
            except ValueError:
                parts.append(f"EOS: {self.eos}")
        if self.ecc is not None:
            parts.append(f"ECC: {self.ecc}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        from .symbols import FormatSpecifier as FS, CategoryOfCall as CC
        from .symbols import FirstTelecommand as TC1, SecondTelecommand as TC2
        from .symbols import EndOfSequence as EOS, NatureOfDistress as ND

        def sym_name(val, enum_cls):
            try:
                return enum_cls(val).name
            except (ValueError, TypeError):
                return str(val)

        return {
            "format": sym_name(self.format_specifier, FS),
            "category": sym_name(self.category, CC),
            "mmsi_dest": self.mmsi_dest,
            "mmsi_self": self.mmsi_self,
            "tc1": sym_name(self.telecommand_1, TC1),
            "tc2": sym_name(self.telecommand_2, TC2),
            "nature": sym_name(self.nature_of_distress, ND),
            "position": str(self.position) if self.position else None,
            "time_utc": self.time_utc,
            "channel": self.channel,
            "frequency": self.frequency,
            "eos": sym_name(self.eos, EOS),
            "ecc": self.ecc,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "frequency_rx": self.frequency_rx,
            "status": self.status,
            "is_distress": self.is_distress,
        }
