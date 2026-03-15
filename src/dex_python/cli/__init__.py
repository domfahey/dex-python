"""Dex CLI - Unified command-line interface for Dex CRM tools."""

import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

import typer

from .duplicate import app as duplicate_app
from .enrichment import app as enrichment_app
from .sync import app as sync_app

app = typer.Typer(
    name="dex",
    help="Dex CRM CLI tools for sync, deduplication, and enrichment.",
    no_args_is_help=True,
)


def _cli_version() -> str:
    """Return CLI version from installed metadata or local project metadata."""
    try:
        return package_version("dex-python")
    except PackageNotFoundError:
        for parent in Path(__file__).resolve().parents:
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                try:
                    with pyproject.open("rb") as handle:
                        return str(tomllib.load(handle)["project"]["version"])
                except (OSError, tomllib.TOMLDecodeError, KeyError):
                    continue
    return "0.1.0"


def version_callback(value: bool) -> None:
    """
    Print the CLI version and exit if requested.
    """
    if value:
        cli_version = _cli_version()
        typer.echo(f"dex-python {cli_version}")
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
    Entry point for the Dex CLI.
    """
    pass


# Register command groups
app.add_typer(sync_app, name="sync")
app.add_typer(duplicate_app, name="duplicate")
app.add_typer(enrichment_app, name="enrichment")
