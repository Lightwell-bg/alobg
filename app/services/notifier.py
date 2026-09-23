"""Telegram notification service."""

import logging
from typing import Optional
import requests

from app.config import Config

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Service for sending notifications via Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID for sending messages
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> bool:
        """
        Send a text message to Telegram.

        Args:
            text: Message text to send

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("Message sent to Telegram successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}", exc_info=True)
            return False

    def send_report(self, report_text: str) -> bool:
        """
        Send a report message to Telegram.

        Args:
            report_text: Report text to send

        Returns:
            True if report sent successfully, False otherwise
        """
        return self.send_message(report_text)
