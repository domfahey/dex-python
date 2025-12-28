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
    """
    Print the CLI version and exit the process when requested.
    
    Parameters:
        value (bool): If True, print the version string "dex-python 0.1.0" and terminate the application.
    
    Raises:
        typer.Exit: Raised to terminate the CLI after printing the version when `value` is True.
    """
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
    """
    Entry point for the Dex CRM command-line interface.
    
    When invoked with the version option, prints "dex-python 0.1.0" and exits.
    
    Parameters:
        version (bool): If True, display the CLI version and exit immediately.
    """
    pass


# Register command groups
app.add_typer(sync_app, name="sync")
app.add_typer(duplicate_app, name="duplicate")
app.add_typer(enrichment_app, name="enrichment")