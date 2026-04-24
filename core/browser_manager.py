from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright


class BrowserManager:
    """Playwright 浏览器管理器（同步 API）。

    用法示例：
        bm = BrowserManager(browser_type='chromium', headless=True, logger=log)
        bm.start()
        page = bm.new_page()
        page.goto('https://example.com')
        bm.close()

    设计要点：
    - 延迟导入 Playwright（在 start 时导入），以避免在不安装 Playwright 的环境中导入时出错；
    - 提供 start/stop（close）方法管理 playwright/browsers/context/page 生命周期；
    - 支持通过 launch_options 传入 Playwright 的浏览器启动参数，如 args、proxy 等；
    - 日志通过可选的 logger 参数记录操作和异常。
    """

    def __init__(
            self,
            browser_type: str = "chromium",
            headless: bool = True,
            logger: Optional[Any] = None,
            launch_options: Optional[Dict[str, Any]] = None,
            remote_url: Optional[str] = None,  # 远程连接
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

    def start(self) -> Any:
        """启动 Playwright、浏览器和默认 context/page。返回 page 对象。"""
        try:
            self._playwright = sync_playwright().start()
            browser_type = getattr(self._playwright, self.browser_type)
            if self.remote_url:
                if self.logger:
                    self.logger.info(f"Connecting to remote browser: {self.remote_url}")
                self._browser = browser_type.connect(self.remote_url)
            else:
                opts = dict(headless=self.headless)
                opts.update(self.launch_options)
                self._browser = browser_type.launch(**opts)
            # 启动浏览器
            self._context = self._browser.new_context(viewport={'width': 1920, 'height': 1080})
            self._page = self._context.new_page()
            if self.logger:
                self.logger.info(f"Started {self.browser_type} browser (headless={self.headless})")
            return self._page
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start browser: {e}")
            raise

    def new_page(self) -> Any:
        """在当前 context 中打开一个新页面并返回它。若未启动浏览器，会先调用 start()。"""
        if not self._context:
            self.start()
        try:
            self._page = self._context.new_page()
            if self.logger:
                self.logger.info("Created new page")
            return self._page
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create new page: {e}")
            raise

    def get_page(self) -> Optional[Any]:
        """返回当前 page（可能为 None）。"""
        return self._page

    def close(self) -> None:
        """关闭 page/context/browser 并停止 Playwright。"""
        # 依次关闭，忽略单步失败但记录日志
        try:
            if self._page:
                try:
                    self._page.close()
                    if self.logger:
                        self.logger.info("Closed page")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing page: {e}")
            if self._context:
                try:
                    self._context.close()
                    if self.logger:
                        self.logger.info("Closed context")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing context: {e}")
            if self._browser:
                try:
                    self._browser.close()
                    if self.logger:
                        self.logger.info("Closed browser")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing browser: {e}")
            if self._playwright:
                try:
                    self._playwright.stop()
                    if self.logger:
                        self.logger.info("Stopped Playwright")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error stopping Playwright: {e}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    # 支持上下文管理协议
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class AsyncBrowserManager:
    """Playwright 浏览器管理器（异步 API）。

    用法示例：
        bm = AsyncBrowserManager(browser_type='chromium', headless=True, logger=log)
        async with bm as manager:
            page = await manager.get_page()
            await page.goto('https://example.com')

    设计要点：
    - 延迟导入 Playwright（在 start 时导入），以避免在不安装 Playwright 的环境中导入时出错；
    - 提供 start/close 方法管理 playwright/browsers/context/page 生命周期；
    - 支持通过 launch_options 传入 Playwright 的浏览器启动参数，如 args、proxy 等；
    - 日志通过可选的 logger 参数记录操作和异常。
    """

    def __init__(
            self,
            browser_type: str = "chromium",
            headless: bool = True,
            logger: Optional[Any] = None,
            remote_url: Optional[str] = None,  # 远程和本地访问控制
            launch_options: Optional[Dict[str, Any]] = None,

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

    async def start(self) -> Any:
        """启动 Playwright、浏览器和默认 context/page。返回 page 对象。"""
        try:
            # 延迟导入异步 API
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            browser_type = getattr(self._playwright, self.browser_type)
            if self.remote_url:
                if self.logger:
                    self.logger.info(f"Connecting to remote browser: {self.remote_url}")
                self._browser = await browser_type.connect(self.remote_url)
            else:
                opts = dict(headless=self.headless)
                opts.update(self.launch_options)
                self._browser = await browser_type.launch(**opts)
            self._context = await self._browser.new_context(viewport={'width': 1920, 'height': 1080})
            self._page = await self._context.new_page()
            if self.logger:
                self.logger.info(f"Started {self.browser_type} browser (headless={self.headless})")
            return self._page
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start async browser: {e}")
            raise

    async def new_page(self) -> Any:
        """在当前 context 中打开一个新页面并返回它。若未启动浏览器，会先调用 start()。"""
        if not self._context:
            await self.start()
        try:
            self._page = await self._context.new_page()
            if self.logger:
                self.logger.info("Created new async page")
            return self._page
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create new async page: {e}")
            raise

    def get_page(self) -> Optional[Any]:
        """返回当前 page（可能为 None）。"""
        return self._page

    async def close(self) -> None:
        """关闭 page/context/browser 并停止 Playwright（异步）。"""
        # 依次关闭，忽略单步失败但记录日志
        try:
            if self._page:
                try:
                    await self._page.close()
                    if self.logger:
                        self.logger.info("Closed async page")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing async page: {e}")
            if self._context:
                try:
                    await self._context.close()
                    if self.logger:
                        self.logger.info("Closed async context")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing async context: {e}")
            if self._browser:
                try:
                    await self._browser.close()
                    if self.logger:
                        self.logger.info("Closed async browser")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error closing async browser: {e}")
            if self._playwright:
                try:
                    await self._playwright.stop()
                    if self.logger:
                        self.logger.info("Stopped async Playwright")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error stopping async Playwright: {e}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    # 支持异步上下文管理协议
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
