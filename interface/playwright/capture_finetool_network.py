from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


OUTPUT_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"

LOGIN_URL = "https://x.finetool.cn/login"
BUSINESS_URL = "https://x.finetool.cn/surgicalDesignList"

QUERY_TEXT = "\u67e5\u8be2"
USER_AGREEMENT_TEXT = "\u7528\u6237\u534f\u8bae"
ACK_TEXT = "\u6211\u5df2\u4e86\u89e3"
NEW_PATIENT_TEXTS = ["\u65b0\u5efa\u60a3\u8005", "\u65b0\u589e\u60a3\u8005"]
CANCEL_TEXTS = ["\u53d6\u6d88", "\u5173\u95ed"]

SENSITIVE_KEY_PARTS = (
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "session",
    "q-ak",
    "q-signature",
    "q-sign-time",
    "q-key-time",
    "security-token",
    "access-key",
    "access_key",
    "accesskey",
    "credential",
)

SENSITIVE_QUERY_KEYS = (
    "q-ak",
    "q-signature",
    "q-sign-time",
    "q-key-time",
    "x-oss-security-token",
    "x-cos-security-token",
    "security-token",
    "session",
    "token",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture finetool network traffic with Playwright.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=60000)
    return parser.parse_args()


def is_sensitive_key(key: Any) -> bool:
    key_text = str(key).lower()
    return any(part in key_text for part in SENSITIVE_KEY_PARTS)


def redact_string(value: str, secrets: list[str]) -> str:
    result = value
    for secret in secrets:
        if secret:
            result = result.replace(secret, "<redacted>")
    result = re.sub(r"(?i)(\bsession=)[^;\s&\"]+", r"\1<redacted>", result)
    for key in SENSITIVE_QUERY_KEYS:
        result = re.sub(rf"(?i)([?&]{re.escape(key)}=)[^&\s\"]+", rf"\1<redacted>", result)
    return result


def sanitize_obj(obj: Any, secrets: list[str], parent_key: str = "") -> Any:
    if isinstance(obj, dict):
        header_name = str(obj.get("name", "")).lower()
        sanitized: dict[str, Any] = {}
        for key, value in obj.items():
            if key == "value" and is_sensitive_key(header_name):
                sanitized[key] = "<redacted>"
            elif is_sensitive_key(key) or is_sensitive_key(parent_key):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = sanitize_obj(value, secrets, str(key))
        return sanitized
    if isinstance(obj, list):
        return [sanitize_obj(item, secrets, parent_key) for item in obj]
    if isinstance(obj, str):
        return redact_string(obj, secrets)
    return obj


def truncate(value: Any, limit: int = 1600) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"... <truncated {len(value) - limit} chars>"
    if isinstance(value, list):
        return [truncate(item, limit) for item in value[:20]]
    if isinstance(value, dict):
        return {key: truncate(val, limit) for key, val in list(value.items())[:40]}
    return value


def try_parse_body(text: str | None) -> Any:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except Exception:
        parsed_qs = parse_qs(stripped, keep_blank_values=True)
        if parsed_qs and len(parsed_qs) > 1:
            return {key: values if len(values) > 1 else values[0] for key, values in parsed_qs.items()}
        return stripped


def sanitize_headers(headers: dict[str, str], secrets: list[str]) -> dict[str, str]:
    return {key: ("<redacted>" if is_sensitive_key(key) else redact_string(value, secrets)) for key, value in headers.items()}


def safe_response_body(response: Any, headers: dict[str, str], secrets: list[str]) -> Any:
    content_type = headers.get("content-type", "")
    if not any(marker in content_type for marker in ("json", "text", "xml", "javascript")):
        return None

    length_header = headers.get("content-length")
    try:
        if length_header and int(length_header) > 2_000_000:
            return "<omitted: response body too large>"
    except ValueError:
        pass

    try:
        text = response.text()
    except Exception as exc:
        return f"<unavailable: {type(exc).__name__}>"
    return truncate(sanitize_obj(try_parse_body(text), secrets))


def request_query(url: str, secrets: list[str]) -> dict[str, Any]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {key: values if len(values) > 1 else values[0] for key, values in params.items()}
    return sanitize_obj(cleaned, secrets)


