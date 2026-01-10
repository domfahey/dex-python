"""Common utilities for CLI commands."""

import os
from pathlib import Path
from typing import Optional


def resolve_data_dir(explicit_path: Optional[Path] = None) -> Path:
    """
    Resolve the data directory using an explicit override or DEX_DATA_DIR.
    """
    if explicit_path:
        return explicit_path
    return Path(os.getenv("DEX_DATA_DIR", "output"))


def resolve_db_path(
    db_path: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> Path:
    """
    Resolve the database path using an explicit override or data dir.
    """
    if db_path:
        return db_path
    return resolve_data_dir(data_dir) / "dex_contacts.db"
