"""CLI encode command."""

import click
import numpy as np

from vhf_dsc.encoder import DSCMessageBuilder, DSCModulator, TestMessageGenerator
from vhf_dsc.encoder.modulator import DSCModulator as Mod
from vhf_dsc.io.wav import write_wav, write_wav_normalized
from vhf_dsc.io.raw import write_real
from vhf_dsc.protocol.symbols import (
    SYM_DISTRESS, SYM_ALL_SHIPS, SYM_INDIVIDUAL, SYM_GROUP, SYM_GEO_AREA,
    SYM_CAT_DISTRESS, SYM_CAT_URGENCY, SYM_CAT_SAFETY, SYM_CAT_ROUTINE,
    SYM_NATURE_FIRE, SYM_NATURE_FLOODING, SYM_NATURE_COLLISION,
    SYM_NATURE_GROUNDING, SYM_NATURE_LISTING, SYM_NATURE_SINKING,
    SYM_NATURE_DISABLED, SYM_NATURE_UNDESIGNATED, SYM_NATURE_ABANDONING,
    SYM_NATURE_PIRACY, SYM_NATURE_MAN_OVERBOARD,
    SYM_EOS_ACK_RQ, SYM_EOS_EOT,
    SYM_TC1_TEST, SYM_TC2_NO_INFO, SYM_TC1_F3E_G3E_ALL,
)
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


NATURE_MAP = {
    "not_specified": SYM_NATURE_UNDESIGNATED,
    "fire_explosion": SYM_NATURE_FIRE,
    "flooding": SYM_NATURE_FLOODING,
    "collision": SYM_NATURE_COLLISION,
    "grounding": SYM_NATURE_GROUNDING,
    "listing": SYM_NATURE_LISTING,
    "sinking": SYM_NATURE_SINKING,
    "disabled_adrift": SYM_NATURE_DISABLED,
    "abandoning_ship": SYM_NATURE_ABANDONING,
    "piracy": SYM_NATURE_PIRACY,
    "man_overboard": SYM_NATURE_MAN_OVERBOARD,
}


@click.command()
@click.option("--type", "-t", "msg_type", default="test",
              type=click.Choice(["distress", "safety", "urgency", "routine",
                                 "test", "group", "geo", "distress_ack"]),
              help="Message type to generate")
@click.option("--mmsi", "-m", default="234567890", help="Source MMSI")
@click.option("--dest-mmsi", "-d", default="000000000", help="Destination MMSI")
@click.option("--lat", default=51.5074, help="Latitude")
@click.option("--lon", default=-0.1278, help="Longitude")
@click.option("--time", default="1200", help="UTC time (HHMM)")
@click.option("--nature", default="not_specified",
              type=click.Choice(list(NATURE_MAP.keys())),
              help="Nature of distress")
@click.option("--output", "-o", "output_file", default="dsc_test.wav",
              help="Output file path")
@click.option("--format", "-f", "file_format", default="wav",
              type=click.Choice(["wav", "raw"]), help="Output format")
@click.option("--sample-rate", "-r", default=INTERNAL_SAMPLE_RATE,
              help="Sample rate")
@click.option("--pulse-shaping", is_flag=True, help="Apply pulse shaping")
@click.option("--count", "-n", default=1, help="Number of messages to generate")
@click.option("--gap-ms", default=500, help="Gap between messages (ms)")
@click.option("--channel", "-c", "channel_model", default="perfect",
              type=click.Choice(["perfect", "good", "moderate", "poor", "marginal"]),
              help="Radio channel model")
@click.option("--snr", type=float, help="Custom SNR in dB (overrides channel model)")
@click.option("--seed", type=int, help="Random seed for reproducibility")
@click.option("--suite", is_flag=True, help="Generate full test suite (all models)")
@click.option("--suite-dir", default="./test_suite", help="Output directory for test suite")
def encode(msg_type, mmsi, dest_mmsi, lat, lon, time, nature,
           output_file, file_format, sample_rate, pulse_shaping, count, gap_ms,
           channel_model, snr, seed, suite, suite_dir):
    """Generate DSC test messages as audio files."""
    nature_sym = NATURE_MAP.get(nature, SYM_NATURE_UNDESIGNATED)

    if msg_type == "distress":
        msg = TestMessageGenerator.distress(mmsi, nature_sym, lat, lon, time)
    elif msg_type == "safety":
        msg = TestMessageGenerator.all_ships_safety(mmsi)
    elif msg_type == "urgency":
        msg = TestMessageGenerator.all_ships_urgency(mmsi)
    elif msg_type == "routine":
        msg = TestMessageGenerator.individual_routine(mmsi, dest_mmsi)
    elif msg_type == "test":
        msg = TestMessageGenerator.test(mmsi)
    elif msg_type == "group":
        msg = TestMessageGenerator.group_call(mmsi, dest_mmsi)
    elif msg_type == "geo":
        msg = TestMessageGenerator.geo_area(mmsi, lat, lon)
    elif msg_type == "distress_ack":
        msg = TestMessageGenerator.distress_ack(dest_mmsi, mmsi)
    else:
        msg = TestMessageGenerator.test(mmsi)

    modulator = Mod(sample_rate)

    if suite:
        import os
        os.makedirs(suite_dir, exist_ok=True)
        test_suite = modulator.generate_test_suite(msg, seed=seed or 42)
        for name, audio in test_suite.items():
            filepath = os.path.join(suite_dir, f"{msg_type}_{name}.wav")
            write_wav_normalized(filepath, audio, sample_rate)
            click.echo(f"Generated: {filepath} ({len(audio) / sample_rate:.2f}s)")
        click.echo(f"\nGenerated {len(test_suite)} test files in {suite_dir}/")
        return

    snr_db = snr
    if snr_db is None and channel_model == "custom":
        snr_db = 15

    if count == 1:
        audio = modulator.modulate(
            msg, pulse_shaping=pulse_shaping,
            channel_model=channel_model, snr_db=snr_db, seed=seed)
    else:
        messages = [msg] * count
        audio = modulator.modulate_messages(
            messages, gap_ms=gap_ms,
            channel_model=channel_model, snr_db=snr_db, seed=seed)

    if file_format == "wav":
        write_wav_normalized(output_file, audio, sample_rate)
    else:
        write_real(output_file, audio)

    click.echo(f"Generated {count} {msg_type} message(s)")
    click.echo(f"Channel model: {channel_model}" + (f" (SNR: {snr_db} dB)" if snr_db else ""))
    click.echo(f"Output: {output_file}")
    click.echo(f"Format: {file_format}")
    click.echo(f"Sample rate: {sample_rate} Hz")
    click.echo(f"Duration: {len(audio) / sample_rate:.2f} seconds")
