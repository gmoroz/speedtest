"""Конфигурация приложения из окружения и файла `.env`."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from speedtest.const import DEFAULT_REQUEST_COUNT, DEFAULT_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS


class Settings(BaseSettings):
    """Настройки из окружения и файлов `.env`."""

    model_config = SettingsConfigDict(
        env_prefix="SPEEDTEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    request_count: int = Field(default=DEFAULT_REQUEST_COUNT, ge=1)
    timeout_seconds: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS,
        gt=0,
        le=MAX_TIMEOUT_SECONDS,
        allow_inf_nan=False,
    )
