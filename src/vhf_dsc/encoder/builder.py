"""DSC message builder - fluent API for constructing DSC messages per ITU-R M.493-16."""

from __future__ import annotations

from ..protocol.message import DSCMessage
from ..protocol.position import Position
from ..protocol.symbols import SYM_NO_INFO, SYM_TC2_NO_INFO, SYM_EOS_EOT


class DSCMessageBuilder:
    """Fluent builder for constructing DSC messages."""

    def __init__(self):
        self._msg = DSCMessage()

    def format(self, fmt: int) -> "DSCMessageBuilder":
        self._msg.format_specifier = fmt
        return self

    def category(self, cat: int) -> "DSCMessageBuilder":
        self._msg.category = cat
        return self

    def destination(self, mmsi: str) -> "DSCMessageBuilder":
        self._msg.mmsi_dest = mmsi
        return self

    def source(self, mmsi: str) -> "DSCMessageBuilder":
        self._msg.mmsi_self = mmsi
        return self

    def tc1(self, tc: int) -> "DSCMessageBuilder":
        self._msg.telecommand_1 = tc
        return self

    def tc2(self, tc: int) -> "DSCMessageBuilder":
        self._msg.telecommand_2 = tc
        return self

    def position(self, lat: float, lon: float,
                 time_utc: str | None = None) -> "DSCMessageBuilder":
        self._msg.position = Position(
            latitude=lat, longitude=lon, time_utc=time_utc)
        return self

    def nature(self, nature: int) -> "DSCMessageBuilder":
        self._msg.nature_of_distress = nature
        return self

    def time_utc(self, time_str: str) -> "DSCMessageBuilder":
        self._msg.time_utc = time_str
        return self

    def channel(self, ch: int) -> "DSCMessageBuilder":
        self._msg.channel = ch
        return self

    def frequency(self, freq: float) -> "DSCMessageBuilder":
        self._msg.frequency = freq
        return self

    def eos(self, eos: int) -> "DSCMessageBuilder":
        self._msg.eos = eos
        return self

    def distress_id(self, mmsi: str) -> "DSCMessageBuilder":
        self._msg.distress_id = mmsi
        return self

    def build(self) -> DSCMessage:
        return DSCMessage(
            format_specifier=self._msg.format_specifier,
            category=self._msg.category,
            mmsi_dest=self._msg.mmsi_dest,
            mmsi_self=self._msg.mmsi_self,
            telecommand_1=self._msg.telecommand_1,
            telecommand_2=self._msg.telecommand_2,
            position=self._msg.position,
            nature_of_distress=self._msg.nature_of_distress,
            time_utc=self._msg.time_utc,
            channel=self._msg.channel,
            frequency=self._msg.frequency,
            eos=self._msg.eos,
            distress_id=self._msg.distress_id,
        )

    def reset(self) -> "DSCMessageBuilder":
        self._msg = DSCMessage()
        return self
