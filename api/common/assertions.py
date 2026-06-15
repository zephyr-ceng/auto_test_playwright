from typing import Any, Dict

from requests import Response


def assert_status_code(response: Response, expected_status_code: int = 200) -> None:
    """断言 HTTP 状态码符合预期。"""
    assert response.status_code == expected_status_code, (
        f"HTTP 状态码不符合预期，实际: {response.status_code}，"
        f"预期: {expected_status_code}，响应: {response.text}"
    )


def assert_status_code_2xx(response: Response) -> None:
    """断言 HTTP 状态码为 2xx。"""
    assert 200 <= response.status_code <= 299, (
        f"HTTP 状态码不是 2xx，实际: {response.status_code}，响应: {response.text}"
    )


def assert_response_json(response: Response) -> Dict[str, Any]:
    """断言响应体为 JSON 对象，并返回解析后的字典。"""
    try:
        response_body = response.json()
    except ValueError as exc:
        raise AssertionError(f"响应体不是合法 JSON，响应: {response.text}") from exc

    assert isinstance(response_body, dict), f"响应体不是 JSON 对象，实际: {type(response_body).__name__}"
    return response_body


def assert_business_code(response_body: Dict[str, Any], expected_code: int = 0) -> None:
    """断言业务 code 符合预期。"""
    actual_code = response_body.get("code")
    assert actual_code == expected_code, (
        f"业务 code 不符合预期，实际: {actual_code}，预期: {expected_code}，响应: {response_body}"
    )


def assert_business_message(response_body: Dict[str, Any], expected_message: str) -> None:
    """断言业务 message 或 msg 符合预期。"""
    actual_message = response_body.get("message", response_body.get("msg"))
    assert actual_message == expected_message, (
        f"业务 message 不符合预期，实际: {actual_message}，"
        f"预期: {expected_message}，响应: {response_body}"
    )
