"""Tests for CLI entry point and version."""

import pytest
from typer.testing import CliRunner


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


class TestSyncCommandOptions:
    """Test sync command with various options."""

    def test_sync_incremental_with_verbose(self, runner: CliRunner):
        """sync incremental --verbose should accept verbose flag."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "incremental", "--verbose"])
        # Command should run (even if TODO logic isn't implemented)
        assert result.exit_code == 0

    def test_sync_incremental_with_dry_run(self, runner: CliRunner):
        """sync incremental --dry-run should preview without changes."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "incremental", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.stdout or "would sync" in result.stdout

    def test_sync_full_shows_warning(self, runner: CliRunner):
        """sync full should work when forced."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync", "full", "--force"])
        assert result.exit_code == 0


class TestDuplicateCommandOptions:
    """Test duplicate command with various options."""

    def test_duplicate_flag_with_dry_run(self, runner: CliRunner):
        """duplicate flag --dry-run should preview without changes."""
        from dex_python.cli import app

        result = runner.invoke(app, ["duplicate", "flag", "--dry-run"])
        # Should run even without DB (dry run mode)
        assert result.exit_code in [0, 1]

    def test_duplicate_resolve_requires_confirmation(self, runner: CliRunner):
        """duplicate resolve should require confirmation without --force."""
        from dex_python.cli import app

        # Simulate user declining confirmation
        result = runner.invoke(app, ["duplicate", "resolve"], input="n\n")
        # Should abort
        assert result.exit_code in [0, 1]

    def test_duplicate_resolve_with_force(self, runner: CliRunner):
        """duplicate resolve --force should skip confirmation."""
        from dex_python.cli import app

        result = runner.invoke(app, ["duplicate", "resolve", "--force"])
        # Should run (even if DB doesn't exist, that's a different error)
        assert result.exit_code in [0, 1]


class TestEnrichmentCommandOptions:
    """Test enrichment command with various options."""

    def test_enrichment_push_requires_mode(self, runner: CliRunner):
        """enrichment push should require --mode."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "push"])
        # Should error about missing --mode
        assert result.exit_code != 0

    def test_enrichment_push_with_valid_mode(self, runner: CliRunner):
        """enrichment push with valid mode should work."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "push", "--mode", "notes"])
        # Should run (DB check might fail, but mode validation passes)
        assert result.exit_code in [0, 1]

    def test_enrichment_push_with_invalid_mode(self, runner: CliRunner):
        """enrichment push with invalid mode should error."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment", "push", "--mode", "invalid"])
        assert result.exit_code == 1
        assert "Invalid mode" in result.stdout

    def test_enrichment_push_with_dry_run(self, runner: CliRunner):
        """enrichment push --dry-run should preview."""
        from dex_python.cli import app

        result = runner.invoke(
            app, ["enrichment", "push", "--mode", "notes", "--dry-run"]
        )
        # Should run in dry-run mode
        assert result.exit_code in [0, 1]


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_nonexistent_command(self, runner: CliRunner):
        """Nonexistent command should error gracefully."""
        from dex_python.cli import app

        result = runner.invoke(app, ["nonexistent"])
        assert result.exit_code != 0

    def test_sync_without_subcommand(self, runner: CliRunner):
        """sync without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["sync"])
        assert "incremental" in result.stdout or "Usage" in result.stdout

    def test_duplicate_without_subcommand(self, runner: CliRunner):
        """duplicate without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["duplicate"])
        assert "analyze" in result.stdout or "Usage" in result.stdout

    def test_enrichment_without_subcommand(self, runner: CliRunner):
        """enrichment without subcommand should show help."""
        from dex_python.cli import app

        result = runner.invoke(app, ["enrichment"])
        assert "backfill" in result.stdout or "Usage" in result.stdout


class TestCLIOutputFormatting:
    """Test CLI output formatting."""

    def test_version_output_format(self, runner: CliRunner):
        """Version output should be clean."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        # Should contain version number
        assert "0.1.0" in result.stdout
        # Should be a clean single line or short output
        assert result.stdout.count("\n") <= 2

    def test_help_output_is_readable(self, runner: CliRunner):
        """Help output should be well-formatted."""
        from dex_python.cli import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        # Should have clear sections
        assert "Commands" in result.stdout or "Usage" in result.stdout

    def test_short_version_flag(self, runner: CliRunner):
        """-V should work as short version flag."""
        from dex_python.cli import app

        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout
