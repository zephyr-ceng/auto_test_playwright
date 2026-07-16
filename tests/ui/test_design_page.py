import allure
import pytest
from pathlib import Path

from core.browser_manager import BrowserManager
from core.read_config import ConfigValue
from utils.logger import Logger
from pages.design_manager import DesignManager


@pytest.fixture(scope="class")
def page():
    logger = Logger("patients_test")
    cv = ConfigValue()
    # manager = BrowserManager(browser_type="chromium", headless=True, logger=logger, remote_url=cv.remote_url)
    manager = BrowserManager(browser_type="chromium", headless=False, logger=logger)
    # browser_page = manager.start()
    browser_page = manager.new_page()
    patients = DesignManager(browser_page, logger)
    yield patients
    manager.close()


@pytest.fixture(scope="class")
def ct_design_report(page):
    """Run one CT design flow and share its structured report across assertion cases."""
    return page.case_create_ct_design_report(
        '',
        15,
        "./data/dicom/wujia",
        "术前手术",
    )


@pytest.fixture(scope="class")
def stl_design_report(page):
    """Run one CT+STL design flow and share its structured report across assertion cases."""
    return page.case_create_stl_design_report(
        '',
        35,
        "./data/dicom/wujia",
        "术前CT",
        "./data/stl/wujia_dow.stl",
        "下颌口扫",
        "low_stl",
    )


def _assert_upload_files(upload_report: dict, suffixes: tuple[str, ...]) -> None:
    """Assert upload file metadata collected by the page object is complete."""
    file_paths = upload_report.get("file_paths") or []
    assert upload_report.get("file_count") == len(file_paths) > 0, f"上传文件数量异常: {upload_report}"
    for file_path in file_paths:
        resolved_path = Path(file_path)
        assert resolved_path.exists(), f"上传文件不存在: {file_path}, report={upload_report}"
        assert resolved_path.suffix.lower() in suffixes, f"上传文件扩展名异常: {file_path}, report={upload_report}"


def _assert_upload_success(upload_report: dict) -> None:
    """Assert upload succeeded and upload duration was collected."""
    assert upload_report.get("success") is True, f"上传失败: {upload_report}"
    assert upload_report.get("duration_ms", 0) > 0, f"未采集上传耗时: {upload_report}"
    assert upload_report.get("upload_started_at"), f"未采集上传开始时间: {upload_report}"
    assert upload_report.get("upload_finished_at"), f"未采集上传结束时间: {upload_report}"


def _assert_canvas_rendered(render_report: dict) -> None:
    """Assert visible canvas has dimensions and non-blank pixels."""
    assert render_report.get("canvas_visible") is True, f"canvas 不可见: {render_report}"
    assert render_report.get("canvas_width", 0) > 0, f"canvas 宽度无效: {render_report}"
    assert render_report.get("canvas_height", 0) > 0, f"canvas 高度无效: {render_report}"
    assert render_report.get("non_blank") is True, f"canvas 为空白: {render_report}"
    assert render_report.get("checked_at"), f"未采集 canvas 检查时间: {render_report}"


