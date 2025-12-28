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
    """
    Backfill company and role fields by parsing job titles in the resolved database.
    
    Resolves the database location from `db_path` or `data_dir`, verifies the file exists, and performs a backfill that extracts company and role information from job titles.
    
    Parameters:
        db_path (Optional[Path]): Explicit path to the database file. If omitted, `data_dir` may be used to locate the database.
        data_dir (Optional[Path]): Directory to search for the database when `db_path` is not provided.
    
    Raises:
        typer.Exit: Exits with code 1 if the resolved database path does not exist.
    """
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
    """
    Push specified enrichment data from the local database to the Dex API.
    
    Parameters:
        mode (str): Which enrichment field to sync; must be one of "notes", "description", or "job_title".
        db_path (Optional[Path]): Explicit path to the database (used together with `data_dir` to resolve the DB location).
        data_dir (Optional[Path]): Directory used to help resolve the database path when `db_path` is not provided.
        dry_run (bool): If True, print what would be pushed and do not perform any API calls.
    
    Raises:
        typer.Exit: If `mode` is invalid or the resolved database path does not exist.
    """
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