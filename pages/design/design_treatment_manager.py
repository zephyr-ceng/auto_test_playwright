from typing import Any, Callable, Dict, List, Optional, Tuple


TREATMENT_SEQUENCE_COMMAND = "15003"
DELETE_TREATMENT_SEQUENCE_COMMAND = "15004"
SORT_TREATMENT_SEQUENCE_COMMAND = "15005"
ADD_DESIGN_COMMAND = "14002"
DELETE_DESIGN_COMMAND = "14008"


class DesignTreatmentMixin:
    """设计页治疗路径面板操作、请求记录和相关用例能力。"""

    def _init_treatment_state(
            self,
            design_path: str,
            login_page,
            patients_page,
            random_manager,
            patient_name: str,
            cookies,
    ) -> None:
        """初始化治疗路径流程依赖和运行状态。"""
        self._treatment_design_path = design_path
        self._treatment_login_page = login_page
        self._treatment_patients_page = patients_page
        self._treatment_random = random_manager
        self._treatment_cookies = cookies
        self._treatment_patient_name = patient_name
        self._treatment_path_ready = False
        self._treatment_path_context = {}

    def _treatment_selector(self, key: str, required: bool = False):
        """读取治疗路径流程使用的设计页定位配置。"""
        selector = self.design_locators.get(key)
        if required and not selector:
            raise RuntimeError(f"locator `{key}` is not configured in {self._treatment_design_path}")
        return selector

    def _set_treatment_patient_name(self, patient_name: str) -> None:
        """更新治疗路径患者名，并同步给宿主页面对象。"""
        self._treatment_patient_name = patient_name
        sync = getattr(self, "_sync_design_patient_name", None)
        if sync:
            sync(patient_name)

    def _set_treatment_cookies(self, cookies) -> None:
        """更新治疗路径 cookies，并同步给宿主页面对象。"""
        self._treatment_cookies = cookies
        sync = getattr(self, "_sync_design_cookies", None)
        if sync:
            sync(cookies)

    def _drag_surgical(self) -> bool:
        """将第 5 个可见手术阶段拖到第 6 个位置。"""
        surgical_stage_cards = self._treatment_selector("surgical_stage_draggable_cards", required=True)

        changed = self.drag_nth_locator_to_nth_locator(
            surgical_stage_cards,
            4,
            5,
            screenshot_name="surgical_stage_drag",
        )
        if self.logger:
            self.logger.info(f"Surgical stage drag changed={changed}")
        return changed

    def _get_current_surgical_path(self) -> dict:
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

    def _is_locator_visible(self, selector: Optional[str], timeout: int = 1000) -> bool:
        """判断配置的定位器是否可见，异常时返回 False。"""
        if not selector:
            return False
        try:
            locator = self.driver.locator(selector).first
            return locator.count() > 0 and locator.is_visible(timeout=timeout)
        except Exception:
            return False

    def _visible_text_exists(self, text: str, timeout: int = 1000) -> bool:
        """判断当前页面是否存在可见的指定文本。"""
        if not text:
            return False
        try:
            locator = self.driver.get_by_text(text, exact=False).first
            return locator.count() > 0 and locator.is_visible(timeout=timeout)
        except Exception:
            return False

    def _collect_texts(self, selector: Optional[str]) -> List[str]:
        """收集指定定位器下的非空文本。"""
        if not selector:
            return []
        try:
            return [
                text.strip()
                for text in self.driver.locator(selector).all_inner_texts()
                if text and text.strip()
            ]
        except Exception:
            return []

    def _toast_texts(self) -> List[str]:
        """返回治疗路径断言使用的可见提示或校验文本。"""
        selectors = [
            self._treatment_selector("toast_message"),
            self._treatment_selector("form_error"),
            self._treatment_selector("treatment_stage_success_message"),
        ]
        texts: List[str] = []
        for selector in selectors:
            texts.extend(self._collect_texts(selector))
        return texts

    def _click_current_case(self, tooth_position: int) -> bool:
        """点击目标牙位已创建的病例卡片或标签。"""
        tooth_label = self._treatment_tooth_selector("tooth_label_template", tooth_position, required=True)
        if self.click_nth(tooth_label, 0):
            self.wait_for_time(800)
            return True

        case_selector = self._treatment_selector("case_card")
        if case_selector:
            try:
                self.driver.locator(case_selector).first.click()
                self.wait_for_time(800)
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(f"click case card failed: {e}")
        return False

    def _treatment_steps(self) -> dict:
        """返回当前可见治疗路径步骤标题。"""
        path = self._get_current_surgical_path()
        if path:
            return path

        selector = self._treatment_selector("treatment_stage_cards")
        texts = self._collect_texts(selector)
        return {index + 1: text for index, text in enumerate(texts)}

    def _current_treatment_path_state(self, tooth_position: Optional[int] = None) -> dict:
        """收集治疗路径面板可见性和步骤状态，供断言使用。"""
        title_selector = self._treatment_selector("treatment_path_title")
        visible = self._is_locator_visible(title_selector) or self._visible_text_exists("治疗路径")
        steps = self._treatment_steps() if visible else {}
        return {
            "patient_url": self.get_page_url(),
            "case_selected": visible,
            "treatment_visible": visible,
            "steps": steps,
            "tooth_position": tooth_position,
        }

    def _open_created_case_treatment_path(self, tooth_position: int) -> dict:
        """打开当前患者页面中已创建病例的治疗路径。"""
        tooth_position = self._validate_treatment_tooth_position(tooth_position)
        clicked = self._click_current_case(tooth_position)
        state = self._current_treatment_path_state(tooth_position)
        state["case_selected"] = clicked and state["treatment_visible"]
        return state

    def treatment_path(self, url: str = "", tooth_position: int = 32) -> dict:
        """按 URL 打开治疗路径；未传 URL 时创建患者和病例。"""
        tooth_position = self._validate_treatment_tooth_position(tooth_position)
        if url:
            self._treatment_login_page.refresh_cookies()
            self._set_treatment_cookies(self._treatment_login_page.cookies)
            if self._treatment_cookies:
                self.add_cookies(self._treatment_cookies)
            else:
                self._treatment_login_page.login_account(
                    self._treatment_login_page.username,
                    self._treatment_login_page.password,
                )
            self.open_url(url)
            state = self._open_created_case_treatment_path(tooth_position)
            state.update(
                {
                    "patient_name": self._treatment_patient_name,
                    "case_created": None,
                    "create_message": None,
                }
            )
            self._treatment_path_ready = bool(state["treatment_visible"])
            self._treatment_path_context = state
            return state

        self._set_treatment_patient_name("T_" + self._treatment_random.random_chinese_name())
        self._treatment_patients_page.create_patient(self._treatment_patient_name)
        created_message = self._create_treatment_tooth([tooth_position])
        state = self._open_created_case_treatment_path(tooth_position)
        state.update(
            {
                "patient_name": self._treatment_patient_name,
                "case_created": created_message == "操作成功",
                "create_message": created_message,
            }
        )
        self._treatment_path_ready = bool(state["treatment_visible"])
        self._treatment_path_context = state
        return state

    def case_treatment_path_not_visible_without_case(self) -> dict:
        """创建患者工作区但不选择病例，并返回治疗路径可见性。"""
        self._set_treatment_patient_name("T_" + self._treatment_random.random_chinese_name())
        self._treatment_patients_page.create_patient(self._treatment_patient_name)
        state = self._current_treatment_path_state()
        state["patient_name"] = self._treatment_patient_name
        return state

    def _record_gateway_requests(
            self,
            command_responses: Optional[Dict[str, dict]] = None,
    ) -> Tuple[List[dict], Callable[[], None]]:
        """模拟指定网关命令并记录请求参数，供 UI 断言使用。"""
        requests: List[dict] = []
        responses = command_responses or {}
        route_pattern = "**/gateway"

        def handler(route):
            request = route.request
            command = request.headers.get("command") or request.headers.get("Command")
            payload: Any = None
            try:
                payload = request.post_data_json
            except Exception:
                payload = request.post_data
            requests.append({"command": str(command), "payload": payload, "url": request.url})
            response_body = responses.get(str(command))
            if response_body is None:
                route.continue_()
                return
            route.fulfill(status=200, content_type="application/json", json=response_body)

        self.driver.route(route_pattern, handler)

        def cleanup() -> None:
            try:
                self.driver.unroute(route_pattern, handler)
            except Exception:
                return

        return requests, cleanup

    @staticmethod
    def _requests_for(requests: List[dict], command: str) -> List[dict]:
        """按命令过滤已记录的网关请求。"""
        return [request for request in requests if request.get("command") == command]

    def _open_treatment_form(self) -> bool:
        """从当前治疗路径面板打开新增治疗表单。"""
        selector = self._treatment_selector("add_treatment_button", required=True)
        ok = self.click(selector)
        self.wait_for_time(500)
        return ok

    def _fill_treatment_form(
            self,
            *,
            title: str = "",
            date_text: str = "",
            remark: str = "",
            status: str = "",
    ) -> None:
        """填写可见的治疗路径表单字段。"""
        title_selector = (
                self._treatment_selector("add_treatment_title_input")
                or self._treatment_selector("treatment_stage_title_input", required=True)
        )
        date_selector = (
                self._treatment_selector("add_treatment_date_input")
                or self._treatment_selector("treatment_stage_date_input", required=True)
        )
        remark_selector = (
                self._treatment_selector("add_treatment_remark_textarea")
                or self._treatment_selector("treatment_stage_remark_textarea", required=True)
        )
        if title:
            self.type_text(title_selector, title, clear_first=True)
        if date_text:
            self.type_text(date_selector, date_text, clear_first=True)
            self.send_keys(date_selector, "Enter")
        if remark:
            remark_input = self.driver.locator(remark_selector).first
            remark_input.fill("")
            remark_input.fill(remark)
            if self.logger:
                self.logger.info(f"Typed treatment remark into {remark_selector}")
        if status:
            status_selector = self._treatment_selector("treatment_stage_status_combobox")
            options_selector = self._treatment_selector("treatment_stage_status_options")
            if status_selector and options_selector:
                self.click(status_selector)
                self.click_by_text(options_selector, status)

    def _submit_treatment_form(self, edit: bool = False) -> bool:
        """提交新增或编辑治疗路径表单。"""
        selector_key = "treatment_stage_confirm_button" if edit else "add_treatment_submit_button"
        selector = self._treatment_selector(selector_key, required=True)
        ok = self.click(selector)
        self.wait_for_time(1000)
        return ok

    def case_add_treatment_success(self, url: str = "", tooth_position: int = 32) -> dict:
        """新增有效治疗路径，并返回网关请求字段。"""
        base_state = self.treatment_path(url, tooth_position)
        requests, cleanup = self._record_gateway_requests(
            {TREATMENT_SEQUENCE_COMMAND: {"code": 0, "data": {"id": "mock-treatment-id"}, "message": "success"}}
        )
        try:
            self._open_treatment_form()
            self._fill_treatment_form(title="UI Treatment Add", date_text="2026-07-21", remark="UI treatment add")
            submitted = self._submit_treatment_form()
            self.wait_for_time(800)
            command_requests = self._requests_for(requests, TREATMENT_SEQUENCE_COMMAND)
            return {
                "base_state": base_state,
                "submitted": submitted,
                "requests": command_requests,
                "request_count": len(command_requests),
                "toast": self._toast_texts(),
            }
        finally:
            cleanup()

    def case_add_treatment_validation(self, validation_type: str, url: str = "", tooth_position: int = 32) -> dict:
        """提交无效的新增治疗数据，并返回前端校验状态。"""
        self.treatment_path(url, tooth_position)
        requests, cleanup = self._record_gateway_requests()
        try:
            self._open_treatment_form()
            if validation_type == "title_max":
                self._fill_treatment_form(title="A" * 201, date_text="2026-07-21", remark="valid")
            elif validation_type == "remark_max":
                self._fill_treatment_form(title="valid", date_text="2026-07-21", remark="B" * 4097)
            else:
                self._fill_treatment_form(title="", date_text="", remark="")
            self._submit_treatment_form()
            self.wait_for_time(800)
            return {
                "errors": self._toast_texts(),
                "request_count": len(self._requests_for(requests, TREATMENT_SEQUENCE_COMMAND)),
                "form_visible": self._is_locator_visible(self._treatment_selector("add_treatment_title_input")),
            }
        finally:
            cleanup()

    def _click_treatment_action(self, locator_key: str, stage_index: int = 1) -> bool:
        """点击由定位模板渲染的治疗阶段操作按钮。"""
        selector_template = self._treatment_selector(locator_key, required=True)
        selector = selector_template.format(stage_index=stage_index)
        ok = self.click(selector)
        self.wait_for_time(500)
        return ok

    def case_edit_treatment(self, url: str = "", success: bool = True, tooth_position: int = 32) -> dict:
        """编辑第一个治疗阶段，并返回成功或失败状态。"""
        self.treatment_path(url, tooth_position)
        response = {"code": 0, "data": {}, "message": "success"} if success else {"code": 1, "data": {}, "message": "operate failed"}
        requests, cleanup = self._record_gateway_requests({TREATMENT_SEQUENCE_COMMAND: response})
        try:
            edit_clicked = self._click_treatment_action("treatment_stage_edit_button_template")
            self._fill_treatment_form(
                title="UI Treatment Edit",
                date_text="2026-07-22",
                remark="UI treatment edit",
                status="in_progress",
            )
            submitted = self._submit_treatment_form(edit=True)
            self.wait_for_time(800)
            command_requests = self._requests_for(requests, TREATMENT_SEQUENCE_COMMAND)
            return {
                "edit_clicked": edit_clicked,
                "submitted": submitted,
                "requests": command_requests,
                "request_count": len(command_requests),
                "toast": self._toast_texts(),
                "still_editing": self._is_locator_visible(self._treatment_selector("treatment_stage_title_input")),
            }
        finally:
            cleanup()

    def case_editing_disables_other_treatment(self, url: str = "", tooth_position: int = 32) -> dict:
        """开始编辑一条治疗路径，并检查其他路径操作是否仍然无效。"""
        self.treatment_path(url, tooth_position)
        first_clicked = self._click_treatment_action("treatment_stage_edit_button_template", stage_index=1)
        second_clicked = self._click_treatment_action("treatment_stage_edit_button_template", stage_index=2)
        return {
            "first_edit_clicked": first_clicked,
            "second_edit_clicked": second_clicked,
            "still_editing": self._is_locator_visible(self._treatment_selector("treatment_stage_title_input")),
        }

    def case_delete_treatment(self, url: str = "", linked_design: bool = False, tooth_position: int = 32) -> dict:
        """删除或尝试删除治疗路径，并返回请求和提示状态。"""
        self.treatment_path(url, tooth_position)
        requests, cleanup = self._record_gateway_requests(
            {DELETE_TREATMENT_SEQUENCE_COMMAND: {"code": 0, "data": {}, "message": "success"}}
        )
        try:
            delete_clicked = self._click_treatment_action("treatment_stage_delete_button_template")
            confirm_selector = self._treatment_selector("delete_treatment_confirm_button")
            if confirm_selector and self._is_locator_visible(confirm_selector):
                self.click(confirm_selector)
                self.wait_for_time(800)
            command_requests = self._requests_for(requests, DELETE_TREATMENT_SEQUENCE_COMMAND)
            return {
                "delete_clicked": delete_clicked,
                "linked_design": linked_design,
                "request_count": len(command_requests),
                "requests": command_requests,
                "toast": self._toast_texts(),
            }
        finally:
            cleanup()

    def case_sort_treatment(self, url: str = "", tooth_position: int = 32) -> dict:
        """拖拽治疗步骤，并返回排序请求状态。"""
        state = self.treatment_path(url, tooth_position)
        before = state["steps"]
        requests, cleanup = self._record_gateway_requests(
            {SORT_TREATMENT_SEQUENCE_COMMAND: {"code": 0, "data": {}, "message": "success"}}
        )
        try:
            changed = self._drag_surgical()
            self.wait_for_time(1000)
            after = self._treatment_steps()
            command_requests = self._requests_for(requests, SORT_TREATMENT_SEQUENCE_COMMAND)
            return {
                "changed": changed,
                "steps_before": before,
                "steps_after": after,
                "request_count": len(command_requests),
                "requests": command_requests,
                "toast": self._toast_texts(),
            }
        finally:
            cleanup()

    def case_create_design_from_treatment(self, file_count: int, url: str = "", tooth_position: int = 32) -> dict:
        """从治疗路径点击创建设计，并返回 addDesign 请求和 URL 状态。"""
        self.treatment_path(url, tooth_position)
        requests, cleanup = self._record_gateway_requests(
            {ADD_DESIGN_COMMAND: {"code": 0, "data": {"surgicalDesignID": "mock-design-id", "version": 0}, "message": "success"}}
        )
        try:
            create_button = self._treatment_selector("treatment_create_design_button") or self._treatment_selector("create_design_button", required=True)
            clicked = self.click_role("button", role_name=create_button) if create_button == self._treatment_selector("create_design_button") else self.click(create_button)
            self.wait_for_time(1200)
            command_requests = self._requests_for(requests, ADD_DESIGN_COMMAND)
            return {
                "clicked": clicked,
                "file_count": file_count,
                "request_count": len(command_requests),
                "requests": command_requests,
                "toast": self._toast_texts(),
                "url": self.get_page_url(),
            }
        finally:
            cleanup()

    def case_design_action(self, action: str, url: str = "", success: bool = True, tooth_position: int = 32) -> dict:
        """从治疗路径执行设计操作，并返回结果 URL 或提示信息。"""
        self.treatment_path(url, tooth_position)
        response = {"code": 0, "data": {}, "message": "success"} if success else {"code": 1, "data": {}, "message": "operate failed"}
        requests, cleanup = self._record_gateway_requests({DELETE_DESIGN_COMMAND: response})
        try:
            key_by_action = {
                "edit": "design_edit_button",
                "preview": "design_preview_button",
                "delete": "design_delete_button",
                "start_surgery": "design_start_surgery_button",
                "verification": "design_verification_button",
            }
            selector = self._treatment_selector(key_by_action[action], required=False)
            clicked = self.click(selector) if selector else self.click_role("button", role_name={
                "edit": "编辑设计",
                "preview": "预览设计",
                "delete": "删除设计",
                "start_surgery": "开始手术",
                "verification": "精度验证",
            }[action])
            confirm_selector = self._treatment_selector("design_confirm_button")
            if confirm_selector and self._is_locator_visible(confirm_selector):
                self.click(confirm_selector)
            self.wait_for_time(1000)
            return {
                "action": action,
                "clicked": clicked,
                "url": self.get_page_url(),
                "toast": self._toast_texts(),
                "requests": self._requests_for(requests, DELETE_DESIGN_COMMAND),
            }
        finally:
            cleanup()

    def case_drop_surgical(self, url: str = "", tooth_position: int = 32):
        """手术阶段拖拽排序测试。"""
        surgical = self.treatment_path(url, tooth_position)
        if not surgical["treatment_visible"]:
            raise RuntimeError("treatment path is not ready")
        before = self._get_current_surgical_path()
        print(before)
        self._drag_surgical()
        after = self._get_current_surgical_path()
        print(after)
        return not (after == before)

    def case_refresh_drop_surgical(self, url: str = "", tooth_position: int = 32):
        """手术阶段拖拽排序保存测试。"""
        surgical = self.treatment_path(url, tooth_position)
        if not surgical["treatment_visible"]:
            raise RuntimeError("treatment path is not ready")
        before = self._get_current_surgical_path()
        print(before)
        if self.logger:
            self.logger.info(f"before: {before}")
        self._drag_surgical()
        self._open_created_case_treatment_path(tooth_position)
        self.wait_for_time(1000)
        self._open_created_case_treatment_path(tooth_position)
        after = self._get_current_surgical_path()
        print(after)
        if self.logger:
            self.logger.info(f"after: {after}")
        return not (after == before)
