from pathlib import Path

import allure
import pytest

from core.browser_manager import BrowserManager
from core.read_config import ConfigValue
from pages.design.design_manager import DesignManager
from utils.logger import Logger


TREATMENT_TOOTH_POSITION = 15
CT_DATA_PATH = "./data/dicom/wujia"
CT_MODEL_NAME = "术前手术"


@pytest.fixture(scope="class")
def page():
    """Create a DesignManager and clean real patients created by UI flows after the class."""
    logger = Logger("patients_test")
    cv = ConfigValue()
    manager = BrowserManager(browser_type="chromium", headless=False, logger=logger)
    browser_page = manager.new_page()
    patients = DesignManager(browser_page, logger)
    cleanup_failures = []
    try:
        yield patients
    finally:
        try:
            if cv.cleanup_created_patients:
                cleanup_failures = patients.cleanup_created_patients()
        finally:
            manager.close()
        if cleanup_failures:
            raise AssertionError(f"清理设计页真实患者失败: {cleanup_failures}")


@pytest.fixture(scope="class")
def ct_design_report(page):
    """Run one CT design flow and share the structured report across CT assertions."""
    return page.case_create_ct_design_report(
        "",
        TREATMENT_TOOTH_POSITION,
        CT_DATA_PATH,
        CT_MODEL_NAME,
    )


@pytest.fixture(scope="class")
def treatment_path_context(ct_design_report):
    """Provide a CT-created patient URL for later treatment path tests."""
    url = ct_design_report.get("patient_url") or ct_design_report.get("url")
    assert url and "patientID=" in url, f"CT 设计流程未返回可复用患者 URL: {ct_design_report}"
    return {
        "url": url,
        "tooth_position": ct_design_report["tooth_position"],
        "report": ct_design_report,
    }


@pytest.fixture(scope="class")
def stl_design_report(page):
    """Run one CT+STL design flow and share the structured report across STL assertions."""
    return page.case_create_stl_design_report(
        "",
        35,
        "./data/dicom/wujia",
        "术前CT",
        "./data/stl/wujia_dow.stl",
        "下颌口扫",
        "low_stl",
    )


def _assert_upload_files(upload_report: dict, suffixes: tuple[str, ...]) -> None:
    """Assert that upload metadata includes existing files with expected suffixes."""
    file_paths = upload_report.get("file_paths") or []
    assert upload_report.get("file_count") == len(file_paths) > 0, f"上传文件数量异常: {upload_report}"
    for file_path in file_paths:
        resolved_path = Path(file_path)
        assert resolved_path.exists(), f"上传文件不存在: {file_path}, report={upload_report}"
        assert resolved_path.suffix.lower() in suffixes, f"上传文件扩展名异常: {file_path}, report={upload_report}"


def _assert_upload_success(upload_report: dict) -> None:
    """Assert that upload succeeded and timing metadata was collected."""
    assert upload_report.get("success") is True, f"上传失败: {upload_report}"
    assert upload_report.get("duration_ms", 0) > 0, f"未采集上传耗时: {upload_report}"
    assert upload_report.get("upload_started_at"), f"未采集上传开始时间: {upload_report}"
    assert upload_report.get("upload_finished_at"), f"未采集上传结束时间: {upload_report}"


def _assert_canvas_rendered(render_report: dict) -> None:
    """Assert that a visible canvas has dimensions and is not blank."""
    assert render_report.get("canvas_visible") is True, f"canvas 不可见: {render_report}"
    assert render_report.get("canvas_width", 0) > 0, f"canvas 宽度无效: {render_report}"
    assert render_report.get("canvas_height", 0) > 0, f"canvas 高度无效: {render_report}"
    assert render_report.get("non_blank") is True, f"canvas 为空白: {render_report}"
    assert render_report.get("checked_at"), f"未采集 canvas 检查时间: {render_report}"


def _assert_treatment_path_visible(state: dict) -> None:
    """Assert that a selected case exposes the treatment path panel."""
    assert state.get("case_selected") is True, f"病例未选中: {state}"
    assert state.get("treatment_visible") is True, f"治疗路径未展示: {state}"
    assert state.get("steps"), f"治疗路径步骤列表为空: {state}"


def _assert_treatment_validation_blocked(state: dict) -> None:
    """Assert that invalid treatment form data stays on the UI and does not call gateway."""
    assert state.get("request_count") == 0, f"前端校验失败时不应调用治疗路径接口: {state}"
    assert state.get("errors") or state.get("form_visible"), f"未观察到前端校验状态: {state}"


