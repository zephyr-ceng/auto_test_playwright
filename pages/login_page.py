from typing import Any, List, Optional

from core.base_page import BasePage
from utils.yaml_reader import YamlManager


class LoginPage(BasePage):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            login_url: Optional[str] = None,
            locators_path: str = "data/login_data.yaml",
    ):
        super().__init__(driver, logger)
        cfg = YamlManager(self.logger).read(locators_path)
        self.login_url = login_url or cfg.get("url")
        self.locators = cfg.get("locators")
        self.username_input = self.locators.get("username_input")
        self.password_input = self.locators.get("password_input")
        self.login_button = self.locators.get("login_button")
        self.form_error = self.locators.get("form_error")
        self.toast_message = self.locators.get("toast_message")
        self.modal_content = self.locators.get("modal_content")
        self.ack_button = self.locators.get("ack_button")

    def open_login_page(self) -> None:
        if not self.login_url:
            raise RuntimeError("login_url is not configured for LoginPage")
        self.driver.goto(self.login_url)
        self.driver.wait_for_load_state("networkidle")

    def accept_webgl_ack(self) -> None:
        if not self.ack_button:
            return
        ack_locator = self.driver.locator(self.ack_button)
        if ack_locator.count():
            ack_locator.first.click()
            self.driver.wait_for_timeout(500)

    def input_account(self, account: str) -> bool:
        if not self.username_input:
            return False
        return self.type_text(self.username_input, account, clear_first=True)

    def input_password(self, password: str) -> bool:
        if not self.password_input:
            return False
        return self.type_text(self.password_input, password, clear_first=True)

    def click_login(self) -> bool:
        if not self.login_button:
            return False
        return self.click(self.login_button)

    def _collect_texts(self, selector: Optional[str]) -> List[str]:
        if not selector:
            return []
        locator = self.driver.locator(selector)
        try:
            texts = locator.all_inner_texts()
            return [text.strip() for text in texts if text and text.strip()]
        except Exception:
            return []

    def login_account(self, account: str, password: str) -> Optional[str]:
        try:
            self.open_login_page()
            self.accept_webgl_ack()
            self.input_account(account)
            self.input_password(password)
            self.click_login()
            self.driver.wait_for_timeout(1200)

            texts = []
            texts.extend(self._collect_texts(self.form_error))
            texts.extend(self._collect_texts(self.toast_message))
            texts.extend(self._collect_texts(self.modal_content))
            combined = "\n".join(texts).strip()
            return combined or None
        except Exception as e:
            self.driver.take_screenshot('登录失败')

    def get_cookies(self, account: str, password: str) -> Optional[list]:
        self.open_login_page()
        self.accept_webgl_ack()
        self.input_account(account)
        self.input_password(password)
        self.click_login()
        self.driver.wait_for_timeout(1200)
        cookies = self.driver.context.cookies()
        return cookies if cookies else None


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("login_test")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        login = LoginPage(page, logger=log)
        print(login.get_cookies("admin", "fyton@202602"))
    finally:
        manager.close()
