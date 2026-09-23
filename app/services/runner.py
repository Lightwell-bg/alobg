"""Main runner service that orchestrates the ad bumping process."""

import logging
from typing import List, Dict, Optional
from playwright.async_api import Page
from app.alo.browser import BrowserManager
from app.alo.actions import AloActions
from app.services.notifier import TelegramNotifier
from app.utils.time_utils import get_sofia_time, format_datetime
from app.config import Config

logger = logging.getLogger(__name__)


class AdBumpRunner:
    """Main runner for ad bumping automation."""

    def __init__(self):
        """Initialize the runner."""
        self.browser_manager = BrowserManager()
        self.page: Optional[Page] = None
        self.alo_actions: Optional[AloActions] = None
        self.notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
        self.results: List[Dict[str, str]] = []

    async def run(self) -> None:
        """Execute the main ad bumping process."""
        start_time = get_sofia_time()
        logger.info(f"Starting ad bumping process at {format_datetime(start_time)}")

        try:
            # Start browser (headless mode from config)
            await self.browser_manager.start(headless=Config.BROWSER_HEADLESS)
            self.page = self.browser_manager.get_page()
            self.alo_actions = AloActions(self.page)

            # Login
            login_success = await self.alo_actions.login(
                Config.ALO_LOGIN,
                Config.ALO_PASSWORD
            )

            if not login_success:
                error_msg = "Не удалось выполнить вход на сайт"
                logger.error(error_msg)
                self._send_error_report(start_time, error_msg)
                return

            # Get active ads
            ads = await self.alo_actions.get_active_ads()

            if not ads:
                logger.warning("No active ads found")
                self._send_report(start_time, 0, 0, 0, [])
                return

            logger.info(f"Found {len(ads)} active ads to process")

            # Process each ad
            processed_count = 0
            bumped_count = 0
            skipped_count = 0
            already_updated_count = 0

            # Process ads one by one, reloading the list after each successful bump
            while ads:
                processed_count += 1
                ad = ads[0]  # Always process the first ad
                title = ad.get("title", "Неизвестное объявление")

                logger.info(f"Processing ad {processed_count}: {title}")

                if ad.get("button_index") is None:
                    self.results.append({
                        "title": title,
                        "status": "Ошибка: индекс кнопки не найден"
                    })
                    skipped_count += 1
                    ads.pop(0)  # Remove processed ad
                    continue

                # Try to bump the ad
                success, message = await self.alo_actions.bump_ad(ad)

                if success:
                    bumped_count += 1
                    self.results.append({
                        "title": title,
                        "status": "Обновлено"
                    })
                    logger.info(f"Successfully bumped ad: {title}")

                    # After successful bump, reload the page and get fresh list of ads
                    # This ensures we don't use stale elements
                    logger.info("Reloading page to get fresh list of ads...")
                    await self.page.wait_for_timeout(2000)  # Wait for page to update
                    ads = await self.alo_actions.get_active_ads()
                    logger.info(f"Found {len(ads)} remaining ads after reload")
                elif message == "already_updated_today":
                    # Ad was already updated today, just skip it
                    already_updated_count += 1
                    self.results.append({
                        "title": title,
                        "status": "Уже обновлено сегодня"
                    })
                    logger.info(f"Ad '{title}' was already updated today, skipping")
                    ads.pop(0)  # Remove processed ad, no need to reload
                else:
                    skipped_count += 1
                    self.results.append({
                        "title": title,
                        "status": f"Пропущено: {message}"
                    })
                    logger.warning(f"Failed to bump ad '{title}': {message}")
                    ads.pop(0)  # Remove failed ad from list

                # Small delay between ads
                await self.page.wait_for_timeout(1000)

            # Check if all ads were already updated today
            if processed_count > 0 and bumped_count == 0 and already_updated_count == processed_count:
                logger.info("All ads were already updated today")
                self._send_already_updated_report(start_time, processed_count)
                return

            # Send report
            self._send_report(start_time, processed_count, bumped_count, skipped_count, self.results, already_updated_count)

        except Exception as e:
            logger.error(f"Error during ad bumping process: {e}", exc_info=True)
            self._send_error_report(start_time, str(e))
        finally:
            # Close browser
            await self.browser_manager.close()
            logger.info("Ad bumping process completed")

    def _send_report(
        self,
        start_time,
        processed_count: int,
        bumped_count: int,
        skipped_count: int,
        results: List[Dict[str, str]],
        already_updated_count: int = 0
    ) -> None:
        """
        Generate and send report to Telegram.

        Args:
            start_time: Start time of the process
            processed_count: Number of ads processed
            bumped_count: Number of ads successfully bumped
            skipped_count: Number of ads skipped
            results: List of results for each ad
            already_updated_count: Number of ads already updated today
        """
        end_time = get_sofia_time()

        report_lines = [
            "<b>📊 Отчёт о поднятии объявлений</b>",
            "",
            f"<b>Дата и время:</b> {format_datetime(start_time)}",
            f"<b>Обработано объявлений:</b> {processed_count}",
            f"<b>Успешно поднято:</b> {bumped_count}",
        ]

        if already_updated_count > 0:
            report_lines.append(f"<b>Уже обновлено сегодня:</b> {already_updated_count}")

        report_lines.extend([
            f"<b>Пропущено:</b> {skipped_count}",
            ""
        ])

        if results:
            report_lines.append("<b>Детали по объявлениям:</b>")
            for i, result in enumerate(results, 1):
                title = result.get("title", "Неизвестное")
                status = result.get("status", "Неизвестный статус")

                # Determine emoji based on status
                if "Обновлено" in status:
                    emoji = "✅"
                elif "Уже обновлено" in status:
                    emoji = "ℹ️"
                elif "Пропущено" in status:
                    emoji = "⏭️"
                else:
                    emoji = "❌"

                report_lines.append(f"{emoji} {i}. {title}")
                report_lines.append(f"   Статус: {status}")
                report_lines.append("")

        report_text = "\n".join(report_lines)

        # Telegram has a 4096 character limit, truncate if necessary
        if len(report_text) > 4000:
            report_text = report_text[:3900] + "\n\n... (отчёт обрезан)"

        self.notifier.send_report(report_text)

    def _send_already_updated_report(self, start_time, count: int) -> None:
        """
        Send report when all ads were already updated today.

        Args:
            start_time: Start time of the process
            count: Number of ads checked
        """
        report_lines = [
            "<b>ℹ️ Все объявления уже обновлены</b>",
            "",
            f"<b>Дата и время:</b> {format_datetime(start_time)}",
            f"<b>Проверено объявлений:</b> {count}",
            "",
            "Все объявления уже были обновлены или опубликованы сегодня.",
            "Действия не требуются."
        ]

        report_text = "\n".join(report_lines)
        self.notifier.send_report(report_text)

    def _send_error_report(self, start_time, error_message: str) -> None:
        """
        Send error report to Telegram.

        Args:
            start_time: Start time of the process
            error_message: Error message
        """
        report_lines = [
            "<b>❌ Ошибка при выполнении скрипта</b>",
            "",
            f"<b>Дата и время:</b> {format_datetime(start_time)}",
            f"<b>Ошибка:</b> {error_message}",
        ]

        report_text = "\n".join(report_lines)
        self.notifier.send_report(report_text)
