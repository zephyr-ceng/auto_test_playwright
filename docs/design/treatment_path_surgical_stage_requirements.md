# 治疗路径手术阶段自动化需求

## 1. 需求背景

针对设计编辑页的治疗路径进行自动化覆盖，重点验证手术阶段的新增、编辑和删除能力，并保留阶段读取能力供页面对象内部复用。后续实现需符合当前项目的 POM + pytest + Allure 分层结构：

`data/*.yaml -> pages/*_manager.py -> tests/test_*_page.py -> pytest assert -> core/conftest.py 失败截图 -> Allure report`

本需求只使用现有登录态访问目标页面，测试代码不得硬编码 cookie、账号密码或真实患者敏感信息。`DesignManager` 初始化时已经创建 `LoginPage` 并可获得 `self._cookies`，因此鉴权页面应直接复用 `self._cookies` 注入浏览器上下文，不再在治疗路径方法中重复读取 cookie 或重新组织登录逻辑。

实际脚本需要兼容“已有 URL 数据”和“新建患者数据”两种入口，入口判断逻辑应复用 `DesignManager.create_design(...)` 中对 `url` 是否为空的分支思路；同时优先读取并复用项目已有方法，例如新建患者、上传 DCM、创建牙位/病例、打开页面、点击和等待等能力，不在治疗路径用例中重复实现。

## 2. 测试对象

- 页面名称：设计编辑页
- 页面 URL path：`/createDesign`
- 目标访问参数：`surgicalDesignID=677156612823187456&mode=edit&patientID=677134467964960768&medicalRecordID=677156587053318144`
- 页面标题：`Fyton`
- 测试区域：治疗路径
- 目标牙位：参数化传入 `tooth_position`，不得固定为 `46`
- 目标功能：治疗路径阶段读取、阶段新增、阶段信息编辑、阶段删除

说明：历史调试可使用 `46` 作为样例牙位，但正式脚本必须通过参数传入牙位，并直接复用已有 `_create_tooth(tooth_position)` 创建对应病例，不需要新增或改造创建牙位方法。牙位创建只属于治疗路径显示前的准备工作，不作为测试断言点。

## 3. 前置条件与入口分支

目标 URL 是带前置条件的数据入口：该设计上下文中的 DCM 已完成上传并可渲染，但不会保证目标牙位/病例已存在。已有 URL 分支不得重复执行新建患者或上传 DCM；治疗路径准备时应优先进入已有目标牙位病例，仅当目标牙位不存在时才复用 `DesignManager._create_tooth(tooth_position)` 创建。牙位只能创建一次，后续同一数据验证需复用已有牙位，或改用其他未创建牙位。

实际自动化需同时支持新建患者场景，建议按以下分支处理：

| 分支 | 触发条件 | 可复用脚本 | 进入治疗路径准备状态 |
| --- | --- | --- | --- |
| 已有 URL 分支 | 调用方传入非空 `url` 或完整 query | `self._cookies`、`add_cookies()`、`open_url()`、病例选择能力；目标牙位不存在时再复用 `DesignManager._create_tooth(tooth_position)` | 当前 URL 包含 `createDesign`；页面存在患者数据，如 `术前CT`；DCM 已上传；进入或创建目标牙位后治疗路径可见 |
| 新建患者分支 | 调用方未传入 `url` | `PatientsPage.create_patient(...)`、`DesignManager._dcm_upload(...)`、`DesignManager._create_tooth(tooth_position)`，必要时复用已有创建设计流程 | 新患者 URL 中存在 `patientID`；DCM 上传/AI 渲染状态为成功；创建牙位后治疗路径可见 |

建议新增一个统一准备方法，例如：

```python
_prepare_treatment_path_context(
    url: str = "",
    tooth_position: int | None = None,
    dcm_dir: str = "",
    ct_name: str = "",
) -> dict
```

该方法只负责把页面带到可验证治疗路径的状态，并返回上下文信息，如 `mode`、`current_url`、`patient_id`、`tooth_position`、`dcm_uploaded`、`case_created`、`created_patient`、`treatment_path_ready`。其中 `tooth_position` 和牙位创建结果只用于准备流程排查，不在 pytest 中做业务断言；外部方法通过 `treatment_path_ready` 判定是否可以继续读取、编辑或删除手术阶段。

## 4. 实测页面状态

使用 Browser 内置浏览器进入目标 URL 后，页面可见患者信息、患者数据和 3D CT 渲染。该 URL 仅保证 DCM 数据已存在，不代表病例牙位已创建；治疗路径脚本应在准备阶段优先进入已有目标牙位病例，若目标牙位不存在再调用 `_create_tooth(tooth_position)`，随后读取或进入治疗路径区域。

