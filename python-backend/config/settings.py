from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv
import os


class Settings(BaseSettings):
    # URL to the school/homework system
    school_base_url: Optional[str] = Field(None, env="SCHOOL_BASE_URL")
    login_path: Optional[str] = Field(None, env="SCHOOL_LOGIN_PATH")

    # Selectors for login flow (site-specific)
    username_selector: Optional[str] = Field(None, env="SCHOOL_USERNAME_SELECTOR")
    password_selector: Optional[str] = Field(None, env="SCHOOL_PASSWORD_SELECTOR")
    submit_selector: Optional[str] = Field(None, env="SCHOOL_SUBMIT_SELECTOR")

    username: Optional[str] = Field(None, env="SCHOOL_USERNAME")
    password: Optional[str] = Field(None, env="SCHOOL_PASSWORD")

    # Playwright/Browser options
    headless: bool = Field(True, env="SCRAPER_HEADLESS")

    # Paths
    data_dir: Path = Field(default=Path(__file__).resolve().parents[1] / "data")

    class Config:
        # pydantic will still read os.environ, we use dotenv to populate it first
        env_file = ".env"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return a singleton Settings instance. Load .env or fallback to .env.example if present."""
    global _settings
    if _settings is None:
        base = Path(__file__).resolve().parents[1]
        env_file = base / ".env"
        example_file = base / ".env.example"

        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        elif example_file.exists():
            load_dotenv(dotenv_path=example_file)

        _settings = Settings()
        # ensure data dir exists
        _settings.data_dir.mkdir(parents=True, exist_ok=True)
    return _settings
