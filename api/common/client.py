from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests import Response, Session
from requests.exceptions import RequestException

from utils.logger import Logger
from utils.yaml_reader import YamlManager

SENSITIVE_KEYS = {
    "password",
    "token",
    "accessToken",
    "access_token",
    "Authorization",
    "Cookie",
    "cookie",
    "sessionCookie",
    "phone",
    "telephone",
    "code",
}

ENVIRONMENT_CONFIG_PATH = "config/environment.yaml"


class HTTPClient:
    """HTTP 客户端，统一处理请求日志、Token 关联和异常。"""

    def __init__(
            self,
            base_url: str,
            gateway_url: Optional[str] = None,
            token: Optional[str] = None,
            timeout: int = 10,
            logger: Optional[Logger] = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must be a non-empty string")

        self.base_url = base_url.rstrip("/")
        # 防止 gateway_url 为 None 时调用 rstrip 报错
        self.gateway_url = gateway_url.rstrip("/") if gateway_url else None
        self.timeout = timeout
        self.session: Session = requests.Session()
        self._logger = logger or Logger("api_client")
        self._token: Optional[str] = None
        if token:
            self.set_token(token)

    def set_token(self, token: str) -> None:
        """设置 Bearer Token，并自动注入后续请求头。"""
        if not token:
            return

        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self) -> None:
        """清理已关联的 Token。"""
        self._token = None
        self.session.headers.pop("Authorization", None)

    def send_request(self, method: str, path: Optional[str] = None, command: Optional[str] = None,
                     **kwargs: Any) -> Response:
        """发送 HTTP 请求，并在响应中自动提取 Token。"""
        if command:
            if not self.gateway_url:
                raise ValueError("gateway_url must be configured before sending a command request")
            url = self.gateway_url
        else:
            if not path:
                raise ValueError("path must be a non-empty string")
            url = self._build_url(path)
        has_files = "files" in kwargs
        headers = self._merge_headers(kwargs.pop("headers", None), use_json_content_type=not has_files)

        if command:
            headers["command"] = str(command)
        if command or path == "/upload_part":
            self._inject_gateway_cookie(headers)
        self._log_request(method, url, kwargs)
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                timeout=kwargs.pop("timeout", self.timeout),
                **kwargs,
            )
        except RequestException as exc:
            self._logger.error(f"HTTP request failed: {method.upper()} {url}, error: {exc}")
            raise RuntimeError(f"HTTP request failed: {method.upper()} {url}") from exc

        self._log_response(response)
        self._auto_update_token(response)
        # print(url)
        # print(response.json())
        return response

    def _build_url(self, path: str) -> str:
        """拼接 base_url 和请求 path。"""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def _merge_headers(
            self,
            headers: Optional[Dict[str, str]],
            use_json_content_type: bool = True,
    ) -> Dict[str, str]:
        """合并默认请求头和单次请求头。"""
        merged_headers = {"Content-Type": "application/json"} if use_json_content_type else {}
        if headers:
            merged_headers.update(headers)
        return merged_headers

    def _inject_gateway_cookie(self, headers: Dict[str, str]) -> None:
        """Read sessionCookie from environment.yaml and inject it into gateway request headers."""
        session_cookie = self._read_session_cookie()
        if session_cookie:
            headers["Cookie"] = session_cookie

    def _read_session_cookie(self) -> Optional[str]:
        """Return sessionCookie from the API environment config, if configured."""
        config = YamlManager(self._logger).read(ENVIRONMENT_CONFIG_PATH)
        if not isinstance(config, dict):
            return None

        session_cookie = config.get("sessionCookie")
        if session_cookie in (None, ""):
            return None
        return str(session_cookie)

    def _auto_update_token(self, response: Response) -> None:
        """从常见响应字段中提取 Token 并自动关联到后续请求。"""
        try:
            response_body = response.json()
        except ValueError:
            return

        if not isinstance(response_body, dict):
            return

        token = (
                response_body.get("token")
                or response_body.get("accessToken")
                or response_body.get("access_token")
        )
        data = response_body.get("data")
        if not token and isinstance(data, dict):
            token = data.get("token") or data.get("accessToken") or data.get("access_token")

        if token:
            self.set_token(str(token))

    def _log_request(self, method: str, url: str, kwargs: Dict[str, Any]) -> None:
        """打印请求日志。"""
        self._logger.info(
            f"Request: {method.upper()} {url}, "
            f"params={self._redact(kwargs.get('params'))}, json={self._redact(kwargs.get('json'))}"
        )

    def _log_response(self, response: Response) -> None:
        """打印响应日志。"""
        self._logger.info(
            f"Response: {response.status_code} {response.url}, body={self._response_body_for_log(response)}")

    def _response_body_for_log(self, response: Response) -> Any:
        """返回脱敏后的响应日志内容。"""
        try:
            response_body = response.json()
        except ValueError:
            return response.text[:1000]
        return self._redact(response_body)

    def _redact(self, value: Any) -> Any:
        """递归脱敏敏感字段。"""
        if isinstance(value, dict):
            return {
                key: "***" if key in SENSITIVE_KEYS else self._redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        return value
