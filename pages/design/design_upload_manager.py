import re
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence


UPLOAD_TYPE_CONFIG = {
    "ct": {
        "button_key": "ct_dicom_type_button_name",
        "extensions": (".dcm",),
        "label": "CT数据",
        "wait_for_ai": True,
    },
    "up_stl": {
        "button_key": "up_stl_type_button_name",
        "extensions": (".stl", ".ply"),
        "label": "上颌口扫",
        "wait_for_ai": False,
    },
    "low_stl": {
        "button_key": "low_stl_type_button_name",
        "extensions": (".stl", ".ply"),
        "label": "下颌口扫",
        "wait_for_ai": False,
    },
    "other_stl": {
        "button_key": "other_stl_type_button_name",
        "extensions": (".stl", ".ply"),
        "label": "其他",
        "wait_for_ai": False,
    },
}


class DesignUploadMixin:
    """设计页患者数据上传、AI 状态监听和上传报告能力。"""

    def _init_upload_state(self, design_path: str) -> None:
        """初始化上传监听缓存和定位配置路径。"""
        self._upload_design_path = design_path
        self._upload_responses = deque(maxlen=10)
        self._upload_response_files = deque(maxlen=10)

    def _upload_selector(self, key: str, required: bool = False):
        """读取上传流程使用的设计页定位配置。"""
        selector = self.design_locators.get(key)
        if required and not selector:
            raise RuntimeError(f"locator `{key}` is not configured in {self._upload_design_path}")
        return selector

    @staticmethod
    def _resolve_file_path(file_path: str) -> Path:
        """将上传文件或目录路径解析为绝对路径。"""
        if not file_path:
            raise ValueError("file_path cannot be empty")
        target_path = Path(file_path)
        if not target_path.is_absolute():
            target_path = (Path(__file__).resolve().parents[2] / target_path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"upload path not found: {target_path}")
        return target_path

    @classmethod
    def _collect_files_by_extensions(cls, file_path: str, extensions: Sequence[str]) -> List[str]:
        """从文件或目录中收集符合指定扩展名的上传文件。"""
        normalized_extensions = tuple(ext.lower() for ext in extensions)
        if not normalized_extensions:
            raise ValueError("extensions cannot be empty")

        target_path = cls._resolve_file_path(file_path)
        if target_path.is_file():
            files = [target_path]
        elif target_path.is_dir():
            files = sorted(
                f for f in target_path.iterdir()
                if f.is_file() and f.suffix.lower() in normalized_extensions
            )
        else:
            raise FileNotFoundError(f"upload path must be file or directory: {target_path}")

        invalid_files = [str(f) for f in files if f.suffix.lower() not in normalized_extensions]
        if invalid_files:
            expected = ", ".join(normalized_extensions)
            raise ValueError(f"upload file extension must be one of {expected}: {invalid_files}")
        if not files:
            expected = ", ".join(normalized_extensions)
            raise FileNotFoundError(f"no upload files with extension {expected} found in: {target_path}")

        files_to_upload = [str(f) for f in files]
        print(f"文件类型：{files_to_upload}")
        return files_to_upload

    @staticmethod
    def _now_iso() -> str:
        """返回当前本地时间字符串，供测试报告记录步骤时间点。"""
        return datetime.now().isoformat(timespec="milliseconds")

    @staticmethod
    def _elapsed_ms(start_time: float) -> int:
        """返回从起始时间到当前的毫秒耗时，最小为 1。"""
        return max(1, int((time.time() - start_time) * 1000))

    @staticmethod
    def _empty_ai_report() -> dict:
        """构造默认 AI 观察结果。"""
        return {
            "observed_statuses": [],
            "final_status": None,
            "duration_ms": 0,
            "success": False,
            "files": [],
        }

    @staticmethod
    def _png_idat_has_variation(png_bytes: bytes) -> bool:
        """轻量检查 PNG 截图数据是否包含非空图像变化。"""
        return b"IDAT" in png_bytes and len(set(png_bytes)) > 16

    def _handle_upload_response(self, response):
        """捕获 AI 任务状态响应。"""
        if "/tars/v1/gateway" in response.url:
            try:
                body = response.json()
                data = body.get("data") or {}
                files = data.get("files", [])

                if files:
                    current_status = files[0].get("aiTaskStatus")
                    patient_name = data.get("name", "未知")

                    self._upload_responses.append(current_status)
                    self._upload_response_files.append(files)

                    if current_status == 2:
                        log_msg = f"📡 捕获状态 | 患者: {patient_name} | 状态: {current_status}"
                        print("🎉 AI 任务处理成功！")
                        if self.logger:
                            self.logger.info(log_msg)
            except ValueError as e:
                if self.logger:
                    self.logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"接口错误，未监听到指定内容: {e}")
                else:
                    print(e)

    def _wait_ai_status_report(self, target_status=2, timeout_ms=180000) -> dict:
        """等待 AI 任务到达目标状态，并返回可用于断言的状态报告。"""
        self._upload_responses.clear()
        self._upload_response_files.clear()
        self.driver.on("response", self._handle_upload_response)
        start_time = time.time()
        timeout_sec = timeout_ms / 1000
        success = False

        try:
            while time.time() - start_time < timeout_sec:
                if target_status in self._upload_responses:
                    print(f"最终捕获的状态序列: {list(self._upload_responses)}")
                    success = True
                    break
                self.wait_for_time(500)
        finally:
            self.driver.remove_listener("response", self._handle_upload_response)

        observed_statuses = list(self._upload_responses)
        files = list(self._upload_response_files[-1]) if self._upload_response_files else []
        report = {
            "observed_statuses": observed_statuses,
            "final_status": observed_statuses[-1] if observed_statuses else None,
            "duration_ms": self._elapsed_ms(start_time),
            "success": success,
            "files": files,
        }
        self._upload_responses.clear()
        self._upload_response_files.clear()
        return report

    def _is_ai_status(self, target_status=2, timeout_ms=180000):
        """等待 AI 任务到达目标状态。"""
        return self._wait_ai_status_report(target_status=target_status, timeout_ms=timeout_ms)["success"]

    def _open_import_data_modal(self) -> None:
        """打开导入数据弹窗，并等待文件类型入口可见。"""
        import_data_button_name = self._upload_selector("import_data_button_name", required=True)
        ct_type_button_name = self._upload_selector("ct_dicom_type_button_name", required=True)
        if not self.click_role("button", role_name=import_data_button_name):
            raise RuntimeError("failed to open import data modal")
        self.driver.get_by_role("button", name=ct_type_button_name).first.wait_for(state="visible", timeout=10000)

    def _upload_type_config(self, upload_type: str) -> dict:
        """返回指定上传类型对应的按钮名称和文件格式规则。"""
        normalized_type = (upload_type or "").strip().lower()
        config = UPLOAD_TYPE_CONFIG.get(normalized_type)
        if not config:
            valid_types = ", ".join(UPLOAD_TYPE_CONFIG.keys())
            raise ValueError(f"invalid upload_type: {upload_type}, expected one of {valid_types}")
        return config

    def _select_upload_type(self, upload_type: str) -> None:
        """在导入数据弹窗中选择 CT、上颌口扫、下颌口扫或其他文件类型。"""
        config = self._upload_type_config(upload_type)
        type_button_name = self._upload_selector(config["button_key"], required=True)
        if not self.click_role("button", role_name=type_button_name):
            raise RuntimeError(f"failed to select upload type: {config['label']}")

    def _set_file_chooser_files(self, files_to_upload: List[str]) -> None:
        """触发导入数据文件选择器，并设置已校验格式的文件列表。"""
        upload_area_name = self._upload_selector("upload_area_button_name", required=True)
        upload_area_locator = self.driver.get_by_role(
            "button",
            name=re.compile(f"^{re.escape(upload_area_name)}"),
        ).first
        upload_area_locator.wait_for(state="visible", timeout=10000)
        with self.driver.expect_file_chooser(timeout=10000) as chooser_info:
            upload_area_locator.click()
        chooser_info.value.set_files(files_to_upload)

    def _wait_for_dcm_confirm_form(self, timeout_ms: int = 60000):
        """等待模型名称输入框出现并返回定位器。"""
        input_dcm_name = (
                self._upload_selector("input_model_name")
                or self._upload_selector("input_dcm_name", required=True)
        )
        name_input_locator = self.driver.locator(input_dcm_name)
        name_input_locator.first.wait_for(state="visible", timeout=timeout_ms)
        return name_input_locator.first

    def _fill_model_name(self, model_name: str, timeout_ms: int = 60000) -> None:
        """填写导入模型名称。"""
        name_input = self._wait_for_dcm_confirm_form(timeout_ms=timeout_ms)
        name_input.click(force=True)
        name_input.fill(model_name)
        name_input.press("Enter")

    def _confirm_dcm_import(self) -> None:
        """点击新版“确认导入”按钮，缺失时兼容旧版确认按钮。"""
        confirm_selectors = [
            self._upload_selector("confirm_import_button"),
            self._upload_selector("confirmed_btn"),
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
        raise RuntimeError(f"cannot find visible import confirm button: {last_error}")

    def upload_patient_data(
            self,
            file_type: str,
            file_path: str,
            file_name: str,
    ) -> bool:
        """按文件类型上传患者数据；文件类型支持 CT、上颌口扫、下颌口扫和其他口扫。"""
        return self._upload_patient_data_report(file_type, file_path, file_name)["success"]

    def _upload_patient_data_report(
            self,
            file_type: str,
            file_path: str,
            file_name: str,
    ) -> dict:
        """按文件类型上传患者数据，并返回文件清单、上传耗时和 AI 观察结果。"""
        config = self._upload_type_config(file_type)
        files_to_upload = self._collect_files_by_extensions(file_path, config["extensions"])
        started_at = self._now_iso()
        start_time = time.time()
        ai_report = self._empty_ai_report()

        self._open_import_data_modal()
        self._select_upload_type(file_type)
        self._set_file_chooser_files(files_to_upload)
        self._fill_model_name(file_name)
        self.wait_for_time(300)
        self._confirm_dcm_import()

        if not config["wait_for_ai"]:
            self.wait_for_time(1000)
            if self.logger:
                self.logger.info(f"{config['label']}上传完成，未等待 AI 解析")
            return {
                "file_count": len(files_to_upload),
                "file_paths": files_to_upload,
                "upload_started_at": started_at,
                "upload_finished_at": self._now_iso(),
                "duration_ms": self._elapsed_ms(start_time),
                "success": True,
                "ai": ai_report,
            }

        ai_report = self._wait_ai_status_report(target_status=2, timeout_ms=180000)
        if self.logger:
            self.logger.info(f"{config['label']}解析状态为{ai_report['success']}")
        return {
            "file_count": len(files_to_upload),
            "file_paths": files_to_upload,
            "upload_started_at": started_at,
            "upload_finished_at": self._now_iso(),
            "duration_ms": self._elapsed_ms(start_time),
            "success": ai_report["success"],
            "ai": ai_report,
        }
