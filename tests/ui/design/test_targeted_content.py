import asyncio
import time
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.async_api import Page, async_playwright, expect

from utils.csv_manager import CSVManager


async def _registration_context_ready(page: Page) -> bool:
    """Return True when registration can be started or is already in progress."""
    start_button = page.get_by_role("button", name="开始配准")
    retry_button = page.get_by_role("button", name="重新配准")
    patient_label = page.locator("xpath=//span[normalize-space(.)='姓名:' or normalize-space(.)='姓名：']")
    implant_label = page.locator("xpath=//span[normalize-space(.)='植体:' or normalize-space(.)='植体：']")

    for locator in (start_button, retry_button):
        try:
            if await locator.count() > 0 and await locator.is_visible(timeout=200):
                return True
        except Exception:
            continue

    return await patient_label.count() > 0 and await implant_label.count() > 0


async def _wait_for_registration_context(page: Page, timeout_ms: int = 10_000) -> None:
    """Wait for the registration page to expose its start/progress/patient state."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if await _registration_context_ready(page):
            return
        await page.wait_for_timeout(500)
    raise RuntimeError("模型解析完成后未出现配准入口或患者/植体信息")


async def _wait_for_model_parse_progress(page: Page, timeout_ms: int = 180_000) -> None:
    """Wait until model parsing progress finishes and the registration entry is ready."""
    progressbar = page.locator("[role='progressbar']")

    start_time = time.time()
    deadline = start_time + timeout_ms / 1000
    progress_was_visible = False
    last_progress = ""

    while time.time() < deadline:
        visible_progressbar = None
        for index in range(await progressbar.count()):
            current_progressbar = progressbar.nth(index)
            try:
                if await current_progressbar.is_visible(timeout=200):
                    visible_progressbar = current_progressbar
                    break
            except Exception:
                continue

        if visible_progressbar is not None:
            progress_was_visible = True
            try:
                progress_value = await visible_progressbar.get_attribute("aria-valuenow", timeout=1_000) or ""
            except Exception:
                await page.wait_for_timeout(200)
                continue

            try:
                progress_number = float(progress_value)
            except ValueError:
                progress_number = 0.0

            progress_label = f"模型解析中 - {progress_value}%" if progress_value else "模型解析中"

            if progress_label != last_progress:
                # print(f"模型解析进度: {progress_label}")
                last_progress = progress_label

            if progress_number >= 100:
                await _wait_for_registration_context(page)
                return

            await page.wait_for_timeout(500)
            continue

        if progress_was_visible:
            await _wait_for_registration_context(page)
            return

        if time.time() - start_time >= 1 and await _registration_context_ready(page):
            return

        await page.wait_for_timeout(500)

    raise RuntimeError("模型解析进度等待超时，未出现可点击的开始配准按钮")


async def _value_after_span_label(page: Page, label: str) -> str:
    """Read text from the value span immediately after labels like `姓名:` or `植体:`."""
    value_locator = page.locator(
        "xpath="
        f"//span[normalize-space(.)='{label}:' or normalize-space(.)='{label}：']"
        "/following-sibling::span[1]"
    ).first
    await expect(value_locator).to_be_attached(timeout=10_000)
    return (await value_locator.inner_text(timeout=5_000)).strip()


async def _implant_info_text(page: Page) -> str:
    """Read implant text from the value span or from the label container lines."""
    implant_info = await _value_after_span_label(page, "植体")
    if implant_info:
        return implant_info

    implant_container = page.locator(
        "xpath="
        "//span[normalize-space(.)='植体:' or normalize-space(.)='植体：']"
        "/ancestor::div[contains(@class, 'items-center')][1]"
    ).first
    await expect(implant_container).to_be_visible(timeout=10_000)

    raw_text = await implant_container.inner_text(timeout=5_000)
    lines = [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip() and line.strip() not in ("植体:", "植体：")
    ]
    return " ".join(lines)


def _patient_id_from_url(url: str) -> str:
    """Extract patientID query value from the current registration URL."""
    query_params = parse_qs(urlparse(url).query)
    return query_params.get("patientID", [""])[0]


def _write_registration_info_csv(current_url: str, patient_name: str, implant_info: str) -> str:
    """Append registration page patient and implant information to CSV."""
    patient_id = _patient_id_from_url(current_url)
    if not patient_id:
        raise RuntimeError(f"patientID为空，当前页面URL: {current_url}")

    csv_manager = CSVManager("targeted_registration_info.csv")
    csv_path = csv_manager.append_row(
        values=[current_url, patient_id, patient_name, implant_info],
        fieldnames=["当前页面URL", "patientID", "患者姓名", "植体信息"],
    )
    # print(f"写入CSV: {csv_path}")
    # print(f"patientID: {patient_id}")
    return patient_id


async def _run_targeted_content_case(run_index: int) -> None:
    """Run one targeted content registration workflow."""
    print(f"执行第 {run_index}/99 次", flush=True)
    playwright = await async_playwright().start()
    browser = None
    context = None
    page = None
    try:
        print("正在连接远程浏览器: ws://192.168.3.120:3000/?browser=chromium", flush=True)
        browser = await asyncio.wait_for(
            playwright.chromium.connect("ws://192.168.3.120:3000/?browser=chromium"),
            timeout=30,
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        print("远程浏览器连接成功", flush=True)
        await page.wait_for_timeout(1000)
        await page.goto("http://localhost/login")
        print(page.url)
        await page.screenshot(path="screenshot.png")
        await page.get_by_role("combobox", name="请输入用户名").click()
        await page.get_by_role("combobox", name="请输入用户名").fill("finetool_test")
        await page.get_by_role("combobox", name="请输入用户名").press("Tab")
        await page.get_by_role("textbox", name="请输入密码").fill("123456")
        await page.get_by_role("button", name="登 录").click()
        await page.get_by_text("设计管理").click()
        await page.locator("#status").click()
        await page.get_by_title("手术中").nth(3).click()
        await page.get_by_role("button", name="查询").click()
        await page.get_by_role("button", name="开始手术").nth(1).click()
        await page.get_by_role("button", name="确 定").click()
        await _wait_for_model_parse_progress(page)

        registration_url = page.url
        # print(f"开始配准前页面URL: {registration_url}")
        start_registration_button = page.get_by_role("button", name="开始配准")
        if await start_registration_button.count() > 0 and await start_registration_button.is_visible(timeout=1_000):
            await start_registration_button.click()
        else:
            print("开始配准按钮未显示，当前已处于配准流程，跳过点击")
        patient_name = await _value_after_span_label(page, "姓名")
        implant_info = await _implant_info_text(page)
        # print(f"患者姓名: {patient_name}")
        # print(f"植体信息: {implant_info}")
        assert patient_name, "患者姓名为空"
        assert implant_info, "植体信息为空"
        _write_registration_info_csv(registration_url, patient_name, implant_info)
        await page.get_by_role("button", name="回到首页").click()
        await page.get_by_text("设计管理").click()
        await page.locator("#status").click()
        await page.get_by_text("手术中").nth(3).click()
        await page.get_by_role("button", name="查询").click()
        await page.get_by_role("button", name="开始手术").nth(3).click()
        await page.get_by_role("button", name="确 定").click()
        await _wait_for_model_parse_progress(page)

        registration_url2 = page.url
        # print(f"开始配准前页面URL: {registration_url2}")
        start_registration_button = page.get_by_role("button", name="开始配准")
        if await start_registration_button.count() > 0 and await start_registration_button.is_visible(timeout=1_000):
            await start_registration_button.click()
        else:
            print("开始配准按钮未显示，当前已处于配准流程，跳过点击")
        patient_name2 = await _value_after_span_label(page, "姓名")
        implant_info2 = await _implant_info_text(page)
        assert patient_name2, "患者姓名为空"
        assert implant_info2, "植体信息为空"
        _write_registration_info_csv(registration_url2, patient_name2, implant_info2)
    finally:
        if page and not page.is_closed():
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()
        await playwright.stop()


@pytest.mark.parametrize("run_index", range(1, 100), ids=lambda index: f"run_{index:02d}")
def test_example(run_index: int) -> None:
    asyncio.run(_run_targeted_content_case(run_index))


if __name__ == "__main__":
    for run_index in range(1, 100):
        asyncio.run(_run_targeted_content_case(run_index))
