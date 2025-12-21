"""Configuration management for Dex API client.

This module provides the Settings class for loading configuration from
environment variables or .env files using pydantic-settings.

Example:
    >>> from dex_python import Settings
    >>> settings = Settings()  # Loads from environment
    >>> print(settings.dex_base_url)
    'https://api.getdex.com/api/rest'
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Settings are loaded in the following priority order:
    1. Environment variables (e.g., DEX_API_KEY)
    2. .env file in the current directory
    3. Default values

    Attributes:
        dex_api_key: Dex API key for authentication. Required.
        dex_base_url: Base URL for the Dex API. Defaults to production API.

    Example:
        >>> settings = Settings(dex_api_key="your-key")
        >>> settings.dex_base_url
        'https://api.getdex.com/api/rest'
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    dex_api_key: str
    dex_base_url: str = "https://api.getdex.com/api/rest"
