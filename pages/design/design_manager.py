import time
from typing import List, Optional, Tuple

from pages.login.login_manager import LoginPage
from core.base_page import BasePage
from pages.design.design_treatment_manager import (
    ADD_DESIGN_COMMAND,
    DELETE_DESIGN_COMMAND,
    DELETE_TREATMENT_SEQUENCE_COMMAND,
    DesignTreatmentMixin,
    SORT_TREATMENT_SEQUENCE_COMMAND,
    TREATMENT_SEQUENCE_COMMAND,
)
from pages.design.design_upload_manager import DesignUploadMixin, UPLOAD_TYPE_CONFIG
from pages.patient_manager.patient_manager import PatientsPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager

DESIGN_LOCATORS_PATH = "data/ui/design/design_page.yaml"
UPPER_TOOTH_POSITIONS = frozenset((17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27))
LOWER_TOOTH_POSITIONS = frozenset((31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47))
STANDARD_TOOTH_POSITIONS = UPPER_TOOTH_POSITIONS | LOWER_TOOTH_POSITIONS


class DesignManager(DesignTreatmentMixin, DesignUploadMixin, BasePage):
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
        self._init_upload_state(self.__design_path)
        self.__patient_name = "T_" + self.__random.random_chinese_name()
        self._init_treatment_state(
            self.__design_path,
            self.__login_page,
            self.__patients_page,
            self.__random,
            self.__patient_name,
            self.__cookies,
        )

    def _sync_design_patient_name(self, patient_name: str) -> None:
        """同步抽离模块中的患者名到设计页主对象。"""
        self.__patient_name = patient_name

    def _sync_design_cookies(self, cookies) -> None:
        """同步抽离模块中的 cookies 到设计页主对象。"""
        self.__cookies = cookies

    def _validate_treatment_tooth_position(self, tooth_position: int) -> int:
        """供治疗路径模块复用牙位校验。"""
        return self.__validate_tooth_position(tooth_position)

    def _treatment_tooth_selector(self, locator_key: str, tooth_position: int, required: bool = True) -> Optional[str]:
        """供治疗路径模块复用牙位定位格式化。"""
        return self.__tooth_selector(locator_key, tooth_position, required=required)

    def _create_treatment_tooth(self, tooth_positions: List[int]) -> str:
        """供治疗路径模块复用病例创建流程。"""
        return self.__create_tooth(tooth_positions)

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

    @classmethod
    def __validate_tooth_positions(cls, tooth_positions: List[int]) -> List[int]:
        """校验非空且同颌的牙位列表。"""
        if not isinstance(tooth_positions, list):
            raise ValueError("tooth_positions must be list")
        if not tooth_positions:
            raise ValueError("tooth_positions cannot be empty")

        validated_positions = [cls.__validate_tooth_position(position) for position in tooth_positions]
        has_upper = any(position in UPPER_TOOTH_POSITIONS for position in validated_positions)
        has_lower = any(position in LOWER_TOOTH_POSITIONS for position in validated_positions)
        if has_upper and has_lower:
            raise ValueError("tooth_positions cannot contain both upper and lower jaw positions")
        return validated_positions

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

    def __input_label(self, label_name):
        """输入病例标签。"""
        selector = self.__selector_design("input_label")
        input_role = self.__selector_design("input_combobox")
        # print(selector)
        if not selector:
            return False
        self.click(selector)
        return self.type_text_role(str(input_role), label_name)

    def __latest_create_tooth_message(
            self,
            ignored_messages: Optional[set[str]] = None,
            timeout_ms: int = 3000,
    ) -> str:
        """读取最新病例创建提示，可跳过已知旧提示。"""
        ignored_messages = ignored_messages or set()
        message_selector = self.__selector_design("create_tooth_msg", required=True)
        deadline = time.time() + timeout_ms / 1000
        last_message = ""

        while time.time() < deadline:
            try:
                messages = [
                    text.strip()
                    for text in self.get_locator(message_selector).all_inner_texts()
                    if text and text.strip()
                ]
                if messages:
                    last_message = messages[-1]
                    if last_message not in ignored_messages:
                        return last_message
            except Exception as e:
                if self.__logger:
                    self.__logger.info(f"Create tooth message is not ready: {e}")
            self.wait_for_time(200)
        return last_message

    def __create_tooth(self, tooth_positions: List[int]) -> str:
        """创建同一颌牙位列表对应的单个病例。"""
        tooth_positions = self.__validate_tooth_positions(tooth_positions)
        page_url = self.get_page_url()
        self.wait_for_time(500)
        if "patientID" not in page_url:
            self.__logger.error(f"patientID not found in url: {page_url}")
            raise RuntimeError("cannot find patientID in url")
        case_list = self.__read_case_tooth_positions(self.get_page_url())  # 获取所有牙位
        is_duplicate_tooth = bool(
            case_list
            and any(
                str(tooth_position) in case_tooth_text
                for tooth_position in tooth_positions
                for case_tooth_text in case_list
            )
        )

        # 新建病例
        if not self.click(self.__selector_design("new_case_button", required=True)):
            raise RuntimeError("failed to open create tooth dialog")
        for tooth_position in tooth_positions:
            self.__click_tooth_by_arch("tooth_path_template", tooth_position)

        # 标签输入
        # self._input_label(f"牙位：{tooth_position}")
        tooth_label = ",".join(str(position) for position in tooth_positions)
        selector = self.__selector_design("input_label", required=True)
        input_role = self.__selector_design("input_combobox", required=True)
        self.click(selector)
        self.type_text_role(str(input_role), f"牙位：{tooth_label}")
        self.click(self.__selector_design("save_button", required=True))

        # 获取弹窗文本
        ignored_messages = {"操作成功"} if is_duplicate_tooth else None
        alert_text = self.__latest_create_tooth_message(ignored_messages=ignored_messages)
        if is_duplicate_tooth:
            self.click(self.__selector_design("cancel_button", required=True))
        self.wait_for_time(1000)
        return alert_text

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

    def __wait_create_design_progress(
            self,
            tooth_position: int,
            create_design_button: str,
            progress: str,
            ready_selector: str,
    ) -> dict:
        """等待创建设计进度结束，并返回进度耗时与就绪状态。"""
        progress_was_visible = False
        progress_locator = self.driver.locator(progress)
        start_time = time.time()
        deadline = start_time + 180
        ready = False
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
                ready = True
                break
            self.wait_for_time(500)
        else:
            # self.take_screenshot("dcm_download_timeout")
            raise RuntimeError(f"create design progress did not complete for tooth position {tooth_position}")

        # self.take_screenshot("dcm_download")
        self.wait_for_time(10000)
        return {
            "created": True,
            "progress_duration_ms": self._elapsed_ms(start_time),
            "ready": ready,
        }

    def __create_design_context(self) -> Tuple[str, str, str]:
        """读取创建设计需要的按钮、进度条和就绪态定位。"""
        create_design_button = self.__selector_design("create_design_button", required=True)
        progress = self.__selector_design("progressbar", required=True)
        ready_selector = (
                self.__selector_design("implant_design_ready_button")
                or self.__selector_design("tool_button")
        )
        if not create_design_button or not progress or not ready_selector:
            raise RuntimeError("create design button, progressbar or tool button locator is not configured")
        return create_design_button, progress, ready_selector

    def create_design_and_wait_progress(self, tooth_position: int) -> None:
        """触发创建设计并等待进度完成。"""
        self.__create_design_and_wait_progress_report(tooth_position)

    def __create_design_and_wait_progress_report(self, tooth_position: int) -> dict:
        """触发 CT 创建设计并返回进度报告。"""
        self.__validate_tooth_position(tooth_position)
        # tooth_label = self._selector_design("tooth_label_template").format(tooth_position=tooth_position)
        self.wait_for_time(500)
        create_design_button, progress, ready_selector = self.__create_design_context()

        # self.click_nth(tooth_label, 0)
        self.click_role("button", role_name=create_design_button)
        return self.__wait_create_design_progress(tooth_position, create_design_button, progress, ready_selector)

    def __load_model_dialog(self):
        """返回“加载模型”弹窗定位器。"""
        dialog_selector = self.__selector_design("load_model_dialog")
        if dialog_selector:
            return self.driver.locator(dialog_selector)
        dialog_name = self.__selector_design("load_model_dialog_name", required=True)
        return self.driver.get_by_role("dialog", name=dialog_name)

    def __select_load_model(self, dialog, model_name: str) -> None:
        """在加载模型弹窗中按模型名称勾选 CT 或 STL 模型。"""
        if not model_name:
            raise ValueError("model_name cannot be empty")

        item_template = self.__selector_design("load_model_item_template", required=True)
        checkbox_selector = self.__selector_design("load_model_checkbox", required=True)
        model_item = dialog.locator(item_template.format(model_name=model_name)).first
        model_item.wait_for(state="visible", timeout=10000)

        checkbox = model_item.locator(checkbox_selector).first
        try:
            if checkbox.is_checked(timeout=500):
                return
        except Exception:
            pass

        try:
            checkbox.set_checked(True, force=True)
        except Exception:
            model_item.click()

        if not checkbox.is_checked(timeout=1000):
            raise RuntimeError(f"failed to select load model: {model_name}")

    def __confirm_load_model_dialog(self, dialog) -> None:
        """确认加载模型弹窗。"""
        confirm_text = self.__selector_design("load_model_confirm_button_text", required=True)
        self.__click_implant_dialog_footer_button(dialog.first, confirm_text)
        dialog.first.wait_for(state="hidden", timeout=10000)

    def create_stl_design_and_wait_progress(
            self,
            tooth_position: int,
            ct_name: str,
            stl_name: str,
    ) -> None:
        """触发 CT+STL 创建设计，先选择加载模型，再等待设计进度完成。"""
        self.__create_stl_design_and_wait_progress_report(tooth_position, ct_name, stl_name)

    def __create_stl_design_and_wait_progress_report(
            self,
            tooth_position: int,
            ct_name: str,
            stl_name: str,
    ) -> dict:
        """触发 CT+STL 创建设计，选择加载模型后返回进度报告。"""
        self.__validate_tooth_position(tooth_position)
        self.wait_for_time(500)
        create_design_button, progress, ready_selector = self.__create_design_context()

        self.click_role("button", role_name=create_design_button)
        dialog = self.__load_model_dialog()
        dialog.first.wait_for(state="visible", timeout=10000)
        self.__select_load_model(dialog.first, ct_name)
        self.__select_load_model(dialog.first, stl_name)
        self.__confirm_load_model_dialog(dialog)
        return self.__wait_create_design_progress(tooth_position, create_design_button, progress, ready_selector)

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

    def __assertion_render_canvas(self, timeout_ms: int = 30000) -> dict:
        """检查可见画布是否有尺寸且不是空白画布。"""
        canvas_selector = self.__selector_design("render_canvas") or "canvas:visible"
        checked_at = self._now_iso()
        canvas = self.driver.locator(canvas_selector).first
        try:
            canvas.wait_for(state="visible", timeout=timeout_ms)
            result = canvas.evaluate(
                """canvas => {
                    const width = canvas.width || canvas.clientWidth || 0;
                    const height = canvas.height || canvas.clientHeight || 0;
                    const visible = !!(canvas.offsetWidth || canvas.offsetHeight || canvas.getClientRects().length);
                    if (!visible || width <= 0 || height <= 0) {
                        return {canvas_visible: visible, canvas_width: width, canvas_height: height, non_blank: false};
                    }

                    const webgl = canvas.getContext('webgl2') || canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (webgl) {
                        const sampleWidth = Math.max(1, Math.min(width, 64));
                        const sampleHeight = Math.max(1, Math.min(height, 64));
                        const pixels = new Uint8Array(sampleWidth * sampleHeight * 4);
                        webgl.readPixels(0, 0, sampleWidth, sampleHeight, webgl.RGBA, webgl.UNSIGNED_BYTE, pixels);
                        return {
                            canvas_visible: visible,
                            canvas_width: width,
                            canvas_height: height,
                            non_blank: pixels.some(value => value !== 0)
                        };
                    }

                    const context2d = canvas.getContext('2d');
                    if (!context2d) {
                        return {canvas_visible: visible, canvas_width: width, canvas_height: height, non_blank: true};
                    }
                    const sampleWidth = Math.max(1, Math.min(width, 64));
                    const sampleHeight = Math.max(1, Math.min(height, 64));
                    const data = context2d.getImageData(0, 0, sampleWidth, sampleHeight).data;
                    return {
                        canvas_visible: visible,
                        canvas_width: width,
                        canvas_height: height,
                        non_blank: Array.from(data).some(value => value !== 0)
                    };
                }"""
            )
            if not result.get("non_blank"):
                screenshot_bytes = canvas.screenshot(type="png")
                result["non_blank"] = self._png_idat_has_variation(screenshot_bytes)
                result["screenshot_bytes"] = len(screenshot_bytes)
            result["checked_at"] = checked_at
            return result
        except Exception as e:
            if self.__logger:
                self.__logger.error(f"render canvas check failed: {e}")
            return {
                "canvas_visible": False,
                "canvas_width": 0,
                "canvas_height": 0,
                "non_blank": False,
                "checked_at": checked_at,
                "error": str(e),
            }

    def create_tooth_case(
            self,
            tooth_position: int,
    ):
        """在当前患者页面为目标牙位创建病例。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        page_url = self.get_page_url()
        if "patientID" not in page_url:
            self.__logger.error(f"patientID not found in url: {page_url}")
            raise RuntimeError("cannot find patientID in url")
        self.wait_for_time(1000)  # 添加延时，触发系统判定
        self.__create_tooth([tooth_position])
        return tooth_position

    def case_create_tooth(self, tooth_position_list: list) -> list:
        """创建患者后按牙位列表创建一个病例。"""
        tooth_position_list = self.__validate_tooth_positions(tooth_position_list)
        self.__patients_page.create_patient("T_" + self.__random.random_chinese_name())
        return [self.__create_tooth(tooth_position_list)]

    def case_create_duplicate_tooth_detection(self, tooth_positions: list[int]) -> dict:
        """创建患者并重复创建同牙位病例，返回两次创建提示供测试断言。"""
        tooth_positions = self.__validate_tooth_positions(tooth_positions)
        patient_name = "T_" + self.__random.random_chinese_name()
        self.__patients_page.create_patient(patient_name)

        first_message = self.__create_tooth(tooth_positions)
        duplicate_message = self.__create_tooth(tooth_positions)
        return {
            "patient_name": patient_name,
            "tooth_positions": tooth_positions,
            "first_message": first_message,
            "duplicate_message": duplicate_message,
            "url": self.get_page_url(),
        }

    def cleanup_created_patients(self) -> list[dict]:
        """清理设计页流程中通过患者页真实创建的患者。"""
        return self.__patients_page.cleanup_created_patients()

    def __new_design_report(self, tooth_position: int) -> dict:
        """创建完整设计诊断报告的基础结构。"""
        self.__patient_name = "T_" + self.__random.random_chinese_name()
        return {
            "patient_name": self.__patient_name,
            "tooth_position": tooth_position,
            "uploads": {},
            "ai": {},
            "render": {},
            "case": {
                "created_tooth_position": None,
                "treatment_path_ready": False,
            },
            "design": {
                "created": False,
                "progress_duration_ms": 0,
                "ready": False,
                "final_search_success": False,
            },
        }

    @staticmethod
    def __upload_assertion_report(upload_report: dict) -> dict:
        """移除上传报告中的 AI 子对象，避免上传结果和 AI 结果重复表达同一内容。"""
        return {
            key: value
            for key, value in upload_report.items()
            if key != "ai"
        }

    def __open_or_create_patient_for_design(self, url: str) -> None:
        """打开已有患者设计页，或创建新患者并进入设计页。"""
        if url:
            self.__login_page.refresh_cookies()
            self.__cookies = self.__login_page.cookies
            if self.__cookies:
                self.driver.context.add_cookies(self.__cookies)
            else:
                self.__login_page.login_account(self.__login_page.username, self.__login_page.password)
            self.open_url(url)
            return

        self.__patients_page.create_patient(self.__patient_name)
        self.wait_for_time(500)
        if "patientID" not in self.get_page_url():
            self.__logger.error(f"patientID not found in url: {self.get_page_url()}")
            raise RuntimeError("cannot find patientID in url")

    def case_create_ct_design_report(
            self,
            url: str,
            tooth_position: int,
            ct_path: str = '',
            ct_name: str = '',
    ) -> dict:
        """运行 CT 完整设计流程，并返回上传、AI、渲染和最终状态报告。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        self._collect_files_by_extensions(ct_path, UPLOAD_TYPE_CONFIG["ct"]["extensions"])
        report = self.__new_design_report(tooth_position)
        self.__open_or_create_patient_for_design(url)

        ct_upload_report = self._upload_patient_data_report("ct", ct_path, ct_name)
        report["uploads"]["ct"] = self.__upload_assertion_report(ct_upload_report)
        report["ai"]["ct"] = ct_upload_report["ai"]

        tooth_status = self.create_tooth_case(tooth_position) if ct_upload_report["success"] else None
        report["case"]["created_tooth_position"] = tooth_status
        surgical = self._open_created_case_treatment_path(tooth_position)
        report["case"]["treatment_path_ready"] = bool(surgical["treatment_visible"])

        if tooth_status and surgical["treatment_visible"]:
            design_report = self.__create_design_and_wait_progress_report(tooth_position)
            report["design"].update(design_report)
            report["render"]["ct"] = self.__assertion_render_canvas()
            self.select_implant(tooth_position)
            self.skip_apex_adjustment()
            report["design"]["final_search_success"] = self.__patients_page.search_design(
                self.__patient_name,
                "设计完成",
            )
            report["patient_url"] = surgical["patient_url"]
            report["url"] = surgical["patient_url"]
            return report

        self.logger.error("tooth_position not found")
        raise RuntimeError("tooth_position not found")

    def case_create_stl_design_report(
            self,
            url: str,
            tooth_position: int,
            ct_path: str = '',
            ct_name: str = '',
            stl_path: str = '',
            stl_name: str = '',
            stl_type: str = 'low_stl',
    ) -> dict:
        """运行 CT+STL 完整设计流程，并返回上传、AI、渲染和最终状态报告。"""
        tooth_position = self.__validate_tooth_position(tooth_position)
        self._collect_files_by_extensions(ct_path, UPLOAD_TYPE_CONFIG["ct"]["extensions"])
        if stl_type == "ct":
            raise ValueError("stl_type must be one of up_stl, low_stl, other_stl")
        stl_config = self._upload_type_config(stl_type)
        self._collect_files_by_extensions(stl_path, stl_config["extensions"])

        report = self.__new_design_report(tooth_position)
        self.__open_or_create_patient_for_design(url)

        ct_upload_report = self._upload_patient_data_report("ct", ct_path, ct_name)
        report["uploads"]["ct"] = self.__upload_assertion_report(ct_upload_report)
        report["ai"]["ct"] = ct_upload_report["ai"]
        if not ct_upload_report["success"]:
            raise RuntimeError("CT upload or AI parsing failed")

        stl_upload_report = self._upload_patient_data_report(stl_type, stl_path, stl_name)
        report["uploads"]["stl"] = self.__upload_assertion_report(stl_upload_report)

        tooth_status = self.create_tooth_case(tooth_position) if stl_upload_report["success"] else None
        report["case"]["created_tooth_position"] = tooth_status
        surgical = self._open_created_case_treatment_path(tooth_position)
        report["case"]["treatment_path_ready"] = bool(surgical["treatment_visible"])

        if tooth_status and surgical["treatment_visible"]:
            design_report = self.__create_stl_design_and_wait_progress_report(tooth_position, ct_name, stl_name)
            report["design"].update(design_report)
            render_report = self.__assertion_render_canvas()
            report["render"]["ct"] = render_report
            report["render"]["stl"] = dict(render_report)
            self.select_implant(tooth_position)
            self.skip_apex_adjustment()
            report["design"]["final_search_success"] = self.__patients_page.search_design(
                self.__patient_name,
                "设计完成",
            )
            report["patient_url"] = surgical["patient_url"]
            report["url"] = surgical["patient_url"]
            return report

        self.logger.error("tooth_position not found")
        raise RuntimeError("tooth_position not found")

    def case_create_ct_design(
            self,
            url: str,
            tooth_position: int,
            ct_path: str = '',
            ct_name: str = '',
    ):
        """组合 CT 完整设计用例：建患者、上传 CT、建病例、创建设计并选择植体。"""
        report = self.case_create_ct_design_report(url, tooth_position, ct_path, ct_name)
        return report["design"]["final_search_success"]

    def case_create_stl_design(
            self,
            url: str,
            tooth_position: int,
            ct_path: str = '',
            ct_name: str = '',
            stl_path: str = '',
            stl_name: str = '',
            stl_type: str = 'low_stl',
    ):
        """组合 CT+STL 完整设计用例：上传 CT 和口扫模型后，选择模型并完成完整设计。"""
        report = self.case_create_stl_design_report(
            url,
            tooth_position,
            ct_path,
            ct_name,
            stl_path,
            stl_name,
            stl_type,
        )
        return report["design"]["final_search_success"]


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = DesignManager(page, log)
        # pp.create_design('', 45, "./data/dicom/wujia", "术前手术")
        # print(pp.case_create_ct_design('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32))
        # print(pp.get_current_surgical_path('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32))
        pp.case_refresh_drop_surgical(32)
        # print(pp.case_create_tooth([13, 15, 17]))
        # print(pp.case_create_ct_design('', 43, './data/dicom/wujia', "术前手术"))

    finally:
        manager.close()
