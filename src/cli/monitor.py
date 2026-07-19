"""CLI monitor command for live UDP stream."""

import click
import signal

from vhf_dsc.decoder import DSCDecoderPipeline
from vhf_dsc.io.udp_stream import UDPStreamReceiver
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


@click.command()
@click.option("--host", default="0.0.0.0", help="UDP listen address")
@click.option("--port", "-p", default=6000, help="UDP listen port")
@click.option("--sample-rate", "-r", default=INTERNAL_SAMPLE_RATE,
              help="Expected sample rate")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def monitor(host, port, sample_rate, output_json):
    """Monitor live DSC messages from UDP stream."""
    pipeline = DSCDecoderPipeline(sample_rate)

    def on_audio(samples):
        messages = pipeline.process(samples)
        for msg in messages:
            if output_json:
                import json
                click.echo(json.dumps(msg.to_dict()))
            else:
                click.echo("=" * 60)
                click.echo(msg.format_summary())
                click.echo(f"Time: {msg.timestamp}")
                click.echo(f"Status: {msg.status}")
                click.echo("")

    receiver = UDPStreamReceiver(host, port, sample_rate)
    receiver.on_audio(on_audio)

    click.echo(f"Listening on {host}:{port} (sample rate: {sample_rate} Hz)")
    click.echo("Press Ctrl+C to stop\n")

    def stop(signum, frame):
        click.echo("\nStopping...")
        receiver.stop()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    receiver.start()