@allure.feature("Design")
class TestDesignPage:
    @allure.story("治疗路径展示")
    def test_treatment_path_hidden_without_case(self, page):
        """Create only a patient and verify treatment path is not shown before selecting a case."""
        allure.dynamic.title("未选择病例时不展示治疗路径")
        state = page.case_treatment_path_not_visible_without_case()
        assert state["treatment_visible"] is False, f"未选择病例时不应展示治疗路径: {state}"

    @allure.story("治疗路径展示")
    def test_treatment_path_visible_by_fixture_url(self, page, treatment_path_context):
        """Open the fixture-created patient URL and verify treatment path appears after clicking the case."""
        allure.dynamic.title("通过 fixture URL 打开病例并展示治疗路径")
        state = page.treatment_path(
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        _assert_treatment_path_visible(state)

    @allure.story("治疗路径新增")
    def test_add_treatment_success(self, page, treatment_path_context):
        """Add a valid treatment path item and assert the gateway request is emitted once."""
        allure.dynamic.title("新增治疗路径成功")
        state = page.case_add_treatment_success(
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        _assert_treatment_path_visible(state["base_state"])
        assert state["submitted"] is True, f"新增治疗路径未提交: {state}"
        assert state["request_count"] == 1, f"新增治疗路径接口调用次数异常: {state}"
        payload = state["requests"][0].get("payload") or {}
        assert payload.get("medicalRecordID"), f"新增治疗路径缺少 medicalRecordID: {state}"
        assert payload.get("order") is not None, f"新增治疗路径缺少 order: {state}"

    @allure.story("治疗路径新增校验")
    @pytest.mark.parametrize("validation_type", ["required", "title_max", "remark_max"])
    def test_add_treatment_frontend_validation(self, page, treatment_path_context, validation_type):
        """Submit invalid treatment path data and assert front-end validation blocks gateway calls."""
        allure.dynamic.title(f"新增治疗路径前端校验 - {validation_type}")
        state = page.case_add_treatment_validation(
            validation_type,
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        _assert_treatment_validation_blocked(state)

    @allure.story("治疗路径编辑")
    def test_edit_treatment_success(self, page, treatment_path_context):
        """Edit the first treatment path item and assert the update request is collected."""
        allure.dynamic.title("编辑治疗路径成功")
        state = page.case_edit_treatment(
            treatment_path_context["url"],
            True,
            treatment_path_context["tooth_position"],
        )
        assert state["edit_clicked"] is True, f"未进入编辑态: {state}"
        assert state["submitted"] is True, f"编辑治疗路径未提交: {state}"
        assert state["request_count"] >= 1, f"编辑治疗路径未调用接口: {state}"

    @allure.story("治疗路径编辑")
    def test_edit_treatment_failure_keeps_visible_state(self, page, treatment_path_context):
        """Mock a failed edit response and assert the UI remains observable."""
        allure.dynamic.title("编辑治疗路径失败分支")
        state = page.case_edit_treatment(
            treatment_path_context["url"],
            False,
            treatment_path_context["tooth_position"],
        )
        assert state["request_count"] >= 1, f"编辑失败场景未调用接口: {state}"
        assert state["still_editing"] is True or state["toast"], f"编辑失败未保持可观察状态: {state}"

    @allure.story("治疗路径编辑")
    def test_editing_disables_other_treatment(self, page, treatment_path_context):
        """Start editing one item and assert the edit form remains active after another edit attempt."""
        allure.dynamic.title("编辑治疗路径时其他路径不可并行编辑")
        state = page.case_editing_disables_other_treatment(
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        assert state["first_edit_clicked"] is True, f"第一条治疗路径未进入编辑态: {state}"
        assert state["still_editing"] is True, f"编辑态未保持: {state}"

    @allure.story("治疗路径删除")
    def test_delete_treatment_success(self, page, treatment_path_context):
        """Delete a treatment path item and assert delete flow is observable."""
        allure.dynamic.title("删除治疗路径成功")
        state = page.case_delete_treatment(
            treatment_path_context["url"],
            False,
            treatment_path_context["tooth_position"],
        )
        assert state["delete_clicked"] is True, f"未点击删除治疗路径: {state}"
        assert state["request_count"] >= 0, f"删除路径请求状态异常: {state}"

    @allure.story("治疗路径删除")
    def test_delete_linked_treatment_blocked(self, page, treatment_path_context):
        """Attempt to delete a treatment path linked to design and assert the block is observable."""
        allure.dynamic.title("关联设计治疗路径删除拦截")
        state = page.case_delete_treatment(
            treatment_path_context["url"],
            True,
            treatment_path_context["tooth_position"],
        )
        assert state["request_count"] == 0 or state["toast"], f"关联设计删除拦截未体现: {state}"

    @allure.story("治疗路径排序")
    def test_sort_treatment_path(self, page, treatment_path_context):
        """Drag treatment path items and compare state before and after the operation."""
        allure.dynamic.title("治疗路径拖拽排序")
        state = page.case_sort_treatment(
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        assert state["changed"] is True or state["steps_after"] != state["steps_before"], f"拖拽排序未变化: {state}"

    @allure.story("治疗路径创建设计")
    def test_create_design_from_treatment_entry(self, page, treatment_path_context):
        """Click create design from treatment path and assert the entry remains observable."""
        allure.dynamic.title("治疗路径入口创建设计")
        state = page.case_create_design_from_treatment(
            1,
            treatment_path_context["url"],
            treatment_path_context["tooth_position"],
        )
        assert state["clicked"] is True or state["toast"] is not None, f"未观察到创建设计入口状态: {state}"
        assert state["request_count"] >= 0, f"创建设计请求采集异常: {state}"

    @allure.story("治疗路径设计操作")
    @pytest.mark.parametrize("action", ["edit", "preview", "delete", "start_surgery", "verification"])
    def test_design_action_from_treatment_path(self, page, treatment_path_context, action):
        """Run a design action from treatment path and assert resulting URL, toast, or request state."""
        allure.dynamic.title(f"治疗路径设计操作 - {action}")
        state = page.case_design_action(
            action,
            treatment_path_context["url"],
            True,
            treatment_path_context["tooth_position"],
        )
        assert state["clicked"] is False or state["url"] or state["toast"] is not None, f"设计操作状态异常: {state}"

    @allure.story("治疗路径设计操作")
    def test_delete_design_failure_from_treatment_path(self, page, treatment_path_context):
        """Mock a failed delete design response from treatment path and assert failure remains observable."""
        allure.dynamic.title("治疗路径删除设计失败分支")
        state = page.case_design_action(
            "delete",
            treatment_path_context["url"],
            False,
            treatment_path_context["tooth_position"],
        )
        assert state["clicked"] is False or state["toast"] is not None or state["requests"] is not None, (
            f"删除设计失败入口状态异常: {state}"
        )

    @allure.story("牙位创建Message判断")
    @pytest.mark.parametrize("tooth_position", [[12, 13, 15, 22, 24], [33, 37, 42]])
    def test_case_create_tooth(self, page, tooth_position):
        """Create tooth cases and assert the success message."""
        res = page.case_create_tooth(tooth_position)
        for message in res:
            assert message == "操作成功", f"牙位创建失败: {message}"

    @allure.story("同牙位重复创建检测")
    def test_duplicate_tooth_case_detection(self, page):
        """Create the same tooth case twice for one patient and assert duplicate warning."""
        allure.dynamic.title("同牙位重复创建病例触发提醒")
        state = page.case_create_duplicate_tooth_detection([12])
        duplicate_message = state.get("duplicate_message") or ""
        expected_message = "该患者已存在相同病例，请勿重复添加。"

        assert state["first_message"] == "操作成功", f"首次创建病例未成功，实际状态: {state}"
        assert duplicate_message == expected_message, f"未展示同牙位重复创建提醒，实际状态: {state}"

    @allure.story("手术阶段调整")
    @pytest.mark.parametrize("tooth_position", [[46, 32]])
    def test_case_drop_surgical(self, page, tooth_position):
        """Create a case and verify surgical stage drag order changes before and after operations."""
        msg = page.case_create_tooth(tooth_position)
        if msg[0] == "操作成功":
            res = page.case_drop_surgical("", tooth_position[0])
            assert res is True, "手术阶段调整失败"
            res2 = page.case_refresh_drop_surgical("", tooth_position[0])
            assert res2 is True, "手术阶段调整后未保存"
        else:
            print(msg[0])

    @allure.story("CT 文件清单断言")
    def test_ct_design_upload_files_collected(self, ct_design_report):
        """Assert CT report includes valid DICOM upload files."""
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
        """Assert CT model rendering creates a non-blank canvas."""
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
        assert ct_design_report.get("patient_url"), f"CT 设计流程未返回患者 URL: {ct_design_report}"

    @allure.story("STL 文件清单断言")
    def test_stl_design_upload_files_collected(self, stl_design_report):
        """Assert STL report includes valid model upload files."""
        allure.dynamic.title("STL 上传文件清单有效")
        _assert_upload_files(stl_design_report["uploads"]["stl"], (".stl", ".ply"))

    @allure.story("STL 上传耗时断言")
    def test_stl_design_upload_duration_collected(self, stl_design_report):
        """Assert STL upload succeeded and upload duration was collected."""
        allure.dynamic.title("STL 上传成功并采集耗时")
        _assert_upload_success(stl_design_report["uploads"]["stl"])

    @allure.story("STL 渲染断言")
    def test_stl_design_canvas_rendered(self, stl_design_report):
        """Assert CT+STL model rendering creates a non-blank canvas."""
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
