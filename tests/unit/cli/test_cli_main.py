"""Tests for CLI entry point and version."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """
    Provide a Typer CliRunner for invoking the application's CLI in tests.
    
    Returns:
        CliRunner: An isolated runner instance for executing CLI commands.
    """
    return CliRunner()


class TestCLIApp:
    """Test CLI app exists and is callable."""

    def test_cli_app_exists(self):
        """CLI app should be importable."""
        from dex_python.cli import app

        assert app is not None

    def test_version_flag(self, runner: CliRunner):
        """--version flag should work."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout

    def test_help_shows_command_groups(self, runner: CliRunner):
        """--help should show all command groups."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "sync" in result.stdout
        assert "duplicate" in result.stdout
        assert "enrichment" in result.stdout


class TestSyncCommands:
    """Test sync command group."""

    def test_sync_help(self, runner: CliRunner):
        """sync --help should work."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "incremental" in result.stdout
        assert "full" in result.stdout


class TestDuplicateCommands:
    """Test duplicate command group."""

    def test_duplicate_help(self, runner: CliRunner):
        """duplicate --help should work."""
        from dex_python.cli import app

        result = runner.invoke(app, ["duplicate", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout
        assert "flag" in result.stdout
        assert "review" in result.stdout
        assert "resolve" in result.stdout


class TestEnrichmentCommands:
    """Test enrichment command group."""

    def test_enrichment_help(self, runner: CliRunner):
        """enrichment --help should work."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "--help"])
        assert result.exit_code == 0
        assert "backfill" in result.stdout
        assert "push" in result.stdout