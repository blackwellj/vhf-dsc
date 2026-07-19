"""CLI main entry point."""

import click

from .decode import decode
from .encode import encode
from .monitor import monitor
from .replay import replay
from .test import test as self_test


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """VHF DSC Encoder/Decoder - ITU-R M.493-16 compliant."""
    pass


cli.add_command(decode)
cli.add_command(encode)
cli.add_command(monitor)
cli.add_command(replay)
cli.add_command(self_test)


if __name__ == "__main__":
    cli()
