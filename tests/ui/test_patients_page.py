from pathlib import Path

import allure
import pytest

from core.browser_manager import BrowserManager
from core.read_config import ConfigValue
from pages.patient_manager import PatientsPage
from utils.csv_manager import CSVManager
from utils.logger import Logger
from utils.random_manager import RandomManager

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREATE_PATIENT_CASE_CSV = PROJECT_ROOT / "data" / "rule" / "patient_manager" / "create_patient_form_case.csv"


def _load_create_patient_ui_cases() -> list[dict]:
    """读取新建患者表单规则 CSV 中标记为 UI 自动化的用例。"""
    rows = CSVManager(str(CREATE_PATIENT_CASE_CSV)).read_csv()
    return [row for row in rows if row.get("自动化类型") == "UI自动化"]


CREATE_PATIENT_UI_CASES = _load_create_patient_ui_cases()
CREATE_PATIENT_CASE_BY_ID = {case["用例编号"]: case for case in CREATE_PATIENT_UI_CASES}


def _case(case_id: str) -> dict:
    case = CREATE_PATIENT_CASE_BY_ID.get(case_id)
    if case is None:
        raise KeyError(f"missing create patient UI case: {case_id}")
    return case


def _random_name_text(length: int) -> str:
    """生成指定长度的随机姓名测试文本。"""
    return RandomManager.random_common_chars(length)


def _random_remark_text(length: int) -> str:
    """生成指定长度的随机备注测试文本。"""
    return RandomManager.random_common_chars(length)


def _random_phone_text(length: int) -> str:
    """生成指定长度的随机电话测试文本。"""
    return RandomManager.random_digits(length)


@pytest.fixture(scope="class")
def page():
    """创建患者管理页对象，供 UI 用例复用同一个浏览器会话。"""
    log = Logger("patients_test")
    cv = ConfigValue()
    manager = BrowserManager(browser_type="chromium", headless=True, logger=log, remote_url=cv.remote_url)
    browser_page = manager.new_page()
    patients = PatientsPage(browser_page, log)
    yield patients
    manager.close()


