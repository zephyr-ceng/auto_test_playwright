from pathlib import Path
from typing import Optional, Any
from core.base_page import BasePage
from utils.yaml_reader import YamlManager


class BaiduPage(BasePage):
    """Baidu 页面对象，使用 Playwright 定位（selector 字符串）。

    定位从 data/baidu_page.yaml 加载。
    """

    def __init__(self, driver, logger: Optional[Any] = None, yaml_path: Optional[str] = None):
        super().__init__(driver, logger=logger)
        self.logger = logger
        self.yaml_path = yaml_path or "data/baidu_page.yaml"
        self._load_locators()

    def _load_locators(self):
        cfg = YamlManager(self.logger).read(self.yaml_path)
        if not cfg:
            raise RuntimeError(f"Failed to load locators from {self.yaml_path}")
        self.search_input = cfg.get("search_input")
        self.search_button = cfg.get("search_button")
        self.result_items = cfg.get("result_items")

    def search_text(self, text: str) -> int:
        """执行搜索并返回搜索结果数量。

        - text: 搜索关键字字符串
        """
        self.driver.goto("https://www.baidu.com")

        if not self.search_input:
            raise RuntimeError("search_input locator not configured")

        # 输入文本
        if not self.type_text(self.search_input, text):
            # 记录并继续尝试按键提交
            if self.logger:
                self.logger.warning("typing may have failed, trying to press Enter")

        # 触发搜索（使用页面级回车）
        self.driver.keyboard.press("Enter")
        # 等待结果出现（Playwright 的 locator.wait_for）
        try:
            if self.result_items:
                self.driver.locator(self.result_items).first.wait_for(timeout=5000)
                self.take_screenshot('百度搜索截图')
                count = self.driver.locator(self.result_items).count()
            else:
                # fallback: try to count results by generic selector
                count = self.driver.locator("#content_left .result").count()

            if self.logger:
                self.logger.info(f"Search for '{text}' returned {count} results")

            return count
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get search results: {e}")
            return 0


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("login_test")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        baidu_page = BaiduPage(page, logger=log)
        res = baidu_page.search_text("selenium")
        print(res)
    finally:
        manager.close()
