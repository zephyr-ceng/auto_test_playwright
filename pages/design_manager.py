import re
import time
from collections import deque
from pathlib import Path
from typing import List, Optional

from pages.login_manager import LoginPage
from core.base_page import BasePage
from pages.patient_manager import PatientsPage
from utils.yaml_reader import YamlManager
from utils.random_manager import RandomManager


class DesignManager(BasePage):
    def __init__(self, driver, logger, design_path: str = "data/design_page.yaml"):
        super().__init__(driver)
        self._logger = logger
        self._login_page = LoginPage(driver)
        self._design_path = design_path
        self._config = YamlManager(self._logger)
        self._random = RandomManager()
        self._cookies = self._login_page.cookies
        self._patients_page = PatientsPage(driver)

        # design_page.yaml
        design_cfg = self._config.read(self._design_path)
        if design_cfg is None:
            raise RuntimeError(f"failed to read yaml config: {design_cfg}")
        self.design_url = design_cfg.get("url")
        self.design_locators = design_cfg.get("locators")

        # other
        self._responses = deque(maxlen=10)

    def _selector_design(self, key: str) -> Optional[str]:
        """ 元素查找 """
        return self.design_locators.get(key)

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

    def _dcm_upload(self, dcm_dir: str, ct_name: str, timeout_ms: int = 180000, target_status: int = 2) -> bool:
        """ 文件上传 """
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

    def _create_tooth(self, tooth_position: int) -> bool:
        """ 病例创建 """
        if not isinstance(tooth_position, int):
            raise ValueError("tooth_position must be int")
        self.click("button:has-text('新增病例')")
        if tooth_position in [17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27]:
            self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 0)
        elif tooth_position in [31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47]:
            self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 1)
        else:
            raise ValueError(f"tooth_position must be standard dental position")

        # self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 1)
        self.wait_for_time(300)
        self._input_label(f"牙位：{tooth_position}")
        self.click("button:has-text('保 存')")
        self.wait_for_time(1000)
        ele_count = self.count_elements("//div[contains(@class,'bg-[#232323]')]")
        if ele_count > 0:
            print(ele_count)
            return True
        return False

    def create_design(self, url: str, tooth_position: int, dcm_dir: str = '', ct_name: str = ''):
        """ 创建设计，URL需要定位到患者详情页，并且DCM渲染完成,URL下不需要写入DCM_dir,ct_name """
        ai_status = False
        if url:
            if self._cookies:
                self.driver.context.add_cookies(self._cookies)
                self.open_url(url)
            else:
                self._login_page.login_account(self._login_page.login_username, self._login_page.login_password)

            ai_status = True  # URL需要定位到患者详情页，并且DCM渲染完成
        else:
            page_url = self._patients_page.create_patient("T_" + self._random.random_chinese_name())
            if "patientID" not in page_url:
                self._logger.error(f"patientID not found in url: {page_url}")
                raise RuntimeError("cannot find patientID in url")
            ai_status = self._dcm_upload(dcm_dir, ct_name)
        if ai_status:
            self._create_tooth(tooth_position)
            self.click_nth(f"span:has-text('{tooth_position}')", 0)
            self.driver.get_by_role("button", name="创建设计").click()
            progress = self.driver.locator('[role="progressbar"]')
            # 等待进度条出现
            progress.wait_for()
            while True:
                value = progress.get_attribute("aria-valuenow")
                percent = int(value) if value else 0
                print("当前进度:", percent)
                # TODO: 并不能监听到100,无法稳定的监听到下载进度
                if percent >= 99:
                    break
            self.take_screenshot("dcm_download")
            self.wait_for_time(10000)
            self.click_nth("div._tool-btn_m3ugk_1", 0)
            # (self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 0) or self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 1))
            self.click_nth(f"[role='dialog'] svg path[data-name='{tooth_position}']", 1)
            self.driver.get_by_role("button", name="选择植体").click()
            self.wait_for_time(1000)
            self.driver.get_by_role("button", name="collapsed 士卓曼").click()
            self.driver.locator("div").filter(has_text=re.compile(r"^骨水平种植体$")).nth(1).click()
            self.driver.get_by_text("021.2608").click()
            self.driver.get_by_label("选择植体").get_by_role("button", name="确 定").click()
            self.wait_for_time(500)
            self.driver.get_by_role("button", name="确 定").click()
            # self.wait_for_time(50000)
        else:
            self._logger.error(f"DCM is not segmentation")


if __name__ == "__main__":
    from core.browser_manager import BrowserManager
    from utils.logger import Logger

    log = Logger("patients")
    manager = BrowserManager(browser_type="chromium", headless=False, logger=log)
    try:
        page = manager.start()
        pp = DesignManager(page, log)
        pp.create_design("https://x.finetool.cn/createDesign?patientID=672043815051198464", 32)
        # pp.create_patient_invalid('test')
    finally:
        manager.close()
