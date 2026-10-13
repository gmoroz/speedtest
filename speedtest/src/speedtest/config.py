"""Конфигурация приложения. Единственный источник - синглтон `settings`."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from speedtest.const import DEFAULT_DB_PATH


class Settings(BaseSettings):
    """Настройки из окружения/.env; os.environ по коду не читать."""

    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = True
    db_path: Path = DEFAULT_DB_PATH

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        """В production путь БД должен быть задан явно."""
        if not self.debug and self.db_path == DEFAULT_DB_PATH:
            error = "В production (debug=False) db_path должен быть переопределён в .env."
            raise ValueError(error)
        return self


settings = Settings()
