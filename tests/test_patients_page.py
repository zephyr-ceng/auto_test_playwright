import allure
import pytest

from core.browser_manager import BrowserManager
from pages.patient_manager import PatientsPage
from utils.csv_manager import CSVManager
from utils.logger import Logger
from utils.random_manager import RandomManager


def _prepare_patients_test_data() -> list[dict]:
    csv_manager = CSVManager("patients_test_date.csv")
    rows = csv_manager.read_csv()
    if rows:
        return rows

    random_manager = RandomManager()
    csv_manager.append_row(
        values=[1, False, "", "", "", "", "", "请填写患者姓名"],
        fieldnames=["序号", "是否有效", "姓名", "生日", "电话", "性别", "备注", "预期结果"],
    )
    data = [
        [2, False, "这是一个超过十字符的文本", "", "", "", "", "姓名最多输入10个字符"],
        [3, False, random_manager.random_chinese_name(), "", random_manager.random_common_chars(3), "", "",
         "手机号格式错误！"],
        [5, False, random_manager.random_chinese_name(), "", random_manager.random_digits(10), "", "",
         "手机号格式错误！"],
        [6, False, random_manager.random_chinese_name(), "", random_manager.random_digits(12), "", "",
         "手机号格式错误！"],
        [6, False, random_manager.random_chinese_name(), "", random_manager.random_phone(), "",
         random_manager.random_common_chars(151), "备注最多150字"],
        [7, True, random_manager.random_chinese_name(), "", random_manager.random_phone(), "",
         random_manager.random_common_chars(20), "patientID"],
    ]
    for row in data:
        csv_manager.append_row(values=row)

    return csv_manager.read_csv()


@pytest.fixture(scope="class")
def page():
    log = Logger("patients_test")
    manager = BrowserManager(browser_type="chromium", headless=True, logger=log)
    # browser_page = manager.start()
    browser_page = manager.new_page()
    patients = PatientsPage(browser_page, log)
    yield patients
    manager.close()


@allure.feature("Patients")
class TestPatientsPage:
    @allure.story("Create Patient Invalid")
    @pytest.mark.parametrize("case", [case for case in _prepare_patients_test_data() if case["是否有效"] == "False"])
    def test_create_patients_page(self, page, case):
        """ 新建患者的错误提示信息验证 """
        allure.dynamic.title(f"测试用例 - {case['序号']} - {case['预期结果']}")
        name = case["姓名"]
        birthday = case["生日"]
        phone = case["电话"]
        gender = case["性别"]
        desc = case["备注"]
        expected = case["预期结果"]
        message = page.create_patient_invalid(name, birthday, phone, gender, desc)
        assert message == expected, f"实际结果:{message} != 预期结果:{expected}"

    @allure.story("Create Patient Success")
    @pytest.mark.parametrize("case", [case for case in _prepare_patients_test_data() if case["是否有效"] == "True"])
    def test_create_patient_success(self, page, case):
        """ 新建患者验证 """
        allure.dynamic.title(f"测试用例 - {case['序号']} - {case['预期结果']}")
        name = case["姓名"]
        birthday = case["生日"]
        phone = case["电话"]
        gender = case["性别"]
        desc = case["备注"]
        expected = case["预期结果"]
        # url = page.create_patient_success_and_get_url(name, birthday, phone, gender, desc)
        url = page.create_patient_effective(name, birthday, phone, gender, desc)
        assert expected in url, f"当前url {url} 中没有包含字段: {expected}"

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
    def test_select_patients_or_design(self, page, name, phone):
        allure.dynamic.title(f"查询患者信息{name, phone}")
        res = page.search_patient(name, phone)
        assert res is True, f"查询功能异常"

    @allure.story("select patients or design")
    @pytest.mark.parametrize("design_name,status", [('test', ''), ('张', '手术中')])
    def test_select_patients_or_design(self, page, design_name, status):
        allure.dynamic.title(f"查询指定患者设计{design_name, status}")
        res = page.search_design(design_name, status)
        assert res is True, f"查询功能异常"

    # @pytest.mark.parametrize('dcm_dir',
    #                          [dir for dir in PathManager(f"data/dicom").get_subdirectory() if os.path.isdir(dir)])
    # def test_dcm_render(self, page, dcm_dir):
    #     print(dcm_dir)
    #     status = page.dcm_upload(dcm_dir, "术前CT", timeout_ms=1000 * 60 * 5)
    #     assert status is True, f"文件未渲染成功，状态为{status}"
