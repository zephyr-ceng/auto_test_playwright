from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
OUTPUT_ROOT = SCRIPT_DIR / "manager_categorized"
BASE_URL = "https://x.finetool.cn"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

import capture_finetool_network as capture_base  # noqa: E402
from pages.login_manager import LoginPage  # noqa: E402
from pages.patient_manager import PatientsPage  # noqa: E402
from pages.design_manager import DesignManager  # noqa: E402
import pages.login_manager as login_module  # noqa: E402


class NullLogger:
    def info(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def error(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def warning(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def debug(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture network requests while executing existing manager scripts."
    )
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=10000)
    return parser.parse_args()


def write_temp_config(path: Path, username: str, password: str, cookies: list[dict[str, Any]] | None = None) -> None:
    config = {
        "base_url": BASE_URL,
        "username": username,
        "password": password,
        "cookies_write_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cookies": cookies or [],
    }
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")


@contextmanager
def patched_login_config(config_path: Path):
    original_init = login_module.LoginPage.__init__

    def patched_init(
        self: LoginPage,
        driver: Any,
        logger: Any | None = None,
        locators_path: str = "data/login_data.yaml",
        config_path: str = str(config_path),
    ) -> None:
        original_init(self, driver, logger, locators_path, str(config_path))

    login_module.LoginPage.__init__ = patched_init
    try:
        yield
    finally:
        login_module.LoginPage.__init__ = original_init


def request_identity(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        record.get("method", "GET"),
        capture_base.request_origin(record.get("url", "")),
        capture_base.request_path(record.get("url", "")),
    )


def attach_network_listeners(
    page: Any,
    manager_name: str,
    current_action: dict[str, str],
    records_by_request: dict[int, dict[str, Any]],
    secrets: list[str],
) -> None:
    def on_request(request: Any) -> None:
        records_by_request[id(request)] = {
            "manager": manager_name,
            "script": f"pages/{manager_name}.py",
            "action": current_action["name"],
            "started_at": now_iso(),
            "method": request.method,
            "url": capture_base.redact_string(request.url, secrets),
            "resource_type": request.resource_type,
            "headers": capture_base.sanitize_headers(dict(request.headers), secrets),
            "post_data": capture_base.sanitize_obj(request.post_data, secrets),
            "query": capture_base.request_query(request.url, secrets),
        }

    def ensure_record(request: Any) -> dict[str, Any]:
        return records_by_request.setdefault(
            id(request),
            {
                "manager": manager_name,
                "script": f"pages/{manager_name}.py",
                "action": current_action["name"],
                "started_at": now_iso(),
                "method": request.method,
                "url": capture_base.redact_string(request.url, secrets),
                "resource_type": request.resource_type,
                "headers": capture_base.sanitize_headers(dict(request.headers), secrets),
                "post_data": capture_base.sanitize_obj(request.post_data, secrets),
                "query": capture_base.request_query(request.url, secrets),
            },
        )

    def on_request_finished(request: Any) -> None:
        record = ensure_record(request)
        record["finished_at"] = now_iso()
        try:
            response = request.response()
        except Exception:
            response = None
        if response:
            response_headers = capture_base.sanitize_headers(dict(response.headers), secrets)
            record["response"] = {
                "status": response.status,
                "status_text": response.status_text,
                "headers": response_headers,
                "body": capture_base.safe_response_body(response, response_headers, secrets),
            }

    def on_request_failed(request: Any) -> None:
        record = ensure_record(request)
        record["failed_at"] = now_iso()
        failure = request.failure
        record["failure"] = str(failure) if failure else "unknown"

    page.on("request", on_request)
    page.on("requestfinished", on_request_finished)
    page.on("requestfailed", on_request_failed)


def wait_quiet(page: Any) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(1200)


def run_operation(
    page: Any,
    current_action: dict[str, str],
    operations: list[dict[str, Any]],
    screenshot_dir: Path,
    manager_name: str,
    operation_name: str,
    fn: Callable[[], Any],
) -> Any:
    current_action["name"] = operation_name
    operation = {
        "manager": manager_name,
        "script": f"pages/{manager_name}.py",
        "name": operation_name,
        "started_at": now_iso(),
        "ok": False,
    }
    result = None
    try:
        result = fn()
        wait_quiet(page)
        operation["ok"] = True
        if result is not None:
            operation["result_preview"] = capture_base.truncate(capture_base.sanitize_obj(result, []), 500)
    except Exception as exc:
        operation["error"] = f"{type(exc).__name__}: {exc}"
        try:
            page.screenshot(path=str(screenshot_dir / f"error_{len(operations) + 1}.png"), full_page=True)
        except Exception:
            pass
    finally:
        operation["ended_at"] = now_iso()
        operations.append(operation)
        current_action["name"] = "idle"
    return result


def capture_manager(
    playwright: Any,
    manager_name: str,
    username: str,
    password: str,
    headed: bool,
    timeout_ms: int,
    action_builder: Callable[[Any, Any, Callable[[str, Callable[[], Any]], Any], Path], None],
    storage_state: dict[str, Any] | None = None,
    cookies_for_config: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manager_dir = OUTPUT_ROOT / manager_name
    screenshot_dir = manager_dir / "screenshots"
    manager_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    temp_config_path = manager_dir / "_temp_config.yaml"
    write_temp_config(temp_config_path, username, password, cookies_for_config)

    secrets = [username, password]
    raw_har_path = manager_dir / f"{manager_name}.raw.har"
    har_path = manager_dir / f"{manager_name}.har"
    requests_path = manager_dir / f"{manager_name}_requests.json"
    openapi_path = manager_dir / f"{manager_name}_openapi.yaml"

    records_by_request: dict[int, dict[str, Any]] = {}
    operations: list[dict[str, Any]] = []
    current_action = {"name": "startup"}
    state: dict[str, Any] | None = None
    cookies: list[dict[str, Any]] = []

    browser = playwright.chromium.launch(headless=not headed)
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        ignore_https_errors=True,
        storage_state=storage_state,
        record_har_path=str(raw_har_path),
        record_har_content="omit",
    )
    context.set_default_timeout(timeout_ms)
    context.set_default_navigation_timeout(timeout_ms)
    page = context.new_page()
    attach_network_listeners(page, manager_name, current_action, records_by_request, secrets)

    def runner(operation_name: str, fn: Callable[[], Any]) -> Any:
        return run_operation(page, current_action, operations, screenshot_dir, manager_name, operation_name, fn)

    try:
        with patched_login_config(temp_config_path):
            action_builder(page, context, runner, temp_config_path)
        try:
            page.screenshot(path=str(screenshot_dir / "final_page.png"), full_page=True)
        except PlaywrightError:
            pass
        state = context.storage_state()
        cookies = context.cookies()
    finally:
        context.close()
        browser.close()
        capture_base.sanitize_har(raw_har_path, har_path, secrets)
        try:
            temp_config_path.unlink()
        except OSError:
            pass

    records = list(records_by_request.values())
    records.sort(key=lambda item: item.get("started_at", ""))
    api_records = [record for record in records if capture_base.is_api_like(record)]
    requests_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    openapi_path.write_text(
        yaml.safe_dump(capture_base.generate_openapi(api_records, secrets), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    return {
        "manager": manager_name,
        "script": f"pages/{manager_name}.py",
        "records": records,
        "api_records": api_records,
        "operations": operations,
        "storage_state": state,
        "cookies": cookies,
        "artifacts": {
            "har": str(har_path),
            "requests_json": str(requests_path),
            "openapi": str(openapi_path),
            "screenshots": str(screenshot_dir),
        },
    }


def build_login_actions(username: str, password: str) -> Callable[[Any, Any, Callable[[str, Callable[[], Any]], Any], Path], None]:
    def actions(page: Any, _context: Any, run: Callable[[str, Callable[[], Any]], Any], temp_config_path: Path) -> None:
        log = NullLogger()
        login = LoginPage(page, log, config_path=str(temp_config_path))
        run("LoginPage.get_user_agreement_text", login.get_user_agreement_text)
        run("LoginPage.get_cookies", lambda: login.get_cookies(username, password))

    return actions


def build_patient_actions() -> Callable[[Any, Any, Callable[[str, Callable[[], Any]], Any], Path], None]:
    def actions(page: Any, _context: Any, run: Callable[[str, Callable[[], Any]], Any], _temp_config_path: Path) -> None:
        patients = PatientsPage(page, NullLogger())
        run("PatientsPage.count_page_patients(10)", lambda: patients.count_page_patients(10))
        run("PatientsPage.count_page_designs(10)", lambda: patients.count_page_designs(10))
        run("PatientsPage.search_patient('test', '139')", lambda: patients.search_patient("test", "139"))
        run("PatientsPage.create_patient_invalid(empty)", lambda: patients.create_patient_invalid("", "", "", "", ""))

    return actions


def build_design_actions() -> Callable[[Any, Any, Callable[[str, Callable[[], Any]], Any], Path], None]:
    def actions(page: Any, _context: Any, run: Callable[[str, Callable[[], Any]], Any], _temp_config_path: Path) -> None:
        design = DesignManager(page, NullLogger())

        def open_design_and_read_cases() -> Any:
            design.add_cookies(design._cookies)
            design.open_url(design.design_url)
            return design._read_case_tooth_positions(page.url)

        run("DesignManager.open_url + _read_case_tooth_positions", open_design_and_read_cases)
        run("DesignManager.treatment_path(url, 32)", lambda: design.treatment_path(design.design_url, 32))
        run("DesignManager._get_current_surgical_path", design._get_current_surgical_path)

    return actions


def endpoint_table(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[request_identity(record)].append(record)
    rows = []
    for (method, origin, path), items in sorted(grouped.items()):
        rows.append(
            {
                "method": method,
                "origin": origin,
                "path": path,
                "count": len(items),
                "statuses": sorted({str(item.get("response", {}).get("status", "n/a")) for item in items}),
                "actions": sorted({str(item.get("action", "")) for item in items if item.get("action")}),
                "resource_types": sorted({str(item.get("resource_type", "")) for item in items if item.get("resource_type")}),
            }
        )
    return rows


def generate_manager_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Finetool Manager-Classified API Documentation",
        "",
        f"- Capture time: `{now_iso()}`",
        "- Grouping rule: requests are categorized by the manager script whose method was executing when the request was observed.",
        "- Sensitive values such as cookies, authorization headers, sessions, tokens, passwords and temporary signed URL credentials are redacted.",
        "- Skipped high-impact design flows: DICOM upload, full design generation, implant selection, apex adjustment, surgical-stage drag/save.",
        "",
    ]

    for result in results:
        api_records = result["api_records"]
        total_records = result["records"]
        rows = endpoint_table(api_records)
        lines.extend(
            [
                f"## {result['script']}",
                "",
                f"- Total captured requests: `{len(total_records)}`",
                f"- API-like requests: `{len(api_records)}`",
                f"- Unique API-like endpoints: `{len(rows)}`",
                "",
                "### Operations",
                "",
            ]
        )
        for operation in result["operations"]:
            status = "ok" if operation.get("ok") else "failed"
            lines.append(f"- `{status}` - `{operation['name']}`")
            if "result_preview" in operation:
                lines.append(f"  Result: `{json.dumps(operation['result_preview'], ensure_ascii=False)}`")
            if operation.get("error"):
                lines.append(f"  Error: `{operation['error']}`")

        lines.extend(["", "### Endpoint Summary", ""])
        if not rows:
            lines.append("No API-like endpoints were observed for this manager.")
        else:
            lines.append("| # | Method | Origin | Path | Count | Status | Trigger Method |")
            lines.append("|---:|---|---|---|---:|---|---|")
            for idx, row in enumerate(rows, 1):
                lines.append(
                    "| {idx} | `{method}` | `{origin}` | `{path}` | {count} | `{statuses}` | {actions} |".format(
                        idx=idx,
                        method=row["method"],
                        origin=row["origin"],
                        path=row["path"],
                        count=row["count"],
                        statuses=", ".join(row["statuses"]),
                        actions=", ".join(f"`{action}`" for action in row["actions"]),
                    )
                )

        lines.extend(["", "### Endpoint Details", ""])
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for record in api_records:
            grouped[request_identity(record)].append(record)

        for idx, ((method, origin, path), items) in enumerate(sorted(grouped.items()), 1):
            sample = items[-1]
            response = sample.get("response") or {}
            request_body = capture_base.truncate(capture_base.try_parse_body(sample.get("post_data")))
            response_body = capture_base.truncate(response.get("body"))
            query = sample.get("query") or {}
            lines.extend(
                [
                    f"#### {idx}. `{method} {path}`",
                    "",
                    f"- Origin: `{origin}`",
                    f"- Observed count: `{len(items)}`",
                    f"- Trigger methods: `{', '.join(sorted({str(item.get('action', '')) for item in items if item.get('action')}))}`",
                    f"- Status codes: `{', '.join(sorted({str(item.get('response', {}).get('status', 'n/a')) for item in items}))}`",
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


def write_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "created_at": now_iso(),
        "group_count": len(results),
        "groups": [],
    }
    for result in results:
        rows = endpoint_table(result["api_records"])
        summary["groups"].append(
            {
                "manager": result["manager"],
                "script": result["script"],
                "total_requests": len(result["records"]),
                "api_like_requests": len(result["api_records"]),
                "unique_api_endpoints": len(rows),
                "operations": result["operations"],
                "artifacts": result["artifacts"],
            }
        )
    return summary


def main() -> int:
    args = parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        login_result = capture_manager(
            playwright,
            "login_manager",
            args.username,
            args.password,
            args.headed,
            args.timeout_ms,
            build_login_actions(args.username, args.password),
        )
        storage_state = login_result["storage_state"]
        cookies = login_result["cookies"]

        patient_result = capture_manager(
            playwright,
            "patient_manager",
            args.username,
            args.password,
            args.headed,
            args.timeout_ms,
            build_patient_actions(),
            storage_state=storage_state,
            cookies_for_config=cookies,
        )
        design_result = capture_manager(
            playwright,
            "design_manager",
            args.username,
            args.password,
            args.headed,
            args.timeout_ms,
            build_design_actions(),
            storage_state=storage_state,
            cookies_for_config=cookies,
        )

    results = [login_result, patient_result, design_result]
    docs_path = OUTPUT_ROOT / "manager_classified_api_documentation.md"
    summary_path = OUTPUT_ROOT / "manager_capture_summary.json"
    docs_path.write_text(generate_manager_markdown(results), encoding="utf-8")
    summary = write_summary(results)
    summary["artifacts"] = {
        "documentation": str(docs_path),
        "summary": str(summary_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
