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


def run(config: str, force: bool = False):
    """Run the workflow step, optionally forcing execution."""
    statesman = Statesman(config)
    statesman.run(force=force)
    logging.info("Run completed.")


app = cli(
    name="statesman",
    help="Statesman CLI for managing workflow states.",
    max_width=120,
    show_types=True,
    show_defaults=True,
    line_connect=True,
    theme="monochrome",
)

run_cmd = command(
    name="run",
    help="Run the workflow step.",
    callback=run,
    options=[
        option(
            flags=["--config", "-c"],
            help="Config file path",
            arg_type=str,
            required=True,
            sort_key=0,
        ),
        option(
            flags=["--force", "-f"],
            help="Force run regardless of state checks",
            arg_type=bool,
            default=False,
            sort_key=1,
        ),
    ],
)
app.commands.append(run_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
