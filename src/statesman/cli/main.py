"""CLI entry point for statesman."""

import logging

from rich.logging import RichHandler
from treeparse import cli, command, option
from statesman.core.base import Statesman

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler()],
)


def check(config: str):
    """Check states in a workflow."""
    statesman = Statesman(config)
    logging.info("State check completed.")


app = cli(
    name="statesman",
    help="Statesman CLI for managing workflow states.",
    max_width=120,
    show_types=True,
    show_defaults=True,
    line_connect=True,
    theme="monochrome",
)

check_cmd = command(
    name="check",
    help="Check states in a workflow.",
    callback=check,
    options=[
        option(
            flags=["--config", "-c"],
            help="Config file path",
            arg_type=str,
            required=True,
            sort_key=0,
        ),
    ],
)
app.commands.append(check_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
