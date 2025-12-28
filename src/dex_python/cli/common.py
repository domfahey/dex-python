"""Common utilities for CLI commands."""

import os
from pathlib import Path
from typing import Optional


def resolve_data_dir(explicit_path: Optional[Path] = None) -> Path:
    """Resolve data directory from explicit path or environment.

    Args:
        explicit_path: Explicit path override.

    Returns:
        Resolved data directory path.
    """
    if explicit_path:
        return explicit_path
    return Path(os.getenv("DEX_DATA_DIR", "output"))


def resolve_db_path(
    db_path: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> Path:
    """Resolve database path from explicit path, data dir, or defaults.

    Args:
        db_path: Explicit database path override.
        data_dir: Data directory override.

    Returns:
        Resolved database path.
    """
    if db_path:
        return db_path
    return resolve_data_dir(data_dir) / "dex_contacts.db"
