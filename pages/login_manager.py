import time
from typing import Any, List, Optional

from core.base_page import BasePage
from utils.yaml_reader import YamlManager


class LoginPage(BasePage):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            locators_path: str = "data/login_data.yaml",
            config_path: str = "config/config.yaml",
    ):
        super().__init__(driver, logger)
        cfg = YamlManager(self.logger).read(locators_path)
        self.login_url = cfg.get("url")
        self.locators = cfg.get("locators")
        self.username_input = self.locators.get("username_input")
        self.password_input = self.locators.get("password_input")
        self.login_button = self.locators.get("login_button")
        self.form_error = self.locators.get("form_error")
        self.toast_message = self.locators.get("toast_message")
        self.modal_content = self.locators.get("modal_content")
        self.ack_button = self.locators.get("ack_button")

        self._config = YamlManager(self.logger)

        # config.yaml
        self._config_path = config_path
        shared_cfg = self._config.read(self._config_path)
        if shared_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {self._config_path}")

        self.login_username = shared_cfg.get("username")
        self.login_password = shared_cfg.get("password")
        self.cookies = shared_cfg.get("cookies")
        self.cookies_write_time = shared_cfg.get("cookies_write_time")

        if not self.login_username or not self.login_password:
            raise RuntimeError(f"username/password not configured in {config_path}")

    def open_login(self) -> None:
        if not self.login_url:
            raise RuntimeError("login_url is not configured for LoginPage")
        self.open_url(self.login_url)

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
            self.open_login()
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
            self.logger.error(f"filed is {e}")
            self.driver.take_screenshot('登录失败')

    def get_cookies(self, account: str, password: str) -> Optional[list]:
        self.open_login()
        self.accept_webgl_ack()
        self.input_account(account)
        self.input_password(password)
        self.click_login()
        self.driver.wait_for_timeout(1200)
        cookies = self.driver.context.cookies()
        return cookies if cookies else None

    def refresh_cookies(self) -> None:
        """ 刷新cookies """
        now = time.time()
        if self.cookies_write_time is None:
            cookies_write_ts = 0.0
        else:
            time_array = time.strptime(self.cookies_write_time, "%Y-%m-%d %H:%M:%S")
            cookies_write_ts = time.mktime(time_array)

        is_expired = (
                self.cookies is None
                or self.cookies_write_time is None
                or (now - cookies_write_ts) > 24 * 3600
        )
        if not is_expired:
            return
        new_cookies = LoginPage(self.driver, self.logger).get_cookies(
            self.login_username, self.login_password
        )
        self.cookies = new_cookies
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.cookies_write_time = local_time
        self._config.update(self._config_path, {"cookies_write_time": local_time})
        self._config.update(self._config_path, {"cookies": self.cookies})


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
