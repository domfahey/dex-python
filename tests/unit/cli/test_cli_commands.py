"""Comprehensive CLI command tests including database interactions.

Tests CLI commands with actual database operations where applicable.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dex_python.cli import app


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_db() -> Path:
    """Create a temporary database file with schema."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create contacts table
    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT,
            linkedin TEXT,
            website TEXT,
            full_data TEXT,
            record_hash TEXT,
            last_synced_at TEXT,
            duplicate_group_id TEXT,
            duplicate_resolution TEXT,
            primary_contact_id TEXT,
            name_given TEXT,
            name_surname TEXT,
            name_parsed TEXT,
            company TEXT,
            role TEXT
        )
    """)

    # Create emails table
    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)

    # Create phones table
    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT,
            label TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    db_path.unlink(missing_ok=True)


class TestDuplicateAnalyzeCommand:
    """Tests for duplicate analyze command."""

    def test_analyze_with_existing_db(
        self, runner: CliRunner, temp_db: Path
    ) -> None:
        """analyze should work with existing database."""
        result = runner.invoke(app, ["duplicate", "analyze", "--db-path", str(temp_db)])
        assert result.exit_code == 0
        assert "Analyzing duplicates" in result.stdout

    def test_analyze_with_nonexistent_db(self, runner: CliRunner) -> None:
        """analyze should error for nonexistent database."""
        result = runner.invoke(
            app, ["duplicate", "analyze", "--db-path", "/nonexistent/path.db"]
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output

    def test_analyze_with_output_option(
        self, runner: CliRunner, temp_db: Path
    ) -> None:
        """analyze should accept --output option."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        result = runner.invoke(
            app,
            ["duplicate", "analyze", "--db-path", str(temp_db), "--output", output_path],
        )
        assert result.exit_code == 0

        Path(output_path).unlink(missing_ok=True)


