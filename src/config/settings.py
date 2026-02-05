import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Verification
    SMTP_TIMEOUT: int = 10
    DNS_TIMEOUT: int = 5
    
    # Scraping
    PROXY_URL: str | None = None
    PROXIES: list[str] = [] # List of proxy URLs

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
