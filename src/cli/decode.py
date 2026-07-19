"""CLI decode command."""

import click
import numpy as np

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.io.wav import read_wav
from vhf_dsc.io.raw import read_real
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--sample-rate", "-r", default=0, help="Sample rate (0 = auto-detect)")
@click.option("--format", "-f", "file_format", default="wav",
              type=click.Choice(["wav", "raw"]), help="Input file format")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def decode(input_file, sample_rate, file_format, output_json):
    """Decode DSC messages from an audio file."""
    if file_format == "wav":
        samples, sr = read_wav(input_file)
    else:
        samples = read_real(input_file)
        sr = sample_rate if sample_rate > 0 else INTERNAL_SAMPLE_RATE

    if sample_rate > 0:
        sr = sample_rate

    pipeline = DSCDecoderPipeline(sr)

    if output_json:
        import json
        messages = pipeline.process(samples)
        result = [msg.to_dict() for msg in messages]
        click.echo(json.dumps(result, indent=2))
    else:
        def on_message(msg):
            click.echo("=" * 60)
            click.echo(msg.format_summary())
            click.echo(f"Time: {msg.timestamp}")
            click.echo(f"Status: {msg.status}")
            click.echo("")

        pipeline.on_message(on_message)
        messages = pipeline.process(samples)

        click.echo(f"\nDecoded {len(messages)} message(s)")
        click.echo(f"Errors: {pipeline.error_count}")
