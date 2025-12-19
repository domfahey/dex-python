"""Configuration management for Dex API."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    dex_api_key: str
    dex_base_url: str = "https://api.getdex.com/api/rest"
