"""Database session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_PATH = Path("dex_contacts.db")


def get_engine(db_path: Path | str | None = None) -> Engine:
    """Create SQLAlchemy engine for the database.

    Args:
        db_path: Path to SQLite database file. Defaults to dex_contacts.db.

    Returns:
        SQLAlchemy Engine instance.
    """
    path = db_path or DEFAULT_DB_PATH
    return create_engine(f"sqlite:///{path}", echo=False)


def get_session(db_path: Path | str | None = None) -> Session:
    """Create a new database session.

    Args:
        db_path: Path to SQLite database file. Defaults to dex_contacts.db.

    Returns:
        SQLAlchemy Session instance.
    """
    engine = get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    return session_factory()
