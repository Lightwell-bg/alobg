"""Browser automation module using Playwright."""

import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import Config

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser instance and context for automation."""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = False) -> None:
        """
        Start browser.

        Args:
            headless: If True, browser runs in headless mode. Default is False (visible).
        """
        logger.info(f"Starting browser (headless={headless})...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()
        logger.info("Browser started successfully")

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        logger.info("Closing browser...")
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")

    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: Playwright wait condition (load, domcontentloaded, networkidle)
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        logger.info(f"Navigating to {url}")
        await self.page.goto(url, wait_until=wait_until)
        logger.debug(f"Page loaded: {self.page.url}")

    def get_page(self) -> Page:
        """
        Get the current page instance.

        Returns:
            Current Playwright Page instance
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self.page
