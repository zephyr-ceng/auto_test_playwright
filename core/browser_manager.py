from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright


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

        self.__playwright = None
        self.__browser = None
        self.__context = None
        self.__page = None

    def __log_and_print(self, message: str, level: str = "info"):
        """统一处理日志记录与终端打印"""
        try:
            print(message)
        except UnicodeEncodeError:
            safe_message = message.encode("gbk", errors="ignore").decode("gbk", errors="ignore")
            print(safe_message)
        if self.logger:
            log_func = getattr(self.logger, level, self.logger.info)
            log_func(message)

    def start(self) -> Any:
        """根据 self.remote_url 是否有值，自动决定走远程连接还是本地启动"""
        try:
            self.__playwright = sync_playwright().start()
            browser_type = getattr(self.__playwright, self.browser_type)

            # --- 根据参数纯净分流 ---
            if self.remote_url:
                self.__log_and_print(f"🚀 [远程模式] 正在连接设备: {self.remote_url}")
                self.__browser = browser_type.connect(self.remote_url)
            else:
                self.__log_and_print(f"🏠 [本地模式] 正在启动浏览器 (headless={self.headless})...")
                opts = dict(headless=self.headless)
                opts.update(self.launch_options)
                self.__browser = browser_type.launch(**opts)
            # ---------------------

            # 创建全局唯一的上下文与初始页面
            self.__context = self.__browser.new_context(viewport={'width': 1920, 'height': 1080})
            self.__page = self.__context.new_page()

            self.__log_and_print(f"✨ 浏览器就绪！模式: {'远程' if self.remote_url else '本地'}")
            return self.__page

        except Exception as e:
            error_msg = f"❌ 浏览器启动失败: {e}"
            self.__log_and_print(error_msg, level="error")
            raise

    def new_page(self) -> Any:
        """打开新页面。如果未启动，内部自动调用 start()"""
        if not self.__context:
            self.start()
        try:
            # 如果是首次调用，start() 内部已建好 self._page，直接返回
            # 如果后续多次调用 new_page()，则在原有的 context 下新建标签页
            if not self.__page or self.__page.is_closed():
                self.__page = self.__context.new_page()
                self.__log_and_print("Created new page")
            return self.__page
        except Exception as e:
            self.__log_and_print(f"Failed to create new page: {e}", "error")
            raise

    def get_page(self) -> Optional[Any]:
        return self.__page

    def close(self) -> None:
        """优雅释放资源链"""
        try:
            if self.__page:
                try:
                    self.__page.close()
                except Exception:
                    pass
            if self.__context:
                try:
                    self.__context.close()
                except Exception:
                    pass
            if self.__browser:
                try:
                    self.__browser.close()
                except Exception:
                    pass
            if self.__playwright:
                try:
                    self.__playwright.stop()
                except Exception:
                    pass
            self.__log_and_print(f"\n🔒 浏览器及 Playwright 实例已安全关闭")
        finally:
            self.__page = None
            self.__context = None
            self.__browser = None
            self.__playwright = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


if __name__ == "__main__":
    bm = BrowserManager(remote_url="ws://192.168.3.120:3000/?browser=chromium")
    page = bm.start()
    page.goto("https://x.finetool.cn/login")
    page.wait_for_timeout(1000)
    print(page.url)
    page.screenshot(path="screenshot.png")
    page.close()
