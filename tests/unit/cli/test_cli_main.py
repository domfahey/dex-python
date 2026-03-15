"""Tests for CLI entry point and version."""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

import pytest
from typer.testing import CliRunner


def _expected_cli_version() -> str:
    """Resolve the CLI version from installed metadata or project file."""
    try:
        return package_version("dex-python")
    except PackageNotFoundError:
        for parent in [
            Path(__file__).resolve().parent,
            *Path(__file__).resolve().parents,
        ]:
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                try:
                    with pyproject.open("rb") as handle:
                        return tomllib.load(handle)["project"]["version"]
                except (OSError, tomllib.TOMLDecodeError, KeyError):
                    continue
        return "0.1.0"


CLI_VERSION = _expected_cli_version()


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
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
        assert CLI_VERSION in result.stdout


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


class TestSyncCommandOptions:
    """Test sync command with various options."""

    def test_help_shows_sync_commands(self, runner: CliRunner):
        """--help should show sync subcommands."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "incremental" in result.stdout
        assert "full" in result.stdout

    def test_sync_incremental_with_verbose(self, runner: CliRunner):
        """sync incremental --verbose should accept verbose flag."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "incremental", "--verbose"])
        assert result.exit_code == 0
        assert "Starting incremental sync to:" in result.stdout

    def test_sync_incremental_with_dry_run(self, runner: CliRunner):
        """sync incremental --dry-run should preview without changes."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "incremental", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run - would sync to:" in result.stdout

    def test_sync_full_shows_warning(self, runner: CliRunner):
        """sync full should work when forced."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "full", "--force"])
        assert result.exit_code == 0
        assert "Starting full sync to:" in result.stdout


class TestDuplicateCommandOptions:
    """Test duplicate command with various options."""

    def test_duplicate_flag_with_dry_run(self, runner: CliRunner, tmp_path: Path):
        """duplicate flag --dry-run should preview without changes."""
        from dex_python.cli import app

        db_path = tmp_path / "existing.db"
        db_path.touch()

        result = runner.invoke(
            app, ["duplicate", "flag", "--dry-run", "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert f"Dry run - would flag duplicates in: {db_path}" in result.stdout

    def test_duplicate_resolve_requires_confirmation(
        self, runner: CliRunner, tmp_path: Path
    ):
        """duplicate resolve should require confirmation without --force."""
        from dex_python.cli import app

        db_path = tmp_path / "existing.db"
        db_path.touch()

        result = runner.invoke(
            app, ["duplicate", "resolve", "--db-path", str(db_path)], input="n\n"
        )
        assert result.exit_code == 1
        assert "Aborted." in result.stdout

    def test_duplicate_resolve_with_force(self, runner: CliRunner, tmp_path: Path):
        """duplicate resolve --force should skip confirmation."""
        from dex_python.cli import app

        db_path = tmp_path / "existing.db"
        db_path.touch()

        result = runner.invoke(
            app, ["duplicate", "resolve", "--force", "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert "Resolution complete." in result.stdout


class TestEnrichmentCommandOptions:
    """Test enrichment command with various options."""

    def test_enrichment_push_requires_mode(self, runner: CliRunner):
        """enrichment push should require --mode."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "push"])
        assert result.exit_code == 2
        assert "Missing option '--mode'" in result.output

    def test_enrichment_push_with_valid_mode(self, runner: CliRunner, tmp_path: Path):
        """enrichment push with valid mode should work."""
        from dex_python.cli import app

        db_path = tmp_path / "existing.db"
        db_path.touch()

        result = runner.invoke(
            app, ["enrichment", "push", "--mode", "notes", "--db-path", str(db_path)]
        )
        assert result.exit_code == 0
        assert "Pushing notes from:" in result.stdout

    def test_enrichment_push_with_invalid_mode(self, runner: CliRunner):
        """enrichment push with invalid mode should error."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "push", "--mode", "invalid"])
        assert result.exit_code == 1
        assert "Invalid mode" in result.output

    def test_enrichment_push_with_dry_run(self, runner: CliRunner, tmp_path: Path):
        """enrichment push --dry-run should preview."""
        from dex_python.cli import app

        db_path = tmp_path / "existing.db"
        db_path.touch()

        result = runner.invoke(
            app,
            [
                "enrichment",
                "push",
                "--mode",
                "notes",
                "--dry-run",
                "--db-path",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert "Dry run - would push notes from:" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_nonexistent_command(self, runner: CliRunner):
        """Nonexistent command should error gracefully."""
        from dex_python.cli import app

        result = runner.invoke(app, ["nonexistent"])
        assert result.exit_code == 2
        assert "No such command" in result.output

    def test_sync_without_subcommand(self, runner: CliRunner):
        """sync without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 2
        assert "Usage: dex sync" in result.output

    def test_duplicate_without_subcommand(self, runner: CliRunner):
        """duplicate without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["duplicate"])
        assert result.exit_code == 2
        assert "Usage: dex duplicate" in result.output

    def test_enrichment_without_subcommand(self, runner: CliRunner):
        """enrichment without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment"])
        assert result.exit_code == 2
        assert "Usage: dex enrichment" in result.output


class TestCLIOutputFormatting:
    """Test CLI output formatting."""

    def test_version_output_format(self, runner: CliRunner):
        """Version output should be clean."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert CLI_VERSION in result.stdout
        assert result.stdout.count("\n") <= 2

    def test_help_output_is_readable(self, runner: CliRunner):
        """Help output should be well-formatted."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Commands" in result.stdout or "Usage" in result.stdout

    def test_short_version_flag(self, runner: CliRunner):
        """-V should work as short version flag."""
        from dex_python.cli import app

        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert CLI_VERSION in result.stdout
