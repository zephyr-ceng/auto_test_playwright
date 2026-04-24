import os
from pathlib import Path
from typing import Any, Optional


class BasePage:
    """Base page object helpers for Playwright sync API."""

    def __init__(self, driver: Any, logger: Optional[Any] = None):
        self.driver = driver
        self.logger = logger

    def get_locator(self, selector: str):
        if not isinstance(selector, str):
            raise ValueError("selector must be a string for Playwright locator")
        return self.driver.locator(selector)

    def click(self, selector: str) -> bool:
        try:
            self.get_locator(selector).click()
            if self.logger:
                self.logger.info(f"Clicked element: {selector}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click failed for {selector}: {e}")
            return False

    def click_nth(self, selector: str, index: int = 0) -> bool:
        try:
            if index < 0:
                raise ValueError("index must be >= 0")
            self.get_locator(selector).nth(index).click()
            if self.logger:
                self.logger.info(f"Clicked nth element: {selector}[{index}]")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click nth failed for {selector}[{index}]: {e}")
            return False

    def click_by_text(self, selector: str, text: str) -> bool:
        try:
            self.get_locator(selector).filter(has_text=text).first.click()
            if self.logger:
                self.logger.info(f"Clicked by text: {selector}, text={text}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click by text failed for {selector}, text={text}: {e}")
            return False

    def type_text(self, selector: str, text: str, clear_first: bool = True) -> bool:
        try:
            el = self.get_locator(selector)
            if clear_first:
                el.fill("")
            el.fill(text)
            if self.logger:
                self.logger.info(f"Typed text into {selector}: {text}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Type text failed for {selector}: {e}")
            return False

    def send_keys(self, selector: str, keys: str) -> bool:
        try:
            self.get_locator(selector).press(keys)
            if self.logger:
                self.logger.info(f"Sent keys to {selector}: {keys}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Send keys failed for {selector}: {e}")
            return False

    def count_elements(self, selector: str) -> int:
        try:
            count = self.get_locator(selector).count()
            if self.logger:
                self.logger.info(f"Count elements for {selector}: {count}")
            return int(count)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Count elements failed for {selector}: {e}")
            return 0

    def get_alert_text(self, timeout: int = 5000, accept: bool = False) -> Optional[str]:
        try:
            dialog = self.driver.wait_for_event("dialog", timeout=timeout)
            text = dialog.message
            if self.logger:
                self.logger.info(f"Dialog text: {text}")
            if accept:
                try:
                    dialog.accept()
                    if self.logger:
                        self.logger.info("Dialog accepted")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to accept dialog: {e}")
            return text
        except Exception as e:
            if self.logger:
                self.logger.error(f"Get dialog text failed: {e}")
            return None

    def take_screenshot(self, name: str) -> bool:
        """Take a page screenshot and save it under logs/screenshots."""
        try:
            # 参数检查
            if not isinstance(name, str) or not name.strip():
                raise ValueError("name must be a non-empty string")

            # 路径组合
            screenshot_dir = Path(__file__).resolve().parents[1] / "logs" / "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{name}.png")

            # Playwright page.screenshot expects keyword arguments.
            self.driver.screenshot(path=screenshot_path)
            if self.logger:
                self.logger.info(f"Screenshot saved to {screenshot_path}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Take screenshot failed: {e}")
            return False

    def wait_for_time(self, time):
        if time is None:
            raise ValueError("time cannot be None")
        try:
            self.driver.wait_for_timeout(time)
            if self.logger:
                self.logger.info(f"Wait for time: {time}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Wait for time: {e}")

    async def click_async(self, selector: str) -> bool:
        try:
            await self.get_locator(selector).click()
            if self.logger:
                self.logger.info(f"Clicked element: {selector}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click failed for {selector}: {e}")
            return False

    async def click_nth_async(self, selector: str, index: int = 0) -> bool:
        try:
            if index < 0:
                raise ValueError("index must be >= 0")
            await self.get_locator(selector).nth(index).click()
            if self.logger:
                self.logger.info(f"Clicked nth element: {selector}[{index}]")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click nth failed for {selector}[{index}]: {e}")
            return False

    async def click_by_text_async(self, selector: str, text: str) -> bool:
        try:
            await self.get_locator(selector).filter(has_text=text).first.click()
            if self.logger:
                self.logger.info(f"Clicked by text: {selector}, text={text}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click by text failed for {selector}, text={text}: {e}")
            return False

    async def type_text_async(self, selector: str, text: str, clear_first: bool = True) -> bool:
        try:
            el = self.get_locator(selector)
            if clear_first:
                await el.fill("")
            await el.fill(text)
            if self.logger:
                self.logger.info(f"Typed text into {selector}: {text}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Type text failed for {selector}: {e}")
            return False

    async def send_keys_async(self, selector: str, keys: str) -> bool:
        try:
            await self.get_locator(selector).press(keys)
            if self.logger:
                self.logger.info(f"Sent keys to {selector}: {keys}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Send keys failed for {selector}: {e}")
            return False

    async def count_elements_async(self, selector: str) -> int:
        try:
            count = await self.get_locator(selector).count()
            if self.logger:
                self.logger.info(f"Count elements for {selector}: {count}")
            return int(count)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Count elements failed for {selector}: {e}")
            return 0

    async def wait_for_time_async(self, time):
        if time is None:
            raise ValueError("time cannot be None")
        try:
            await self.driver.wait_for_timeout(time)
            if self.logger:
                self.logger.info(f"Wait for time: {time}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Wait for time: {e}")
