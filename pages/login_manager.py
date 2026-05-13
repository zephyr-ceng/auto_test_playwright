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
        self._config = YamlManager(self.logger)

        # config.yaml
        self._config_path = config_path
        shared_cfg = self._config.read(self._config_path)
        if shared_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {self._config_path}")

        self.login_username = shared_cfg.get("username")
        self.login_password = shared_cfg.get("password")
        self.base_url = shared_cfg.get("base_url")  # config中的url
        self.cookies = shared_cfg.get("cookies")
        self.cookies_write_time = shared_cfg.get("cookies_write_time")

        if not self.login_username or not self.login_password or not self.base_url:
            raise RuntimeError(f"username/password/base_url not configured in {config_path}")

        # login_data.yaml
        login_cfg = self._config.read(locators_path)
        self.locators = login_cfg.get("locators")
        self.login_url = self.build_url(self.base_url, login_cfg.get("url"))  # 拼接url

    def _get_locator(self, key: str, required: bool = False):
        selector = self.locators.get(key)
        if required and not selector:
            raise RuntimeError(f"locator `{key}` is not configured for LoginPage")
        return selector

    def open_login(self) -> None:
        if not self.login_url:
            raise RuntimeError("login_url is not configured for LoginPage")
        self.open_url(self.login_url)

    def accept_webgl_ack(self) -> None:
        act_btn = self._get_locator("ack_button")
        if not act_btn:
            return
        ack_locator = self.driver.locator(act_btn)
        if ack_locator.count():
            ack_locator.first.click()
            self.driver.wait_for_timeout(500)

    def input_account(self, account: str) -> bool:
        username_locator = self._get_locator("username_input")
        if not username_locator:
            return False
        return self.type_text(username_locator, account, clear_first=True)

    def input_password(self, password: str) -> bool:
        password_locator = self._get_locator("password_input")
        if not password_locator:
            return False
        return self.type_text(password_locator, password, clear_first=True)

    def _click_login(self) -> bool:
        login_btn = self._get_locator("login_button")
        if not login_btn:
            return False
        return self.click(login_btn)

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
            self._click_login()
            self.driver.wait_for_timeout(1200)

            texts = []
            texts.extend(self._collect_texts(self._get_locator("form_error")))
            texts.extend(self._collect_texts(self._get_locator("toast_message")))
            texts.extend(self._collect_texts(self._get_locator("modal_content")))
            combined = "\n".join(texts).strip()
            return combined or None
        except Exception as e:
            self.logger.error(f"filed is {e}")
            self.driver.take_screenshot('登录失败')

    def get_user_agreement_text(self) -> str:
        self.open_login()
        agreement_text = self._get_locator("agreement_text", required=True)
        agreement_dialog = self._get_locator("agreement_dialog", required=True)
        self.click(agreement_text)
        if not self.wait_for_selector(agreement_dialog):
            return ""
        dialog = self.driver.locator(agreement_dialog)
        if dialog.count() <= 0:
            return ""
        return dialog.first.inner_text().strip()

    def get_cookies(self, account: str, password: str) -> Optional[list]:
        self.open_login()
        self.accept_webgl_ack()
        self.input_account(account)
        self.input_password(password)
        self._click_login()
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