@allure.feature("Patients")
class TestPatientsPage:
    @allure.story("Create Patient Modal")
    def test_open_create_patient_modal(self, page):
        """UI-CP-001：打开新建患者弹窗。"""
        case = _case("UI-CP-001")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.open_create_patient_modal()
        assert state["opened"] is True, f"新建患者弹窗未打开，实际状态: {state}"
        assert state["title_visible"] is True, f"未展示新建患者信息标题，实际状态: {state}"

    @allure.story("Create Patient Modal")
    def test_create_patient_form_elements(self, page):
        """UI-CP-002：新建患者弹窗基础元素展示。"""
        case = _case("UI-CP-002")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.get_create_patient_form_state()
        assert state["modal_open"] is True, f"新建患者弹窗未打开，实际状态: {state}"
        assert state["title_visible"] is True, f"未展示弹窗标题，实际状态: {state}"
        assert state["name_present"] is True, f"未找到姓名输入框，实际状态: {state}"
        assert state["birthday_present"] is True, f"未找到生日输入框，实际状态: {state}"
        assert state["phone_present"] is True, f"未找到电话号码输入框，实际状态: {state}"
        assert state["remark_present"] is True, f"未找到备注输入框，实际状态: {state}"
        assert state["gender_count"] >= 2, f"性别选项数量不足，实际状态: {state}"
        assert state["submit_present"] is True, f"未找到确定按钮，实际状态: {state}"
        assert state["cancel_present"] is True, f"未找到取消按钮，实际状态: {state}"
        assert state["name_placeholder"] == "请输入姓名", f"姓名占位符不符合预期，实际状态: {state}"
        assert state["phone_placeholder"] == "请输入电话号码", f"电话占位符不符合预期，实际状态: {state}"
        assert state["remark_placeholder"] == "请输入备注信息", f"备注占位符不符合预期，实际状态: {state}"

    @allure.story("Create Patient Validation")
    @pytest.mark.parametrize(
        "case_id,patient_data,expected_error",
        [
            ("UI-CP-003", {"name": ""}, "请填写患者姓名"),
            ("UI-CP-004", {"name": _random_name_text(201)}, "姓名最多输入200个字符"),
            ("UI-CP-011", {"name": "自动化患者", "remark": _random_remark_text(4097)}, "备注最多4096个字符"),
        ],
        ids=["name_required", "name_max_200", "remark_max_4096"],
    )
    def test_create_patient_frontend_validation(self, page, case_id, patient_data, expected_error):
        """前端表单校验错误提示。"""
        case = _case(case_id)
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.submit_create_patient_form(**patient_data)
        assert expected_error in state["errors"], f"未展示预期错误 {expected_error}，实际状态: {state}"
        assert state["modal_open"] is True, f"前端校验失败后弹窗应保持打开，实际状态: {state}"

    @allure.story("Create Patient Validation")
    @pytest.mark.parametrize(
        "case_id,patient_data,unexpected_error",
        [
            ("UI-CP-006", {"name": "自动化患者"}, "请输入患者生日"),
            ("UI-CP-007", {"name": "自动化患者", "phone": ""}, "请输入患者手机号"),
            ("UI-CP-009", {"name": "自动化患者", "gender": ""}, "请选择患者性别"),
        ],
        ids=["birthday_optional", "phone_optional", "gender_optional"],
    )
    def test_create_patient_optional_fields_do_not_show_required_error(
            self,
            page,
            case_id,
            patient_data,
            unexpected_error,
    ):
        """生日、电话、性别为空时不展示必填错误。"""
        case = _case(case_id)
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.submit_create_patient_form(
            **patient_data,
            mock={"success": False, "message": "接口返回message"},
        )
        assert unexpected_error not in state["errors"], f"展示了不应出现的错误 {unexpected_error}，实际状态: {state}"
        assert "/createDesign" not in state["url"], f"失败 mock 不应跳转创建设计页，实际状态: {state}"

    @allure.story("Create Patient Validation")
    def test_create_patient_phone_max_length(self, page):
        """UI-CP-008：电话号码输入框最多允许 50 字符。"""
        case = _case("UI-CP-008")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.input_phone_and_get_state(_random_phone_text(51))
        assert state["maxlength"] == 50, f"电话输入框 maxlength 不符合预期，实际状态: {state}"
        assert state["length"] <= 50, f"电话输入实际长度超过 50，实际状态: {state}"

    @allure.story("Create Patient Validation")
    def test_create_patient_gender_toggle(self, page):
        """UI-CP-010：性别选项可切换。"""
        case = _case("UI-CP-010")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.toggle_gender_and_get_state()
        assert state["male_clicked"] is True, f"点击男性选项失败，实际状态: {state}"
        assert state["after_male"] == 0, f"点击男性后选中态不正确，实际状态: {state}"
        assert state["female_clicked"] is True, f"点击女性选项失败，实际状态: {state}"
        assert state["after_female"] == 1, f"点击女性后选中态不正确，实际状态: {state}"

    @allure.story("Create Patient Modal")
    def test_cancel_create_patient_modal_resets_form(self, page):
        """UI-CP-012：取消新建患者弹窗并重新打开后表单重置。"""
        case = _case("UI-CP-012")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.cancel_and_reopen_create_patient_form(
            name="自动化患者",
            phone="13800000000",
            remark="自动化备注",
        )
        assert state["closed"] is True, f"点击取消后弹窗未关闭，实际状态: {state}"
        assert state["reopened"] is True, f"未能重新打开弹窗，实际状态: {state}"
        assert state["name"] == "", f"姓名未重置，实际状态: {state}"
        assert state["phone"] == "", f"电话未重置，实际状态: {state}"
        assert state["remark"] == "", f"备注未重置，实际状态: {state}"

    @allure.story("Create Patient Success")
    @pytest.mark.parametrize(
        "case_id,name,mock_patient_id",
        [
            ("UI-CP-005", _random_name_text(200), "mock-ui-cp-005"),
            ("UI-CP-013", "自动化患者", "mock-ui-cp-013"),
        ],
        ids=["name_200_success", "create_success"],
    )
    def test_create_patient_success_with_mock(self, page, case_id, name, mock_patient_id):
        """mock 新建患者成功响应，校验成功提示和跳转地址。"""
        case = _case(case_id)
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        state = page.submit_create_patient_form(
            name=name,
            mock={"success": True, "patient_id": mock_patient_id},
        )
        assert "姓名最多输入200个字符" not in state["errors"], f"200 字符姓名不应展示长度错误，实际状态: {state}"
        assert state["toast"] == "新增患者成功", f"未展示新增患者成功提示，实际状态: {state}"
        assert "/createDesign" in state["url"], f"成功后未跳转创建设计页，实际状态: {state}"
        assert f"patientID={mock_patient_id}" in state["url"], f"URL 未包含 mock patientID，实际状态: {state}"

    @allure.story("Create Patient Failure")
    def test_create_patient_failure_with_mock(self, page):
        """UI-CP-014：mock 新建患者失败响应，展示接口 message 且不跳转。"""
        case = _case("UI-CP-014")
        allure.dynamic.title(f"{case['用例编号']} - {case['用例标题']}")
        expected_message = "接口返回message"
        state = page.submit_create_patient_form(
            name="失败患者",
            mock={"success": False, "message": expected_message},
        )
        assert state["toast"] == expected_message, f"未展示接口失败 message，实际状态: {state}"
        assert "/createDesign" not in state["url"], f"创建失败不应跳转创建设计页，实际状态: {state}"

    @allure.story("select page show number")
    @pytest.mark.parametrize("number", [10, 20, 50, 100])
    def test_count_patients(self, page, number):
        """ 单页面显示设计及患者数量 """
        allure.dynamic.title(f"每页显示数量为: {number}")
        count_pa = page.count_page_patients(number)
        count_de = page.count_page_designs(number)
        assert count_pa == number, f"并未查询到对应数据:实际值{count_pa} != 预设值{number}"
        assert count_de == number, f"并未查询到对应数据:实际值{count_pa} != 预设值{number}"

    @allure.story("select patients")
    @pytest.mark.parametrize("name,phone", [('test', '16666666666'), ('演示', ''), ("", "139")])
    def test_select_patients(self, page, name, phone):
        """查询患者信息。"""
        allure.dynamic.title(f"查询患者信息{name, phone}")
        res = page.search_patient(name, phone)
        assert res is True, "查询功能异常"

    @allure.story("select patients or design")
    @pytest.mark.parametrize("design_name,status", [('test', ''), ('张', '手术中')])
    def test_select_design(self, page, design_name, status):
        """查询指定患者设计。"""
        allure.dynamic.title(f"查询指定患者设计{design_name, status}")
        res = page.search_design(design_name, status)
        assert res is True, "查询功能异常"
