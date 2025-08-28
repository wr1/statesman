"""CLI entry point for statesman."""

import logging
from typing import Optional

from treeparse import cli, command, option
from statesman.core.base import Statesman

logging.basicConfig(level=logging.INFO)


def check(workdir: Optional[str] = None, config: Optional[str] = None):
    """Check states in a workflow."""
    if not workdir or not config:
        raise ValueError("Workdir and config are required.")
    statesman = Statesman(workdir, config)
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
            flags=["--workdir", "-w"],
            help="Working directory",
            arg_type=str,
            required=True,
            sort_key=0,
        ),
        option(
            flags=["--config", "-c"],
            help="Config file path",
            arg_type=str,
            required=True,
            sort_key=1,
        ),
    ],
)
app.commands.append(check_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
