import pytest

from api.common.assertions import assert_business_code, assert_response_json, assert_status_code_2xx
from api.login_verification.login import Login, GatewayAPI
from tests.api.conftest import api_env
from api.common.client import HTTPClient


@pytest.fixture(scope="function")  # 如果希望每条用例独立会话，用 function；如果想跨用例共享，用 session
def http_client(base_url, gateway_url):
    """创建底层的 HTTP 客户端，用于维系 Session 和 Cookie"""
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    yield client
    client.session.close()


@pytest.fixture(scope="function")
def login_api(http_client):
    """创建登录接口对象；每条用例独立持有 HTTP 会话。"""
    return Login(http_client)


@pytest.fixture(scope="function")
def gateway_api(http_client):
    """创建网关接口对象，与登录接口共享同一个底层 http_client (Session)"""
    return GatewayAPI(http_client)


class TestLoginAPI:
    """登录接口单接口测试。"""

    @pytest.mark.api
    def test_login_fail_with_wrong_password(self, login_api, api_env) -> None:
        """测试错误密码登录，预期无法登录。"""
        username = api_env.require("username")
        response = login_api.login_by_username(username, "wrong_pwd")
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert response_body.get("code") == -10103, f"错误密码验证失败， code 不符合预期，响应: {response_body}"
        message = response_body.get("message", "")
        assert message.startswith("密码输入错误，连续输入错误5次将导致账号锁定，当前错误次数:"), (
            f"错误密码验证失败， message 不符合预期，响应: {response_body}"
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
        # assert get_scope_value("sessionCookie"), "登录成功后未写入 sessionCookie"

    @pytest.mark.api
    def test_logout_success(self, login_api, api_env) -> None:
        """测试登录后退出登录成功。"""
        username = api_env.require("username")
        password = api_env.require("password")
        login_response = login_api.login_by_username(username, password)
        login_response_body = assert_response_json(login_response)

        assert_status_code_2xx(login_response)
        assert_business_code(login_response_body, 0)
        # assert get_scope_value("sessionCookie"), "登出前未成功写入 sessionCookie"

        logout_response = login_api.logout_success()
        logout_response_body = assert_response_json(logout_response)

        assert_status_code_2xx(logout_response)
        assert_business_code(logout_response_body, 0)

    @pytest.mark.api
    # @pytest.mark.external_api
    def test_login_by_telephone_success(self, login_api, api_env, request) -> None:
        """测试手机号验证码登录成功。"""
        phone = api_env.require("phone")
        capture_manager = request.config.pluginmanager.getplugin("capturemanager")
        if capture_manager:
            capture_manager.suspend_global_capture(in_=True)
        try:
            response = login_api.login_by_telephone(phone)
        finally:
            if capture_manager:
                capture_manager.resume_global_capture()
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert_business_code(response_body, 0)
        # assert get_scope_value("sessionCookie"), "手机号登录成功后未写入 sessionCookie"

    @pytest.mark.api
    def test_login_by_telephone_fail(self, login_api, api_env) -> None:
        phone = api_env.require("phone")
        code = "123456"
        response = login_api.login_by_telephone(phone, code)
        assert_status_code_2xx(response)
        response_body = assert_response_json(response)
        assert response_body.get("code") == -10104, f"错误验证码登录验证失败， code 不符合预期，响应: {response_body}"
        message = response_body.get("message", "")
        assert message.startswith("验证码输入错误，连续输入错误5次将导致账号锁定，当前错误次数:"), (
            f"错误验证码登录验证失败， message 不符合预期，响应: {response_body}"
        )

    @pytest.mark.api
    def test_reset_password_success(self, login_api, api_env, request) -> None:
        """测试手机号验证码重置密码成功。"""
        phone = api_env.require("phone")
        capture_manager = request.config.pluginmanager.getplugin("capturemanager")
        if capture_manager:
            capture_manager.suspend_global_capture(in_=True)
        try:
            response = login_api.reset_password(phone)
        finally:
            if capture_manager:
                capture_manager.resume_global_capture()
        response_body = assert_response_json(response)

        assert_status_code_2xx(response)
        assert response_body.get("code") == 0, f"重置密码成功 code 不符合预期，响应: {response_body}"

    @pytest.mark.api
    def test_reset_password_fail_with_wrong_code(self, login_api, api_env) -> None:
        """测试错误验证码重置密码失败。"""
        phone = api_env.require("phone")
        response = login_api.reset_password(phone, code="123456")
        assert_status_code_2xx(response)
        response_body = assert_response_json(response)
        assert response_body.get("code") == -10104, f"错误验证码重置密码验证失败， code 不符合预期，响应: {response_body}"
        message = response_body.get("message", "")
        assert message.startswith("验证码输入错误，连续输入错误5次将导致账号锁定，当前错误次数:"), (
            f"错误验证码重置密码验证失败， message 不符合预期，响应: {response_body}"
        )

    @pytest.mark.api
    @pytest.mark.destructive_api
    def test_reset_password_fail_after_five_wrong_codes(self, login_api, api_env) -> None:
        """测试重置密码验证码连续错误五次后账号锁定。"""
        phone = api_env.require("phone")
        login_api.send_sms(phone, sms_type="reset")

        response = None
        for _ in range(5):
            response = login_api.reset_password(phone, code="123456")
            assert_status_code_2xx(response)

        response_body = assert_response_json(response)
        assert response_body == {
            "code": -10106,
            "message": "账号已被锁定，请联系管理员",
        }, f"重置密码验证码连续错误五次响应不符合预期，响应: {response_body}"

    @pytest.mark.api
    def test_query_information(self, login_api, gateway_api) -> None:
        login_api.login_by_username("admin", "admin")
        res = gateway_api.query_information()
        assert_status_code_2xx(res)
        response_body = assert_response_json(res)
        assert response_body == {'code': 0, 'data': {'ID': '1', 'Name': '张飞', 'TenantID': '1', 'AccountID': '5',
                                                     'TenantType': 'public'}}