历史调试中以样例牙位 `46` 读取到以下治疗路径阶段，正式断言不得依赖固定牙位：

| 序号 | 阶段标题 | 状态 | 日期 | 备注 |
| --- | --- | --- | --- | --- |
| 1 | 种植术前检查 | 未开始 | 2026-05-15 | 包含CBCT影像检查、生化检验、局部麻醉评估和种植体方案设计 |
| 2 | 种植一期手术 | 未开始 | 2026-05-22 | 进行种植体植入手术，术后进行影像检查确认位置 |
| 3 | 种植手术拆线 | 未开始 | 2026-06-01 | 拆除一期手术缝线，检查伤口愈合情况 |
| 4 | 种植二期手术 | 未开始 | 2026-10-02 | 安装愈合基台，为后续修复做准备 |
| 5 | 种植手术拆线 | 未开始 | 2026-10-12 | 拆除二期手术缝线，确认牙龈成形效果 |
| 6 | 种植模型制备 | 未开始 | 2026-11-04 | 取模制作个性化牙冠，确保修复体精准匹配 |
| 7 | 种植牙冠置入 | 未开始 | 2026-11-14 | 安装最终牙冠，完成修复并进行咬合调整 |

以上阶段数据只作为页面读取结构示例，不再作为 pytest 排序用例或排序断言依据。

## 5. 建议改造范围

### 5.1 YAML 层

更新 `data/design_page.yaml`，保留现有设计流程定位器，并补充治疗路径相关定位器。`url` 仍应只保存 path，不写完整域名。

```yaml
url: "/createDesign"
locators:
  case_card_template: "text={case_no}"
  treatment_path_title: "text=治疗路径"
  treatment_stage_cards: "xpath=//*[contains(text(),'治疗路径')]/following::*[contains(@class,'rounded') or self::div]"
  treatment_stage_edit_button_template: "xpath=(//*[normalize-space()='{stage_index}']/following::button[.//*[name()='svg']])[1]"
  treatment_stage_delete_button_template: "xpath=(//*[normalize-space()='{stage_index}']/following::button[.//*[name()='svg']])[2]"
  treatment_stage_title_input: "input[placeholder='请输入治疗标题']"
  treatment_stage_status_combobox: "input[role='combobox']"
  treatment_stage_status_options: ".ant-select-dropdown:visible .ant-select-item-option"
  treatment_stage_date_input: "input[placeholder='请选择日期']"
  treatment_stage_remark_textarea: "textarea[placeholder='请备注相关的信息']"
  treatment_stage_confirm_button: "button:has-text('确 认')"
  treatment_stage_cancel_button: "button:has-text('取 消')"
  treatment_stage_success_message: "text=操作成功"
  add_treatment_title_input: "input[placeholder='请输入治疗标题']"
  add_treatment_date_input: "input[placeholder='请选择日期']"
  add_treatment_remark_textarea: "textarea[placeholder='请备注相关的信息']"
  add_treatment_button: "button:has-text('添加流程')"
  delete_treatment_confirm_button: "button:has-text('确 认')"
```

说明：当前页面可通过文本和 placeholder 定位。若前端后续增加 `data-testid`，应优先替换为 `data-testid`，避免依赖视觉层级或图标按钮顺序。

### 5.2 Page Object 层

更新 `pages/design_manager.py`，新增面向断言的业务方法。测试层不得直接写选择器。已有脚本可以复用，尤其是新建患者、DCM 上传、牙位/病例新建、打开设计页这几类已有能力，不要在治疗路径测试里重复实现。

方法颗粒度参考 `create_design(...)`：一个业务方法应串起完整页面流程，避免把点击、字段读取、弹窗关闭、文本解析等短步骤拆成大量互相依赖的小方法。准备工作、牙位创建、路径显示判定属于内部流程，不作为独立测试断言方法。

对外调用方法用于 pytest 用例直接调用，命名不以下划线开头，返回值必须便于断言：

- `read_treatment_stages() -> dict`：读取治疗路径手术阶段，返回 `{ready: bool, stages: list[dict]}`。该方法只负责读取阶段数据，不计算排序结果；`ready=False` 时返回清晰错误信息或抛出 `RuntimeError`。
- `add_treatment_stage() -> dict`：新增一个手术阶段，参数生成规则与编辑一致：随机选择状态下拉选项、日期改为当天、文本字段通过 `RandomManager` 生成随机字符串。返回新增入参、保存文本、阶段列表和新增后回显内容。
- `read_treatment_stage_edit_content(stage_index: int) -> dict`：按传入阶段序号打开编辑区并读取内容，同时调用内部随机编辑保存方法完成编辑验证。返回原始编辑内容、随机编辑入参、保存提示和保存后回显内容；不恢复原始内容。
- `delete_treatment_stage(stage_index: int) -> dict`：按传入阶段序号删除已有手术阶段，返回删除前目标阶段、返回文本、删除前后阶段列表。删除类用例通过 `stage_index` 指定目标阶段，不需要先创建临时阶段。

