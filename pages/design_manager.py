import time
from collections import deque
from pathlib import Path
from typing import List, Optional

from pages.login_manager import LoginPage
from core.base_page import BasePage
from pages.patient_manager import PatientsPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager

DESIGN_LOCATORS_PATH = "data/rule/design/design_page.yaml"
UPPER_TOOTH_POSITIONS = frozenset((17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27))
LOWER_TOOTH_POSITIONS = frozenset((31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47))
STANDARD_TOOTH_POSITIONS = UPPER_TOOTH_POSITIONS | LOWER_TOOTH_POSITIONS


class DesignManager(BasePage):
    """设计管理页面对象。"""

    def __init__(self, driver, logger, design_path: str = DESIGN_LOCATORS_PATH):
        """初始化页面对象和定位配置。"""
        super().__init__(driver, logger)
        self.__logger = logger
        self.__login_page = LoginPage(driver, self.__logger)
        self.__design_path = design_path
        self.__config = YamlManager(self.__logger)
        self.__random = RandomManager()
        self.__cookies = self.__login_page.cookies
        self.__patients_page = PatientsPage(driver, self.__logger)

        # 定位配置
        design_cfg = self.__config.read(self.__design_path)
        if design_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {self.__design_path}")
        self.design_url = self.build_url(self.__login_page.base_url, design_cfg.get("url"))
        self.design_locators = design_cfg.get("locators") or {}

        # 运行状态
        self.__responses = deque(maxlen=10)
        self.__patient_name = "T_" + self.__random.random_chinese_name()
        self.__treatment_path_ready = False
        self.__treatment_path_context = {}

    def __selector_design(self, key: str, required: bool = False):
        """读取设计页定位配置。"""
        selector = self.design_locators.get(key)
        if required and not selector:
            raise RuntimeError(f"locator `{key}` is not configured in {self.__design_path}")
        return selector

    @staticmethod
    def __validate_tooth_position(tooth_position: int) -> int:
        """校验并返回标准牙位编号。"""
        if not isinstance(tooth_position, int):
            raise ValueError("tooth_position must be int")
        if tooth_position not in STANDARD_TOOTH_POSITIONS:
            raise ValueError("tooth_position must be standard dental position")
        return tooth_position

    def __tooth_arch_index(self, tooth_position: int) -> int:
        """返回牙位图中的上下颌索引。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        return 0 if tooth_position in UPPER_TOOTH_POSITIONS else 1

    def __tooth_selector(self, locator_key: str, tooth_position: int, required: bool = True) -> Optional[str]:
        """按牙位格式化定位表达式。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        selector_template = self.__selector_design(locator_key, required=required)
        if not selector_template:
            return None
        return selector_template.format(tooth_position=tooth_position)

    def __click_tooth_by_arch(
            self,
            locator_key: str,
            tooth_position: int,
            *,
            force: bool = False,
    ) -> None:
        """按上下颌索引点击牙位图。"""
        tooth_selector = self.__tooth_selector(locator_key, tooth_position, required=True)
        tooth_index = self.__tooth_arch_index(tooth_position)
        if force:
            tooth_path = self.driver.locator(tooth_selector).nth(tooth_index)
            tooth_path.wait_for(state="visible", timeout=3000)
            tooth_path.click(force=True)
        elif not self.click_nth(tooth_selector, tooth_index):
            raise RuntimeError(f"failed to click tooth position {tooth_position}")
        self.wait_for_time(300)

    def __read_case_tooth_positions(self, url: str = "") -> Optional[List[str]]:
        """读取病例卡片中的牙位文本。"""

        if "patientID" not in url:
            print(f"当前页面不在患者详情页，{url}")
            if self.__logger:
                self.__logger.error(f"当前页面不在患者详情页，{url}")
            return None

        selector = self.__selector_design("case_tooth_position_cards", required=True)

        locator = self.driver.locator(selector)
        try:
            locator.first.wait_for(timeout=10000)
        except Exception:
            return None

        tooth_texts = []
        seen = set()
        for card in locator.all():
            tooth_text = card.locator("xpath=.//span[contains(@class,'text-base')]").first.inner_text().strip()
            if tooth_text and tooth_text not in seen:
                seen.add(tooth_text)
                tooth_texts.append(tooth_text)
        return tooth_texts if tooth_texts else None

    @staticmethod
    def __file_is_dcm(dcm_dir: str) -> List[str]:
        """返回目录中的 DICOM 文件列表。"""
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

    def __handle_response(self, response):
        """捕获 AI 任务状态响应。"""
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
                    self.__responses.append(current_status)

                    # log_msg = f"📡 捕获状态 | 患者: {patient_name} | 状态: {current_status}"
                    # print(log_msg)
                    # 判定终态：2 为成功
                    if current_status == 2:
                        log_msg = f"📡 捕获状态 | 患者: {patient_name} | 状态: {current_status}"
                        print("🎉 AI 任务处理成功！")
                        if self.__logger:
                            self.__logger.info(log_msg)
            except ValueError as e:  # 更精确的异常处理（JSON解析错误）
                if self.__logger:
                    self.__logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)
            except Exception as e:  # 其他异常
                if self.__logger:
                    self.__logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)

    def __is_ai_status(self, target_status=2, timeout_ms=180000):
        """等待 AI 任务到达目标状态。"""
        # 1. 注册监听
        self.driver.on('response', self.__handle_response)
        start_time = time.time()
        timeout_sec = timeout_ms / 1000  # 将毫秒转为秒

        try:
            # 2. 动态轮询检查
            while time.time() - start_time < timeout_sec:
                # 检查最新捕获的状态是否包含目标值
                if target_status in self.__responses:
                    print(f"最终捕获的状态序列: {list(self.__responses)}")
                    self.__responses.clear()  # 清空缓存队列
                    return True
                self.wait_for_time(500)  # Playwright 推荐的非阻塞等待（500ms 检查一次，响应更快）

        finally:
            # 3. 核心：无论成功、失败或超时，必须移除监听器，否则下次调用会产生重复日志
            self.driver.remove_listener('response', self.__handle_response)

        return False

    def __input_label(self, label_name):
        """输入病例标签。"""
        selector = self.__selector_design("input_label")
        input_role = self.__selector_design("input_combobox")
        # print(selector)
        if not selector:
            return False
        self.click(selector)
        return self.type_text_role(str(input_role), label_name)

    def __open_import_data_modal(self) -> None:
        """打开导入数据弹窗，并等待 CT/DICOM 类型入口可见。"""
        import_data = self.__selector_design("import_data", required=True)
        ct_type_button = self.__selector_design("ct_dicom_type_button", required=True)
        if not self.click(import_data):
            raise RuntimeError("failed to open import data modal")
        self.driver.locator(ct_type_button).first.wait_for(state="visible", timeout=10000)

    def __select_ct_dicom_type(self) -> None:
        """在导入数据弹窗中选择 CT 数据/DICOM 格式。"""
        ct_type_button = self.__selector_design("ct_dicom_type_button", required=True)
        if not self.click(ct_type_button):
            raise RuntimeError("failed to select CT DICOM data type")

    def __choose_dcm_files(self, dcm_files: List[str]) -> None:
        """从新版上传区域触发文件选择器，并设置 DICOM 文件序列。"""
        upload_area = self.__selector_design("dcm_upload_area", required=True)
        upload_area_locator = self.driver.locator(upload_area).first
        upload_area_locator.wait_for(state="visible", timeout=10000)
        with self.driver.expect_file_chooser(timeout=10000) as chooser_info:
            upload_area_locator.click()
        chooser_info.value.set_files(dcm_files)

    def __wait_for_dcm_confirm_form(self, timeout_ms: int = 60000):
        """等待模型名称输入框出现并返回定位器。"""
        input_dcm_name = self.__selector_design("input_dcm_name", required=True)
        name_input_locator = self.driver.locator(input_dcm_name)
        name_input_locator.first.wait_for(state="visible", timeout=timeout_ms)
        return name_input_locator.first

    def __fill_dcm_name(self, ct_name: str, timeout_ms: int = 60000) -> None:
        """填写 DICOM 模型名称。"""
        name_input = self.__wait_for_dcm_confirm_form(timeout_ms=timeout_ms)
        name_input.click(force=True)
        name_input.fill(ct_name)
        name_input.press("Enter")

    def __confirm_dcm_import(self) -> None:
        """点击新版“确认导入”按钮，缺失时兼容旧版确认按钮。"""
        confirm_selectors = [
            self.__selector_design("confirm_import_button"),
            self.__selector_design("confirmed_btn"),
        ]
        if not any(confirm_selectors):
            raise RuntimeError("locator `confirm_import_button` or `confirmed_btn` is not configured")

        last_error = None
        for selector in confirm_selectors:
            if not selector:
                continue
            try:
                confirm_locator = self.driver.locator(selector).first
                confirm_locator.wait_for(state="visible", timeout=3000)
                confirm_locator.click()
                return
            except Exception as e:
                last_error = e
        raise RuntimeError(f"cannot find visible DCM import confirm button: {last_error}")

    def __dcm_upload(self, dcm_dir: str, ct_name: str, timeout_ms: int = 180000, target_status: int = 2) -> bool:
        """上传 DICOM 并等待 AI 解析完成。"""
        dcm_files = self.__file_is_dcm(dcm_dir)

        self.__open_import_data_modal()
        self.__select_ct_dicom_type()
        self.__choose_dcm_files(dcm_files)
        self.__fill_dcm_name(ct_name)
        self.wait_for_time(300)
        self.__confirm_dcm_import()

        status = self.__is_ai_status(target_status=target_status, timeout_ms=timeout_ms)
        if self.__logger:
            self.__logger.info(f"DCM解析状态为{status}")
        return status

    def __create_tooth(self, tooth_position: int) -> str:
        """创建指定牙位病例。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        page_url = self.get_page_url()
        self.wait_for_time(500)
        if "patientID" not in page_url:
            self.__logger.error(f"patientID not found in url: {page_url}")
            raise RuntimeError("cannot find patientID in url")
        case_list = self.__read_case_tooth_positions(self.get_page_url())  # 获取所有牙位

        # 新建病例
        if not self.click(self.__selector_design("new_case_button", required=True)):
            raise RuntimeError("failed to open create tooth dialog")
        self.__click_tooth_by_arch("tooth_path_template", tooth_position)

        # 标签输入
        # self._input_label(f"牙位：{tooth_position}")
        selector = self.__selector_design("input_label", required=True)
        input_role = self.__selector_design("input_combobox", required=True)
        self.click(selector)
        self.type_text_role(str(input_role), f"牙位：{tooth_position}")
        self.click(self.__selector_design("save_button", required=True))

        # 获取弹窗文本
        alert_text = self.get_locator(self.__selector_design("create_tooth_msg", required=True)).inner_text()
        if case_list:
            if str(tooth_position) in case_list:
                self.click(self.__selector_design("cancel_button", required=True))
        self.wait_for_time(1000)
        return alert_text

    def __drag_surgical(self) -> bool:
        """将第 5 个可见手术阶段拖到第 6 个位置。"""
        surgical_stage_cards = self.__selector_design("surgical_stage_draggable_cards", required=True)

        changed = self.drag_nth_locator_to_nth_locator(
            surgical_stage_cards,
            4,
            5,
            screenshot_name="surgical_stage_drag",
        )
        if self.__logger:
            self.__logger.info(f"Surgical stage drag changed={changed}")
        return changed

    def __dragg_surgical(self) -> bool:
        """兼容旧拼写方法名。"""
        return self.__drag_surgical()

    """******************************************* 公共方法 ******************************************************************"""

    def is_create_design_progress_completed(
            self,
            progress_selector: str,
            create_design_button: str,
            ready_selector: str,
            progress_was_visible: bool = False,
            elapsed_ms: int = 0,
    ) -> bool:
        """判断创建设计进度是否完成。"""
        ready_locator = self.driver.locator(ready_selector)
        progress_locator = self.driver.locator(progress_selector)
        create_button_locator = self.driver.get_by_role("button", name=create_design_button)
        try:
            progress_visible = progress_locator.count() > 0 and progress_locator.first.is_visible(timeout=200)
        except Exception as e:
            if self.__logger:
                self.__logger.info(f"Create design progress bar is no longer visible: {e}")
            progress_visible = False

        if progress_visible:
            return False

        if progress_was_visible:
            return True

        try:
            create_button_hidden = (
                    create_button_locator.count() == 0
                    or not create_button_locator.first.is_visible(timeout=200)
            )
        except Exception:
            create_button_hidden = True

        try:
            ready_visible = ready_locator.count() > 0 and ready_locator.first.is_visible(timeout=200)
        except Exception:
            ready_visible = False

        return elapsed_ms >= 1000 and create_button_hidden and ready_visible

    def create_design_and_wait_progress(self, tooth_position: int) -> None:
        """触发创建设计并等待进度完成。"""
        self.__validate_tooth_position(tooth_position)
        # tooth_label = self._selector_design("tooth_label_template").format(tooth_position=tooth_position)
        self.wait_for_time(500)
        create_design_button = self.__selector_design("create_design_button", required=True)
        progress = self.__selector_design("progressbar", required=True)
        ready_selector = (
                self.__selector_design("implant_design_ready_button")
                or self.__selector_design("tool_button")
        )
        if not create_design_button or not progress or not ready_selector:
            raise RuntimeError("create design button, progressbar or tool button locator is not configured")

        # self.click_nth(tooth_label, 0)
        self.click_role("button", role_name=create_design_button)
        progress_was_visible = False
        progress_locator = self.driver.locator(progress)
        start_time = time.time()
        deadline = start_time + 180
        while time.time() < deadline:
            try:
                progress_was_visible = (
                        progress_was_visible
                        or progress_locator.count() > 0
                        and progress_locator.first.is_visible(timeout=200)
                )
            except Exception:
                pass

            if self.is_create_design_progress_completed(
                    progress,
                    create_design_button,
                    ready_selector,
                    progress_was_visible,
                    int((time.time() - start_time) * 1000),
            ):
                break
            self.wait_for_time(500)
        else:
            # self.take_screenshot("dcm_download_timeout")
            raise RuntimeError(f"create design progress did not complete for tooth position {tooth_position}")

        # self.take_screenshot("dcm_download")
        self.wait_for_time(10000)

    def __implant_edit_dialog(self):
        """返回植体编辑弹窗。"""
        dialog_selector = self.__selector_design("implant_editor_dialog")
        if dialog_selector:
            return self.driver.locator(dialog_selector)
        dialog_name = self.__selector_design("implant_edit_dialog_name", required=True)
        return self.driver.get_by_role("dialog", name=dialog_name)

    def __implant_select_dialog(self):
        """返回植体库弹窗。"""
        dialog_name = self.__selector_design("implant_select_dialog_name", required=True)
        return self.driver.get_by_label(dialog_name)

    def __implant_edit_dialog_is_visible(self) -> bool:
        """判断植体编辑弹窗是否已打开。"""
        dialog = self.__implant_edit_dialog()
        try:
            return dialog.count() > 0 and dialog.first.is_visible(timeout=500)
        except Exception:
            return False

    def __implant_dialog_is_add_mode(self) -> bool:
        """判断当前弹窗是否为新增植体。"""
        add_dialog_name = self.__selector_design("implant_add_dialog_name")
        if not add_dialog_name:
            return False
        try:
            add_dialog = self.driver.get_by_role("dialog", name=add_dialog_name)
            return add_dialog.count() > 0 and add_dialog.first.is_visible(timeout=300)
        except Exception:
            return False

    def __open_implant_card_edit_dialog(self, tooth_position: int) -> bool:
        """尝试从牙位卡片打开植体编辑弹窗。"""
        tooth_card = self.__tooth_selector("implant_tooth_card_template", tooth_position, required=True)
        edit_icon = self.__selector_design("implant_tooth_card_edit_icon", required=True)
        card = self.driver.locator(tooth_card).first
        try:
            card.wait_for(state="visible", timeout=3000)
            card.locator(edit_icon).first.click()
            self.__implant_edit_dialog().first.wait_for(state="visible", timeout=10000)
            return True
        except Exception as e:
            if self.__logger:
                self.__logger.info(f"Implant tooth card edit entry is not available: {e}")
            return False

    def __open_add_implant_dialog_from_toolbar(self) -> None:
        """通过工具栏提示打开新增植体弹窗。"""
        tool_button_selector = self.__selector_design("implant_toolbar_tool_button", required=True)
        tooltip_text = self.__selector_design("implant_add_tooltip_text", required=True)
        tooltip_template = self.__selector_design("implant_visible_tooltip_template", required=True)
        tooltip_selector = tooltip_template.format(tooltip_text=tooltip_text)

        tool_buttons = self.driver.locator(tool_button_selector)
        tool_buttons.first.wait_for(state="visible", timeout=10000)
        last_error = None
        for index in range(tool_buttons.count()):
            button = tool_buttons.nth(index)
            try:
                if not button.is_visible(timeout=300):
                    continue
                button.hover()
                tooltip = self.driver.locator(tooltip_selector).first
                tooltip.wait_for(state="visible", timeout=1000)
                button.click()
                self.__implant_edit_dialog().first.wait_for(state="visible", timeout=10000)
                return
            except Exception as e:
                last_error = e

        raise RuntimeError(f"cannot find add implant toolbar button by tooltip `{tooltip_text}`: {last_error}")

    def __open_implant_edit_dialog(self, tooth_position: int) -> None:
        """打开目标牙位的植体编辑弹窗。"""
        self.__validate_tooth_position(tooth_position)
        if self.__implant_edit_dialog_is_visible():
            return

        if self.__open_implant_card_edit_dialog(tooth_position):
            return

        self.__open_add_implant_dialog_from_toolbar()

    def __select_dialog_tooth_position(self, tooth_position: int) -> None:
        """在植体弹窗中选择目标牙位。"""
        tooth_selector = self.__tooth_selector("implant_dialog_tooth_path_template", tooth_position, required=True)
        tooth_paths = self.driver.locator(tooth_selector)
        try:
            if tooth_paths.count() <= 0:
                return
            target_state = tooth_paths.evaluate_all(
                """paths => {
                    let selected = false;
                    paths.forEach((path, index) => {
                        const fill = String(path.getAttribute('fill') || '').toLowerCase();
                        if (fill && !['#818181', '#525252', 'none', 'currentcolor'].includes(fill)) {
                            selected = true;
                        }
                    });
                    return {selected};
                }"""
            )
            if target_state.get("selected") and not self.__implant_dialog_is_add_mode():
                return

            self.__click_tooth_by_arch("implant_dialog_tooth_path_template", tooth_position, force=True)
        except Exception as e:
            if self.__logger:
                self.__logger.info(f"Implant tooth map selection skipped: {e}")

    def __click_implant_dialog_footer_button(self, dialog, button_text: str) -> None:
        """点击指定弹窗底部按钮。"""
        footer_button_template = self.__selector_design("implant_dialog_footer_button_template", required=True)
        button_selector = footer_button_template.format(button_text=button_text)
        button = dialog.locator(button_selector).first
        try:
            button.wait_for(state="visible", timeout=3000)
            button.click()
            return
        except Exception as e:
            if self.__logger:
                self.__logger.info(f"Dialog footer locator click fallback triggered: {e}")

        try:
            dialog.get_by_role("button", name=button_text).click()
            return
        except Exception as e:
            if self.__logger:
                self.__logger.info(f"Dialog role button click fallback triggered: {e}")

        clicked = dialog.evaluate(
            """(dialog, buttonText) => {
                const compact = value => String(value || '').replace(/\\s+/g, '');
                const footer = dialog.querySelector(':scope > .ant-modal-content > .ant-modal-footer');
                if (!footer) {
                    return false;
                }
                const buttons = Array.from(footer.querySelectorAll('button'));
                const target =
                    buttons.find(button => compact(button.innerText) === compact(buttonText)) ||
                    buttons.find(button => button.className.includes('ant-btn-primary')) ||
                    buttons[buttons.length - 1];
                if (!target) {
                    return false;
                }
                target.click();
                return true;
            }""",
            button_text,
        )
        if not clicked:
            raise RuntimeError(f"cannot find dialog footer button: {button_text}")

    def __choose_implant_model(self) -> None:
        """选择配置的植体型号。"""
        edit_dialog = self.__implant_edit_dialog()
        select_button = self.__selector_design("select_implant_button", required=True)
        edit_dialog.get_by_role("button", name=select_button).click()

        select_dialog = self.__implant_select_dialog()
        select_dialog.first.wait_for(state="visible", timeout=10000)

        favorite_tab_text = self.__selector_design("implant_favorite_tab_text")
        if favorite_tab_text:
            favorite_tab = select_dialog.get_by_text(favorite_tab_text, exact=True)
            if favorite_tab.count() > 0:
                favorite_tab.first.click()

        model_button_name = self.__selector_design("implant_model_button_name", required=True)
        model_button = select_dialog.get_by_role("button", name=model_button_name)
        model_button.first.wait_for(state="visible", timeout=10000)
        model_button.first.click()

        confirm_text = self.__selector_design("implant_confirm_button_text", required=True)
        self.__click_implant_dialog_footer_button(select_dialog.first, confirm_text)
        select_dialog.first.wait_for(state="hidden", timeout=10000)

    def __confirm_implant_edit_dialog(self) -> None:
        """确认植体编辑弹窗。"""
        dialog = self.__implant_edit_dialog()
        confirm_text = self.__selector_design("implant_confirm_button_text", required=True)
        self.__click_implant_dialog_footer_button(dialog.first, confirm_text)
        dialog.first.wait_for(state="hidden", timeout=10000)

    def select_implant(self, tooth_position: int) -> None:
        """为指定牙位选择植体型号。"""
        self.__validate_tooth_position(tooth_position)
        self.__open_implant_edit_dialog(tooth_position)
        self.__select_dialog_tooth_position(tooth_position)
        self.__choose_implant_model()
        self.__confirm_implant_edit_dialog()

    def skip_apex_adjustment(self) -> None:
        """跳过牙尖点调整流程。"""
        self.click_role("button", role_name=self.__selector_design("next_apex_button_text", required=True))
        self.wait_for_time(2000)
        self.get_by_text("全部删除").wait_for(state="visible", timeout=10000)
        self.click_role("button", role_name=self.__selector_design("finish_adjustment_button_text", required=True))
        self.click_role("button", role_name=self.__selector_design("skip_button_text", required=True))

    def create_tooth_case(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
        tooth_position = self.__validate_tooth_position(tooth_position)
        # ai_status = False
        if url:
            if self.__cookies:
                self.driver.context.add_cookies(self.__cookies)
                self.open_url(url)
            else:
                self.__login_page.login_account(self.__login_page.login_username, self.__login_page.login_password)

            ai_status = True  # URL需要定位到患者详情页，并且DCM渲染完成
        else:
            self.__patients_page.create_patient(self.__patient_name)
            page_url = self.get_page_url()
            # ai_status = True
            self.wait_for_time(500)
            if "patientID" not in page_url:
                self.__logger.error(f"patientID not found in url: {page_url}")
                raise RuntimeError("cannot find patientID in url")
            ai_status = self.__dcm_upload(dcm_dir, ct_name)
        if ai_status:
            self.wait_for_time(1000)  # 添加延时，触发系统判定
            self.__create_tooth(tooth_position)
            return tooth_position
        else:
            self.__logger.error(f"DCM is not segmentation")
            return None

    def __get_current_surgical_path(
            self,
    ) -> dict:
        """返回当前治疗路径标题。"""
        wrapper_selector = "div.ant-steps-item-wrapper:visible"
        wrapper_count = self.count_elements(wrapper_selector)
        if wrapper_count <= 0:
            return {}

        surgical_path = {}
        wrappers = self.driver.locator(wrapper_selector)
        for index in range(wrapper_count):
            wrapper = wrappers.nth(index)
            content = wrapper.locator(".ant-steps-item-content")
            source = content.first if content.count() > 0 else wrapper

            raw_text = source.inner_text(timeout=5000).strip()
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

            if lines and lines[0].isdigit() and len(lines) > 1:
                title = lines[1]
            elif lines:
                title = lines[0]
            else:
                title = ""

            surgical_path[index + 1] = title

        return surgical_path

    def treatment_path(self, url: str, tooth_position: int):
        tooth_position = self.__validate_tooth_position(tooth_position)
        if url:
            self.add_cookies(self.__cookies)
            self.open_url(url)
        tooth_label = self.__tooth_selector("tooth_label_template", tooth_position, required=True)
        self.click_nth(tooth_label, 0)
        ele = self.get_by_text("治疗路径")
        if ele:
            return True
        else:
            return False

    """******************************************* 用例流程 ******************************************************************"""

    def case_drop_surgical(self, url: str, tooth_position: int):
        """ 手术阶拖曳排序测试 """
        surgical = self.treatment_path(url, tooth_position)
        if not surgical:
            raise RuntimeError("treatment path is not ready")
        before = self.__get_current_surgical_path()
        print(before)
        self.__drag_surgical()
        after = self.__get_current_surgical_path()
        print(after)
        return not (after == before)

    def case_refresh_drop_surgical(self, url, tooth_position):
        """ 手术阶段拖曳排序保存测试 """
        surgical = self.treatment_path(url, tooth_position)
        if not surgical:
            raise RuntimeError("treatment path is not ready")
        before = self.__get_current_surgical_path()
        print(before)
        if self.logger:
            self.logger.info(f"before: {before}")
        self.__drag_surgical()
        self.treatment_path('', tooth_position)
        self.wait_for_time(1000)
        self.treatment_path('', tooth_position)
        after = self.__get_current_surgical_path()
        print(after)
        if self.logger:
            self.logger.info(f"after: {after}")
        return not (after == before)

    def case_create_tooth(self, tooth_position_list: list) -> list:
        """创建患者后批量创建牙位病例。"""
        msg_list = []
        self.__patients_page.create_patient(self.__random.random_chinese_name())
        for tooth_position in tooth_position_list:
            msg_list.append(self.__create_tooth(tooth_position))
        return msg_list

    def case_create_design(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
        """创建完整手术设计流程。"""
        # page_status = self.treatment_path_manager(url, tooth_position, dcm_dir, ct_name)
        tooth_status = self.create_tooth_case(url, tooth_position, dcm_dir, ct_name)
        surgical = self.treatment_path('', tooth_position)
        page_status = tooth_status and surgical
        if page_status:
            self.create_design_and_wait_progress(tooth_position)
            self.select_implant(tooth_position)
            self.skip_apex_adjustment()
            return self.__patients_page.search_design(self.__patient_name, "设计完成")
        else:
            self.logger.error("tooth_position not found")
            raise


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = DesignManager(page, log)
        # pp.create_design('', 45, "./data/dicom/wujia", "术前手术")
        # print(pp.case_create_design('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32))
        # print(pp.get_current_surgical_path('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32))
        pp.case_refresh_drop_surgical('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32)
        # print(pp.case_create_tooth([13, 15, 17]))
        # print(pp.case_create_design('', 43, './data/dicom/wujia', "术前手术"))

        # pp.create_patient_invalid('test')
        # res = pp._read_case_tooth_positions(
        #     'https://x.finetool.cn/createDesign?surgicalDesignID=677156612823187456&mode=edit&patientID=677134467964960768&medicalRecordID=677156587053318144')
        # print(res)
    finally:
        manager.close()
