import os
# from os import name
from pathlib import Path
from functools import wraps
from typing import Any, Optional
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import Error as PlaywrightError


def _handle_role_action(action_name: str):
    """Role 操作统一异常处理装饰器。"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"{action_name} failed: {e}")
                return False

        return wrapper

    return decorator


class BasePage:
    """Base page object helpers for Playwright sync API."""

    def __init__(self, driver: Any, logger: Optional[Any] = None):
        """初始化页面对象，注入 Playwright page 与日志器。"""
        self.driver = driver
        self.logger = logger

    def open_url(self, url):
        self.driver.goto(url)
        self.driver.wait_for_load_state("networkidle")
        if self.logger:
            self.logger.info(f"Opened url: {url}")

    def add_cookies(self, cookies: dict):
        if not cookies:
            raise ValueError("cookies is empty")
        self.driver.context.add_cookies(cookies)

    """*************************************************** CSS定位 *************************************************************************** """

    def get_locator(self, selector: str):
        """通过 CSS/XPath 选择器获取 Locator。"""
        if not isinstance(selector, str):
            raise ValueError("selector must be a string for Playwright locator")
        return self.driver.locator(selector)

    def click(self, selector: str) -> bool:
        """点击匹配 selector 的元素。"""
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
        """点击匹配 selector 的第 index 个元素。"""
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
        """在 selector 结果中按文本过滤后点击首个元素。"""
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
        """向 selector 对应输入框填写文本。"""
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
        """向 selector 对应元素发送键盘按键。"""
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
        """统计 selector 匹配到的元素数量。"""
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
        """等待浏览器弹窗并返回文本，可选自动点击确认。"""
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
        """按毫秒等待固定时长。"""
        if time is None:
            raise ValueError("time cannot be None")
        try:
            self.driver.wait_for_timeout(time)
            if self.logger:
                self.logger.info(f"Wait for time: {time}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Wait for time: {e}")

    """*************************************************** Role定位方式 *************************************************************************** """

    def _get_locator_single_role(self, role_ele: str):
        return self.driver.get_by_role(role_ele)

    def _get_locator_multi_role(self, role_ele, role_name):
        return self.driver.get_by_role(role_ele, role_name)

    @_handle_role_action("Click role")
    def click_role(self, role_ele: str, role_name: str) -> bool:
        self._get_locator_single_role(role_ele).click()
        if self.logger:
            self.logger.info(f"Click role: {role_ele}")
        return True

    @_handle_role_action("Type text role")
    def type_text_role(self, role_ele: str, text: str) -> bool:
        self._get_locator_single_role(role_ele).fill(text)
        if self.logger:
            self.logger.info(f"Type text role: {role_ele}")
        return True

    """*************************************************** 异步方法 *************************************************************************** """

    async def click_async(self, selector: str) -> bool:
        """异步点击匹配 selector 的元素。"""
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
        """异步点击匹配 selector 的第 index 个元素。"""
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
        """异步在 selector 结果中按文本过滤后点击首个元素。"""
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
        """异步向 selector 对应输入框填写文本。"""
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
        """异步向 selector 对应元素发送键盘按键。"""
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
        """异步统计 selector 匹配到的元素数量。"""
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
        """异步按毫秒等待固定时长。"""
        if time is None:
            raise ValueError("time cannot be None")
        try:
            await self.driver.wait_for_timeout(time)
            if self.logger:
                self.logger.info(f"Wait for time: {time}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Wait for time: {e}")