内部复用方法只在 Page Object 内部调用，命名应以下划线开头，但颗粒度应保持粗一些。已有 `_selector_design(key: str)` 和 `_create_tooth(tooth_position)` 可直接复用，不需要重新实现或改名。

- `_prepare_treatment_path_context(url: str = "", tooth_position: int | None = None, dcm_dir: str = "", ct_name: str = "") -> dict`：统一准备函数。`url` 分支直接添加 `self._cookies` 后打开目标 URL；新建患者分支复用 `PatientsPage.create_patient(...)` 和 `_dcm_upload(...)`；两条分支随后统一进入目标牙位，优先复用已有病例，未存在时才调用 `_create_tooth(tooth_position)`，触发治疗路径显示，并写入 `self._treatment_path_ready` / `self._treatment_path_context` 供外部方法判定。
- `_ensure_treatment_path_ready() -> dict`：读取准备状态，若治疗路径未准备完成则给外部方法提供明确失败原因。
- `_read_treatment_stages() -> list[dict]`：等待治疗路径并读取阶段结构，内部自行完成文本截取和解析。
- `_build_random_stage_payload() -> dict`：生成新增和编辑共用的随机阶段参数，包含随机状态、当天日期和 `RandomManager` 生成的随机文本。
- `_edit_random_treatment_stage(stage_index: int | None = None, stage_total: int = 7) -> dict`：选择任意阶段进行编辑保存。`stage_index` 传入时编辑指定阶段，未传入时在 `1..stage_total` 中随机选择；编辑内容来自 `_build_random_stage_payload()`。
- `_save_stage_form(...) -> dict`：在编辑或新增阶段时完成表单填写、确认保存和成功提示读取。

除上述通用复用点外，不强制新增 `_wait_for_treatment_path()`、`_parse_stage_block()`、`_stage_by_index()`、`_first_stage_field()`、`_cancel_treatment_stage_editor()` 等细粒度方法；如果实现中只被一个业务流程使用，应优先内联在对应业务方法里。

Page Object 中只返回可断言数据，不在业务方法内写最终 pytest 断言。所有新增函数应添加简洁函数说明，并优先复用当前文件、其他 page manager、`BasePage` 和 `utils` 中已有能力。

### 5.3 pytest 层

新增或更新 `tests/test_design_treatment_path_page.py`，使用 `BrowserManager` fixture 创建页面对象，失败截图继续交由 `core/conftest.py` 处理。测试 case 只保留新增、编辑、删除三类；阶段读取、入口准备、新建患者兼容、cookie 注入、牙位创建和页面等待属于 fixture 或 Page Object 内部准备逻辑，不作为独立测试 case。

#### DESIGN_TREATMENT_PATH_001：手术阶段新增校验

- Allure story：手术阶段新增校验
- 前置条件：已打开目标牙位治疗路径
- 操作：调用 `add_treatment_stage()`，由方法内部使用与编辑一致的随机状态、当天日期和随机文本创建阶段
- 预期结果：返回文本包含 `操作成功`；调用 `read_treatment_stages()` 后，阶段列表包含随机新增内容

#### DESIGN_TREATMENT_PATH_002：手术阶段编辑校验

- Allure story：手术阶段信息编辑校验
- 前置条件：已打开目标牙位治疗路径
- 操作：调用 `read_treatment_stage_edit_content(stage_index=目标阶段序号)`，由方法内部读取编辑内容并调用随机编辑保存流程
- 预期结果：原始编辑内容可读取；返回文本包含 `操作成功`；调用 `read_treatment_stages()` 后，保存后回显内容与随机编辑入参一致；测试结束不恢复原内容

#### DESIGN_TREATMENT_PATH_003：手术阶段删除校验

- Allure story：手术阶段删除校验
- 前置条件：已打开目标牙位治疗路径
- 操作：调用 `delete_treatment_stage(stage_index=目标阶段序号)`，删除传入序号对应的已有手术阶段
- 预期结果：返回文本包含 `操作成功`；调用 `read_treatment_stages()` 后，删除前目标阶段不再出现在阶段列表中

## 6. Allure 要求

建议测试类使用：

- `@allure.feature("Design Treatment Path")`
- `@allure.story("手术阶段新增校验")`
- `@allure.story("手术阶段信息编辑校验")`
- `@allure.story("手术阶段删除校验")`

