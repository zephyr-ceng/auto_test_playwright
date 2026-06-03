from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright

from pages import remote


class BrowserManager:
    """Playwright 浏览器管理器（同步 API 纯净版）。

    移除了内部配置文件解析，完全依赖外部入参决定执行模式。
    """

    def __init__(
            self,
            browser_type: str = "chromium",
            headless: bool = False,
            logger: Optional[Any] = None,
            launch_options: Optional[Dict[str, Any]] = None,
            remote_url: Optional[str] = None,  # 如果传入此参数，则优先连接远程设备
    ):
        self.browser_type = browser_type
        self.headless = headless
        self.launch_options = launch_options or {}
        self.logger = logger
        self.remote_url = remote_url

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _log_and_print(self, message: str, level: str = "info"):
        """统一处理日志记录与终端打印"""
        print(message)
        if self.logger:
            log_func = getattr(self.logger, level, self.logger.info)
            log_func(message)

    def start(self) -> Any:
        """根据 self.remote_url 是否有值，自动决定走远程连接还是本地启动"""
        try:
            self._playwright = sync_playwright().start()
            browser_type = getattr(self._playwright, self.browser_type)

            # --- 根据参数纯净分流 ---
            if self.remote_url:
                self._log_and_print(f"🚀 [远程模式] 正在连接设备: {self.remote_url}")
                self._browser = browser_type.connect(self.remote_url)
            else:
                self._log_and_print(f"🏠 [本地模式] 正在启动浏览器 (headless={self.headless})...")
                opts = dict(headless=self.headless)
                opts.update(self.launch_options)
                self._browser = browser_type.launch(**opts)
            # ---------------------

            # 创建全局唯一的上下文与初始页面
            self._context = self._browser.new_context(viewport={'width': 1920, 'height': 1080})
            self._page = self._context.new_page()

            self._log_and_print(f"✨ 浏览器就绪！模式: {'远程' if self.remote_url else '本地'}")
            return self._page

        except Exception as e:
            error_msg = f"❌ 浏览器启动失败: {e}"
            self._log_and_print(error_msg, level="error")
            raise

    def new_page(self) -> Any:
        """打开新页面。如果未启动，内部自动调用 start()"""
        if not self._context:
            self.start()
        try:
            # 如果是首次调用，start() 内部已建好 self._page，直接返回
            # 如果后续多次调用 new_page()，则在原有的 context 下新建标签页
            if not self._page or self._page.is_closed():
                self._page = self._context.new_page()
                self._log_and_print("Created new page")
            return self._page
        except Exception as e:
            self._log_and_print(f"Failed to create new page: {e}", "error")
            raise

    def get_page(self) -> Optional[Any]:
        return self._page

    def close(self) -> None:
        """优雅释放资源链"""
        try:
            if self._page:
                try:
                    self._page.close()
                except Exception:
                    pass
            if self._context:
                try:
                    self._context.close()
                except Exception:
                    pass
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
            self._log_and_print(f"\n🔒 浏览器及 Playwright 实例已安全关闭")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


if __name__ == "__main__":
    bm = BrowserManager(remote_url="ws://192.168.58.128:3000/?browser=chromium")
    page = bm.start()
    page.goto("https://x.finetool.cn/login")
    page.wait_for_timeout(1000)
    print(page.url)
    page.screenshot(path="screenshot.png")
    page.close()
