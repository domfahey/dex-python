"""Tests for Settings configuration."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from dex_python import Settings


def test_settings_loads_from_env(monkeypatch) -> None:
    monkeypatch.setenv("DEX_API_KEY", "test-api-key")
    monkeypatch.setenv("DEX_BASE_URL", "https://example.com")

    settings = Settings()

    assert settings.dex_api_key == "test-api-key"
    assert settings.dex_base_url == "https://example.com"


def test_settings_default_base_url(monkeypatch) -> None:
    monkeypatch.setenv("DEX_API_KEY", "test-api-key")
    monkeypatch.delenv("DEX_BASE_URL", raising=False)

    settings = Settings()

    assert settings.dex_base_url == "https://api.getdex.com/api/rest"


class TestSettingsValidation:
    """Test Settings validation and edge cases."""

    def test_missing_api_key_raises_error(self, monkeypatch) -> None:
        """Settings should raise ValidationError when DEX_API_KEY is missing."""
        monkeypatch.delenv("DEX_API_KEY", raising=False)
        monkeypatch.delenv("DEX_BASE_URL", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "dex_api_key" in str(exc_info.value).lower()

    def test_empty_api_key_is_valid(self, monkeypatch) -> None:
        """Empty API key should be accepted (validation happens at API level)."""
        monkeypatch.setenv("DEX_API_KEY", "")

        settings = Settings()
        assert settings.dex_api_key == ""

    def test_whitespace_api_key_preserved(self, monkeypatch) -> None:
        """Whitespace in API key should be preserved."""
        monkeypatch.setenv("DEX_API_KEY", "  key-with-spaces  ")

        settings = Settings()
        assert settings.dex_api_key == "  key-with-spaces  "

    def test_special_characters_in_api_key(self, monkeypatch) -> None:
        """API key with special characters should work."""
        api_key = "key_with-special.chars/and+more==="
        monkeypatch.setenv("DEX_API_KEY", api_key)

        settings = Settings()
        assert settings.dex_api_key == api_key

    def test_direct_initialization(self, monkeypatch) -> None:
        """Settings can be initialized with direct values."""
        monkeypatch.delenv("DEX_API_KEY", raising=False)

        settings = Settings(dex_api_key="direct-key")
        assert settings.dex_api_key == "direct-key"

    def test_direct_overrides_env(self, monkeypatch) -> None:
        """Direct initialization should override environment variables."""
        monkeypatch.setenv("DEX_API_KEY", "env-key")

        settings = Settings(dex_api_key="direct-key")
        assert settings.dex_api_key == "direct-key"

    def test_custom_base_url(self, monkeypatch) -> None:
        """Custom base URL should be accepted."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")
        monkeypatch.setenv("DEX_BASE_URL", "https://custom.api.com/v2")

        settings = Settings()
        assert settings.dex_base_url == "https://custom.api.com/v2"

    def test_base_url_trailing_slash_preserved(self, monkeypatch) -> None:
        """Trailing slash in base URL should be preserved."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")
        monkeypatch.setenv("DEX_BASE_URL", "https://api.example.com/")

        settings = Settings()
        assert settings.dex_base_url == "https://api.example.com/"

    def test_localhost_base_url(self, monkeypatch) -> None:
        """Localhost URL should be accepted for development."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")
        monkeypatch.setenv("DEX_BASE_URL", "http://localhost:8080/api")

        settings = Settings()
        assert settings.dex_base_url == "http://localhost:8080/api"


class TestSettingsFromDotEnv:
    """Test Settings loading from .env file."""

    def test_loads_from_dotenv_file(self, monkeypatch, tmp_path) -> None:
        """Settings should load from .env file in current directory."""
        # Clear environment
        monkeypatch.delenv("DEX_API_KEY", raising=False)
        monkeypatch.delenv("DEX_BASE_URL", raising=False)

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("DEX_API_KEY=dotenv-key\nDEX_BASE_URL=https://dotenv.com")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        settings = Settings()
        assert settings.dex_api_key == "dotenv-key"
        assert settings.dex_base_url == "https://dotenv.com"

    def test_env_vars_override_dotenv(self, monkeypatch, tmp_path) -> None:
        """Environment variables should override .env file."""
        # Set environment variable
        monkeypatch.setenv("DEX_API_KEY", "env-key")

        # Create .env file with different value
        env_file = tmp_path / ".env"
        env_file.write_text("DEX_API_KEY=dotenv-key")

        monkeypatch.chdir(tmp_path)

        settings = Settings()
        assert settings.dex_api_key == "env-key"

    def test_handles_missing_dotenv_gracefully(self, monkeypatch, tmp_path) -> None:
        """Settings should work when .env file doesn't exist."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")
        monkeypatch.chdir(tmp_path)  # Directory without .env

        settings = Settings()
        assert settings.dex_api_key == "test-key"


class TestSettingsImmutability:
    """Test that Settings fields behave as expected."""

    def test_settings_fields_are_accessible(self, monkeypatch) -> None:
        """Settings fields should be accessible as attributes."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")

        settings = Settings()

        assert hasattr(settings, "dex_api_key")
        assert hasattr(settings, "dex_base_url")

    def test_settings_model_dump(self, monkeypatch) -> None:
        """Settings should be serializable with model_dump."""
        monkeypatch.setenv("DEX_API_KEY", "test-key")

        settings = Settings()
        data = settings.model_dump()

        assert "dex_api_key" in data
        assert "dex_base_url" in data
        assert data["dex_api_key"] == "test-key"