每个测试使用 `allure.dynamic.title(...)` 设置中文标题。新增、修改和删除类用例应在 Allure step 或日志中记录原始阶段信息、随机入参、返回文本、保存回显和删除结果。入口准备方法应记录当前使用的分支：`existing_url` 或 `new_patient`。

## 7. 断言标准

入口准备状态：

- 已有 URL 分支：准备函数应记录 `mode == "existing_url"`，当前 URL 包含 `createDesign`，页面可见已上传 DCM 数据，如 `术前CT`，并在统一创建牙位并触发路径显示后写入 `treatment_path_ready=True`。
- 新建患者分支：准备函数应记录 `mode == "new_patient"`，创建后 URL 或上下文包含 `patientID`，DCM 上传返回成功状态，并在统一创建牙位并触发路径显示后写入 `treatment_path_ready=True`。
- pytest 不直接断言牙位创建结果；牙位创建失败应表现为准备状态不可用，外部方法据此停止读取、编辑或删除。
- 任一分支最终都必须进入同一个治疗路径读取方法，避免后续编辑、删除因入口不同而重复实现。
- pytest 不新增阶段排序用例，也不在测试层做序号或日期排序断言。

新增断言：

- `add_treatment_stage()` 返回的文本信息必须包含 `操作成功`。
- 新增后必须调用 `read_treatment_stages()` 读取治疗路径手术阶段。
- 新增阶段的状态、日期和文本字段与随机新增入参一致。
- 新增后阶段列表能读取到本次随机新增内容。

编辑断言：

- `read_treatment_stage_edit_content(stage_index)` 返回的原始编辑内容中应包含标题、状态、日期和备注。
- 保存修改后返回的文本信息必须包含 `操作成功`。
- 保存后必须调用 `read_treatment_stages()` 读取治疗路径手术阶段。
- 目标阶段保存后的状态、日期和文本字段与 `_edit_random_treatment_stage(...)` 生成的随机编辑入参一致。
- 编辑用例不恢复原始内容，随机编辑后的内容保留在当前真实数据中。

删除断言：

- 删除类用例不需要创建临时阶段，直接通过 `stage_index` 删除已有阶段。
- 删除保存后返回的文本信息必须包含 `操作成功`。
- 删除后必须调用 `read_treatment_stages()` 读取治疗路径手术阶段。
- 删除前阶段列表包含 `stage_index` 对应的目标阶段。
- 删除后阶段列表不再包含删除前目标阶段的唯一内容组合，如标题、日期、备注。

## 8. 工具验证记录

- 使用 Playwright CLI 检查工具链，`npx` 可用；PowerShell 包装脚本需通过 `powershell -ExecutionPolicy Bypass -File ...` 执行。
- 使用 Playwright CLI 打开目标页面，页面 URL 为目标设计编辑地址，标题为 `Fyton`；CLI 生成的页面快照为空，符合该页面大量使用画布和动态渲染的表现。
- 使用 Browser 内置浏览器打开目标页面，成功读取到患者 ID `677134467964960768`、患者姓名 `T_张凤` 和患者数据 `术前CT`。
- 目标 URL 按“已有 URL 分支”理解为 DCM 已存在，不再假设牙位病例已存在；后续脚本需要用参数化 `tooth_position` 调用 `_create_tooth` 创建牙位病例。
- 历史调试中以样例牙位 `46` 验证过治疗路径区域、阶段列表、编辑弹窗字段、备注保存与恢复、状态下拉选项；该样例只作为页面能力验证记录，不作为固定测试数据或独立状态下拉测试用例。
- 打开第 1 个阶段编辑区，识别到字段：标题输入框、状态下拉、日期输入框、备注文本域、确认按钮、取消按钮。
- 状态下拉可见选项为 `未开始`、`进行中`、`已完成`。

## 9. 风险与注意事项

- 该页面包含 3D CT 画布和异步模型加载，DOM 快照可能为空或不完整，自动化应优先在治疗路径区域出现后再读取阶段信息。
- 阶段编辑和删除按钮主要表现为图标按钮，当前缺少稳定可读名称；建议前端补充 `data-testid` 或 `aria-label`。
- 修改类用例会写入远端真实业务数据，应使用唯一测试后缀；当前需求要求不恢复原始值。
- 删除类用例会删除传入 `stage_index` 对应的已有阶段，执行环境必须允许该数据变更；如需保留数据，应在用例外部准备可删除的数据或使用可重置环境。
- 状态字段代表治疗进度，自动化默认只验证选项，不建议在常规回归中修改状态。
- 新建患者分支会消耗远端资源并产生测试数据，建议仅在独立测试环境或带清理策略的流水线中启用；常规回归优先使用已有 URL 分支。