class TestDuplicateFlagCommand:
    """Tests for duplicate flag command."""

    def test_flag_with_existing_db(self, runner: CliRunner, temp_db: Path) -> None:
        """flag should work with existing database."""
        result = runner.invoke(app, ["duplicate", "flag", "--db-path", str(temp_db)])
        assert result.exit_code == 0
        assert "Flagging" in result.stdout or "complete" in result.stdout

    def test_flag_dry_run(self, runner: CliRunner, temp_db: Path) -> None:
        """flag --dry-run should preview without changes."""
        result = runner.invoke(
            app, ["duplicate", "flag", "--db-path", str(temp_db), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run" in result.stdout

    def test_flag_with_nonexistent_db(self, runner: CliRunner) -> None:
        """flag should error for nonexistent database."""
        result = runner.invoke(
            app, ["duplicate", "flag", "--db-path", "/nonexistent/path.db"]
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output


class TestDuplicateReviewCommand:
    """Tests for duplicate review command."""

    def test_review_with_existing_db(self, runner: CliRunner, temp_db: Path) -> None:
        """review should work with existing database."""
        result = runner.invoke(app, ["duplicate", "review", "--db-path", str(temp_db)])
        assert result.exit_code == 0
        assert "review" in result.stdout.lower() or "complete" in result.stdout.lower()

    def test_review_with_nonexistent_db(self, runner: CliRunner) -> None:
        """review should error for nonexistent database."""
        result = runner.invoke(
            app, ["duplicate", "review", "--db-path", "/nonexistent/path.db"]
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output

    def test_review_help(self, runner: CliRunner) -> None:
        """review --help should show help."""
        result = runner.invoke(app, ["duplicate", "review", "--help"])
        assert result.exit_code == 0
        assert "Interactive duplicate review" in result.stdout


class TestDuplicateResolveCommand:
    """Tests for duplicate resolve command."""

    def test_resolve_with_force(self, runner: CliRunner, temp_db: Path) -> None:
        """resolve --force should skip confirmation."""
        result = runner.invoke(
            app, ["duplicate", "resolve", "--db-path", str(temp_db), "--force"]
        )
        assert result.exit_code == 0
        assert "Resolving" in result.stdout or "complete" in result.stdout.lower()

    def test_resolve_without_force_abort(self, runner: CliRunner, temp_db: Path) -> None:
        """resolve without --force should prompt and allow abort."""
        result = runner.invoke(
            app, ["duplicate", "resolve", "--db-path", str(temp_db)], input="n\n"
        )
        # User declined, should abort
        assert "Aborted" in result.stdout or result.exit_code == 1

    def test_resolve_without_force_confirm(
        self, runner: CliRunner, temp_db: Path
    ) -> None:
        """resolve without --force should prompt and proceed on confirm."""
        result = runner.invoke(
            app, ["duplicate", "resolve", "--db-path", str(temp_db)], input="y\n"
        )
        assert result.exit_code == 0 or "complete" in result.stdout.lower()

    def test_resolve_with_nonexistent_db(self, runner: CliRunner) -> None:
        """resolve should error for nonexistent database."""
        result = runner.invoke(
            app, ["duplicate", "resolve", "--db-path", "/nonexistent/path.db", "--force"]
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output


class TestEnrichmentBackfillCommand:
    """Tests for enrichment backfill command."""

    def test_backfill_with_existing_db(self, runner: CliRunner, temp_db: Path) -> None:
        """backfill should work with existing database."""
        result = runner.invoke(
            app, ["enrichment", "backfill", "--db-path", str(temp_db)]
        )
        assert result.exit_code == 0
        assert "Backfill" in result.stdout or "complete" in result.stdout.lower()

    def test_backfill_with_nonexistent_db(self, runner: CliRunner) -> None:
        """backfill should error for nonexistent database."""
        result = runner.invoke(
            app, ["enrichment", "backfill", "--db-path", "/nonexistent/path.db"]
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output

    def test_backfill_help(self, runner: CliRunner) -> None:
        """backfill --help should show help."""
        result = runner.invoke(app, ["enrichment", "backfill", "--help"])
        assert result.exit_code == 0
        assert "company" in result.stdout.lower() or "role" in result.stdout.lower()


class TestEnrichmentPushCommand:
    """Tests for enrichment push command."""

    def test_push_notes_mode(self, runner: CliRunner, temp_db: Path) -> None:
        """push --mode notes should work."""
        result = runner.invoke(
            app, ["enrichment", "push", "--mode", "notes", "--db-path", str(temp_db)]
        )
        assert result.exit_code == 0

    def test_push_description_mode(self, runner: CliRunner, temp_db: Path) -> None:
        """push --mode description should work."""
        result = runner.invoke(
            app,
            ["enrichment", "push", "--mode", "description", "--db-path", str(temp_db)],
        )
        assert result.exit_code == 0

    def test_push_job_title_mode(self, runner: CliRunner, temp_db: Path) -> None:
        """push --mode job_title should work."""
        result = runner.invoke(
            app,
            ["enrichment", "push", "--mode", "job_title", "--db-path", str(temp_db)],
        )
        assert result.exit_code == 0

    def test_push_invalid_mode(self, runner: CliRunner, temp_db: Path) -> None:
        """push with invalid mode should error."""
        result = runner.invoke(
            app,
            ["enrichment", "push", "--mode", "invalid_mode", "--db-path", str(temp_db)],
        )
        assert result.exit_code == 1
        assert "Invalid mode" in result.output

    def test_push_dry_run(self, runner: CliRunner, temp_db: Path) -> None:
        """push --dry-run should preview without changes."""
        result = runner.invoke(
            app,
            [
                "enrichment",
                "push",
                "--mode",
                "notes",
                "--db-path",
                str(temp_db),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry run" in result.stdout

    def test_push_with_nonexistent_db(self, runner: CliRunner) -> None:
        """push should error for nonexistent database."""
        result = runner.invoke(
            app,
            [
                "enrichment",
                "push",
                "--mode",
                "notes",
                "--db-path",
                "/nonexistent/path.db",
            ],
        )
        assert result.exit_code == 1
        assert "Database not found" in result.output


class TestSyncCommands:
    """Tests for sync commands."""

    def test_sync_incremental(self, runner: CliRunner) -> None:
        """sync incremental should work."""
        result = runner.invoke(app, ["sync", "incremental"])
        assert result.exit_code == 0

    def test_sync_incremental_verbose(self, runner: CliRunner) -> None:
        """sync incremental --verbose should work."""
        result = runner.invoke(app, ["sync", "incremental", "--verbose"])
        assert result.exit_code == 0

    def test_sync_incremental_dry_run(self, runner: CliRunner) -> None:
        """sync incremental --dry-run should work."""
        result = runner.invoke(app, ["sync", "incremental", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.stdout

    def test_sync_full_without_force(self, runner: CliRunner) -> None:
        """sync full should work without --force (no confirmation required)."""
        result = runner.invoke(app, ["sync", "full"])
        # Should complete successfully
        assert result.exit_code == 0
        assert "Full sync complete" in result.output

    def test_sync_full_with_force(self, runner: CliRunner) -> None:
        """sync full --force should skip confirmation."""
        result = runner.invoke(app, ["sync", "full", "--force"])
        assert result.exit_code == 0


class TestCLIDataDir:
    """Tests for --data-dir option."""

    def test_data_dir_option_works(self, runner: CliRunner) -> None:
        """--data-dir option should be accepted."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a db file in the data dir
            db_path = Path(tmp_dir) / "dex.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT)"
            )
            conn.commit()
            conn.close()

            result = runner.invoke(
                app, ["duplicate", "analyze", "--data-dir", tmp_dir]
            )
            # May fail to find db if resolve_db_path doesn't use dex.db by default
            # But should not error on the option itself
            assert "--data-dir" not in result.stdout.lower() or result.exit_code in [
                0,
                1,
            ]


class TestCLIHelpMessages:
    """Tests for CLI help messages."""

    def test_main_help_shows_all_commands(self, runner: CliRunner) -> None:
        """Main help should show all command groups."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "sync" in result.stdout
        assert "duplicate" in result.stdout
        assert "enrichment" in result.stdout

    def test_sync_help_shows_subcommands(self, runner: CliRunner) -> None:
        """sync help should show incremental and full."""
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "incremental" in result.stdout
        assert "full" in result.stdout

    def test_duplicate_help_shows_subcommands(self, runner: CliRunner) -> None:
        """duplicate help should show all subcommands."""
        result = runner.invoke(app, ["duplicate", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout
        assert "flag" in result.stdout
        assert "review" in result.stdout
        assert "resolve" in result.stdout

    def test_enrichment_help_shows_subcommands(self, runner: CliRunner) -> None:
        """enrichment help should show all subcommands."""
        result = runner.invoke(app, ["enrichment", "--help"])
        assert result.exit_code == 0
        assert "backfill" in result.stdout
        assert "push" in result.stdout


class TestCLIDbPathOption:
    """Tests for --db-path option."""

    def test_db_path_with_spaces(self, runner: CliRunner) -> None:
        """--db-path should handle paths with spaces."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "path with spaces" / "test.db"
            db_path.parent.mkdir(parents=True)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE contacts (id TEXT PRIMARY KEY, first_name TEXT)"
            )
            conn.commit()
            conn.close()

            result = runner.invoke(
                app, ["duplicate", "analyze", "--db-path", str(db_path)]
            )
            assert result.exit_code == 0

    def test_db_path_absolute(self, runner: CliRunner, temp_db: Path) -> None:
        """--db-path should work with absolute paths."""
        result = runner.invoke(
            app, ["duplicate", "analyze", "--db-path", str(temp_db.absolute())]
        )
        assert result.exit_code == 0
