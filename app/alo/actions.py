"""Actions module for interacting with alo.bg website."""

import logging
from typing import List, Dict, Optional, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import Config

logger = logging.getLogger(__name__)


class AloActions:
    """Actions for interacting with alo.bg website."""

    def __init__(self, page: Page):
        """
        Initialize AloActions with a Playwright page.

        Args:
            page: Playwright Page instance
        """
        self.page = page

    async def _handle_cookie_consent(self) -> None:
        """
        Handle cookie consent dialog if present.
        """
        try:
            # Wait a bit for cookie dialog to appear
            await self.page.wait_for_timeout(2000)

            # Common cookie consent selectors
            cookie_selectors = [
                'button:has-text("Приемам")',
                'button:has-text("Accept")',
                'button:has-text("Приемам всички")',
                'button:has-text("Accept All")',
                'button.fc-button',
                '.fc-consent-root button',
                '#cookie-consent-accept',
                'button[id*="accept"]',
                'button[class*="accept"]',
                'button[class*="consent"]'
            ]

            for selector in cookie_selectors:
                try:
                    cookie_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if cookie_button:
                        logger.info(f"Found cookie consent button with selector: {selector}")
                        await cookie_button.click()
                        await self.page.wait_for_timeout(1000)
                        logger.info("Cookie consent dialog closed")
                        return
                except PlaywrightTimeoutError:
                    continue

            # Try to find and close any overlay
            overlay_selectors = [
                '.fc-dialog-overlay',
                '.cookie-consent',
                '#cookie-consent',
                '[class*="consent"]',
                '.fc-consent-root'
            ]

            for selector in overlay_selectors:
                try:
                    overlay = await self.page.query_selector(selector)
                    if overlay:
                        # Try to find close button inside overlay
                        close_button = await overlay.query_selector('button')
                        if close_button:
                            await close_button.click()
                            await self.page.wait_for_timeout(1000)
                            logger.info("Closed cookie consent overlay")
                            return
                except Exception:
                    continue

            # Last resort: try to hide overlay with JavaScript
            try:
                await self.page.evaluate("""
                    () => {
                        const overlays = document.querySelectorAll('.fc-dialog-overlay, .fc-consent-root, [class*="consent"]');
                        overlays.forEach(el => {
                            if (el) {
                                el.style.display = 'none';
                                el.remove();
                            }
                        });
                    }
                """)
                await self.page.wait_for_timeout(500)
                logger.info("Removed cookie consent overlay using JavaScript")
            except Exception as e:
                logger.debug(f"JavaScript overlay removal: {e}")

        except Exception as e:
            logger.debug(f"Cookie consent handling: {e}")

    async def login(self, username: str, password: str) -> bool:
        """
        Login to alo.bg.

        Args:
            username: Login email/username
            password: Login password

        Returns:
            True if login successful, False otherwise
        """
        logger.info("Attempting to login...")

        try:
            # Navigate directly to login page
            logger.info(f"Navigating directly to login page: {Config.ALO_LOGIN_URL}")
            await self.page.goto(Config.ALO_LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)

            # Handle cookie consent dialog first
            await self._handle_cookie_consent()

            # Check if already logged in by looking for user menu or "Мои объявления" link
            try:
                # Try to find "Мои объявления" link - if exists, we're already logged in
                my_ads_link = await self.page.wait_for_selector(
                    'a[href*="user_online_ads"]',
                    timeout=3000
                )
                if my_ads_link:
                    logger.info("Already logged in")
                    return True
            except PlaywrightTimeoutError:
                pass

            # Wait for login form to appear on the login page
            logger.info("Waiting for login form to appear...")
            await self.page.wait_for_timeout(2000)

            # Wait for login form to appear - try to find at least 2 input fields (email + password)
            try:
                # Wait for at least 2 input fields to appear (email + password)
                await self.page.wait_for_function(
                    "() => document.querySelectorAll('input[type=\"text\"], input[type=\"email\"], input[type=\"password\"]').length >= 2",
                    timeout=10000
                )
                await self.page.wait_for_timeout(2000)  # Additional wait for form to fully render
                input_count = await self.page.evaluate("() => document.querySelectorAll('input').length")
                logger.info(f"Login form detected - found {input_count} input fields")
            except PlaywrightTimeoutError:
                logger.warning("Not enough input fields found, checking if form is in modal or iframe...")
                # Check for modal dialogs
                try:
                    modal_selectors = ['.modal', '.dialog', '[role="dialog"]', '.popup', '.overlay']
                    for selector in modal_selectors:
                        modal = await self.page.query_selector(selector)
                        if modal:
                            is_visible = await modal.is_visible()
                            logger.info(f"Found modal/dialog: {selector}, visible: {is_visible}")
                            if is_visible:
                                # Try to find inputs in modal
                                modal_inputs = await modal.query_selector_all('input')
                                logger.info(f"Found {len(modal_inputs)} inputs in modal")
                except Exception as e:
                    logger.debug(f"Error checking modals: {e}")

                # Check for iframes
                try:
                    iframes = await self.page.query_selector_all('iframe')
                    logger.info(f"Found {len(iframes)} iframes on page")
                    for i, iframe in enumerate(iframes):
                        try:
                            iframe_src = await iframe.get_attribute('src') or ''
                            logger.info(f"Iframe {i}: src={iframe_src}")
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug(f"Error checking iframes: {e}")

            # Fill login form - expanded selectors
            email_selectors = [
                'input[type="email"]',
                'input[name*="email"]',
                'input[name*="login"]',
                'input[name*="username"]',
                'input[name*="user"]',
                'input[id*="email"]',
                'input[id*="login"]',
                'input[id*="username"]',
                'input[id*="user"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="имейл" i]',
                'input[placeholder*="login" i]',
                'form input[type="text"]:first-of-type',
                'form input:not([type="password"]):not([type="submit"]):not([type="hidden"])'
            ]

            password_selectors = [
                'input[type="password"]',
                'input[name*="password"]',
                'input[name*="pass"]',
                'input[id*="password"]',
                'input[id*="pass"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="парола" i]',
                'form input[type="password"]',
                'form input:last-of-type[type="password"]',
                'input[type="password"]:last-of-type'
            ]

            email_input = None
            logger.info("Searching for email input field...")
            for selector in email_selectors:
                try:
                    email_input = await self.page.wait_for_selector(selector, timeout=2000)
                    if email_input:
                        logger.info(f"Found email input with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            password_input = None
            logger.info("Searching for password input field...")

            # If email was found but password not found yet, wait a bit more for dynamic loading
            if email_input:
                input_count = await self.page.evaluate("() => document.querySelectorAll('input').length")
                logger.info(f"Email found, current input count: {input_count}")
                if input_count < 2:
                    logger.info("Waiting for password field to appear (dynamic loading)...")
                    await self.page.wait_for_timeout(3000)
                    # Try to trigger any lazy loading by scrolling
                    try:
                        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                        await self.page.wait_for_timeout(1000)
                    except Exception:
                        pass

            for selector in password_selectors:
                try:
                    password_input = await self.page.wait_for_selector(selector, timeout=2000)
                    if password_input:
                        logger.info(f"Found password input with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # If not found with selectors, try JavaScript approach to find selectors
            if not email_input:
                logger.warning("Email input not found with selectors, trying JavaScript to find selector...")
                try:
                    email_selector = await self.page.evaluate("""
                        () => {
                            const inputs = Array.from(document.querySelectorAll('input'));
                            const emailInput = inputs.find(input =>
                                input.type !== 'password' &&
                                input.type !== 'submit' &&
                                input.type !== 'hidden' &&
                                input.type !== 'checkbox' &&
                                input.type !== 'button' &&
                                input.type !== 'radio'
                            );
                            if (emailInput) {
                                // Try to create a unique selector
                                if (emailInput.id) return `#${emailInput.id}`;
                                if (emailInput.name) return `input[name="${emailInput.name}"]`;
                                if (emailInput.className) return `input.${emailInput.className.split(' ')[0]}`;
                                return 'input[type="text"]:first-of-type';
                            }
                            return null;
                        }
                    """)
                    if email_selector:
                        logger.info(f"Found email selector using JavaScript: {email_selector}")
                        email_input = await self.page.query_selector(email_selector)
                except Exception as e:
                    logger.debug(f"JavaScript email search failed: {e}")

            if not password_input:
                logger.warning("Password input not found with selectors, trying JavaScript to find selector...")
                try:
                    password_selector = await self.page.evaluate("""
                        () => {
                            const passwordInput = document.querySelector('input[type="password"]');
                            if (passwordInput) {
                                // Try to create a unique selector
                                if (passwordInput.id) return `#${passwordInput.id}`;
                                if (passwordInput.name) return `input[name="${passwordInput.name}"]`;
                                if (passwordInput.className) return `input.${passwordInput.className.split(' ')[0]}`;
                                return 'input[type="password"]';
                            }
                            return null;
                        }
                    """)
                    if password_selector:
                        logger.info(f"Found password selector using JavaScript: {password_selector}")
                        password_input = await self.page.query_selector(password_selector)
                except Exception as e:
                    logger.debug(f"JavaScript password search failed: {e}")

            if not email_input or not password_input:
                logger.error("Could not find email or password input fields")
                # Log page HTML structure for debugging
                try:
                    logger.info(f"Page URL: {self.page.url}")
                    logger.info(f"Page title: {await self.page.title()}")

                    # Log all input fields found
                    all_inputs = await self.page.query_selector_all('input')
                    logger.info(f"Found {len(all_inputs)} input fields on page")
                    for i, inp in enumerate(all_inputs):
                        try:
                            input_type = await inp.get_attribute('type') or 'text'
                            input_name = await inp.get_attribute('name') or ''
                            input_id = await inp.get_attribute('id') or ''
                            input_class = await inp.get_attribute('class') or ''
                            input_placeholder = await inp.get_attribute('placeholder') or ''
                            is_visible = await inp.is_visible()
                            logger.info(f"Input {i}: type={input_type}, name={input_name}, id={input_id}, class={input_class}, placeholder={input_placeholder}, visible={is_visible}")
                        except Exception as e:
                            logger.debug(f"Error getting input {i} info: {e}")

                    # Try to find form elements
                    forms = await self.page.query_selector_all('form')
                    logger.info(f"Found {len(forms)} forms on page")
                    for i, form in enumerate(forms):
                        try:
                            form_id = await form.get_attribute('id') or ''
                            form_class = await form.get_attribute('class') or ''
                            form_action = await form.get_attribute('action') or ''
                            is_visible = await form.is_visible()
                            logger.info(f"Form {i}: id={form_id}, class={form_class}, action={form_action}, visible={is_visible}")
                        except Exception:
                            pass

                    # Check if form might be in iframe
                    iframes = await self.page.query_selector_all('iframe')
                    logger.info(f"Found {len(iframes)} iframes on page")

                except Exception as e:
                    logger.debug(f"Error logging page info: {e}")

                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="logs/login_form_error.png", full_page=True)
                    logger.info("Screenshot saved to logs/login_form_error.png")
                except Exception:
                    pass
                return False

            await email_input.fill(username)
            await password_input.fill(password)
            await self.page.wait_for_timeout(500)

            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Вход")',
                'button:has-text("Login")',
                'button:has-text("Влез")',
                'form button',
                'form input[type="submit"]',
                'button.btn-primary',
                'button[class*="submit"]'
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if submit_button:
                        logger.info(f"Found submit button with selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not submit_button:
                logger.error("Could not find submit button")
                # Take screenshot for debugging
                try:
                    await self.page.screenshot(path="logs/login_submit_error.png")
                    logger.info("Screenshot saved to logs/login_submit_error.png")
                except Exception:
                    pass
                return False

            # Try to click submit button
            try:
                await submit_button.click(timeout=5000)
            except Exception as e:
                logger.warning(f"Normal submit click failed: {e}, trying force click")
                await submit_button.click(force=True)

            # Use domcontentloaded instead of networkidle to avoid timeout issues
            try:
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning("Page load timeout, continuing anyway...")
            await self.page.wait_for_timeout(1000)
            await self.page.wait_for_timeout(2000)

            # Verify login success - check multiple indicators
            success_indicators = [
                'a[href*="user_online_ads"]',
                'a[href*="user"]:has-text("Мои")',
                '.user-menu',
                '.logout',
                '[class*="user"]'
            ]

            for indicator in success_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=3000)
                    logger.info(f"Login successful - found indicator: {indicator}")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # If no success indicators found, check current URL
            current_url = self.page.url
            logger.info(f"Checking current URL: {current_url}")

            # URLs that indicate successful login (user panel pages)
            success_url_patterns = [
                'user_edit_panel.php',
                'user_online_ads.php',
                'user_',
                '/user/',
                'edit_panel'
            ]

            for pattern in success_url_patterns:
                if pattern.lower() in current_url.lower():
                    logger.info(f"Login successful - URL contains user panel indicator: {pattern}")
                    return True

            # Also check if URL changed from login page (indicates redirect after login)
            if 'login.php' not in current_url.lower() and 'alo.bg' in current_url.lower():
                logger.info("URL changed from login page - likely successful login")
                # Wait a bit more for page to fully load
                await self.page.wait_for_timeout(2000)
                # Check page content for user dashboard elements
                try:
                    page_content = await self.page.content()
                    if any(word in page_content.lower() for word in ['моите обяви', 'мои обяви', 'начален панел', 'изход', 'my ads']):
                        logger.info("Login successful - page contains user dashboard elements")
                        return True
                except Exception:
                    pass

            logger.warning(f"Login verification failed - current URL: {current_url}")

            # Take screenshot for debugging
            try:
                await self.page.screenshot(path="logs/login_verification_failed.png")
                logger.info("Screenshot saved to logs/login_verification_failed.png")
            except Exception:
                pass

            return False

        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            return False

    async def get_active_ads(self) -> List[Dict[str, str]]:
        """
        Get list of active ads from "Мои объявления" page.

        Returns:
            List of dictionaries with ad information (title, url, container element)
        """
        logger.info("Fetching active ads...")

        try:
            await self.page.goto(Config.ALO_MY_ADS_URL, wait_until="domcontentloaded", timeout=30000)

            # Wait for ads to load
            await self.page.wait_for_timeout(3000)

            # Find all ad containers - look for containers that have the bump button
            # Each ad is likely in a container (div, tr, etc.) that contains the button "Направи първа безплатна"
            ads = []

            # Find all buttons with text "Направи първа безплатна"
            # We'll use indices instead of ElementHandle to avoid stale element issues
            try:
                # Find all buttons with text "Направи първа безплатна"
                bump_buttons = await self.page.query_selector_all('button:has-text("Направи първа безплатна"), a:has-text("Направи първа безплатна")')
                logger.info(f"Found {len(bump_buttons)} buttons with 'Направи първа безплатна' text")

                for index, button in enumerate(bump_buttons):
                    try:
                        # Get title from the button's context using JavaScript
                        title = await button.evaluate("""
                            (button) => {
                                let parent = button.closest('div, tr, li, article');
                                // Go up until we find a container that likely contains the ad
                                while (parent && parent.parentElement) {
                                    const text = parent.textContent || '';
                                    // Check if this container has ad-like content
                                    if (text.length > 50 && (
                                        text.includes('обява') ||
                                        text.includes('Активна') ||
                                        text.includes('Преглеждания')
                                    )) {
                                        // Try to find title in this container
                                        const titleEl = parent.querySelector('h1, h2, h3, h4, .title, a[href*="ad"]');
                                        if (titleEl) {
                                            return titleEl.textContent.trim().substring(0, 100);
                                        }
                                        // Extract first meaningful line
                                        const lines = text.split('\\n');
                                        for (const line of lines) {
                                            const trimmed = line.trim();
                                            if (trimmed.length > 10 && trimmed.length < 200) {
                                                return trimmed;
                                            }
                                        }
                                        return parent.textContent.trim().substring(0, 100);
                                    }
                                    parent = parent.parentElement;
                                }
                                return 'Неизвестное объявление';
                            }
                        """)

                        if not title or title == 'Неизвестное объявление':
                            title = f"Объявление {index + 1}"

                        # Store index instead of ElementHandle
                        ads.append({
                            "title": title,
                            "button_index": index
                        })
                    except Exception as e:
                        logger.debug(f"Error processing ad container at index {index}: {e}")
                        # Still add the ad with a generic title
                        ads.append({
                            "title": f"Объявление {index + 1}",
                            "button_index": index
                        })
                        continue

            except Exception as e:
                logger.warning(f"Error finding ads by button: {e}")

            logger.info(f"Found {len(ads)} active ads")
            return ads

        except Exception as e:
            logger.error(f"Error fetching active ads: {e}", exc_info=True)
            return []

    async def bump_ad(self, ad_data: Dict[str, any]) -> Tuple[bool, str]:
        """
        Attempt to bump (raise) an ad by clicking the bump button.

        Args:
            ad_data: Dictionary with ad information, should contain 'button_index' key

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get button index from ad_data
            button_index = ad_data.get('button_index')

            if button_index is None:
                return False, "Индекс кнопки не найден"

            # Find all buttons with text "Направи първа безплатна" and get the one at the specified index
            bump_buttons = await self.page.query_selector_all('button:has-text("Направи първа безплатна"), a:has-text("Направи първа безплатна")')

            if button_index >= len(bump_buttons):
                return False, f"Кнопка с индексом {button_index} не найдена (найдено {len(bump_buttons)} кнопок)"

            bump_button = bump_buttons[button_index]

            # Verify button is still attached and visible
            try:
                is_visible = await bump_button.is_visible()
                if not is_visible:
                    return False, "Кнопка не видна"
            except Exception as e:
                return False, f"Кнопка недоступна: {str(e)}"

            # Scroll button into view if needed
            try:
                await bump_button.scroll_into_view_if_needed()
                await self.page.wait_for_timeout(500)
            except Exception:
                pass

            # Check if button is already disabled before clicking
            try:
                is_enabled = await bump_button.is_enabled()
                if not is_enabled:
                    logger.info("Button is already disabled, ad was likely already updated")
                    return False, "already_updated_today"
            except Exception:
                pass  # Continue if we can't check enabled state

            # Click the button once
            logger.info(f"Clicking bump button 'Направи първа безплатна' (index {button_index})...")
            try:
                await bump_button.click(timeout=5000)
            except Exception as e:
                logger.warning(f"Normal click failed: {e}, trying force click")
                try:
                    await bump_button.click(force=True)
                except Exception as e2:
                    return False, f"Не удалось кликнуть кнопку: {str(e2)}"

            # Wait a bit for page to react
            await self.page.wait_for_timeout(2000)

            # Check if dialog appeared with "already updated" message
            dialog_message = None
            try:
                modal_selectors = [
                    '.modal',
                    '.dialog',
                    '[class*="modal"]',
                    '[class*="dialog"]',
                    '[role="dialog"]'
                ]

                for modal_selector in modal_selectors:
                    try:
                        modal = await self.page.wait_for_selector(modal_selector, timeout=2000)
                        if modal:
                            dialog_text = await modal.inner_text()
                            dialog_message = dialog_text.strip()
                            logger.info(f"Found dialog with message: {dialog_message[:100]}")
                            break
                    except PlaywrightTimeoutError:
                        continue
            except Exception as e:
                logger.debug(f"Could not read dialog message: {e}")

            # If dialog says "already updated today", close it and return
            if dialog_message and ("обновявана или публикувана днес" in dialog_message or
                                  "обновявана днес" in dialog_message or
                                  "публикувана днес" in dialog_message):
                logger.info("Ad was already updated today, closing dialog...")
                # Find and click OK/close button to dismiss the dialog
                close_selectors = [
                    'button:has-text("OK")',
                    'button:has-text("ОК")',
                    '.modal button',
                    '.dialog button',
                    '[class*="modal"] button'
                ]

                for selector in close_selectors:
                    try:
                        close_button = await self.page.wait_for_selector(selector, timeout=2000)
                        if close_button and await close_button.is_visible():
                            await close_button.click(timeout=3000)
                            await self.page.wait_for_timeout(1000)
                            logger.info("Dialog closed")
                            break
                    except (PlaywrightTimeoutError, Exception):
                        continue

                return False, "already_updated_today"

            # Re-find the button to check if it became disabled
            await self.page.wait_for_timeout(1000)  # Give page time to update
            try:
                # Re-find all buttons to get fresh reference
                all_bump_buttons = await self.page.query_selector_all(
                    'button:has-text("Направи първа безплатна"), a:has-text("Направи първа безплатна")'
                )

                if button_index < len(all_bump_buttons):
                    updated_button = all_bump_buttons[button_index]
                    try:
                        is_enabled_after = await updated_button.is_enabled()
                        is_visible_after = await updated_button.is_visible()

                        # If button is disabled or not visible, ad was successfully bumped
                        if not is_enabled_after or not is_visible_after:
                            logger.info("Button became disabled/invisible after click - ad bumped successfully")
                            # If there's a confirmation dialog, close it once
                            try:
                                confirmation_selectors = [
                                    'button:has-text("OK")',
                                    'button:has-text("Да")',
                                    'button:has-text("Потвърди")',
                                    '.modal button:not([disabled])',
                                    '.dialog button:not([disabled])'
                                ]
                                for selector in confirmation_selectors:
                                    try:
                                        conf_button = await self.page.wait_for_selector(selector, timeout=1000)
                                        if conf_button and await conf_button.is_visible():
                                            await conf_button.click(timeout=2000)
                                            await self.page.wait_for_timeout(1000)
                                            logger.info("Closed confirmation dialog")
                                            break
                                    except (PlaywrightTimeoutError, Exception):
                                        continue
                            except Exception:
                                pass  # Ignore errors when closing dialog

                            return True, "Обновлено"
                    except Exception as e:
                        logger.debug(f"Could not check button state after click: {e}")
            except Exception as e:
                logger.debug(f"Could not re-find button after click: {e}")

            # If button is still active, check for confirmation dialog and click OK once
            try:
                confirmation_selectors = [
                    'button:has-text("OK")',
                    'button:has-text("Да")',
                    'button:has-text("Потвърди")',
                    'button:has-text("Направи")',
                    '.modal button:not([disabled])',
                    '.dialog button:not([disabled])'
                ]

                for selector in confirmation_selectors:
                    try:
                        conf_button = await self.page.wait_for_selector(selector, timeout=2000)
                        if conf_button and await conf_button.is_visible():
                            logger.info(f"Found confirmation dialog, clicking OK once...")
                            await conf_button.click(timeout=3000)
                            await self.page.wait_for_timeout(1500)
                            break
                    except (PlaywrightTimeoutError, Exception):
                        continue
            except Exception:
                pass

            # After handling dialog, check button state one more time
            await self.page.wait_for_timeout(1000)
            try:
                all_bump_buttons = await self.page.query_selector_all(
                    'button:has-text("Направи първа безплатна"), a:has-text("Направи първа безплатна")'
                )
                if button_index < len(all_bump_buttons):
                    final_button = all_bump_buttons[button_index]
                    is_enabled_final = await final_button.is_enabled()
                    is_visible_final = await final_button.is_visible()

                    if not is_enabled_final or not is_visible_final:
                        logger.info("Button became disabled after confirmation - ad bumped successfully")
                        return True, "Обновлено"
            except Exception:
                pass

            # If we get here, button might still be active, but we've done our best
            # Move to next ad anyway
            logger.info("Button state unclear, but moving to next ad")
            return True, "Обновлено"

        except PlaywrightTimeoutError:
            return False, "Таймаут при ожидании элементов"
        except Exception as e:
            logger.error(f"Error bumping ad: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}"
