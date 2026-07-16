import re
import time
from typing import Any, List, Optional

from core.base_page import BasePage
from pages.login_manager import LoginPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager

PATIENT_MANAGER_LOCATORS_PATH = "data/rule/patient_manager/patient_manager_page.yaml"


class PatientsPage(BasePage):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            locators_path: str = PATIENT_MANAGER_LOCATORS_PATH,
    ):
        super().__init__(driver, logger)
        self.__config = YamlManager(self.logger)
        self.__random = RandomManager()
        self.__login_page = LoginPage(driver, logger)

        # patient manager yaml 文件读取
        page_cfg = self.__config.read(locators_path)
        if page_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {locators_path}")
        self.patient_url = self.build_url(self.__login_page.base_url, page_cfg.get("url"))
        self.patient_locators = page_cfg.get("locators")
        self.__locators_path = locators_path
        self.__created_patient_names: list[str] = []

    """************************************************  基础函数  **********************************************************************************  """

    def __open_url(self, url) -> None:
        if not url:
            raise RuntimeError("patients url is not configured")
        self.__login_page.refresh_cookies()
        if self.__login_page.cookies:
            self.add_cookies(self.__login_page.cookies)
        self.driver.goto(url)
        self.driver.wait_for_load_state("networkidle")
        self.__accept_webgl_ack()

    def __open_create_form(self) -> bool:
        selector = self.__selector_patient("new_patient_button")
        if not selector:
            return False
        ok = self.click(selector)
        if ok:
            modal_selector = self.__selector_patient("create_patient_modal")
            if modal_selector:
                self.wait_for_selector(modal_selector)
            self.wait_for_time(300)
        return ok

    def __input_name(self, name: str) -> bool:
        selector = self.__selector_patient("name")
        if not selector:
            return False
        return self.type_text(selector, name or "", clear_first=True)

    def __input_birthday(self, birthday: str) -> bool:
        selector = self.__selector_patient("birthday")
        if not selector:
            return False
        return self.type_text(selector, birthday or "", clear_first=True)

    def __input_phone(self, phone: str) -> bool:
        selector = self.__selector_patient("phone")
        if not selector:
            return False
        return self.type_text(selector, phone or "", clear_first=True)

    def __select_gender(self, gender: str) -> bool:
        gender_text = (gender or "").strip()
        if not gender_text:
            return True
        generic_selector = self.__selector_patient("gender")
        if generic_selector:
            return self.type_text(generic_selector, gender_text, clear_first=True)

        lower_text = gender_text.lower()
        if lower_text in {"male", "m", "男", "男性"}:
            male_selector = self.__selector_patient("gender_male")
            return self.click(male_selector) if male_selector else False
        if lower_text in {"female", "f", "女", "女性"}:
            female_selector = self.__selector_patient("gender_female")
            return self.click(female_selector) if female_selector else False
        return False

    def __input_remark(self, remark: str) -> bool:
        selector = self.__selector_patient("remark")
        if not selector:
            return False
        return self.type_text(selector, remark or "", clear_first=True)

    def __click_submit(self) -> bool:
        selector = self.__selector_patient("create_patient_submit_button")
        if not selector:
            return False
        return self.click(selector)

    def __click_cancel(self) -> bool:
        selector = self.__selector_patient("create_patient_cancel_button")
        if not selector:
            return False
        return self.click(selector)

    def __selector_patient(self, key: str) -> Optional[str]:
        return self.patient_locators.get(key)

    def __required_selector(self, key: str) -> str:
        selector = self.__selector_patient(key)
        if not selector:
            raise RuntimeError(f"locator `{key}` is not configured in {self.__locators_path}")
        return selector

    def __collect_texts(self, selector: Optional[str]) -> List[str]:
        if not selector:
            return []
        try:
            texts = self.driver.locator(selector).all_inner_texts()
            return [text.strip() for text in texts if text and text.strip()]
        except Exception:
            return []

    def __first_error_text(self) -> Optional[str]:
        errors: List[str] = []
        for selector in self.patient_locators.get("error_locators", []) or []:
            errors.extend(self.__collect_texts(selector))

        for key in ("name_error", "phone_error", "remark_error", "form_error", "toast_error", "modal_error"):
            errors.extend(self.__collect_texts(self.__selector_patient(key)))

        return errors[0] if errors else None

    def __all_error_texts(self) -> List[str]:
        errors: List[str] = []
        for selector in self.patient_locators.get("error_locators", []) or []:
            errors.extend(self.__collect_texts(selector))
        errors.extend(self.__collect_texts(self.__selector_patient("form_error")))
        return errors

    def __toast_text(self) -> Optional[str]:
        texts = self.__collect_texts(self.__selector_patient("toast_message"))
        return texts[0] if texts else None

    def __is_modal_open(self) -> bool:
        selector = self.__selector_patient("create_patient_modal")
        if not selector:
            return False
        try:
            modal = self.driver.locator(selector).first
            return modal.count() > 0 and modal.is_visible()
        except Exception:
            return False

    def __input_value(self, selector_key: str) -> str:
        selector = self.__required_selector(selector_key)
        try:
            value = self.driver.locator(selector).first.input_value()
            return value or ""
        except Exception:
            return ""

    def __visible_text_exists(self, text: str) -> bool:
        if not text:
            return True
        try:
            locator = self.driver.get_by_text(text, exact=True)
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def __visible_modal_text_exists(self, pattern: str) -> bool:
        selector = self.__selector_patient("create_patient_modal")
        if not selector or not pattern:
            return False
        try:
            modal = self.driver.locator(selector).first
            return modal.get_by_text(re.compile(pattern)).count() > 0
        except Exception:
            return False

    def __gender_selected_index(self) -> Optional[int]:
        items_selector = self.__required_selector("gender_items")
        items = self.driver.locator(items_selector)
        item_count = items.count()
        for index in range(item_count):
            try:
                item = items.nth(index)
                style = item.get_attribute("style") or ""
                if "ft-font-blue-color" in style or "rgb(24, 35, 44)" in style:
                    return index
                indicator_selector = self.__selector_patient("gender_selected_indicator")
                if indicator_selector and item.locator(indicator_selector).count() > 0:
                    return index
            except Exception:
                continue
        return None

    def __select_gender_by_index(self, index: int) -> bool:
        selector = self.__required_selector("gender_items")
        try:
            self.driver.locator(selector).nth(index).click()
            self.wait_for_time(200)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Select gender index failed: {index}, error: {e}")
            return False

    def __fill_create_form(
            self,
            name: str = "",
            birthday: str = "",
            phone: str = "",
            gender: str = "",
            remark: str = "",
    ) -> None:
        self.__input_name(name)
        if birthday:
            self.__input_birthday(birthday)
        self.__input_phone(phone)
        self.__select_gender(gender)
        self.__input_remark(remark)

    def __mock_save_patient_response(
            self,
            *,
            success: bool,
            patient_id: str = "mock-patient-id",
            message: str = "接口返回message",
    ) -> None:
        """模拟保存患者网关响应，避免界面用例写入真实患者数据。"""
        route_pattern = "**/gateway"

        def handler(route):
            request = route.request
            if request.headers.get("command") != "13002":
                route.continue_()
                return
            body = {
                "code": 0 if success else 1,
                "message": "success" if success else message,
                "data": {"id": patient_id} if success else None,
            }
            route.fulfill(status=200, content_type="application/json", json=body)

        self.driver.route(route_pattern, handler)

    def __clear_save_patient_mock(self) -> None:
        try:
            self.driver.unroute("**/gateway")
        except Exception:
            return

    def __accept_webgl_ack(self) -> None:
        ack_selector = self.__selector_patient("ack_button")
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

    def __register_created_patient(self, name: str) -> None:
        """记录界面用例真实创建的患者，供类级夹具收尾阶段统一清理。"""
        patient_name = (name or "").strip()
        if patient_name and patient_name not in self.__created_patient_names:
            self.__created_patient_names.append(patient_name)

    def __unregister_created_patient(self, name: str) -> None:
        """从待清理患者列表中移除已确认删除的患者。"""
        patient_name = (name or "").strip()
        if not patient_name:
            return
        self.__created_patient_names = [
            created_name
            for created_name in self.__created_patient_names
            if created_name != patient_name
        ]

    def __count_page_items(self, tab_selector_key: str, rows_selector_key: str, number: int) -> int:
        """统计设计或患者的数量。"""
        if number <= 0:
            raise ValueError("number must be > 0")

        tab_selector = self.__selector_patient(tab_selector_key)
        rows_selector = self.__selector_patient(rows_selector_key)
        trigger = self.__selector_patient("page_size_trigger")
        options = self.__selector_patient("page_size_option")
        if not rows_selector:
            raise RuntimeError(f"missing rows locator: {rows_selector_key}")
        if not trigger or not options:
            raise RuntimeError(f"page size locators are not configured in {self.__locators_path}")

        if tab_selector:
            self.click(tab_selector)
            self.wait_for_time(600)
        if not self.click(trigger):
            raise RuntimeError("failed to open page size dropdown")
        if not self.click_by_text(options, str(number)):
            raise RuntimeError(f"failed to select page size option: {number}")
        self.wait_for_time(1000)
        count = self.count_elements(rows_selector)
        print(count)
        return count

    def __open_patient_management_tab(self) -> None:
        """打开患者管理页并切换到患者管理页签。"""
        self.__open_url(self.patient_url)
        tab = self.__selector_patient("patient_management_tab")
        if tab:
            self.click(tab)
            self.wait_for_time(500)

    def __search_patient_rows(self, name: str = "", phone: str = ""):
        """按姓名和电话筛选患者列表，返回搜索后的表格行定位器。"""
        name_input = self.__required_selector("patient_search_name_input")
        phone_input = self.__required_selector("patient_search_phone_input")
        search_button = self.__required_selector("patient_search_button")
        row_selector = self.__required_selector("patients_rows")

        self.type_text(name_input, name or "", clear_first=True)
        self.type_text(phone_input, phone or "", clear_first=True)
        self.click(search_button)
        self.wait_for_time(1200)
        return self.driver.locator(row_selector)

    def __patient_exists_in_rows(self, rows, name: str = "", phone: str = "") -> bool:
        """判断搜索结果中是否存在匹配姓名或电话的患者。"""
        ele_count = rows.count()
        if ele_count == 0:
            return False
        for i in range(ele_count):
            row = rows.nth(i)
            cells = row.locator("td")
            row_name = cells.nth(0).inner_text().strip()
            row_phone = cells.nth(1).inner_text().strip()
            if name and name in row_name:
                return True
            if phone and phone in row_phone:
                return True
        return False

    def __click_first_patient_delete_button(self) -> bool:
        """点击患者搜索结果中的第一个删除按钮。"""
        selector = self.__required_selector("patient_delete_button")
        try:
            self.driver.locator(selector).first.click()
            self.wait_for_time(500)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Click first patient delete button failed: {e}")
            return False

    def __confirm_delete_patient(self) -> bool:
        """确认删除患者弹窗。"""
        selector = self.__required_selector("patient_delete_confirm_button")
        try:
            self.driver.locator(selector).click()
            self.wait_for_time(1200)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Confirm delete patient failed: {e}")
            return False

    """  ************************************************  测试函数  **********************************************************************************  """

    def count_page_patients(self, number: int) -> int | None:
        """ 统计单页患者数量 """
        self.__open_url(self.patient_url)
        return self.__count_page_items("patient_management_tab", "patients_rows", number)

    def count_page_designs(self, number: int) -> int:
        """ 统计单页设计数量 """
        self.__open_url(self.patient_url)
        return self.__count_page_items("design_management_tab", "designs_rows", number)

    def create_patient(self, name: str, birthday: str = "", phone: str = "", gender: str = "", remark: str = "", ) -> \
            Optional[str]:
        """ 新建患者 """
        self.__open_url(self.patient_url)
        self.__open_create_form()
        self.__fill_create_form(name, birthday, phone, gender, remark)
        self.__click_submit()
        self.wait_for_time(1000)
        if "createDesign" in self.driver.url or "patientID=" in self.driver.url:
            self.__register_created_patient(name)

    def create_patient_invalid(self, name: str, birthday: str = "", phone: str = "", gender: str = "",
                               remark: str = "", ) -> Optional[str]:
        """ 新建无效患者，返回表单提示 """
        self.create_patient(name, birthday, phone, gender, remark)
        return self.__first_error_text()

    def create_patient_effective(self, name: str, birthday: str = "", phone: str = "", gender: str = "",
                                 remark: str = "", ) -> Optional[str]:
        """新建有效患者，并返回患者页面地址。"""
        self.create_patient(name, birthday, phone, gender, remark)
        deadline = time.time() + 15
        while time.time() < deadline:
            current_url = self.driver.url
            if "createDesign" in current_url or "patientID=" in current_url:
                return current_url
            self.wait_for_time(500)
        return self.driver.url

    def open_create_patient_modal(self) -> dict:
        """打开新建患者弹窗，返回弹窗标题和可见状态。"""
        self.__open_url(self.patient_url)
        opened = self.__open_create_form()
        return {
            "opened": opened and self.__is_modal_open(),
            "title_visible": self.__visible_modal_text_exists("新建患者信息"),
            "modal_open": self.__is_modal_open(),
        }

    def get_create_patient_form_state(self) -> dict:
        """打开弹窗并返回基础字段、按钮、性别项和占位符状态。"""
        self.__open_url(self.patient_url)
        self.__open_create_form()
        return {
            "modal_open": self.__is_modal_open(),
            "title_visible": self.__visible_modal_text_exists("新建患者信息"),
            "name_present": self.driver.locator(self.__required_selector("name")).count() > 0,
            "birthday_present": self.driver.locator(self.__required_selector("birthday")).count() > 0,
            "phone_present": self.driver.locator(self.__required_selector("phone")).count() > 0,
            "remark_present": self.driver.locator(self.__required_selector("remark")).count() > 0,
            "gender_count": self.driver.locator(self.__required_selector("gender_items")).count(),
            "submit_present": self.driver.locator(self.__required_selector("create_patient_submit_button")).count() > 0,
            "cancel_present": self.driver.locator(self.__required_selector("create_patient_cancel_button")).count() > 0,
            "name_placeholder": self.driver.locator(self.__required_selector("name")).first.get_attribute("placeholder"),
            "phone_placeholder": self.driver.locator(self.__required_selector("phone")).first.get_attribute("placeholder"),
            "remark_placeholder": self.driver.locator(self.__required_selector("remark")).first.get_attribute("placeholder"),
        }

    def submit_create_patient_form(
            self,
            name: str = "",
            birthday: str = "",
            phone: str = "",
            gender: str = "",
            remark: str = "",
            *,
            mock: Optional[dict] = None,
    ) -> dict:
        """提交新建患者弹窗，返回错误、提示、页面地址和弹窗状态。"""
        self.__open_url(self.patient_url)
        self.__open_create_form()
        if mock:
            self.__mock_save_patient_response(**mock)
        try:
            self.__fill_create_form(name, birthday, phone, gender, remark)
            self.__click_submit()
            self.wait_for_time(1200)
            return {
                "errors": self.__all_error_texts(),
                "first_error": self.__first_error_text(),
                "toast": self.__toast_text(),
                "url": self.driver.url,
                "modal_open": self.__is_modal_open(),
            }
        finally:
            if mock:
                self.__clear_save_patient_mock()

    def input_phone_and_get_state(self, phone: str) -> dict:
        """输入电话号码并返回输入框实际长度和最大长度限制。"""
        self.__open_url(self.patient_url)
        self.__open_create_form()
        self.__input_phone(phone)
        selector = self.__required_selector("phone")
        phone_input = self.driver.locator(selector).first
        value = phone_input.input_value()
        maxlength = phone_input.get_attribute("maxlength")
        return {
            "value": value,
            "length": len(value),
            "maxlength": int(maxlength) if maxlength and maxlength.isdigit() else None,
        }

    def toggle_gender_and_get_state(self) -> dict:
        """依次点击性别男/女选项，返回互斥选中状态。"""
        self.__open_url(self.patient_url)
        self.__open_create_form()
        male_clicked = self.__select_gender_by_index(0)
        after_male = self.__gender_selected_index()
        female_clicked = self.__select_gender_by_index(1)
        after_female = self.__gender_selected_index()
        return {
            "male_clicked": male_clicked,
            "after_male": after_male,
            "female_clicked": female_clicked,
            "after_female": after_female,
        }

    def cancel_and_reopen_create_patient_form(
            self,
            name: str,
            phone: str = "",
            remark: str = "",
    ) -> dict:
        """填写部分表单后取消，再重新打开并返回表单重置状态。"""
        self.__open_url(self.patient_url)
        self.__open_create_form()
        self.__fill_create_form(name=name, phone=phone, remark=remark)
        self.__click_cancel()
        self.wait_for_time(500)
        closed = not self.__is_modal_open()
        self.__open_create_form()
        return {
            "closed": closed,
            "reopened": self.__is_modal_open(),
            "name": self.__input_value("name"),
            "phone": self.__input_value("phone"),
            "remark": self.__input_value("remark"),
        }

    def search_patient(self, name: str, phone: str) -> bool:
        """通过姓名和电话查询患者，存在返回 True，不存在返回 False。"""
        self.__open_patient_management_tab()
        rows = self.__search_patient_rows(name=name, phone=phone)
        ele_count = rows.count()
        if ele_count == 0:
            return True
        if not name and not phone:
            return ele_count > 0
        return self.__patient_exists_in_rows(rows, name=name, phone=phone)

    def delete_patient(self, name: str) -> dict:
        """按姓名搜索并删除首个匹配患者，返回删除链路和删除后查询状态。"""
        if not name:
            raise ValueError("name is required to delete patient")

        self.__open_patient_management_tab()
        rows = self.__search_patient_rows(name=name)
        searched_before_delete = self.__patient_exists_in_rows(rows, name=name)
        delete_clicked = False
        confirm_clicked = False
        toast = None
        exists_after_delete = searched_before_delete

        if searched_before_delete:
            delete_clicked = self.__click_first_patient_delete_button()
            if delete_clicked:
                confirm_clicked = self.__confirm_delete_patient()
                toast = self.__toast_text()
                rows_after_delete = self.__search_patient_rows(name=name)
                exists_after_delete = self.__patient_exists_in_rows(rows_after_delete, name=name)
                if confirm_clicked and not exists_after_delete:
                    self.__unregister_created_patient(name)

        return {
            "searched_before_delete": searched_before_delete,
            "delete_clicked": delete_clicked,
            "confirm_clicked": confirm_clicked,
            "toast": toast,
            "exists_after_delete": exists_after_delete,
        }

    def cleanup_created_patients(self) -> list[dict]:
        """删除本页面对象生命周期内登记的真实患者，返回清理失败明细。"""
        failures = []
        for patient_name in reversed(self.__created_patient_names[:]):
            try:
                state = self.delete_patient(patient_name)
                if state.get("exists_after_delete") is not False:
                    failures.append({"patient_name": patient_name, "state": state})
            except Exception as e:
                failures.append({"patient_name": patient_name, "error": str(e)})
        return failures

    def search_design(self, name: str, status: str) -> bool:
        """查询手术设计：先切到设计管理，再按姓名和状态筛选。"""
        if status == '' or status is None:
            status = "全部状态"
        valid_status = {"全部状态", "编辑中", "设计完成", "手术中", "完成手术"}
        if status not in valid_status:
            print(f"请输入指定类型参数")
            raise ValueError(f"invalid status: {status}")

        self.__open_url(self.patient_url)
        # 点击设计管理
        tab = self.__selector_patient("design_management_tab")
        if tab:
            self.click(tab)
            self.wait_for_time(500)

        # 元素定位
        name_input = self.__selector_patient("design_search_name_input")
        status_trigger = self.__selector_patient("design_status_trigger")  # 点击状态切换
        status_option = self.__selector_patient("design_status_option")  # 切换手术状态
        search_button = self.__selector_patient("design_search_button")  # 搜索按钮
        cards_selector = self.__selector_patient("designs_rows")  # 指定元素
        if not name_input or not status_trigger or not status_option or not search_button or not cards_selector:
            raise RuntimeError(f"design query locators are not configured in {self.__locators_path}")

        # 流程处理
        self.type_text(name_input, name or "", clear_first=True)
        self.click(status_trigger)
        self.click_by_text(status_option, status)
        self.click(search_button)
        self.wait_for_time(1200)
        cards = self.driver.locator(cards_selector)
        self.take_screenshot("患者查询结果")
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
        for i in range(1, 5):
            pp.count_page_designs(100)
        # pp.create_patient_invalid('test')
    finally:
        manager.close()
