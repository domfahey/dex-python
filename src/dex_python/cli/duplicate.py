"""Duplicate command group for Dex CLI."""

from pathlib import Path
from typing import Optional

import typer

from .common import resolve_db_path

app = typer.Typer(
    name="duplicate",
    help="Deduplication workflow commands.",
    no_args_is_help=True,
)


@app.command("analyze")
def analyze(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output report path"
    ),
) -> None:
    """
    Generate a duplicate analysis report for the resolved database.
    
    If the resolved database path does not exist, exits with status code 1 after printing an error.
    Parameters:
        output (Path | None): If provided, path where the analysis report should be written; otherwise the report is printed to stdout.
    """
    resolved_db = resolve_db_path(db_path, data_dir)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Analyzing duplicates in: {resolved_db}")
    # TODO: Call actual analysis logic from analyze_duplicates.py
    typer.echo("Analysis complete.")


@app.command("flag")
def flag(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes"),
) -> None:
    """
    Flag candidate duplicate records in the resolved database without performing merges.
    
    If `dry_run` is True, print a preview of the actions that would be taken and make no changes.
    
    Parameters:
        dry_run (bool): If True, show which duplicates would be flagged but do not modify the database.
    """
    resolved_db = resolve_db_path(db_path, data_dir)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    if dry_run:
        typer.echo(f"Dry run - would flag duplicates in: {resolved_db}")
        return

    typer.echo(f"Flagging duplicates in: {resolved_db}")
    # TODO: Call actual flagging logic from flag_duplicates.py
    typer.echo("Flagging complete.")


@app.command("review")
def review(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
) -> None:
    """Interactive duplicate review tool."""
    resolved_db = resolve_db_path(db_path, data_dir)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Starting review for: {resolved_db}")
    # TODO: Call actual review logic from review_duplicates.py
    typer.echo("Review complete.")


@app.command("resolve")
def resolve(
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Database path"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", help="Data directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """
    Permanently merge confirmed duplicate contacts in the resolved database.
    
    Resolves the database path from `db_path` and `data_dir`, prompts for confirmation unless `force` is true, and performs a destructive merge of confirmed duplicates.
    
    Parameters:
        db_path (Optional[Path]): Explicit path to the database; if omitted, the path is resolved from `data_dir`.
        data_dir (Optional[Path]): Directory used to resolve the database path when `db_path` is not provided.
        force (bool): If true, skip the interactive confirmation prompt and proceed immediately.
    
    Raises:
        typer.Exit: If the resolved database path does not exist (exits with code 1).
        typer.Abort: If the user declines the confirmation prompt.
    """
    resolved_db = resolve_db_path(db_path, data_dir)

    if not resolved_db.exists():
        typer.echo(f"Database not found: {resolved_db}", err=True)
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(
            "This will permanently merge duplicate contacts. Continue?"
        )
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Abort()

    typer.echo(f"Resolving duplicates in: {resolved_db}")
    # TODO: Call actual resolve logic from resolve_duplicates.py
    typer.echo("Resolution complete.")