"""Dex CLI - Unified command-line interface for Dex CRM tools."""

import typer

from .duplicate import app as duplicate_app
from .enrichment import app as enrichment_app
from .sync import app as sync_app

app = typer.Typer(
    name="dex",
    help="Dex CRM CLI tools for sync, deduplication, and enrichment.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo("dex-python 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Dex CRM CLI tools."""
    pass


# Register command groups
app.add_typer(sync_app, name="sync")
app.add_typer(duplicate_app, name="duplicate")
app.add_typer(enrichment_app, name="enrichment")
