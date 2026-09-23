"""Configuration module for loading environment variables."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Alo.bg credentials
    ALO_LOGIN: Optional[str] = os.getenv("ALO_LOGIN")
    ALO_PASSWORD: Optional[str] = os.getenv("ALO_PASSWORD")

    # Telegram bot configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

    # URLs
    ALO_BASE_URL: str = "https://www.alo.bg"
    ALO_LOGIN_URL: str = "https://www.alo.bg/login.php"
    ALO_MY_ADS_URL: str = "https://www.alo.bg/user_online_ads.php?ads_status=active"

    # Browser settings
    BROWSER_HEADLESS: bool = os.getenv("BROWSER_HEADLESS", "true").lower() in ("true", "1", "yes")

    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration values are set."""
        missing = []

        if not cls.ALO_LOGIN:
            missing.append("ALO_LOGIN")
        if not cls.ALO_PASSWORD:
            missing.append("ALO_PASSWORD")
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please check your .env file."
            )
