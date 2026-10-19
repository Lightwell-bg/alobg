"""Main entry point for the alo.bg auto-bump script."""

import asyncio
import sys
import logging

from app.config import Config
from app.logging_config import setup_logging
from app.services.runner import AdBumpRunner
from app.utils.time_utils import get_sofia_time

logger = logging.getLogger(__name__)


async def main():
    """Main async function."""
    try:
        # Validate configuration
        Config.validate()

        # Create and run the ad bump runner
        runner = AdBumpRunner()
        start_time = get_sofia_time()
        try:
            # On timeout the runner's finally block closes the browser
            await asyncio.wait_for(runner.run(), timeout=Config.MAX_RUN_MINUTES * 60)
        except asyncio.TimeoutError:
            error_msg = f"Превышен лимит времени выполнения ({Config.MAX_RUN_MINUTES} мин), скрипт остановлен"
            logger.error(error_msg)
            runner._send_error_report(start_time, error_msg)
            sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Setup logging
    setup_logging(log_level="INFO")

    # Run the main async function
    asyncio.run(main())
