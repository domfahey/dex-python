"""Tests for CLI common utilities."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestResolveDataDir:
    """Test resolve_data_dir function."""

    def test_explicit_path_takes_precedence(self):
        """Explicit path should override environment variable."""
        from dex_python.cli.common import resolve_data_dir

        explicit = Path("/custom/data/dir")
        with patch.dict(os.environ, {"DEX_DATA_DIR": "/env/data/dir"}):
            result = resolve_data_dir(explicit)
            assert result == explicit

    def test_uses_environment_variable(self):
        """Should use DEX_DATA_DIR environment variable when set."""
        from dex_python.cli.common import resolve_data_dir

        with patch.dict(os.environ, {"DEX_DATA_DIR": "/env/data/dir"}):
            result = resolve_data_dir()
            assert result == Path("/env/data/dir")

    def test_defaults_to_output(self):
        """Should default to 'output' when no env var or explicit path."""
        from dex_python.cli.common import resolve_data_dir

        with patch.dict(os.environ, {}, clear=True):
            result = resolve_data_dir()
            assert result == Path("output")

    def test_none_explicit_path_uses_env(self):
        """Passing None should use environment variable."""
        from dex_python.cli.common import resolve_data_dir

        with patch.dict(os.environ, {"DEX_DATA_DIR": "/test/dir"}):
            result = resolve_data_dir(None)
            assert result == Path("/test/dir")

    def test_returns_path_object(self):
        """Should always return a Path object."""
        from dex_python.cli.common import resolve_data_dir

        result = resolve_data_dir()
        assert isinstance(result, Path)

    def test_relative_path_handling(self):
        """Should handle relative paths correctly."""
        from dex_python.cli.common import resolve_data_dir

        relative = Path("./data")
        result = resolve_data_dir(relative)
        assert result == relative


class TestResolveDbPath:
    """Test resolve_db_path function."""

    def test_explicit_db_path_takes_precedence(self):
        """Explicit db_path should override data_dir."""
        from dex_python.cli.common import resolve_db_path

        db_path = Path("/custom/db.sqlite")
        data_dir = Path("/custom/data")
        result = resolve_db_path(db_path, data_dir)
        assert result == db_path

    def test_uses_data_dir_when_no_db_path(self):
        """Should use data_dir / dex_contacts.db when no db_path."""
        from dex_python.cli.common import resolve_db_path

        data_dir = Path("/custom/data")
        result = resolve_db_path(None, data_dir)
        assert result == Path("/custom/data/dex_contacts.db")

    def test_defaults_to_output_dex_contacts_db(self):
        """Should default to output/dex_contacts.db with no args."""
        from dex_python.cli.common import resolve_db_path

        with patch.dict(os.environ, {}, clear=True):
            result = resolve_db_path()
            assert result == Path("output/dex_contacts.db")

    def test_uses_env_var_for_default_data_dir(self):
        """Should use DEX_DATA_DIR env var when no explicit paths."""
        from dex_python.cli.common import resolve_db_path

        with patch.dict(os.environ, {"DEX_DATA_DIR": "/env/data"}):
            result = resolve_db_path()
            assert result == Path("/env/data/dex_contacts.db")

    def test_none_values_use_defaults(self):
        """None values should fall through to defaults."""
        from dex_python.cli.common import resolve_db_path

        with patch.dict(os.environ, {"DEX_DATA_DIR": "/test"}):
            result = resolve_db_path(None, None)
            assert result == Path("/test/dex_contacts.db")

    def test_returns_path_object(self):
        """Should always return a Path object."""
        from dex_python.cli.common import resolve_db_path

        result = resolve_db_path()
        assert isinstance(result, Path)

    def test_absolute_path_handling(self):
        """Should handle absolute paths correctly."""
        from dex_python.cli.common import resolve_db_path

        abs_path = Path("/absolute/path/db.sqlite")
        result = resolve_db_path(abs_path)
        assert result == abs_path

    def test_data_dir_with_trailing_slash(self):
        """Should handle data_dir with trailing slash."""
        from dex_python.cli.common import resolve_db_path

        data_dir = Path("/data/dir/")
        result = resolve_db_path(None, data_dir)
        assert result == Path("/data/dir/dex_contacts.db")