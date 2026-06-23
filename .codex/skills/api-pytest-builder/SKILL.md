---
name: api-pytest-builder
description: Build requests-based API test automation for this Playwright_demo project from endpoint specs. Use when the user provides an API route/address, HTTP method, gateway command, request headers, request body fields, required/optional field rules, response shape, or assertion requirements and wants Codex to create or update API wrapper methods under api/ and pytest cases under tests/api/.
---

# API Pytest Builder

## Purpose

Use this skill to convert an endpoint specification into this repository's API automation shape:

`api/common/client.py -> api/<domain>/<domain>_api.py -> tests/api/single_api/test_<domain>_api.py -> api/common/assertions.py`

Keep API wrapper methods responsible for request construction and transport. Keep response assertions in pytest.

## Context To Read First

Before editing, read the current implementation and nearest examples:

- `api/common/client.py`
- `api/common/assertions.py`
- `tests/api/conftest.py`
- the target API module under `api/`
- nearby API tests under `tests/api/single_api/`
- `utils/random_manager.py` when randomized request data is needed
- `config/environment.yaml` only to understand configured keys; do not hard-code its values

Also inspect `git diff` for files you will touch. Preserve user changes and do not revert unrelated edits.

## API Wrapper Rules

- Reuse the project's `HTTPClient`; do not introduce another HTTP client.
- API classes accept `client: HTTPClient` and keep the current local inheritance style when extending an existing module.
- For normal path APIs, call:

```python
self.client.send_request("POST", path="/some_path", json=payload)
```

- For gateway command APIs, call:

```python
self.client.send_request("POST", command="13002", json=payload)
```

- Do not inject Cookie in business API methods. Gateway Cookie injection belongs in `HTTPClient.send_request()` via `config/environment.yaml` `sessionCookie`.
- API methods build the payload framework. Tests provide parameter values.
- Represent required request fields as required Python parameters.
- Represent optional request fields as parameters defaulting to `None`.
- Add optional fields to payload only when `value is not None`; this preserves explicitly supplied empty strings.
- Keep wire keys exactly as the API expects, for example `dateOfBirth`, `identityCard`, and `patientID`.
- Use Pythonic snake_case parameter names, for example `date_of_birth`, then map them to wire keys inside the payload.
- Return the raw `requests.Response`.
- Add concise docstrings to public API methods.

Example optional-field payload pattern:

```python
def add_patient(
        self,
        name: str,
        gender: int | None = None,
        date_of_birth: int | None = None,
        identity_card: str | None = None,
        telephone: str | None = None,
        desc: str | None = None,
) -> Response:
    payload = {"name": name}
    optional_fields = {
        "gender": gender,
        "dateOfBirth": date_of_birth,
        "identityCard": identity_card,
        "telephone": telephone,
        "desc": desc,
    }
    payload.update({key: value for key, value in optional_fields.items() if value is not None})
    return self.client.send_request("POST", command="13002", json=payload)
```

## Pytest Rules

- Put tests under `tests/api/single_api/test_<domain>_api.py` unless the repo already has a better nearby file.
- Create a function-scoped `HTTPClient` fixture unless an equivalent reusable fixture already exists.
- For authenticated gateway APIs, use a session-scoped login fixture that logs in once and writes `sessionCookie`; do not call login inside every test.
- Make gateway tests depend on that session fixture so later requests authenticate through `HTTPClient` Cookie injection.
- Use `pytest.mark.parametrize` to construct request variations.
- Generate random parameter values in the parametrize layer using `RandomManager`, not inside API methods.
- Put response assertions directly in the test method unless the identical assertion block is needed in at least three tests.
- Use existing assertions:
  - `assert_status_code_2xx(response)`
  - `assert_response_json(response)`
  - `assert_business_code(response_body, expected_code)`
- Add explicit assertions for user-provided response requirements, such as `data` shape, ID existence, message text, or field equality.
- Add `@pytest.mark.api`, `@allure.feature(...)`, and `@allure.story(...)`.
- Add concise fixture and test docstrings.

Example session login fixture:

```python
@pytest.fixture(scope="session")
def auth_session_cookie(base_url, gateway_url, api_env):
    client = HTTPClient(base_url=base_url, gateway_url=gateway_url)
    try:
        Login(client).login_by_username(api_env.require("username"), api_env.require("password"))
    finally:
        client.session.close()
```

Example parameterized success assertions:

```python
@pytest.mark.parametrize(
    "patient_data",
    [
        {"name": f"AP_{RandomManager.random_chinese_name()}"},
        {"name": f"AP_{RandomManager.random_chinese_name()}", "telephone": RandomManager.random_phone()},
    ],
    ids=["name_only", "with_telephone"],
)
def test_add_patient_success(self, patient_api, patient_data) -> None:
    response = patient_api.add_patient(**patient_data)
    assert_status_code_2xx(response)
    response_body = assert_response_json(response)
    assert_business_code(response_body, 0)
    data = response_body.get("data")
    assert isinstance(data, dict), f"response data is not an object: {response_body}"
    assert any(data.get(key) not in (None, "") for key in ("id", "ID", "patientID", "patientId"))
```

## Request Spec Mapping

When the user provides an endpoint spec:

- Determine the target domain module and method name from the endpoint name or existing project naming.
- If the user says address is `gateway` or provides a `command` header, implement as a command request.
- Treat `Content-Type: application/json` as already handled by `HTTPClient` unless a different content type is specified.
- Treat request body placeholders like `{{current_username}}` or `{{patientTelephone}}` as test-layer values, usually generated by `RandomManager`.
- Preserve prefixes the user requests, such as `AP_`.
- If required fields are ambiguous and cannot be inferred from the spec or existing tests, ask before implementing.
- If response ID field paths are ambiguous, assert the explicit path when the user provides it; otherwise support common project variants such as `data.id`, `data.ID`, `data.patientID`, and `data.patientId`.

## Verification

After implementing generated code, run:

```powershell
D:\ubuntu\Playwright_demo\.venv\Scripts\python.exe -m py_compile <changed python files>
D:\ubuntu\Playwright_demo\.venv\Scripts\python.exe -m pytest <target test file> -m api -q
```

If live services are unavailable, report that clearly and still run compile checks.

