"""Tests for database session management."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


class TestGetEngine:
    """Test get_engine function."""

    def test_creates_engine_with_default_path(self):
        """Should create engine with default db path."""
        from dex_python.db.session import get_engine

        engine = get_engine()
        assert isinstance(engine, Engine)
        assert "dex_contacts.db" in str(engine.url)

    def test_creates_engine_with_custom_path(self):
        """Should create engine with custom db path."""
        from dex_python.db.session import get_engine

        custom_path = Path("/tmp/custom.db")
        engine = get_engine(custom_path)
        assert isinstance(engine, Engine)
        assert "custom.db" in str(engine.url)

    def test_creates_engine_with_string_path(self):
        """Should accept string path as well as Path object."""
        from dex_python.db.session import get_engine

        engine = get_engine("test.db")
        assert isinstance(engine, Engine)
        assert "test.db" in str(engine.url)

    def test_echo_is_disabled_by_default(self):
        """Engine should have echo=False by default."""
        from dex_python.db.session import get_engine

        engine = get_engine()
        assert engine.echo is False

    def test_creates_sqlite_engine(self):
        """Should create SQLite engine."""
        from dex_python.db.session import get_engine

        engine = get_engine()
        assert "sqlite" in str(engine.url.drivername)

    def test_none_path_uses_default(self):
        """None path should use default."""
        from dex_python.db.session import get_engine

        engine = get_engine(None)
        assert isinstance(engine, Engine)
        assert "dex_contacts.db" in str(engine.url)

    def test_memory_database(self):
        """Should support in-memory database."""
        from dex_python.db.session import get_engine

        engine = get_engine(":memory:")
        assert isinstance(engine, Engine)
        assert ":memory:" in str(engine.url)


class TestGetSession:
    """Test get_session function."""

    def test_creates_session_with_default_path(self):
        """Should create session with default db path."""
        from dex_python.db.session import get_session

        session = get_session()
        assert isinstance(session, Session)
        session.close()

    def test_creates_session_with_custom_path(self):
        """Should create session with custom db path."""
        from dex_python.db.session import get_session

        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            session = get_session(tmp.name)
            assert isinstance(session, Session)
            session.close()

    def test_session_is_bound_to_engine(self):
        """Session should be bound to an engine."""
        from dex_python.db.session import get_session

        session = get_session()
        assert session.bind is not None
        session.close()

    def test_multiple_sessions_are_independent(self):
        """Multiple get_session calls should create independent sessions."""
        from dex_python.db.session import get_session

        session1 = get_session()
        session2 = get_session()
        assert session1 is not session2
        session1.close()
        session2.close()

    def test_accepts_string_path(self):
        """Should accept string path."""
        from dex_python.db.session import get_session

        session = get_session("test.db")
        assert isinstance(session, Session)
        session.close()

    def test_accepts_path_object(self):
        """Should accept Path object."""
        from dex_python.db.session import get_session

        session = get_session(Path("test.db"))
        assert isinstance(session, Session)
        session.close()

    def test_none_path_uses_default(self):
        """None path should use default."""
        from dex_python.db.session import get_session

        session = get_session(None)
        assert isinstance(session, Session)
        session.close()

    def test_memory_database_session(self):
        """Should work with in-memory database."""
        from dex_python.db.session import get_session

        session = get_session(":memory:")
        assert isinstance(session, Session)
        session.close()


class TestSessionOperations:
    """Test actual database operations with sessions."""

    def test_can_create_tables_with_session(self):
        """Session should allow creating tables."""
        from dex_python.db.models import Base
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)

        session = get_session(":memory:")
        # If we got here without error, tables were created successfully
        session.close()

    def test_session_can_query_empty_table(self):
        """Session should be able to query empty tables."""
        from dex_python.db.models import Base, Contact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)

        session = get_session(":memory:")
        # Query should return empty list, not error
        result = session.query(Contact).all()
        assert result == []
        session.close()