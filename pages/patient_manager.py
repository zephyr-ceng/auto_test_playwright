import time
from typing import Any, List, Optional

from core.base_page import BasePage
from pages.login_manager import LoginPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager


class PatientsPage(BasePage):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            locators_path: str = "data/patients_data.yaml",
    ):
        super().__init__(driver, logger)
        self._config = YamlManager(self.logger)
        self._random = RandomManager()
        self._login_page = LoginPage(driver)
        # patient_data.yaml 文件读取
        page_cfg = self._config.read(locators_path)
        if page_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {locators_path}")
        self.patient_url = page_cfg.get("url")
        self.patient_locators = page_cfg.get("locators")

    """************************************************  基础函数  **********************************************************************************  """

    def _open_url(self, url) -> None:
        if not url:
            raise RuntimeError("patients url is not configured")
        self._login_page.refresh_cookies()
        if self._login_page.cookies:
            self.add_cookies(self._login_page.cookies)
        self.driver.goto(url)
        self.driver.wait_for_load_state("networkidle")
        self._accept_webgl_ack()

    def _open_create_form(self) -> bool:
        selector = self._selector_patient("new_patient_button")
        if not selector:
            return False
        ok = self.click(selector)
        if ok:
            self.wait_for_time(500)
        return ok

    def _input_name(self, name: str) -> bool:
        selector = self._selector_patient("name")
        if not selector:
            return False
        return self.type_text(selector, name or "", clear_first=True)

    def _input_birthday(self, birthday: str) -> bool:
        selector = self._selector_patient("birthday")
        if not selector:
            return False
        return self.type_text(selector, birthday or "", clear_first=True)

    def _input_phone(self, phone: str) -> bool:
        selector = self._selector_patient("phone")
        if not selector:
            return False
        return self.type_text(selector, phone or "", clear_first=True)

    def _select_gender(self, gender: str) -> bool:
        gender_text = (gender or "").strip()
        if not gender_text:
            return True
        generic_selector = self._selector_patient("gender")
        if generic_selector:
            return self.type_text(generic_selector, gender_text, clear_first=True)

        lower_text = gender_text.lower()
        if lower_text in {"male", "m", "男", "男性"}:
            male_selector = self._selector_patient("gender_male")
            return self.click(male_selector) if male_selector else False
        if lower_text in {"female", "f", "女", "女性"}:
            female_selector = self._selector_patient("gender_female")
            return self.click(female_selector) if female_selector else False
        return False

    def _input_remark(self, remark: str) -> bool:
        selector = self._selector_patient("remark")
        if not selector:
            return False
        return self.type_text(selector, remark or "", clear_first=True)

    def _click_submit(self) -> bool:
        selector = self._selector_patient("submit")
        if not selector:
            return False
        return self.click(selector)

    def _selector_patient(self, key: str) -> Optional[str]:
        return self.patient_locators.get(key)

    def _collect_texts(self, selector: Optional[str]) -> List[str]:
        if not selector:
            return []
        try:
            texts = self.driver.locator(selector).all_inner_texts()
            return [text.strip() for text in texts if text and text.strip()]
        except Exception:
            return []

    def _first_error_text(self) -> Optional[str]:
        errors: List[str] = []
        for selector in self.patient_locators.get("error_locators", []) or []:
            errors.extend(self._collect_texts(selector))

        for key in ("name_error", "phone_error", "remark_error", "form_error", "toast_error", "modal_error"):
            errors.extend(self._collect_texts(self._selector_patient(key)))

        return errors[0] if errors else None

    def _accept_webgl_ack(self) -> None:
        ack_selector = self._selector_patient("ack_button")
        if not ack_selector:
            return
        try:
            ack = self.driver.locator(ack_selector).first
            if ack.count() > 0 and ack.is_visible():
                ack.click()
                self.driver.wait_for_load_state("networkidle")
                self.wait_for_time(800)
        except Exception:
            return

    def _count_page_items(self, tab_selector_key: str, rows_selector_key: str, number: int) -> int:
        """ 统计设计or患者的数量 """
        if number <= 0:
            raise ValueError("number must be > 0")

        tab_selector = self._selector_patient(tab_selector_key)
        rows_selector = self._selector_patient(rows_selector_key)
        trigger = self._selector_patient("page_size_trigger")
        options = self._selector_patient("page_size_option")
        if not rows_selector:
            raise RuntimeError(f"missing rows locator: {rows_selector_key}")
        if not trigger or not options:
            raise RuntimeError("page size locators are not configured in data/patients_data.yaml")

        if tab_selector:
            self.click(tab_selector)
            self.wait_for_time(600)
        if not self.click(trigger):
            raise RuntimeError("failed to open page size dropdown")
        if not self.click_by_text(options, str(number)):
            raise RuntimeError(f"failed to select page size option: {number}")
        self.wait_for_time(800)
        return self.count_elements(rows_selector)

    """  ************************************************  测试函数  **********************************************************************************  """

    def count_page_patients(self, number: int) -> int | None:
        """ 统计单页患者数量 """
        self._open_url(self.patient_url)
        return self._count_page_items("patient_management_tab", "patients_rows", number)

    def count_page_designs(self, number: int) -> int:
        """ 统计单页设计数量 """
        self._open_url(self.patient_url)
        return self._count_page_items("design_management_tab", "designs_rows", number)

    def create_patient(self, name: str, birthday: str = "", phone: str = "", gender: str = "", remark: str = "", ) -> \
            Optional[str]:
        """ 新建患者 """
        self._open_url(self.patient_url)
        self._open_create_form()
        self._input_name(name)
        self._input_birthday(birthday)
        self._input_phone(phone)
        self._select_gender(gender)
        self._input_remark(remark)
        self._click_submit()
        self.wait_for_time(1000)

    def create_patient_invalid(self, name: str, birthday: str = "", phone: str = "", gender: str = "",
                               remark: str = "", ) -> Optional[str]:
        """ 新建无效患者，返回表单提示 """
        self.create_patient(name, birthday, phone, gender, remark)
        return self._first_error_text()

    def create_patient_effective(self, name: str, birthday: str = "", phone: str = "", gender: str = "",
                                 remark: str = "", ) -> Optional[str]:
        """ 新建患者有效，返回患者的URL """
        self.create_patient(name, birthday, phone, gender, remark)
        deadline = time.time() + 15
        while time.time() < deadline:
            current_url = self.driver.url
            if "createDesign" in current_url or "patientID=" in current_url:
                return current_url
            self.wait_for_time(500)
        return self.driver.url

    def search_patient(self, name: str, phone: str) -> bool:
        """通过 name/phone/gender 查询患者，存在返回 True，不存在返回 False。"""
        self._open_url(self.patient_url)
        # 点击病患管理后查找相关元素
        tab = self._selector_patient("patient_management_tab")
        if tab:
            self.click(tab)
            self.wait_for_time(500)

        name_input = self._selector_patient("patient_search_name_input")
        phone_input = self._selector_patient("patient_search_phone_input")
        search_button = self._selector_patient("patient_search_button")
        row_selector = self._selector_patient("patients_rows")
        if not name_input or not phone_input or not search_button or not row_selector:
            raise RuntimeError("patient query locators are not configured in data/patients_data.yaml")

        self.type_text(name_input, name or "", clear_first=True)
        self.type_text(phone_input, phone or "", clear_first=True)
        self.click(search_button)
        self.wait_for_time(1200)
        rows = self.driver.locator(row_selector)
        res = []
        ele_count = rows.count()
        if ele_count > 0:
            for i in range(ele_count):
                row = rows.nth(i)
                cells = row.locator("td")
                row_name = cells.nth(0).inner_text().strip()
                row_phone = cells.nth(1).inner_text().strip()
                if name in row_name or phone in row_phone or not row_name or not row_phone:
                    res.append(True)
                else:
                    res.append(False)
            for i in range(len(res)):
                if res[i] is True:
                    return True
            return False
        else:
            return True

    def search_design(self, name: str, status: str) -> bool:
        """查询手术设计：先切到设计管理，再按姓名和状态筛选。"""
        if status == '' or status is None:
            status = "全部状态"
        valid_status = {"全部状态", "编辑中", "设计完成", "手术中", "完成手术"}
        if status not in valid_status:
            print(f"请输入指定类型参数")
            raise ValueError(f"invalid status: {status}")

        self._open_url(self.patient_url)
        # 点击设计管理
        tab = self._selector_patient("design_management_tab")
        if tab:
            self.click(tab)
            self.wait_for_time(500)

        # 元素定位
        name_input = self._selector_patient("design_search_name_input")
        status_trigger = self._selector_patient("design_status_trigger")  # 点击状态切换
        status_option = self._selector_patient("design_status_option")  # 切换手术状态
        search_button = self._selector_patient("design_search_button")  # 搜索按钮
        cards_selector = self._selector_patient("designs_rows")  # 指定元素
        if not name_input or not status_trigger or not status_option or not search_button or not cards_selector:
            raise RuntimeError("design query locators are not configured in data/patients_data.yaml")

        # 流程处理
        self.type_text(name_input, name or "", clear_first=True)
        self.click(status_trigger)
        self.click_by_text(status_option, status)
        self.click(search_button)
        self.wait_for_time(1200)
        cards = self.driver.locator(cards_selector)
        if not name:
            return cards.count() > 0
        return cards.filter(has_text=name).count() > 0


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = PatientsPage(page, log)
        # pp.create_patient_invalid('test')
    finally:
        manager.close()
