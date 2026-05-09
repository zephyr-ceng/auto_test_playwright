import asyncio
import time
from collections import deque
from pathlib import Path
from typing import Any, List, Optional

from core.base_page import BasePage
from pages.login_page import LoginPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager


class PatientsPage(BasePage):
    def __init__(
            self,
            driver: Any,
            logger: Optional[Any] = None,
            locators_path: str = "data/patients_data.yaml",
            config_path: str = "config/config.yaml",
    ):
        super().__init__(driver, logger)
        self._config_path = config_path
        self._config = YamlManager(self.logger)
        self._random = RandomManager()

        # patient_data.yaml 文件读取
        page_cfg = self._config.read(locators_path)
        if page_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {locators_path}")
        self.patient_url = page_cfg.get("url")
        self.patient_locators = page_cfg.get("locators")

        # config.yaml
        shared_cfg = self._config.read(config_path)
        if shared_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {config_path}")

        self.login_username = shared_cfg.get("username")
        self.login_password = shared_cfg.get("password")
        self.cookies = shared_cfg.get("cookies")
        self.cookies_write_time = shared_cfg.get("cookies_write_time")

        if not self.login_username or not self.login_password:
            raise RuntimeError(f"username/password not configured in {config_path}")

        # design_page.yaml
        design_cfg = self._config.read("data/design_page.yaml")
        if design_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {config_path}")
        self.design_url = design_cfg.get("url")
        self.design_locators = design_cfg.get("locators")

        # other
        self._responses = deque(maxlen=10)

    """************************************************  基础函数  **********************************************************************************  """

    def _open_url(self, url) -> None:
        if not url:
            raise RuntimeError("patients url is not configured")
        self._refresh_cookies()
        if self.cookies:
            self.driver.context.add_cookies(self.cookies)
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

    def _refresh_cookies(self) -> None:
        """ 刷新cookies """
        now = time.time()
        if self.cookies_write_time is None:
            cookies_write_ts = 0.0
        else:
            time_array = time.strptime(self.cookies_write_time, "%Y-%m-%d %H:%M:%S")
            cookies_write_ts = time.mktime(time_array)

        is_expired = (
                self.cookies is None
                or self.cookies_write_time is None
                or (now - cookies_write_ts) > 24 * 3600
        )
        if not is_expired:
            return
        new_cookies = LoginPage(self.driver, self.logger).get_cookies(
            self.login_username, self.login_password
        )
        self.cookies = new_cookies
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.cookies_write_time = local_time
        self._config.update(self._config_path, {"cookies_write_time": local_time})
        self._config.update(self._config_path, {"cookies": self.cookies})

    def _selector_patient(self, key: str) -> Optional[str]:
        return self.patient_locators.get(key)

    def _selector_design(self, key: str) -> Optional[str]:
        return self.design_locators.get(key)

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

    @staticmethod
    def _file_is_dcm(dcm_dir: str) -> List[str]:
        """ 获取文件目录 """
        target_dir = Path(dcm_dir)
        if not target_dir.is_absolute():
            target_dir = (Path(__file__).resolve().parents[1] / target_dir).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            raise FileNotFoundError(f"dcm directory not found: {target_dir}")

        dcm_files = [str(f) for f in target_dir.glob("*.dcm")]
        dcm_files.extend([str(f) for f in target_dir.glob("*.DCM")])
        dcm_files = sorted(set(dcm_files))
        if not dcm_files:
            raise FileNotFoundError(f"no .dcm files found in: {target_dir}")
        print(f"文件类型：{dcm_files}")
        return dcm_files

    def _handle_response(self, response):
        """响应拦截函数"""
        # 1. 匹配网关地址并确保是 POST 请求
        if "/tars/v1/gateway" in response.url:
            try:
                body = response.json()
                # 使用更安全的路径解析
                data = body.get("data") or {}
                files = data.get("files", [])

                if files:
                    current_status = files[0].get("aiTaskStatus")
                    patient_name = data.get("name", "未知")

                    # 记录状态
                    self._responses.append(current_status)

                    # log_msg = f"📡 捕获状态 | 患者: {patient_name} | 状态: {current_status}"
                    # print(log_msg)
                    # 判定终态：2 为成功
                    if current_status == 2:
                        log_msg = f"📡 捕获状态 | 患者: {patient_name} | 状态: {current_status}"
                        print("🎉 AI 任务处理成功！")
                        if self.logger:
                            self.logger.info(log_msg)
            except ValueError as e:  # 更精确的异常处理（JSON解析错误）
                if self.logger:
                    self.logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)
            except Exception as e:  # 其他异常
                if self.logger:
                    self.logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)

    def _is_ai_status(self, target_status=2, timeout_ms=180000):
        """持续监听判定函数"""
        # 1. 注册监听
        self.driver.on('response', self._handle_response)
        start_time = time.time()
        timeout_sec = timeout_ms / 1000  # 将毫秒转为秒

        try:
            # 2. 动态轮询检查
            while time.time() - start_time < timeout_sec:
                # 检查最新捕获的状态是否包含目标值
                if target_status in self._responses:
                    print(f"最终捕获的状态序列: {list(self._responses)}")  # 转list打印
                    self._responses.clear()  # 清空缓存队列
                    return True
                self.wait_for_time(500)  # Playwright 推荐的非阻塞等待（500ms 检查一次，响应更快）

        finally:
            # 3. 核心：无论成功、失败或超时，必须移除监听器，否则下次调用会产生重复日志
            self.driver.remove_listener('response', self._handle_response)

        return False

    def _input_label(self, label_name):
        selector = self._selector_design("input_label")
        input_role = self._selector_design("input_combobox")
        # print(selector)
        if not selector:
            return False
        self.click(selector)
        return self.type_text_role(str(input_role), label_name)

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

    def select_patient(self, name: str, phone: str) -> bool:
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

    def select_design(self, name: str, status: str) -> bool:
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

    def dcm_render(self, dcm_dir: str, ct_name: str, timeout_ms: int = 180000, target_status: int = 2) -> bool:
        """ 文件上传 """
        self.create_patient(self._random.random_chinese_name())  # TODO: 暂时使用手动创建用户
        # self._open_url()
        dcm_files = self._file_is_dcm(dcm_dir)

        # 传入文件等待解析
        import_data = self._selector_design("import_data")
        import_model = self._selector_design("import_model")
        if not import_data or not import_model:
            raise RuntimeError("cannot find import data or import model on current page")
        self.click(import_data)

        # 文件选择
        with self.driver.expect_file_chooser(timeout=5000) as chooser_info:
            self.click(import_model)
        chooser_info.value.set_files(dcm_files)
        self.wait_for_time(500)

        # 解析完成触发上传
        input_dcm_name = self._selector_design(
            "input_dcm_name") or "input[placeholder='\u8f93\u5165\u6a21\u578b\u540d\u79f0']"
        confirmed_btn = self._selector_design("confirmed_btn")
        if not confirmed_btn:
            raise RuntimeError("cannot find `confirmed_btn` in modal")

        name_input_locator = self.driver.locator(input_dcm_name)
        deadline = time.time() + 60
        while time.time() < deadline and name_input_locator.count() <= 0:
            self.wait_for_time(500)
        if name_input_locator.count() <= 0:
            raise RuntimeError("cannot find model-name input after selecting files")

        name_input_locator.first.click(force=True)
        name_input_locator.first.fill(ct_name)
        name_input_locator.first.press("Enter")
        self.wait_for_time(300)
        self.click(confirmed_btn)

        status = self._is_ai_status(target_status=target_status, timeout_ms=timeout_ms)
        if self.logger:
            self.logger.info(f"DCM渲染状态为{status}")
        return status

    def create_tooth(self, tooth_position: int) -> bool:
        """ 病例创建 """
        if not isinstance(tooth_position, int):
            raise ValueError("tooth_position must be int")
        if tooth_position <= 0:
            raise ValueError("tooth_position must be > 0")
        # if "patientID" not in (self.driver.url or ""):
        #     raise ValueError("patientID must be set")
        # self.create_patient(self._random.random_chinese_name())  # TODO: 暂时使用手动创建用户
        self._open_url("https://x.finetool.cn/createDesign?patientID=663912333812113408")
        print(self.driver.url)
        self.click("button:has-text('新增病例')")
        self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 0) or self.click_nth(
            f"[role='dialog'] svg path[data-name='{tooth_position}']", 1)
        self.wait_for_time(300)
        self._input_label(f"牙位：{tooth_position}")
        self.click("button:has-text('保 存')")
        self.wait_for_time(1000)
        ele_count = self.count_elements("//div[contains(@class,'bg-[#232323]')]")
        if ele_count > 0:
            print(ele_count)
            return True
        return False

    def open_url(self, url) -> None:
        if not url:
            raise RuntimeError("patients url is not configured")
        self._refresh_cookies()
        if self.cookies:
            self.driver.context.add_cookies(self.cookies)
        self.driver.goto(url)
        self.driver.wait_for_load_state("networkidle")
        self._accept_webgl_ack()


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = PatientsPage(page, log)
        res = pp.create_tooth(17)
        print(res)
        # pp.create_patient_invalid('test')
    finally:
        manager.close()
