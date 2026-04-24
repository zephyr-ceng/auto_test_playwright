import allure
import pytest

from core.browser_manager import BrowserManager
from pages.login_page import LoginPage
from utils.csv_manager import CSVManager
from utils.logger import Logger


def _prepare_login_test_data() -> list[dict]:
    manager = CSVManager("login_test_data.csv")
    rows = manager.read_csv()
    if rows:
        return rows

    manager.append_row(
        values=[1, False, "demo", "123", "该账号未注册，请联系管理员"],
        fieldnames=["序号", "是否有效", "账号", "密码", "预期结果"],
    )
    data = [
        [2, False, "", "123", "请输入用户名!"],
        [3, False, "demo", "", "请输入密码！"],
        [4, False, "", "", "请输入用户名!;请输入密码!"],
    ]
    for row in data:
        manager.append_row(values=row)

    return manager.read_csv()


@pytest.fixture(scope="class")
def login_page():
    log = Logger("login_test")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    # page = manager.start()
    page = manager.new_page()
    login = LoginPage(page, logger=log)
    yield login
    manager.close()


@allure.feature("Login")
class TestLoginPage:
    @allure.story("有效账号登录测试")
    # @allure.title("Login with invalid credentials should show expected message")
    @pytest.mark.parametrize(
        "case",
        [case for case in _prepare_login_test_data() if case["是否有效"] == "False"],
    )
    def test_login_invalid(self, login_page, case):
        allure.dynamic.title(f"测试用例{case['序号']}--{case['预期结果']}")
        user = case["账号"]
        password = case["密码"]
        message = login_page.login_account(user, password)
        message = (message or "").replace("\r\n", "").replace("\n", "").strip()
        expected = case["预期结果"]
        assert message == expected, f"结果不相符，实际值:{message} 不等于 预期值:{expected}"
