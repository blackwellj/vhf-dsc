"""Tests for encoder components."""

import pytest

from vhf_dsc.encoder import DSCMessageBuilder, TestMessageGenerator, DSCModulator
from vhf_dsc.encoder.serializer import DSCSerializer
from vhf_dsc.protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_INDIVIDUAL, SYM_GROUP, SYM_GEO_AREA,
    SYM_CAT_DISTRESS, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_SINKING, SYM_NATURE_MAN_OVERBOARD,
    SYM_EOS_ACK_RQ, SYM_EOS_EOT, SYM_TC1_TEST, SYM_TC2_NO_INFO,
)
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


class TestMessageBuilder:
    def test_build_distress(self):
        msg = (
            DSCMessageBuilder()
            .format(SYM_DISTRESS)
            .destination("000000000")
            .source("234567890")
            .eos(SYM_EOS_ACK_RQ)
            .build()
        )
        assert msg.format_specifier == SYM_DISTRESS
        assert msg.is_distress

    def test_build_routine(self):
        msg = (
            DSCMessageBuilder()
            .format(SYM_INDIVIDUAL)
            .category(SYM_CAT_ROUTINE)
            .destination("334455667")
            .source("234567890")
            .build()
        )
        assert msg.format_specifier == SYM_INDIVIDUAL
        assert not msg.is_distress


class TestMsgGenerator:
    def test_all_messages(self):
        msgs = TestMessageGenerator.all_messages()
        assert len(msgs) == 11

    def test_distress_message(self):
        msg = TestMessageGenerator.distress()
        assert msg.is_distress
        assert msg.mmsi_self == "234567890"
        assert msg.format_specifier == SYM_DISTRESS
        assert msg.category is None

    def test_test_message(self):
        msg = TestMessageGenerator.test()
        assert msg.format_specifier == SYM_INDIVIDUAL
        assert msg.telecommand_1 == SYM_TC1_TEST


class TestSerializer:
    def test_serialize_to_symbols(self):
        msg = TestMessageGenerator.test()
        serializer = DSCSerializer()
        symbols = serializer.serialize(msg)
        assert len(symbols) > 0
        assert all(0 <= s <= 127 for s in symbols)

    def test_distress_serialize(self):
        msg = TestMessageGenerator.distress()
        serializer = DSCSerializer()
        symbols = serializer.serialize(msg)
        assert len(symbols) > 0
        assert symbols[0] == SYM_DISTRESS


class TestModulator:
    def test_modulate(self):
        msg = TestMessageGenerator.test()
        modulator = DSCModulator(INTERNAL_SAMPLE_RATE)
        audio = modulator.modulate(msg)
        assert len(audio) > 0
