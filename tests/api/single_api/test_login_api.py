import pytest

from api.common.assertions import assert_business_code, assert_response_json, assert_status_code_2xx
from api.login_verification.login import Login, get_scope_value


@pytest.fixture(scope="function")
def login_api(base_url):
    """创建登录接口对象；每条用例独立持有 HTTP 会话。"""
    return Login(base_url)


class TestLoginAPI:
    """登录接口单接口测试。"""

    @pytest.mark.api
    def test_login_fail_with_wrong_password(self, login_api, api_env) -> None:
        """测试密码错误登录失败。"""
        username = api_env.require("username")
        response = login_api.login_by_username(username, "wrong_pwd")
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert response_body.get("code") == -10103, f"密码错误业务 code 不符合预期，响应: {response_body}"
        message = response_body.get("message", "")
        assert message.startswith("密码输入错误，连续输入错误5次将导致账号锁定，当前错误次数:"), (
            f"密码错误 message 不符合预期，响应: {response_body}"
        )

    @pytest.mark.api
    @pytest.mark.parametrize(
        "payload_body",
        [
            {},
            {"password": "admin", "returnToken": False},
            {"username": "not_registered_user", "returnToken": False},
        ],
        ids=["empty_body", "missing_username", "missing_password"],
    )
    def test_login_fail_with_missing_field(self, login_api, payload_body) -> None:
        """测试登录请求体为空、缺少 username、缺少 password 的错误响应。"""
        response = login_api.login_by_payload(payload_body)
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert response_body == {
            "code": -10101,
            "message": "该账号未注册，请联系管理员",
        }, f"登录异常请求体响应不符合预期，payload_body: {payload_body}，响应: {response_body}"

    @pytest.mark.api
    def test_login_success(self, login_api, api_env) -> None:
        """测试默认账号登录成功。"""
        username = api_env.require("username")
        password = api_env.require("password")
        response = login_api.login_by_username(username, password)
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert_business_code(response_body, 0)
        assert response_body.get("data", {}).get("username") == username, (
            f"登录用户名不符合预期，实际: {response_body.get('data', {}).get('username')}，"
            f"预期: {username}"
        )
        assert get_scope_value("sessionCookie"), "登录成功后未写入 sessionCookie"

    @pytest.mark.api
    def test_logout_success(self, login_api, api_env) -> None:
        """测试登录后退出登录成功。"""
        username = api_env.require("username")
        password = api_env.require("password")
        login_response = login_api.login_by_username(username, password)
        login_response_body = assert_response_json(login_response)

        assert_status_code_2xx(login_response)
        assert_business_code(login_response_body, 0)
        assert get_scope_value("sessionCookie"), "登出前未成功写入 sessionCookie"

        logout_response = login_api.logout_success()
        logout_response_body = assert_response_json(logout_response)

        assert_status_code_2xx(logout_response)
        assert_business_code(logout_response_body, 0)

    @pytest.mark.api
    @pytest.mark.external_api
    def test_login_phone_success(self, login_api, api_env, request) -> None:
        """测试手机号验证码登录成功。"""
        phone = api_env.require("phone")
        capture_manager = request.config.pluginmanager.getplugin("capturemanager")
        if capture_manager:
            capture_manager.suspend_global_capture(in_=True)
        try:
            response = login_api.login_phone(phone)
        finally:
            if capture_manager:
                capture_manager.resume_global_capture()
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert_business_code(response_body, 0)
        assert get_scope_value("sessionCookie"), "手机号登录成功后未写入 sessionCookie"
