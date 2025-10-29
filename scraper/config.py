from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[1]/".env"), env_prefix="HW_", env_file_encoding="utf-8")
    username: str | None = None
    password: SecretStr | None = None
    base_url: str | None = None
    db_path: str = str(Path(__file__).resolve().parents[1]/"data"/"homework.db")
    anthropic_api_key: SecretStr | None = None

settings = Settings()
