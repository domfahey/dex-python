"""Common utilities for CLI commands."""

import os
from pathlib import Path
from typing import Optional


def resolve_data_dir(explicit_path: Optional[Path] = None) -> Path:
    """
    Determine the data directory to use.
    
    If `explicit_path` is provided, it is returned; otherwise the `DEX_DATA_DIR` environment variable is used, falling back to "output" when unset.
    
    Parameters:
        explicit_path (Path | None): Optional explicit directory path override.
    
    Returns:
        Path: Resolved data directory path.
    """
    if explicit_path:
        return explicit_path
    return Path(os.getenv("DEX_DATA_DIR", "output"))


def resolve_db_path(
    db_path: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> Path:
    """
    Determine the database file path using an explicit override or the data directory.
    
    Parameters:
        db_path (Path | None): Explicit database file path override.
        data_dir (Path | None): Data directory to use when `db_path` is not provided; if omitted, the module's default or environment-configured data directory is used.
    
    Returns:
        Path: Path to the database file — the explicit `db_path` if provided, otherwise `<data_dir>/dex_contacts.db`.
    """
    if db_path:
        return db_path
    return resolve_data_dir(data_dir) / "dex_contacts.db"