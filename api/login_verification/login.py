from typing import Any, Dict, Optional

from requests import Response

from api.common.client import HTTPClient

GLOBAL_SCOPE: Dict[str, str] = {}
sessionCookie = ""


def set_scope_value(key: str, value: Any) -> None:
    """设置全局变量；空值不写入。"""
    if value in (None, ""):
        return

    string_value = str(value)
    GLOBAL_SCOPE[key] = string_value
    globals()[key] = string_value


def get_scope_value(key: str) -> str:
    """按 key 获取全局变量；不存在时返回空字符串。"""
    value = GLOBAL_SCOPE.get(key)
    if value:
        return value

    value = globals().get(key)
    return str(value) if value else ""


class Login:
    """登录接口封装。"""

    def __init__(
            self,
            base_url: str,
    ) -> None:
        self.base_url = base_url
        self.client = HTTPClient(self.base_url)

    def login_by_username(
            self,
            username: str,
            password: str,
            return_token: bool = False,
    ) -> Response:
        """请求用户名密码登录接口，并保存响应中的 sessionCookie。"""
        payload = {
            "username": username,
            "password": password,
            "returnToken": return_token,
        }
        response = self.client.send_request("POST", "/login_by_username", json=payload)
        self._save_session_cookie(response)
        return response

    def login_by_payload(self, payload: Dict[str, Any]) -> Response:
        """使用自定义请求体调用用户名密码登录接口。"""
        response = self.client.send_request("POST", "/login_by_username", json=payload)
        self._save_session_cookie(response)
        return response

    @staticmethod
    def _save_session_cookie(response: Response) -> None:
        """从 Set-Cookie 响应头中提取 sessionCookie 并写入全局变量。"""
        set_cookie = response.headers.get("Set-Cookie") or response.headers.get("set-cookie")
        if set_cookie:
            set_scope_value("sessionCookie", set_cookie.split(";")[0])

    def logout_success(self) -> Response:
        """请求退出登录接口。"""
        return self.client.send_request("POST", "/logout")

    ''' ********************************** 手机号验证  **************************************************************** '''

    def send_sms(self, phone: str) -> Response:
        """发送手机号登录验证码。"""
        payload = {
            "telephone": str(phone),
            "type": "login",
        }
        return self.client.send_request("POST", "/send_sms", json=payload)

    def login_by_telephone(
            self,
            code: str,
            phone: str,
            return_token: bool = False,
    ) -> Response:
        """使用手机号和验证码登录，并保存响应中的 sessionCookie。"""
        payload = {
            "telephone": str(phone),
            "code": code,
            "returnToken": return_token,
        }
        response = self.client.send_request("POST", "/login_by_telephone", json=payload)
        self._save_session_cookie(response)
        return response

    def login_phone(self, phone: str, return_token: bool = False) -> Response:
        """手机号验证码登录：先发送短信，再从终端读取验证码并触发登录。"""
        telephone = phone
        self.send_sms(telephone)
        code = input(f"请输入手机号 {telephone} 收到的验证码: ").strip()
        if not code:
            raise RuntimeError("验证码不能为空")
        return self.login_by_telephone(code, telephone, return_token)


LoginAPI = Login
