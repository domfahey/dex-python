"""Tests for Settings configuration."""

from dex_python import Settings


def test_settings_loads_from_env(monkeypatch) -> None:
    monkeypatch.setenv("DEX_API_KEY", "test-api-key")
    monkeypatch.setenv("DEX_BASE_URL", "https://example.com")

    settings = Settings()

    assert settings.dex_api_key.get_secret_value() == "test-api-key"
    assert settings.dex_base_url == "https://example.com"
    assert "test-api-key" not in repr(settings)


def test_settings_default_base_url(monkeypatch) -> None:
    monkeypatch.setenv("DEX_API_KEY", "test-api-key")
    monkeypatch.delenv("DEX_BASE_URL", raising=False)

    settings = Settings()

    assert settings.dex_base_url == "https://api.getdex.com/api/rest"