def request_path(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path or "/"


def request_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_api_like(record: dict[str, Any]) -> bool:
    url = record.get("url", "")
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = parsed.netloc.lower()
    method = record.get("method", "GET")
    resource_type = record.get("resource_type", "")
    if resource_type in {"xhr", "fetch", "websocket", "eventsource"}:
        return True
    if method not in {"GET", "HEAD", "OPTIONS"}:
        return True
    if "tars.finetool.cn" in host:
        return True
    return any(marker in path for marker in ("/api/", "/v1/", "/v2/", "/gateway", "/graphql", "/login"))


def wait_quiet(page: Any, timeout_ms: int = 5000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(1200)


def click_text_if_visible(page: Any, text: str, timeout: int = 1500) -> bool:
    locators = [
        page.get_by_role("button", name=text),
        page.get_by_text(text, exact=False),
        page.locator(f"button:has-text('{text}')"),
    ]
    for locator in locators:
        try:
            if locator.count() > 0:
                locator.first.click(timeout=timeout)
                return True
        except Exception:
            continue
    return False


def safe_click_locator(locator: Any, index: int = 0, timeout: int = 2000) -> bool:
    try:
        if locator.count() <= index:
            return False
        target = locator.nth(index)
        target.scroll_into_view_if_needed(timeout=timeout)
        target.click(timeout=timeout)
        return True
    except Exception:
        return False


def fill_visible_inputs(page: Any, values: list[str], timeout: int = 1500) -> int:
    filled = 0
    try:
        inputs = page.locator("input:visible")
        count = min(inputs.count(), 8)
    except Exception:
        return 0

    for index in range(count):
        if filled >= len(values):
            break
        locator = inputs.nth(index)
        try:
            input_type = (locator.get_attribute("type") or "text").lower()
            readonly = locator.get_attribute("readonly")
            disabled = locator.get_attribute("disabled")
            role = (locator.get_attribute("role") or "").lower()
            if readonly is not None or disabled is not None or role == "combobox":
                continue
            if input_type not in {"text", "search", "tel", "number", ""}:
                continue
            locator.fill(values[filled], timeout=timeout)
            filled += 1
        except Exception:
            continue
    return filled


def choose_first_dropdown_option(page: Any) -> bool:
    try:
        triggers = page.locator(".ant-select:not(.ant-pagination-options-size-changer):visible")
        if not safe_click_locator(triggers, 0):
            return False
        page.wait_for_timeout(500)
        options = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option")
        return safe_click_locator(options, 0)
    except Exception:
        return False


def choose_page_size(page: Any, value: str = "20") -> bool:
    try:
        trigger = page.locator(".ant-pagination-options .ant-pagination-options-size-changer")
        if not safe_click_locator(trigger, 0):
            return False
        page.wait_for_timeout(500)
        options = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option")
        count = min(options.count(), 10)
        for index in range(count):
            option = options.nth(index)
            try:
                if value in option.inner_text(timeout=1000):
                    option.click(timeout=1500)
                    return True
            except Exception:
                continue
        return safe_click_locator(options, 0)
    except Exception:
        return False


def close_modal_or_popup(page: Any) -> None:
    for text in CANCEL_TEXTS:
        if click_text_if_visible(page, text, timeout=1000):
            page.wait_for_timeout(500)
            return
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass


def generate_markdown(
    records: list[dict[str, Any]],
    api_records: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    secrets: list[str],
) -> str:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in api_records:
        grouped[(record.get("method", "GET"), request_origin(record.get("url", "")), request_path(record.get("url", "")))].append(record)

    lines = [
        "# Finetool Network API Documentation",
        "",
        f"- Capture time: `{now_iso()}`",
        f"- Target login URL: `{LOGIN_URL}`",
        f"- Total network requests in HAR/details: `{len(records)}`",
        f"- API-like endpoints documented: `{len(grouped)}`",
        "- Sensitive values such as cookies, authorization headers, sessions, tokens and passwords are redacted.",
        "",
        "## Operations Covered",
        "",
    ]

    for item in operations:
        status = "ok" if item.get("ok") else "failed"
        lines.append(f"- `{status}` - {item.get('name')} ({item.get('started_at')} -> {item.get('ended_at')})")
        if item.get("error"):
            lines.append(f"  Error: `{item['error']}`")

    lines.extend(["", "## Endpoint Summary", ""])
    if not grouped:
        lines.append("No API-like endpoints were detected. See the HAR for all captured requests.")
    else:
        lines.append("| # | Method | Origin | Path | Status | Resource | Trigger |")
        lines.append("|---:|---|---|---|---|---|---|")
        for idx, ((method, origin, path), items) in enumerate(sorted(grouped.items()), 1):
            statuses = ", ".join(sorted({str(item.get("response", {}).get("status", "n/a")) for item in items}))
            resources = ", ".join(sorted({str(item.get("resource_type", "")) for item in items if item.get("resource_type")}))
            actions = ", ".join(sorted({str(item.get("action", "")) for item in items if item.get("action")}))
            lines.append(f"| {idx} | `{method}` | `{origin}` | `{path}` | `{statuses}` | `{resources}` | {actions} |")

    lines.extend(["", "## Endpoint Details", ""])
    for idx, ((method, origin, path), items) in enumerate(sorted(grouped.items()), 1):
        sample = items[-1]
        response = sample.get("response") or {}
        request_body = truncate(sanitize_obj(try_parse_body(sample.get("post_data")), secrets))
        response_body = truncate(response.get("body"))
        query = request_query(sample.get("url", ""), secrets)

        lines.extend(
            [
                f"### {idx}. `{method} {path}`",
                "",
                f"- Origin: `{origin}`",
                f"- Observed count: `{len(items)}`",
                f"- Trigger actions: `{', '.join(sorted({str(item.get('action', '')) for item in items if item.get('action')}))}`",
                f"- Status codes: `{', '.join(sorted({str(item.get('response', {}).get('status', 'n/a')) for item in items}))}`",
                f"- Request content type: `{sample.get('headers', {}).get('content-type', '')}`",
                f"- Response content type: `{response.get('headers', {}).get('content-type', '')}`",
                "",
            ]
        )

        if query:
            lines.extend(["Query parameters:", "", "```json", json.dumps(query, ensure_ascii=False, indent=2), "```", ""])
        if request_body is not None:
            lines.extend(["Request body sample:", "", "```json", json.dumps(request_body, ensure_ascii=False, indent=2), "```", ""])
        if response_body is not None:
            lines.extend(["Response body sample:", "", "```json", json.dumps(response_body, ensure_ascii=False, indent=2), "```", ""])

    return "\n".join(lines) + "\n"


def openapi_type(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, list):
        item_schema = openapi_type(value[0]) if value else {}
        return {"type": "array", "items": item_schema}
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {str(key): openapi_type(val) for key, val in value.items()},
        }
    return {"type": "string"}


def generate_openapi(api_records: list[dict[str, Any]], secrets: list[str]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in api_records:
        grouped[(record.get("method", "GET"), request_origin(record.get("url", "")), request_path(record.get("url", "")))].append(record)

    servers = sorted({origin for _, origin, _ in grouped})
    spec: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": "Finetool Captured API",
            "version": datetime.now().strftime("%Y.%m.%d"),
            "description": "Generated from Playwright network capture. Sensitive values are redacted. Schemas are inferred from observed samples.",
        },
        "servers": [{"url": origin} for origin in servers],
        "paths": {},
    }

    for (method, origin, path), items in sorted(grouped.items()):
        sample = items[-1]
        operation: dict[str, Any] = {
            "summary": f"Captured {method} {path}",
            "description": f"Observed from origin {origin}. Trigger actions: {', '.join(sorted({str(item.get('action', '')) for item in items if item.get('action')}))}.",
            "parameters": [],
            "responses": {},
        }
        query = request_query(sample.get("url", ""), secrets)
        for key, value in query.items():
            operation["parameters"].append(
                {
                    "name": key,
                    "in": "query",
                    "required": False,
                    "schema": openapi_type(value),
                    "example": value,
                }
            )

        body = sanitize_obj(try_parse_body(sample.get("post_data")), secrets)
        if body is not None:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    sample.get("headers", {}).get("content-type") or "application/json": {
                        "schema": openapi_type(body),
                        "example": truncate(body, 1000),
                    }
                },
            }

        statuses = sorted({str(item.get("response", {}).get("status", "default")) for item in items})
        for status in statuses:
            matching = next((item for item in reversed(items) if str(item.get("response", {}).get("status", "default")) == status), items[-1])
            response = matching.get("response") or {}
            response_body = response.get("body")
            content_type = response.get("headers", {}).get("content-type") or "application/json"
            response_obj: dict[str, Any] = {"description": f"Observed HTTP {status}"}
            if response_body is not None:
                response_obj["content"] = {
                    content_type: {
                        "schema": openapi_type(response_body),
                        "example": truncate(response_body, 1000),
                    }
                }
            operation["responses"][status] = response_obj

        spec["paths"].setdefault(path, {})[method.lower()] = operation

    return spec


