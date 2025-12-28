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
    """Generate duplicate analysis report."""
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
    """Flag duplicate candidates without merging."""
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
    """Merge confirmed duplicates (DESTRUCTIVE)."""
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
