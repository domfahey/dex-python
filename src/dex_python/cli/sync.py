"""Sync command group for Dex CLI."""

from pathlib import Path
from typing import Optional

import typer

from .common import resolve_db_path

app = typer.Typer(
    name="sync",
    help="Sync operations with Dex API.",
    no_args_is_help=True,
)


@app.command("incremental")
def incremental(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes"),
) -> None:
    """Incremental sync preserving deduplication metadata (recommended)."""
    resolved_db = resolve_db_path(db_path, data_dir)

    if dry_run:
        typer.echo(f"Dry run - would sync to: {resolved_db}")
        return

    typer.echo(f"Starting incremental sync to: {resolved_db}")
    # TODO: Call actual sync logic from sync_with_integrity.py
    typer.echo("Sync complete.")


@app.command("full")
def full(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Full sync - WARNING: drops all tables and loses deduplication metadata."""
    resolved_db = resolve_db_path(db_path)

    if resolved_db.exists() and not force:
        confirm = typer.confirm(
            "This will DROP all tables and lose deduplication metadata. Continue?"
        )
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Abort()

    typer.echo(f"Starting full sync to: {resolved_db}")
    # TODO: Call actual sync logic from main.py
    typer.echo("Full sync complete.")
