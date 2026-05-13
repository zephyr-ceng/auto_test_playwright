---
name: pom-pytest-allure
description: Project workflow for Playwright_demo UI automation. Use when Codex receives a feature requirement, page workflow, element locator task, pytest case request, assertion standard, or Allure reporting requirement and must create or update Page Object manager files under pages, page YAML locators under data, pytest tests under tests, and Allure labels for standard reports.
---

# POM Pytest Allure

## Purpose

Use this skill to turn a user requirement plus assertion standard into maintainable Playwright + pytest automation in this repository.

Keep the project flow consistent:

`data/*.yaml -> pages/*_manager.py -> tests/test_*_page.py -> pytest assert -> core.conftest failure screenshot -> Allure report`

## Required Outputs

For a new page or workflow, create or update all three layers unless the user explicitly narrows the scope:

- `data/<page>_page.yaml`: page path and all selectors. The `url` value must be a path only.
- `pages/<page>_manager.py`: Page Object manager, filename must end with `_manager.py`.
- `tests/test_<page>_page.py`: pytest cases with fixtures, assertions, and Allure labels.

Do not put selectors directly in tests. Tests call page manager business methods and assert returned values.

## Naming Rules

- Use snake_case page names.
- Page Object files must be named `pages/<page>_manager.py`; examples: `login_manager.py`, `patient_manager.py`, `order_manager.py`.
- Page classes should use PascalCase plus `Page` or `Manager`, matching existing style when extending a module.
- Locator files should use `data/<page>_page.yaml` for new pages unless the repo already has a domain-specific YAML file.
- Test files should use `tests/test_<page>_page.py`.
- Fixture names should be clear and page-specific, such as `login_page`, `order_page`, or `page` only when the existing file already uses that convention.

## Implementation Flow

1. Read current patterns before editing:
   - `core/base_page.py`
   - `core/browser_manager.py`
   - `core/conftest.py`
   - nearby `pages/*_manager.py`
   - nearby `tests/test_*_page.py`
   - relevant `data/*.yaml`

2. Build or update YAML first:
   - Put `url` at the top as a path only, for example `/login` or `/orders?status=pending`.
   - Put environment host prefixes in `config/config.yaml` as `base_url`.
   - Do not write full URLs such as `https://example.com/login` in page YAML files.
   - Put selectors under `locators`.
   - Prefer stable Playwright selectors, CSS selectors, role/text selectors, and XPath only when useful.
   - Use descriptive locator keys such as `search_input`, `submit_button`, `table_rows`, `toast_message`, `form_error`.
   - Include success and failure observation locators needed by assertions.

3. Build or update the page manager:
   - Inherit from `BasePage`.
   - Read YAML with `YamlManager`.
   - Store locators on the instance.
   - Read `base_url` from `config/config.yaml` or reuse `LoginPage.base_url`.
   - Build the full page URL in `__init__` with `build_url(base_url, path)` and store it on the instance.
   - Business methods should open the already-built instance URL and should not call `build_url()` inside each action method.
   - Add a private selector helper, for example `_selector(self, key: str)`.
   - Keep low-level clicks/fills inside private helpers when repeated.
   - Expose business methods that return assertion-friendly values: `str | None`, `bool`, `int`, URL strings, or structured dicts when needed.
   - For authenticated pages, reuse `LoginPage.refresh_cookies()` and `add_cookies()` like `PatientsPage`.
   - Raise clear `RuntimeError` for missing required locators.

4. Build or update pytest cases:
   - Use `BrowserManager` in a pytest fixture and close it after `yield`.
   - Instantiate the page manager in the fixture.
   - Use `CSVManager` only when data-driven cases are needed or already established.
   - Keep assertions in tests, not in page managers.
   - Match the user-provided assertion standard exactly.
   - Add failure messages that show actual and expected values.

5. Add Allure reporting:
   - Add `@allure.feature("<Feature>")` on the test class.
   - Add `@allure.story("<Story>")` on each test.
   - Use `allure.dynamic.title(...)` for parameterized cases.
   - Let `core/conftest.py` handle failure screenshots and Allure attachments.

## Assertion Contracts

Choose the page manager return type from the assertion standard:

- Text validation: return collected page text or first visible validation error.
- URL navigation: return `self.driver.url` after waiting for expected URL state.
- Search/filter: return `True` when visible results satisfy the condition, `False` otherwise.
- Pagination/count: return an integer element count.
- Creation/update side effect: return URL, toast text, row presence boolean, or a structured summary.

Avoid asserting inside page manager methods unless the user explicitly asks for lower-level self-checking helpers.

## Allure And Execution

The standard report path is:

- pytest writes raw results with `--alluredir reports/results`.
- `run_tests.py` generates HTML into `reports/html`.
- Failed tests are screenshotted by `core/conftest.py` when a fixture exposes a page manager with `take_screenshot()` or a Playwright page with `screenshot()`.

When adding tests, make sure fixture objects are visible to pytest so the failure hook can find a screenshot target.

## Guardrails

- Do not hard-code credentials or cookies in tests.
- Do not duplicate selectors across page managers and tests.
- Do not create one-off helper frameworks when `BasePage`, `BrowserManager`, `YamlManager`, `CSVManager`, and `Logger` already cover the need.
- Do not rename existing files unless the user asks for a rename; for new page managers, always use `*_manager.py`.
- Do not commit refreshed cookies unless explicitly requested.
- Note side effects when tests create or mutate real remote data.
