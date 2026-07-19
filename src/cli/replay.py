"""CLI replay command for sending audio files as UDP stream."""

import click

from vhf_dsc.io.wav import read_wav
from vhf_dsc.io.raw import read_real
from vhf_dsc.io.udp_stream import UDPStreamSender
from vhf_dsc.protocol.constants import INTERNAL_SAMPLE_RATE


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--host", default="127.0.0.1", help="UDP target address")
@click.option("--port", "-p", default=6000, help="UDP target port")
@click.option("--sample-rate", "-r", default=0, help="Sample rate (0 = auto)")
@click.option("--format", "-f", "file_format", default="wav",
              type=click.Choice(["wav", "raw"]), help="Input format")
@click.option("--realtime", is_flag=True, help="Send at real-time speed")
@click.option("--loop", is_flag=True, help="Loop playback")
def replay(input_file, host, port, sample_rate, file_format, realtime, loop):
    """Replay an audio file as a UDP stream."""
    if file_format == "wav":
        samples, sr = read_wav(input_file)
    else:
        samples = read_real(input_file)
        sr = sample_rate if sample_rate > 0 else INTERNAL_SAMPLE_RATE

    if sample_rate > 0:
        sr = sample_rate

    sender = UDPStreamSender(host, port, sr)

    click.echo(f"Replaying {input_file} to {host}:{port}")
    click.echo(f"Sample rate: {sr} Hz")
    click.echo(f"Duration: {len(samples) / sr:.2f} seconds")
    click.echo(f"Real-time: {realtime}")
    click.echo(f"Loop: {loop}")
    click.echo("Press Ctrl+C to stop\n")

    import signal

    running = True

    def stop(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    try:
        while running:
            if realtime:
                sender.send_file(samples)
            else:
                sender.send(samples)

            if not loop:
                break
    finally:
        sender.close()
        click.echo("\nReplay stopped")