def sanitize_har(raw_path: Path, output_path: Path, secrets: list[str]) -> None:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    sanitized = sanitize_obj(raw, secrets)
    output_path.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        raw_path.unlink()
    except OSError:
        pass


def main() -> int:
    args = parse_args()
    ensure_dirs()

    secrets = [args.username, args.password]
    raw_har_path = OUTPUT_DIR / "finetool_network_capture.raw.har"
    har_path = OUTPUT_DIR / "finetool_network_capture.har"
    details_path = OUTPUT_DIR / "finetool_network_requests.json"
    docs_path = OUTPUT_DIR / "finetool_api_documentation.md"
    openapi_path = OUTPUT_DIR / "finetool_openapi.yaml"
    summary_path = OUTPUT_DIR / "finetool_capture_summary.json"

    records_by_request: dict[int, dict[str, Any]] = {}
    operations: list[dict[str, Any]] = []
    current_action = {"name": "startup"}

    def on_request(request: Any) -> None:
        headers = sanitize_headers(dict(request.headers), secrets)
        post_data = request.post_data
        records_by_request[id(request)] = {
            "action": current_action["name"],
            "started_at": now_iso(),
            "method": request.method,
            "url": redact_string(request.url, secrets),
            "resource_type": request.resource_type,
            "headers": headers,
            "post_data": sanitize_obj(post_data, secrets),
            "query": request_query(request.url, secrets),
        }

    def on_request_finished(request: Any) -> None:
        record = records_by_request.setdefault(
            id(request),
            {
                "action": current_action["name"],
                "started_at": now_iso(),
                "method": request.method,
                "url": redact_string(request.url, secrets),
                "resource_type": request.resource_type,
                "headers": sanitize_headers(dict(request.headers), secrets),
                "post_data": sanitize_obj(request.post_data, secrets),
                "query": request_query(request.url, secrets),
            },
        )
        record["finished_at"] = now_iso()
        try:
            response = request.response()
        except Exception:
            response = None
        if response:
            response_headers = sanitize_headers(dict(response.headers), secrets)
            record["response"] = {
                "status": response.status,
                "status_text": response.status_text,
                "headers": response_headers,
                "body": safe_response_body(response, response_headers, secrets),
            }

    def on_request_failed(request: Any) -> None:
        record = records_by_request.setdefault(
            id(request),
            {
                "action": current_action["name"],
                "started_at": now_iso(),
                "method": request.method,
                "url": redact_string(request.url, secrets),
                "resource_type": request.resource_type,
                "headers": sanitize_headers(dict(request.headers), secrets),
                "post_data": sanitize_obj(request.post_data, secrets),
                "query": request_query(request.url, secrets),
            },
        )
        record["failed_at"] = now_iso()
        failure = request.failure
        record["failure"] = str(failure) if failure else "unknown"

    def run_action(page: Any, name: str, fn: Any) -> None:
        current_action["name"] = name
        operation = {"name": name, "started_at": now_iso(), "ok": False}
        try:
            fn()
            wait_quiet(page)
            operation["ok"] = True
        except Exception as exc:
            operation["error"] = f"{type(exc).__name__}: {exc}"
            try:
                page.screenshot(path=str(SCREENSHOT_DIR / f"error_{len(operations) + 1}.png"), full_page=True)
            except Exception:
                pass
        finally:
            operation["ended_at"] = now_iso()
            operations.append(operation)
            current_action["name"] = "idle"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            ignore_https_errors=True,
            record_har_path=str(raw_har_path),
            record_har_content="omit",
        )
        context.set_default_timeout(args.timeout_ms)
        page = context.new_page()
        page.on("request", on_request)
        page.on("requestfinished", on_request_finished)
        page.on("requestfailed", on_request_failed)

        run_action(page, "open login page", lambda: page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=args.timeout_ms))

        def user_agreement() -> None:
            if click_text_if_visible(page, USER_AGREEMENT_TEXT, timeout=2500):
                page.wait_for_timeout(1000)
                close_modal_or_popup(page)

        run_action(page, "open and close user agreement", user_agreement)

        run_action(page, "acknowledge webgl prompt if present", lambda: click_text_if_visible(page, ACK_TEXT, timeout=2000))

        def login() -> None:
            page.locator("#username").fill(args.username)
            page.locator("#password").fill(args.password)
            page.locator("button[type='submit']").click()
            try:
                page.wait_for_url(re.compile(r"^(?!.*\/login).*$"), timeout=15000)
            except PlaywrightTimeoutError:
                pass
            wait_quiet(page, timeout_ms=10000)
            if "/login" in page.url:
                visible_text = page.locator("body").inner_text(timeout=5000)
                raise RuntimeError(f"login did not leave login page; visible text starts with: {visible_text[:200]}")

        run_action(page, "login", login)

        run_action(page, "open surgical design list", lambda: page.goto(BUSINESS_URL, wait_until="domcontentloaded", timeout=args.timeout_ms))

        def patient_tab_search() -> None:
            safe_click_locator(page.locator("xpath=(//li[@role='menuitem'])[1]"), 0)
            page.wait_for_timeout(1000)
            fill_visible_inputs(page, ["test", "139"])
            click_text_if_visible(page, QUERY_TEXT, timeout=2500)
            page.wait_for_timeout(1500)

        run_action(page, "patient tab search", patient_tab_search)

        run_action(page, "patient list page size", lambda: choose_page_size(page, "20"))

        def new_patient_modal() -> None:
            for text in NEW_PATIENT_TEXTS:
                if click_text_if_visible(page, text, timeout=1800):
                    page.wait_for_timeout(1000)
                    break
            close_modal_or_popup(page)

        run_action(page, "open and close new patient modal", new_patient_modal)

        def design_tab_search() -> None:
            safe_click_locator(page.locator("xpath=(//li[@role='menuitem'])[2]"), 0)
            page.wait_for_timeout(1000)
            fill_visible_inputs(page, ["test"])
            choose_first_dropdown_option(page)
            click_text_if_visible(page, QUERY_TEXT, timeout=2500)
            page.wait_for_timeout(1500)

        run_action(page, "design tab search", design_tab_search)
        run_action(page, "design list page size", lambda: choose_page_size(page, "20"))
        run_action(page, "reload business list", lambda: page.reload(wait_until="domcontentloaded", timeout=args.timeout_ms))

        try:
            page.screenshot(path=str(SCREENSHOT_DIR / "final_page.png"), full_page=True)
        except PlaywrightError:
            pass

        page.wait_for_timeout(2000)
        context.close()
        browser.close()

    records = list(records_by_request.values())
    records.sort(key=lambda item: item.get("started_at", ""))
    api_records = [record for record in records if is_api_like(record)]

    details_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    docs_path.write_text(generate_markdown(records, api_records, operations, secrets), encoding="utf-8")
    openapi_path.write_text(
        yaml.safe_dump(generate_openapi(api_records, secrets), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    sanitize_har(raw_har_path, har_path, secrets)

    summary = {
        "created_at": now_iso(),
        "login_url": LOGIN_URL,
        "business_url": BUSINESS_URL,
        "total_requests": len(records),
        "api_like_requests": len(api_records),
        "unique_api_endpoints": len({(item.get("method"), request_origin(item.get("url", "")), request_path(item.get("url", ""))) for item in api_records}),
        "operations": operations,
        "artifacts": {
            "har": str(har_path),
            "details_json": str(details_path),
            "api_documentation": str(docs_path),
            "openapi": str(openapi_path),
            "summary": str(summary_path),
            "screenshots": str(SCREENSHOT_DIR),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
