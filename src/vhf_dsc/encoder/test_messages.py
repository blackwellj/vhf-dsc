"""Pre-built test message templates per ITU-R M.493-16."""

from __future__ import annotations

from ..protocol.message import DSCMessage
from ..protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_GROUP, SYM_INDIVIDUAL,
    SYM_GEO_AREA, SYM_INDIVIDUAL_AUTO,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_FLOODING, SYM_NATURE_COLLISION,
    SYM_NATURE_GROUNDING, SYM_NATURE_LISTING, SYM_NATURE_SINKING,
    SYM_NATURE_DISABLED, SYM_NATURE_UNDESIGNATED, SYM_NATURE_ABANDONING,
    SYM_NATURE_PIRACY, SYM_NATURE_MAN_OVERBOARD,
    SYM_TC1_F3E_G3E_ALL, SYM_TC1_DISTRESS_ACK, SYM_TC1_DISTRESS_RELAY,
    SYM_TC1_TEST,
    SYM_TC2_NO_INFO,
    SYM_EOS_ACK_RQ, SYM_EOS_ACK_BQ, SYM_EOS_EOT,
    SYM_NO_INFO,
)


class TestMessageGenerator:
    """Generate standard test DSC messages per ITU-R M.493-16."""

    @staticmethod
    def distress(mmsi: str = "234567890",
                 nature: int = SYM_NATURE_UNDESIGNATED,
                 lat: float = 51.5074, lon: float = -0.1278,
                 time_utc: str = "1200") -> DSCMessage:
        """Generate a distress alert (Table A1-4.1).
        No category field for distress alerts (Section 6.1).
        """
        from ..protocol.position import Position
        return DSCMessage(
            format_specifier=SYM_DISTRESS,
            mmsi_self=mmsi,
            nature_of_distress=nature,
            position=Position(latitude=lat, longitude=lon, time_utc=time_utc),
            telecommand_1=SYM_TC1_F3E_G3E_ALL,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_ACK_RQ,
        )

    @staticmethod
    def distress_fire(mmsi: str = "234567890",
                      lat: float = 51.5074, lon: float = -0.1278) -> DSCMessage:
        return TestMessageGenerator.distress(
            mmsi=mmsi, nature=SYM_NATURE_FIRE, lat=lat, lon=lon)

    @staticmethod
    def distress_sinking(mmsi: str = "234567890",
                         lat: float = 51.5074, lon: float = -0.1278) -> DSCMessage:
        return TestMessageGenerator.distress(
            mmsi=mmsi, nature=SYM_NATURE_SINKING, lat=lat, lon=lon)

    @staticmethod
    def distress_man_overboard(mmsi: str = "234567890",
                                lat: float = 51.5074, lon: float = -0.1278) -> DSCMessage:
        return TestMessageGenerator.distress(
            mmsi=mmsi, nature=SYM_NATURE_MAN_OVERBOARD, lat=lat, lon=lon)

    @staticmethod
    def all_ships_safety(mmsi: str = "234567890") -> DSCMessage:
        """Generate all-ships safety call (Table A1-4.5)."""
        return DSCMessage(
            format_specifier=SYM_ALL_SHIPS,
            category=SYM_CAT_SAFETY,
            mmsi_self=mmsi,
            telecommand_1=SYM_NO_INFO,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_EOT,
        )

    @staticmethod
    def all_ships_urgency(mmsi: str = "234567890") -> DSCMessage:
        """Generate all-ships urgency call."""
        return DSCMessage(
            format_specifier=SYM_ALL_SHIPS,
            category=SYM_CAT_URGENCY,
            mmsi_self=mmsi,
            telecommand_1=SYM_NO_INFO,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_EOT,
        )

    @staticmethod
    def individual_routine(mmsi_self: str = "234567890",
                           mmsi_dest: str = "334455667") -> DSCMessage:
        """Generate individual routine call (Table A1-4.5)."""
        return DSCMessage(
            format_specifier=SYM_INDIVIDUAL,
            category=SYM_CAT_ROUTINE,
            mmsi_dest=mmsi_dest,
            mmsi_self=mmsi_self,
            telecommand_1=SYM_NO_INFO,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_ACK_RQ,
        )

    @staticmethod
    def test(mmsi: str = "234567890") -> DSCMessage:
        """Generate test call (Table A1-4.7)."""
        return DSCMessage(
            format_specifier=SYM_INDIVIDUAL,
            category=SYM_CAT_ROUTINE,
            mmsi_self=mmsi,
            telecommand_1=SYM_TC1_TEST,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_EOT,
        )

    @staticmethod
    def group_call(mmsi_self: str = "234567890",
                   group_mmsi: str = "003344556") -> DSCMessage:
        """Generate group call (Table A1-4.6)."""
        return DSCMessage(
            format_specifier=SYM_GROUP,
            category=SYM_CAT_ROUTINE,
            mmsi_dest=group_mmsi,
            mmsi_self=mmsi_self,
            telecommand_1=SYM_NO_INFO,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_ACK_RQ,
        )

    @staticmethod
    def geo_area(mmsi_self: str = "002345678",
                 lat: float = 51.5074, lon: float = -0.1278) -> DSCMessage:
        """Generate geographic area call (Table A1-4.7)."""
        return DSCMessage(
            format_specifier=SYM_GEO_AREA,
            category=SYM_CAT_SAFETY,
            mmsi_self=mmsi_self,
            telecommand_1=SYM_NO_INFO,
            telecommand_2=SYM_TC2_NO_INFO,
            eos=SYM_EOS_EOT,
        )

    @staticmethod
    def distress_ack(coast_mmsi: str = "002241022",
                     ship_mmsi: str = "234567890") -> DSCMessage:
        """Generate distress acknowledgment (Table A1-4.2)."""
        return DSCMessage(
            format_specifier=SYM_DISTRESS,
            category=SYM_CAT_DISTRESS,
            mmsi_dest=ship_mmsi,
            mmsi_self=coast_mmsi,
            distress_id=ship_mmsi,
            telecommand_1=SYM_TC1_DISTRESS_ACK,
            telecommand_2=SYM_TC1_DISTRESS_ACK,
            eos=SYM_EOS_EOT,
        )

    @staticmethod
    def all_messages(mmsi: str = "234567890") -> list[DSCMessage]:
        """Generate all standard test messages."""
        return [
            TestMessageGenerator.distress(mmsi),
            TestMessageGenerator.distress_fire(mmsi),
            TestMessageGenerator.distress_sinking(mmsi),
            TestMessageGenerator.distress_man_overboard(mmsi),
            TestMessageGenerator.all_ships_safety(mmsi),
            TestMessageGenerator.all_ships_urgency(mmsi),
            TestMessageGenerator.individual_routine(mmsi_self=mmsi),
            TestMessageGenerator.test(mmsi),
            TestMessageGenerator.group_call(mmsi_self=mmsi),
            TestMessageGenerator.geo_area(mmsi_self="00" + mmsi[2:]),
            TestMessageGenerator.distress_ack(ship_mmsi=mmsi),
        ]
