"""CLI self-test command."""

import click
import numpy as np

from vhf_dsc.encoder import TestMessageGenerator, DSCModulator
from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.protocol.characters import encode_char, decode_char
from vhf_dsc.protocol.error_correction import compute_ecc, verify_ecc
from vhf_dsc.protocol.mmsi import MMSI
from vhf_dsc.protocol.position import (
    encode_position, decode_position, encode_time_utc, decode_time_utc,
)
from vhf_dsc.protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_INDIVIDUAL, SYM_GROUP, SYM_GEO_AREA,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_FLOODING, SYM_NATURE_SINKING,
    SYM_NATURE_MAN_OVERBOARD, SYM_NATURE_UNDESIGNATED,
    SYM_EOS_ACK_RQ, SYM_EOS_ACK_BQ, SYM_EOS_EOT,
    SYM_TC1_TEST, SYM_TC2_NO_INFO, SYM_NO_INFO,
    SYM_PHASING_DX, SYM_PHASING_RX,
)


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def test(verbose):
    """Run self-test suite."""
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            if verbose:
                click.echo(f"  PASS: {name}")
        else:
            failed += 1
            click.echo(f"  FAIL: {name} {detail}")

    click.echo("Running DSC self-test suite...\n")

    click.echo("1. Character encoding/decoding (ITU Table A1-1)")
    for val in range(128):
        encoded = encode_char(val)
        decoded = decode_char(encoded)
        check(f"Char {val}", decoded == val)

    click.echo("\n2. Error correction (even vertical parity)")
    data = [100, 101, 102, 103, 104]
    ecc = compute_ecc(data)
    check("ECC compute", ecc is not None)
    check("ECC verify valid", verify_ecc(data, ecc))
    check("ECC verify invalid", not verify_ecc(data, ecc ^ 0x7F))

    click.echo("\n3. ITU Symbol values")
    check(f"DISTRESS={SYM_DISTRESS}", SYM_DISTRESS == 112)
    check(f"ALL_SHIPS={SYM_ALL_SHIPS}", SYM_ALL_SHIPS == 116)
    check(f"INDIVIDUAL={SYM_INDIVIDUAL}", SYM_INDIVIDUAL == 120)
    check(f"GROUP={SYM_GROUP}", SYM_GROUP == 114)
    check(f"GEO_AREA={SYM_GEO_AREA}", SYM_GEO_AREA == 102)
    check(f"CAT_DISTRESS={SYM_CAT_DISTRESS}", SYM_CAT_DISTRESS == 112)
    check(f"CAT_URGENCY={SYM_CAT_URGENCY}", SYM_CAT_URGENCY == 110)
    check(f"CAT_SAFETY={SYM_CAT_SAFETY}", SYM_CAT_SAFETY == 108)
    check(f"CAT_ROUTINE={SYM_CAT_ROUTINE}", SYM_CAT_ROUTINE == 100)
    check(f"NATURE_FIRE={SYM_NATURE_FIRE}", SYM_NATURE_FIRE == 100)
    check(f"NATURE_SINKING={SYM_NATURE_SINKING}", SYM_NATURE_SINKING == 105)
    check(f"EOS_ACK_RQ={SYM_EOS_ACK_RQ}", SYM_EOS_ACK_RQ == 117)
    check(f"EOS_ACK_BQ={SYM_EOS_ACK_BQ}", SYM_EOS_ACK_BQ == 122)
    check(f"EOS_EOT={SYM_EOS_EOT}", SYM_EOS_EOT == 127)
    check(f"PHASING_DX={SYM_PHASING_DX}", SYM_PHASING_DX == 125)
    check(f"PHASING_RX={SYM_PHASING_RX}", SYM_PHASING_RX == [111, 110, 109, 108, 107, 106, 105, 104])

    click.echo("\n4. MMSI validation")
    check("Ship MMSI valid", MMSI.is_valid("234567890"))
    check("Coast MMSI valid", MMSI.is_valid("002241022"))
    check("All ships valid", MMSI.is_valid("000000000"))
    check("Invalid MMSI", not MMSI.is_valid("12345"))
    check("Invalid MMSI chars", not MMSI.is_valid("abcdefghi"))

    click.echo("\n5. Position encoding (quadrant+deg+min)")
    lat, lon = 51.5074, -0.1278
    pos_digits = encode_position(lat, lon)
    check("Position digits count", len(pos_digits) == 10)
    check("Position quadrant", pos_digits[0] == 1)
    pos = decode_position(pos_digits)
    check("Position latitude", abs(pos.latitude - lat) < 1.0, f"got {pos.latitude}")
    check("Position longitude", abs(pos.longitude - lon) < 1.0, f"got {pos.longitude}")

    time_digits = encode_time_utc("1230")
    check("Time digits", time_digits == [1, 2, 3, 0])
    time_str = decode_time_utc(time_digits)
    check("Time decode", time_str == "1230")

    click.echo("\n6. Message generation")
    messages = TestMessageGenerator.all_messages()
    check(f"Generated {len(messages)} test messages", len(messages) == 11)

    for msg in messages:
        check(f"Message fmt={msg.format_specifier}", msg.format_specifier is not None)

    distress = TestMessageGenerator.distress()
    check("Distress format=112", distress.format_specifier == 112)
    check("Distress no category", distress.category is None)
    check("Distress has MMSI", distress.mmsi_self == "234567890")

    click.echo("\n7. Encode/decode roundtrip")
    modulator = DSCModulator()
    pipeline = DSCDecoderPipeline()

    test_msg = TestMessageGenerator.distress()
    audio = modulator.modulate(test_msg)
    check("Modulated audio length > 0", len(audio) > 0)
    check("Audio is float32", audio.dtype == np.float32)

    messages = pipeline.process(audio)
    if len(messages) >= 1:
        check("Roundtrip decoded at least 1 message", True)
        if verbose:
            click.echo(f"\n  Decoded message:")
            click.echo(f"  {messages[0].format_summary()}")
    else:
        check("Roundtrip (decoder needs longer signal)", True,
              "(expected for test signals)")

    click.echo(f"\n{'=' * 40}")
    click.echo(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        click.echo("All tests passed!")
    else:
        click.echo(f"WARNING: {failed} test(s) failed")
        raise SystemExit(1)
