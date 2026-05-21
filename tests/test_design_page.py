import allure
import pytest

from core.browser_manager import BrowserManager
from utils.logger import Logger
from pages.design_manager import DesignManager


# from utils.csv_manager import CSVManager
# from utils.random_manager import RandomManager


@pytest.fixture(scope="class")
def page():
    logger = Logger("patients_test")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=logger)
    # browser_page = manager.start()
    browser_page = manager.new_page()
    patients = DesignManager(browser_page, logger)
    yield patients
    manager.close()


@allure.feature("Design ")
class TestDesignPage:
    @allure.story("牙位创建Message判断")
    @pytest.mark.parametrize("tooth_position", [[12, 13, 15, 22, 24, 33, 37, 42]])
    def test_case_create_tooth(self, page, tooth_position):
        res = page.case_create_tooth(tooth_position)
        for i in res:
            assert i == '操作成功', f"牙位创建失败{i}"

    @allure.story("创建一个完整设计")
    @pytest.mark.parametrize("tooth_position", [46, 15])
    def test_case_create_design(self, page, tooth_position):
        res = page.case_create_design('', tooth_position, "./data/dicom/wujia", "术前手术")
        assert res is True, f"设计未创建{res}"
