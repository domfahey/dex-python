"""Database session management."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_PATH = Path("dex_contacts.db")


def get_engine(db_path: Path | str | None = None) -> Engine:
    """
    Create an SQLAlchemy Engine configured for a SQLite database file.
    
    Parameters:
        db_path (Path | str | None): Path to the SQLite database file. If omitted or None, DEFAULT_DB_PATH is used.
    
    Returns:
        engine (Engine): SQLAlchemy Engine connected to the specified SQLite database file.
    """
    path = db_path or DEFAULT_DB_PATH
    return create_engine(f"sqlite:///{path}", echo=False)


def get_session(db_path: Path | str | None = None) -> Session:
    """
    Create a new SQLAlchemy Session bound to the SQLite database specified by db_path.
    
    Parameters:
        db_path (Path | str | None): Path to the SQLite database file. If None, the default database path is used.
    
    Returns:
        Session: A SQLAlchemy Session instance bound to the engine for the given database.
    """
    engine = get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    return session_factory()