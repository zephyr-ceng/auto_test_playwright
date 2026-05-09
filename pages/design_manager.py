import re

from pages.login_page import LoginPage
from core.base_page import BasePage
from pages.patients_page import PatientsPage


class ImplantNavigationPage(BasePage):
    def __init__(self, driver, log):
        super().__init__(driver)
        self.login_page = LoginPage(driver)
        self.logger = log or Logger("implant_navigation")
        self.patients_page = PatientsPage(driver)

    def open_url(self):
        self.login_page.login_account('admin', 'admin')
        print(self.driver.url)
        self.wait_for_time(1000000)

    def create_design(self):
        # ai_status = self.patients_page.dcm_render("./data/dicom/wujia", '术前手术')
        self.patients_page.open_url('https://x.finetool.cn/createDesign?patientID=672041547241963520')
        self.wait_for_time(500)
        self.driver.get_by_role("button", name="新增病例").click()
        self.driver.locator("g:nth-child(15) > path:nth-child(2)").click()
        self.driver.get_by_role("button", name="保 存").click()
        self.driver.locator("div").filter(has_text=re.compile(r"^47$")).nth(1).click()
        self.driver.get_by_role("button", name="创建设计").click()
        # self.driver.wait_for_time(500000)  # TODO: 替换为下载进度监听，监听字段“模型解析中”后面的百分比，等待下载完成后再执行后面的步骤
        progress = self.driver.locator('[role="progressbar"]')
        # 等待进度条出现
        progress.wait_for()
        while True:
            value = progress.get_attribute("aria-valuenow")
            percent = int(value) if value else 0
            print("当前进度:", percent)
            if percent >= 99:
                # self.driver.wait_for_time(10000)
                break
        self.take_screenshot("dcm_download")
        self.wait_for_time(30000)
        # self.driver.locator("._tool-btn_m3ugk_1.ant-tooltip-open").click()
        ele = self.driver.locator("div._tool-btn_m3ugk_1")
        # ele = self.count_elements("div._tool-btn_m3ugk_1")
        print(ele)
        ele.nth(0).click()
        self.driver.locator("g:nth-child(15) > path:nth-child(2)").click()
        self.driver.get_by_role("button", name="选择植体").click()
        self.wait_for_time(1000)
        self.driver.get_by_role("button", name="collapsed 士卓曼").click()
        self.driver.locator("div").filter(has_text=re.compile(r"^骨水平种植体$")).nth(1).click()
        self.driver.get_by_text("021.2608").click()
        self.driver.get_by_label("选择植体").get_by_role("button", name="确 定").click()
        self.wait_for_time(500)
        self.driver.get_by_role("button", name="确 定").click()
        self.wait_for_time(50000)


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = ImplantNavigationPage(page, log)
        pp.create_design()
        # pp.create_patient_invalid('test')
    finally:
        manager.close()
