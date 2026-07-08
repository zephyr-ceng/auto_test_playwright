from typing import Any, Dict, Optional
import requests
from requests import Response

from api.common.client import HTTPClient
from utils.yaml_reader import YamlManager
from utils.logger import Logger


class Login:
    """登录接口封装。"""

    def __init__(
            self,
            client: HTTPClient,
            env_path: str = "config/environment.yaml"
    ) -> None:
        self.client = client
        log = Logger("ReadEnv")
        self.env_path = env_path
        self.__config = YamlManager(log)

    ''' ********************************** 手机号  **************************************************************** '''

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
        self.__save_session_cookie(response)
        return response

    def login_by_payload(self, payload: Dict[str, Any]) -> Response:
        """使用自定义请求体调用用户名密码登录接口。"""
        response = self.client.send_request("POST", "/login_by_username", json=payload)
        self.__save_session_cookie(response)
        return response

    def __save_session_cookie(self, response: Response) -> None:
        """从 Set-Cookie 响应头中提取 sessionCookie 并写入全局变量。"""
        cookie_dict = requests.utils.dict_from_cookiejar(self.client.session.cookies)
        if cookie_dict and self.__config:
            # 还原为 http 传输的字符串格式
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
            self.__config.update(self.env_path, {"sessionCookie": cookie_str})
            # 写入的格式为：session=162dce29-5c56-45a0-8ba8-79915535816d
            # print(self._config.read(self.env_path).get("sessionCookie"))

    def logout_success(self) -> Response:
        """请求退出登录接口。"""
        return self.client.send_request("POST", "/logout")

    ''' ********************************** 手机号  **************************************************************** '''

    def send_sms(self, phone: str, sms_type: str) -> Response:
        """发送手机号验证码。"""
        payload = {
            "telephone": phone,
            "type": sms_type,
        }
        return self.client.send_request("POST", "/send_sms", json=payload)

    def login_by_telephone(
            self,
            phone: str,
            code: Optional[str] = None,
            return_token: bool = False,
    ) -> Response:
        """使用手机号验证码登录；未传 code 时先发送短信并从终端读取验证码。"""
        telephone = str(phone)
        verification_code = code
        if verification_code is None:
            self.send_sms(telephone, sms_type="login")
            verification_code = input(f"请输入手机号 {telephone} 收到的验证码: ").strip()

        if not verification_code:
            raise RuntimeError("验证码不能为空")

        payload = {
            "telephone": telephone,
            "code": verification_code,
            "returnToken": return_token,
        }
        response = self.client.send_request("POST", "/login_by_telephone", json=payload)
        self.__save_session_cookie(response)
        return response

    ''' ********************************** 重置密码  **************************************************************** '''

    def reset_password(
            self,
            phone: str,
            code: Optional[str] = None,
            new_password: str = "admin",
    ) -> Response:
        """使用手机号验证码重置密码；未传 code 时先发送 reset 短信并从终端读取验证码。"""
        telephone = str(phone)
        verification_code = code
        if verification_code is None:
            self.send_sms(telephone, sms_type="reset")
            verification_code = input(f"请输入手机号 {telephone} 收到的重置密码验证码: ").strip()

        if not verification_code:
            raise RuntimeError("验证码不能为空")

        payload = {
            "telephone": telephone,
            "code": verification_code,
            "newPassword": new_password,
        }
        return self.client.send_request("POST", "/reset_password", json=payload)


class GatewayAPI:
    def __init__(self, client: HTTPClient) -> None:
        self.client = client

    def query_information(self, command: str = "16001") -> Response:
        """ 查询患者信息 """
        return self.client.send_request(method="POST", command=command)


LoginAPI = Login
