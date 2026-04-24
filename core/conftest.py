import os
import re
from datetime import datetime
from typing import Any, Optional

import pytest

try:
    import allure
except Exception:  # pragma: no cover
    allure = None


def _safe_name(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", text).strip("_")


def _pick_screenshot_target(item: Any) -> Optional[Any]:
    """ 查找可有截图事件的对象 base_page or playwright page """
    for value in item.funcargs.values():
        if (
            hasattr(value, "take_screenshot")
            or hasattr(value, "screenshot")
        ):
            return value
    return None


def _capture_failure_screenshot(target: Any, screenshot_name: str) -> Optional[str]:
    """ 捕获不同级别的失败路径 """
    screenshot_dir = os.path.join("logs", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"{screenshot_name}.png")

    # 1) Project page objects (BasePage descendants)
    take_screenshot = getattr(target, "take_screenshot", None)
    if callable(take_screenshot):
        try:
            ok = bool(take_screenshot(screenshot_name))
            if ok and os.path.exists(screenshot_path):
                return screenshot_path
        except Exception:
            pass

    # 2) Direct Playwright page object
    screenshot = getattr(target, "screenshot", None)
    if callable(screenshot):
        try:
            screenshot(path=screenshot_path)
            if os.path.exists(screenshot_path):
                return screenshot_path
        except Exception:
            pass
    return None


@pytest.hookimpl(hookwrapper=True) # 允许在测试执行前后都执行代码
def pytest_runtest_makereport(item: Any, call: Any):
    outcome = yield
    report = outcome.get_result()

    # Only capture screenshot when test body fails.
    if report.when != "call" or not report.failed:
        return

    target = _pick_screenshot_target(item)  # 获取截图对象
    if target is None:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")                # 时间
    screenshot_name = f"failed_{_safe_name(item.nodeid)}_{timestamp}"   # 截图文件名
    screenshot_path = _capture_failure_screenshot(target, screenshot_name)  # 捕获截图

    # 附加到allure报告中
    if screenshot_path and allure is not None:
        try:
            allure.attach.file(
                screenshot_path,
                name=f"failure_screenshot_{item.name}",
                attachment_type=allure.attachment_type.PNG,
            )
        except Exception:
            pass
