"""Enrichment command group for Dex CLI."""

from pathlib import Path
from typing import Optional

import typer

from .common import resolve_db_path

app = typer.Typer(
    name="enrichment",
    help="Enrichment operations.",
    no_args_is_help=True,
)


@app.command("backfill")
def backfill(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
) -> None:
    """Parse job titles to extract company and role."""
    resolved_db = resolve_db_path(db_path, data_dir)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Backfilling company/role in: {resolved_db}")
    # TODO: Call actual backfill logic from backfill_company.py
    typer.echo("Backfill complete.")


@app.command("push")
def push(
    mode: str = typer.Option(
        ..., "--mode", "-m", help="Sync mode: notes, description, or job_title"
    ),
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without API calls"),
) -> None:
    """Push enrichment data back to Dex API."""
    resolved_db = resolve_db_path(db_path, data_dir)

    valid_modes = {"notes", "description", "job_title"}
    if mode not in valid_modes:
        typer.echo(f"Invalid mode: {mode}. Must be one of: {valid_modes}", err=True)
        raise typer.Exit(1)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    if dry_run:
        typer.echo(f"Dry run - would push {mode} from: {resolved_db}")
        return

    typer.echo(f"Pushing {mode} from: {resolved_db}")
    # TODO: Call actual push logic from sync_enrichment_back.py
    typer.echo("Push complete.")
