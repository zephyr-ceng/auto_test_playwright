import re
import random
import time
from collections import deque
from datetime import date
from pathlib import Path
from typing import List, Optional

from twisted.names import authority

from pages.login_manager import LoginPage
from core.base_page import BasePage
from pages.patient_manager import PatientsPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager


class DesignManager(BasePage):
    """设计管理页面对象，封装 DICOM 上传、病例牙位、创建设计和植体选择流程。"""

    def __init__(self, driver, logger, design_path: str = "data/design_page.yaml"):
        """
        初始化设计管理页面。

        Args:
            driver: Playwright page 实例。
            logger: 项目日志对象。
            design_path: 设计页面 YAML 配置路径，默认读取 `data/design_page.yaml`。
        """
        super().__init__(driver, logger)
        self._logger = logger
        self._login_page = LoginPage(driver, self._logger)
        self._design_path = design_path
        self._config = YamlManager(self._logger)
        self._random = RandomManager()
        self._cookies = self._login_page.cookies
        self._patients_page = PatientsPage(driver, self._logger)

        # design_page.yaml
        design_cfg = self._config.read(self._design_path)
        if design_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {design_cfg}")
        self.design_url = self.build_url(self._login_page.base_url, design_cfg.get("url"))
        self.design_locators = design_cfg.get("locators")

        # other
        self._responses = deque(maxlen=10)
        self._patient_name = "T_" + self._random.random_chinese_name()
        self._treatment_path_ready = False
        self._treatment_path_context = {}

    def _selector_design(self, key: str):
        """
        按 key 获取设计页面定位表达式。

        Args:
            key: `data/design_page.yaml` 中 `locators` 下的定位 key。

        Returns:
            命中的定位表达式；未配置时返回 None。
        """
        return self.design_locators.get(key)

    def _read_case_tooth_positions(self, url: str = "") -> Optional[List[str]]:
        """
        读取设计页病例列表中的所有病例牙位文本。

        Args:
            url: 需要访问的设计页地址；支持完整 URL、path、query 或空字符串。

        Returns:
            存在病例牙位时返回去重后的牙位文本数组；不存在时返回 None。

        Raises:
            RuntimeError: 未配置 cookies 或病例卡片定位器时抛出。
        """

        if "patientID" not in url:
            print(f"当前页面不在患者详情页，{url}")
            if self._logger:
                self._logger.error(f"当前页面不在患者详情页，{url}")
            return None

        selector = self._selector_design("case_tooth_position_cards")
        if not selector:
            raise RuntimeError("locator `case_tooth_position_cards` is not configured")

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
    def _file_is_dcm(dcm_dir: str) -> List[str]:
        """
        获取目录中的 DICOM 文件列表。

        Args:
            dcm_dir: DICOM 文件目录，支持项目相对路径或绝对路径。

        Returns:
            排序后的 `.dcm` / `.DCM` 文件绝对路径列表。

        Raises:
            FileNotFoundError: 目录不存在、路径不是目录或目录内没有 DICOM 文件。
        """
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
        """
        处理 Playwright response 事件，捕获 AI 任务状态。

        Args:
            response: Playwright 响应对象。

        Side Effects:
            当响应中包含文件状态时，将 `aiTaskStatus` 写入 `_responses` 队列。
        """
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
                        if self._logger:
                            self._logger.info(log_msg)
            except ValueError as e:  # 更精确的异常处理（JSON解析错误）
                if self._logger:
                    self._logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)
            except Exception as e:  # 其他异常
                if self._logger:
                    self._logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)

    def _is_ai_status(self, target_status=2, timeout_ms=180000):
        """
        持续监听接口响应，判断 AI 任务是否到达目标状态。

        Args:
            target_status: 期望捕获的 AI 状态，默认 2 表示处理成功。
            timeout_ms: 最大等待时间，单位毫秒。

        Returns:
            捕获到目标状态返回 True，超时返回 False。
        """
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
        """
        在病例标签输入框中输入标签名称。

        Args:
            label_name: 要输入的标签文本，例如 `牙位：32`。

        Returns:
            输入成功返回 True，定位缺失或输入失败返回 False。
        """
        selector = self._selector_design("input_label")
        input_role = self._selector_design("input_combobox")
        # print(selector)
        if not selector:
            return False
        self.click(selector)
        return self.type_text_role(str(input_role), label_name)

    def _dcm_upload(self, dcm_dir: str, ct_name: str, timeout_ms: int = 180000, target_status: int = 2) -> bool:
        """
        上传 DICOM 文件并等待 AI 渲染状态。

        Args:
            dcm_dir: DICOM 文件目录，支持项目相对路径或绝对路径。
            ct_name: 上传模型名称。
            timeout_ms: 等待 AI 状态的超时时间，单位毫秒。
            target_status: 期望的 AI 任务状态，默认 2。

        Returns:
            AI 状态达到目标值返回 True，否则返回 False。

        Raises:
            RuntimeError: 上传入口、模型名称输入框或确认按钮定位缺失。
            FileNotFoundError: DICOM 目录或文件不存在。
        """
        # self.create_patient(self._random.random_chinese_name())  # TODO: 暂时使用手动创建用户
        # self._open_url()
        # TODO: 添加当前页面判定
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
        if self._logger:
            self._logger.info(f"DCM渲染状态为{status}")
        return status

    def _create_tooth(self, tooth_position: int) -> str:
        """
        创建指定牙位的病例。

        Args:
            tooth_position: 标准牙位编号，例如 32。

        Returns:
            创建后页面出现病例卡片返回 True，否则返回 False。

        Raises:
            ValueError: `tooth_position` 不是整数，或不是支持的标准牙位。
        """
        if not isinstance(tooth_position, int):
            raise ValueError("tooth_position must be int")
        page_url = self.get_page_url()
        self.wait_for_time(500)
        if "patientID" not in page_url:
            self._logger.error(f"patientID not found in url: {page_url}")
            raise RuntimeError("cannot find patientID in url")
        case_list = self._read_case_tooth_positions(self.get_page_url())  # 获取所有牙位

        # 新建病例
        self.click(self._selector_design("new_case_button"))
        tooth_selector = self._selector_design("tooth_path_template").format(tooth_position=tooth_position)
        if tooth_position in [17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27]:
            self.click_nth(tooth_selector, 0)
        elif tooth_position in [31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47]:
            self.click_nth(tooth_selector, 1)
        else:
            raise ValueError(f"tooth_position must be standard dental position")
        self.wait_for_time(300)

        # 标签输入
        # self._input_label(f"牙位：{tooth_position}")
        selector = self._selector_design("input_label")
        input_role = self._selector_design("input_combobox")
        self.click(selector)
        self.type_text_role(str(input_role), f"牙位：{tooth_position}")
        self.click(self._selector_design("save_button"))

        # 获取弹窗文本
        alert_text = self.get_locator(self._selector_design("create_tooth_msg")).inner_text()
        if case_list:
            if str(tooth_position) in case_list:
                self.click(self._selector_design("cancel_button"))
        self.wait_for_time(1000)
        return alert_text

    def _drag_surgical(self) -> bool:
        """
        Reorder the 5th visible surgical stage to the 6th visible stage position.

        Returns:
            True when the visible surgical stage order changed; otherwise False.

        Raises:
            RuntimeError: Surgical stage draggable locator is not configured.
        """
        surgical_stage_cards = self._selector_design("surgical_stage_draggable_cards")
        if not surgical_stage_cards:
            raise RuntimeError("locator `surgical_stage_draggable_cards` is not configured")

        changed = self.drag_nth_locator_to_nth_locator(
            surgical_stage_cards,
            4,
            5,
            screenshot_name="surgical_stage_drag",
        )
        if self._logger:
            self._logger.info(f"Surgical stage drag changed={changed}")
        return changed

    def _dragg_surgical(self) -> bool:
        """Backward-compatible wrapper for the old misspelled method name."""
        return self._drag_surgical()

    """******************************************* public function ******************************************************************"""

    def is_create_design_progress_completed(
            self,
            progress_selector: str,
            create_design_button: str,
            ready_selector: str,
            progress_was_visible: bool = False,
            elapsed_ms: int = 0,
    ) -> bool:
        """
        判断创建设计进度是否已经完成。

        不读取进度百分比；只通过页面状态判断完成态：
        进度条出现后隐藏/移除，或进度条未捕获但等待过短暂兜底时间后，
        “创建设计”入口已消失且下游操作区可见。
        """
        ready_locator = self.driver.locator(ready_selector)
        progress_locator = self.driver.locator(progress_selector)
        create_button_locator = self.driver.get_by_role("button", name=create_design_button)
        try:
            progress_visible = progress_locator.count() > 0 and progress_locator.first.is_visible(timeout=200)
        except Exception as e:
            if self._logger:
                self._logger.info(f"Create design progress bar is no longer visible: {e}")
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
        """
        触发指定牙位的创建设计流程并等待进度完成。

        Args:
            tooth_position: 已创建病例的牙位编号。

        Side Effects:
            点击“创建设计”，等待进度条出现，并轮询到完成态。
        """
        # tooth_label = self._selector_design("tooth_label_template").format(tooth_position=tooth_position)
        self.wait_for_time(500)
        create_design_button = self._selector_design("create_design_button")
        progress = self._selector_design("progressbar")
        ready_selector = self._selector_design("tool_button")
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

    def select_implant(self, tooth_position: int) -> None:
        """
        为指定牙位选择植体系统、类型和型号。

        Args:
            tooth_position: 需要选择植体的牙位编号。

        Side Effects:
            打开植体选择弹窗，选择士卓曼骨水平种植体 `021.2608` 并确认。
        """
        self.click_nth(self._selector_design("tool_button"), 0)
        # (self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 0) or self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 1))
        tooth_selector = self._selector_design("implant_tooth_path_template").format(tooth_position=tooth_position)
        # self.click_nth(tooth_selector, 1)  # 点击牙位
        # TODO: 添加牙位判定
        if tooth_position in [17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27]:
            self.click_nth(tooth_selector, 0)
        elif tooth_position in [31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47]:
            self.click_nth(tooth_selector, 1)
        else:
            raise ValueError(f"tooth_position must be standard dental position")
        self.click_role("button", role_name=self._selector_design("select_implant_button"))  # 选择植体
        self.wait_for_time(2000)

        # TODO:植体品牌先保持默认,索引更新，需要重新编辑
        # self.driver.get_by_role("button", name="collapsed 士卓曼").click()  # 选择品牌
        # self.driver.locator("div").filter(has_text=re.compile(r"^骨水平种植体$")).nth(1).click()  # 选择植体类别
        # self.driver.get_by_text("021.2608").click()  # 选择植体型号
        self.driver.get_by_role("button", name="collapsed Straumann").click()
        self.driver.locator("div").filter(has_text=re.compile(r"^Bone Level X Roxolid SLActive$")).first.click()
        self.driver.get_by_text("061.3308").click()
        self.click_nth(self._selector_design("final_confirm_button"), 0)  # 点击确认植体
        self.wait_for_time(500)
        self.click_nth(self._selector_design("final_confirm_button"), 1)  # 点击确认添加

    def skip_apex_adjustment(self) -> None:
        """
        跳过牙尖点调整流程。

        Side Effects:
            依次点击“下一步：选择牙尖点”、“完成调整”和“暂时不用”。
        """
        self.click_role("button", role_name=self._selector_design("next_apex_button_text"))
        self.wait_for_time(2000)
        self.get_by_text("全部删除").wait_for(state="visible", timeout=10000)
        self.click_role("button", role_name=self._selector_design("finish_adjustment_button_text"))
        self.click_role("button", role_name=self._selector_design("skip_button_text"))

    def create_tooth_case(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
        # ai_status = False
        if url:
            if self._cookies:
                self.driver.context.add_cookies(self._cookies)
                self.open_url(url)
            else:
                self._login_page.login_account(self._login_page.login_username, self._login_page.login_password)

            ai_status = True  # URL需要定位到患者详情页，并且DCM渲染完成
        else:
            self._patients_page.create_patient(self._patient_name)
            page_url = self.get_page_url()
            # ai_status = True
            self.wait_for_time(500)
            if "patientID" not in page_url:
                self._logger.error(f"patientID not found in url: {page_url}")
                raise RuntimeError("cannot find patientID in url")
            ai_status = self._dcm_upload(dcm_dir, ct_name)
        if ai_status:
            self.wait_for_time(1000)  # 添加延时，触发系统判定
            self._create_tooth(tooth_position)
            return tooth_position
        else:
            self._logger.error(f"DCM is not segmentation")
            return None

    # def treatment_path_manager(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
    #     """ 手术路径管理 """
    #     tooth = self.create_tooth_case(url, tooth_position, dcm_dir, ct_name)
    #     if tooth:
    #         tooth_label = self._selector_design("tooth_label_template").format(tooth_position=tooth_position)
    #         self.click_nth(tooth_label, 0)
    #         ele = self.get_by_text("治疗路径")
    #         if ele:
    #             return True
    #         else:
    #             return False
    #     else:
    #         self.logger.error("tooth_position not found")
    #         raise

    def _get_current_surgical_path(
            self,
    ) -> dict:
        """Enter treatment path and return visible surgical path titles by 1-based index."""
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
        if url:
            self.add_cookies(self._cookies)
            self.open_url(url)
        tooth_label = self._selector_design("tooth_label_template").format(tooth_position=tooth_position)
        self.click_nth(tooth_label, 0)
        ele = self.get_by_text("治疗路径")
        if ele:
            return True
        else:
            return False

    """******************************************* case ******************************************************************"""

    def drop_surgical(self, url: str, tooth_position: int):
        """ 手术阶拖曳排序测试 """
        surgical = self.treatment_path(url, tooth_position)
        if not surgical:
            raise RuntimeError("treatment path is not ready")
        before = self._get_current_surgical_path()
        print(before)
        self._drag_surgical()
        after = self._get_current_surgical_path()
        print(after)
        return not (after == before)

    def refresh_drop_surgical(self, url, tooth_position):
        """ 手术阶段拖曳排序保存测试 """
        surgical = self.treatment_path(url, tooth_position)
        if not surgical:
            raise RuntimeError("treatment path is not ready")
        before = self._get_current_surgical_path()
        print(before)
        if self.logger:
            self.logger.info(f"before: {before}")
        self._drag_surgical()
        self.treatment_path('', tooth_position)
        self.treatment_path('', tooth_position)
        after = self._get_current_surgical_path()
        print(after)
        if self.logger:
            self.logger.info(f"after: {after}")
        print(after)
        return not (after == before)

    def case_create_tooth(self, tooth_position_list: list) -> list:
        msg_list = []
        self._patients_page.create_patient(self._random.random_chinese_name())
        for tooth_position in tooth_position_list:
            msg_list.append(self._create_tooth(tooth_position))
        return msg_list

    def case_create_design(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
        """
        创建完整手术设计流程。

        Args:
            url: 非空时打开已配置的设计页并认为 DICOM 已完成；为空时先创建患者并上传 DICOM。
            tooth_position: 目标牙位编号。
            dcm_dir: DICOM 文件目录；当 `url` 为空时必需。
            ct_name: DICOM 上传后的模型名称；当 `url` 为空时必需。

        Side Effects:
            可能创建患者、上传 DICOM、创建病例、触发设计生成并选择植体。
        """
        # page_status = self.treatment_path_manager(url, tooth_position, dcm_dir, ct_name)
        tooth_status = self.create_tooth_case(url, tooth_position, dcm_dir, ct_name)
        surgical = self.treatment_path('', tooth_position)
        page_status = tooth_status and surgical
        if page_status:
            self.create_design_and_wait_progress(tooth_position)
            self.select_implant(tooth_position)
            self.skip_apex_adjustment()
            return self._patients_page.search_design(self._patient_name, "设计完成")
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
        # pp.refresh_drop_surgical('https://x.finetool.cn/createDesign?patientID=680133214116421632', 32)
        print(pp.case_create_tooth([13, 15, 17]))
        print(pp.case_create_design('', 43, './data/dicom/wujia', "术前手术"))
        # pp.create_patient_invalid('test')
        # res = pp._read_case_tooth_positions(
        #     'https://x.finetool.cn/createDesign?surgicalDesignID=677156612823187456&mode=edit&patientID=677134467964960768&medicalRecordID=677156587053318144')
        # print(res)
    finally:
        manager.close()