@allure.feature("Design ")
class TestDesignPage:
    @allure.story("牙位创建Message判断")
    @pytest.mark.parametrize("tooth_position", [[12, 13, 15, 22, 24], [33, 37, 42]])
    def test_case_create_tooth(self, page, tooth_position):
        res = page.case_create_tooth(tooth_position)
        for i in res:
            assert i == '操作成功', f"牙位创建失败{i}"

    @allure.story("手术阶段调整")
    @pytest.mark.parametrize("tooth_position", [[46, 32]])
    def test_case_drop_surgical(self, page, tooth_position):
        msg = page.case_create_tooth(tooth_position)
        if msg[0] == '操作成功':
            res = page.case_drop_surgical('', tooth_position[0])
            assert res is True, f"手术阶段调整失败"
            res2 = page.case_refresh_drop_surgical('', tooth_position[0])
            assert res2 is True, f"手术阶段调整后未保存"  # 实际结果需要为True,
        else:
            print(msg[0])

    @allure.story("CT 文件清单断言")
    def test_ct_design_upload_files_collected(self, ct_design_report):
        """Assert the CT report contains valid DICOM upload files."""
        allure.dynamic.title("CT 上传文件清单有效")
        _assert_upload_files(ct_design_report["uploads"]["ct"], (".dcm",))

    @allure.story("CT 上传耗时断言")
    def test_ct_design_upload_duration_collected(self, ct_design_report):
        """Assert CT upload succeeded and upload duration was collected."""
        allure.dynamic.title("CT 上传成功并采集耗时")
        _assert_upload_success(ct_design_report["uploads"]["ct"])

    @allure.story("CT AI 分割断言")
    def test_ct_design_ai_segmentation_collected(self, ct_design_report):
        """Assert CT AI segmentation status and duration were collected."""
        allure.dynamic.title("CT AI 分割成功并采集耗时")
        ai_report = ct_design_report["ai"]["ct"]
        assert ai_report.get("success") is True, f"AI 分割未成功: {ai_report}"
        assert ai_report.get("final_status") == 2, f"AI 分割终态不是 2: {ai_report}"
        assert 2 in (ai_report.get("observed_statuses") or []), f"AI 分割状态未包含 2: {ai_report}"
        assert ai_report.get("duration_ms", 0) > 0, f"未采集 AI 分割耗时: {ai_report}"

    @allure.story("CT 渲染断言")
    def test_ct_design_canvas_rendered(self, ct_design_report):
        """Assert CT model rendering produces a non-blank canvas."""
        allure.dynamic.title("CT canvas 非空渲染")
        _assert_canvas_rendered(ct_design_report["render"]["ct"])

    @allure.story("CT 完整设计状态断言")
    def test_ct_design_case_and_final_status(self, ct_design_report):
        """Assert CT case creation, treatment path, design creation, and final status."""
        allure.dynamic.title("CT 病例与最终设计状态有效")
        case_report = ct_design_report["case"]
        design_report = ct_design_report["design"]
        assert case_report.get("created_tooth_position") == ct_design_report["tooth_position"], (
            f"CT 病例牙位创建异常: {ct_design_report}"
        )
        assert case_report.get("treatment_path_ready") is True, f"CT 治疗路径未就绪: {ct_design_report}"
        assert design_report.get("created") is True, f"CT 设计未创建: {ct_design_report}"
        assert design_report.get("progress_duration_ms", 0) > 0, f"未采集 CT 创建设计耗时: {ct_design_report}"
        assert design_report.get("ready") is True, f"CT 设计工具未就绪: {ct_design_report}"
        assert design_report.get("final_search_success") is True, f"CT 最终设计状态查询失败: {ct_design_report}"

    @allure.story("STL 文件清单断言")
    def test_stl_design_upload_files_collected(self, stl_design_report):
        """Assert the STL report contains valid model upload files."""
        allure.dynamic.title("STL 上传文件清单有效")
        _assert_upload_files(stl_design_report["uploads"]["stl"], (".stl", ".ply"))

    @allure.story("STL 上传耗时断言")
    def test_stl_design_upload_duration_collected(self, stl_design_report):
        """Assert STL upload succeeded and upload duration was collected."""
        allure.dynamic.title("STL 上传成功并采集耗时")
        _assert_upload_success(stl_design_report["uploads"]["stl"])

    @allure.story("STL 渲染断言")
    def test_stl_design_canvas_rendered(self, stl_design_report):
        """Assert CT+STL model rendering produces a non-blank canvas."""
        allure.dynamic.title("STL canvas 非空渲染")
        _assert_canvas_rendered(stl_design_report["render"]["stl"])

    @allure.story("CT+STL 完整设计状态断言")
    def test_stl_design_case_and_final_status(self, stl_design_report):
        """Assert CT+STL case creation, design creation, and final status."""
        allure.dynamic.title("CT+STL 病例与最终设计状态有效")
        case_report = stl_design_report["case"]
        design_report = stl_design_report["design"]
        assert case_report.get("created_tooth_position") == stl_design_report["tooth_position"], (
            f"CT+STL 病例牙位创建异常: {stl_design_report}"
        )
        assert case_report.get("treatment_path_ready") is True, f"CT+STL 治疗路径未就绪: {stl_design_report}"
        assert design_report.get("created") is True, f"CT+STL 设计未创建: {stl_design_report}"
        assert design_report.get("progress_duration_ms", 0) > 0, f"未采集 CT+STL 创建设计耗时: {stl_design_report}"
        assert design_report.get("ready") is True, f"CT+STL 设计工具未就绪: {stl_design_report}"
        assert design_report.get("final_search_success") is True, f"CT+STL 最终设计状态查询失败: {stl_design_report}"
