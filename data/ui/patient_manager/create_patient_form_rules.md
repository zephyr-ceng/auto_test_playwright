# 新建患者表单字段与校验规则

## 模块信息

- 实际模块：患者管理
- 页面入口：`src/v2/page/PatientManage/index.tsx`
- 新建患者弹窗：`src/v2/page/PatientManage/components/PatientModal.tsx`
- 新建接口封装：`src/api/patient/index.ts`
- 接口类型声明：`src/api/patient/typings.d.ts`
- 仓库可见离线网关：`src/utils/sqlite/gatewayOfflineCommandHandlers.ts`
- 仓库可见离线数据层：`src/utils/sqlite/dataLayer.ts`
- 仓库可见 SQLite 表结构：`src/utils/sqlite/opfs.ts`

## 验证标记说明

| 标记 | 含义 | 自动化边界 |
| --- | --- | --- |
| `UI` | 前端页面可见元素、交互、表单校验提示 | UI 自动化只判断前端元素、可见文案、按钮、输入框、弹窗状态、页面跳转 |
| `API` | 通过接口请求/响应验证 | 接口自动化判断请求参数、响应 code/message/data，不依赖页面元素 |
| `SPECIAL` | 提交前转换、trim、字段映射、离线存储归一化等特殊处理 | 通常需要接口拦截、请求抓包、mock、数据库检查或单元测试，不建议作为纯 UI 断言 |
| `UNKNOWN_BACKEND` | 线上后端真实规则当前仓库不可确认 | 需要服务端源码、接口文档或真实接口验证后补充 |

## 新建流程与验证点

| 步骤 | 行为 | 标记 | 可验证内容 |
| --- | --- | --- | --- |
| 1 | 点击“新建患者” | `UI` | 打开“新建患者信息”弹窗 |
| 2 | 点击弹窗确定 | `UI` | 触发表单校验；未通过时展示前端错误提示 |
| 3 | 前端校验通过 | `SPECIAL` | `dateOfBirth` 转毫秒时间戳；`telephone` trim |
| 4 | 调用 `savePatient(params)` | `API` | 请求进入 SavePatient 接口封装 |
| 5 | 接口返回 `code === 0` | `UI` + `API` | UI 展示“新增患者成功”；接口响应包含 `data.id` |
| 6 | 创建成功后跳转 | `UI` | 跳转到 `/createDesign?patientID=<id>` |
| 7 | 接口失败 | `UI` + `API` | UI 展示 `res.message`；接口响应 code 非 0 |

## 表单字段

| 表单字段 | 提交字段 | 控件 | 是否出现在 UI | 标记 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 姓名 | `name` | `Input` | 是 | `UI` + `API` | 新建患者姓名 |
| 生日 | `dateOfBirth` | `DatePicker` | 是 | `UI` + `SPECIAL` + `API` | UI 选择日期；提交前转毫秒时间戳 |
| 电话号码 | `telephone` | `Input type="tel"` | 是 | `UI` + `SPECIAL` + `API` | UI 输入电话；提交前 trim |
| 性别 | `gender` | 自定义单选组 `MyGroup` | 是 | `UI` + `API` | 男为 `1`，女为 `2` |
| 备注 | `desc` | `Input.TextArea` | 是 | `UI` + `API` | 患者备注 |
| 身份证 | `identityCard` | 无 | 否 | `API` + `UNKNOWN_BACKEND` | 接口类型存在该字段，但当前新建患者 UI 不提供输入 |

## 前端 UI 可验证规则

UI 自动化只应判断页面元素和可见结果，不应直接断言后端真实入库逻辑。

| 字段 | UI 可验证规则 | 错误文案 key | zh-CN 文案 | UI 自动化断言建议 |
| --- | --- | --- | --- | --- |
| `name` | 必填 | `patientManage:modal.validation.name.required` | `请填写患者姓名` | 清空姓名后点确定，断言该错误提示可见 |
| `name` | 最多 200 字符 | `patientManage:modal.validation.name.max` | `姓名最多输入200个字符` | 输入 201 个字符后点确定，断言该错误提示可见 |
| `dateOfBirth` | 非必填 | `patientManage:modal.validation.birthday.required` | `请输入患者生日` | 当前规则为 `required: false`，不应期待该错误出现 |
| `telephone` | 非必填 | `patientManage:modal.validation.phone.required` | `请输入患者手机号` | 当前规则为 `required: false`，不应期待该错误出现 |
| `telephone` | 最多 50 字符 | `patientManage:modal.validation.phone.max` | `电话号码最多50个字符` | 输入超过 50 字符时，因 `maxLength=50` 可能无法实际输入超长；该校验更适合组件级或绕过输入限制验证 |
| `gender` | 非必填 | `patientManage:modal.validation.gender.required` | `请选择患者性别` | 当前规则为 `required: false`，不应期待该错误出现 |
| `desc` | 最多 4096 字符 | `patientManage:modal.validation.remark.max` | `备注最多4096个字符` | 输入 4097 个字符后点确定，断言该错误提示可见 |

## UI 自动化可查询的前端元素

i18n key 本身通常不会渲染到 DOM 中，UI 自动化应查询渲染后的前端元素。下表中的 key 仅作为文案来源和维护索引。

| 元素用途 | UI 自动化查询对象 | 推荐查询方式 | zh-CN 可见文案/属性 | 文案来源 key |
| --- | --- | --- | --- | --- |
| 新建患者按钮 | 按钮文本 | 按 role/button name 或文本查询 | `新建患者` | `patientManage:action.create` |
| 新建患者弹窗 | 弹窗标题文本 | 按 dialog 标题或文本查询 | `新建患者信息` | `patientManage:modal.title` |
| 确定按钮 | 按钮文本 | 按 role/button name 查询 | `确定` | `patientManage:action.confirm` |
| 取消按钮 | 按钮文本 | 按 role/button name 查询 | `取消` | `patientManage:action.cancel` |
| 创建成功提示 | message/toast 文本 | 按可见文本查询 | `新增患者成功` | `patientManage:message.createSuccess` |
| 姓名字段 | label 文本 | 按 label 文本关联输入框 | `姓名` | `patientManage:modal.form.name.label` |
| 姓名输入框 | placeholder 属性 | 按 placeholder 查询 | `请输入姓名` | `patientManage:modal.form.name.placeholder` |
| 生日字段 | label 文本 | 按 label 文本或日期输入控件查询 | `生日` | `patientManage:modal.form.birthday.label` |
| 电话号码字段 | label 文本 | 按 label 文本关联输入框 | `电话号码` | `patientManage:modal.form.phone.label` |
| 电话号码输入框 | placeholder 属性 | 按 placeholder 查询 | `请输入电话号码` | `patientManage:modal.form.phone.placeholder` |
| 性别字段 | label 文本 | 按 label 文本查询 | `性别` | `patientManage:modal.form.gender.label` |
| 男性选项 | 选项可见文本 | 按文本查询 | `男` | `patientManage:gender.male` |
| 女性选项 | 选项可见文本 | 按文本查询 | `女` | `patientManage:gender.female` |
| 备注字段 | label 文本 | 按 label 文本关联文本域 | `备注` | `patientManage:modal.form.remark.label` |
| 备注文本域 | placeholder 属性 | 按 placeholder 查询 | `请输入备注信息` | `patientManage:modal.form.remark.placeholder` |

## 后端接口可验证规则

当前前端仓库只能确认接口封装和类型声明。真实线上后端源码不在仓库中，不能仅凭前端代码确定线上后端完整规则。

接口封装：

- `savePatient(data)`
- 请求方法：`post`
- 网关命令：`CommandId.SavePatient`

接口类型声明：

| 字段 | 类型声明 | 是否可选 | 标记 | 接口验证建议 |
| --- | --- | --- | --- | --- |
| `name` | `string` | 否 | `API` + `UNKNOWN_BACKEND` | 发送空、空格、超长姓名，记录真实接口响应 |
| `dateOfBirth` | `Date` | 否 | `API` + `UNKNOWN_BACKEND` | 发送空值、非法日期、未来日期，记录真实接口响应 |
| `gender` | `number` | 否 | `API` + `UNKNOWN_BACKEND` | 发送 `1`、`2`、`0`、非法值，记录真实接口响应 |
| `identityCard` | `string` | 是 | `API` + `UNKNOWN_BACKEND` | 发送 15/18 位、非法长度、空值，记录真实接口响应 |
| `telephone` | `string` | 是 | `API` + `UNKNOWN_BACKEND` | 发送空值、超长、非数字、特殊字符，记录真实接口响应 |
| `desc` | 类型声明未在 `SavePatientRequest` 中列出，但 UI 会提交 | `any` 路径 | `API` + `UNKNOWN_BACKEND` | 发送空值、超长、特殊字符，记录真实接口响应 |

线上后端待确认项：

- 是否要求 `dateOfBirth` 必填。
- 是否要求 `gender` 必填。
- 是否校验电话格式。
- 是否校验身份证 15/18 位。
- 是否限制姓名 200 字符。
- 是否限制电话 50 字符。
- 是否限制备注 4096 字符。
- 是否接受 UI 传入的 `desc` 字段。

## 特殊处理与非纯 UI 断言项

| 字段/行为 | 特殊处理 | 标记 | 推荐验证方式 |
| --- | --- | --- | --- |
| `dateOfBirth` | 前端提交前执行 `valueOf()`，转为毫秒时间戳 | `SPECIAL` | 拦截请求或 mock `savePatient`，断言请求体字段类型和值 |
| `telephone` | 前端提交前执行 `trim()` | `SPECIAL` | 拦截请求或 mock `savePatient`，输入前后空格后断言请求体已 trim |
| `name` | 前端提交前没有 trim，也没有 `whitespace: true` | `SPECIAL` | UI 可验证纯空格可能不触发必填提示；接口验证后端是否拒绝 |
| `gender` | UI 值为男 `1`、女 `2`；离线层转本地 `1/0` | `SPECIAL` | 接口层验证请求值；离线模式可验证本地存储映射 |
| `identityCard` | UI 没有字段，但接口类型声明存在 | `SPECIAL` + `API` | 仅通过接口自动化验证，不做 UI 自动化用例 |
| 创建成功跳转 | 使用接口返回的 `data.id` 拼接 URL | `UI` + `API` | UI 断言 URL 包含 `patientID`；接口断言响应含 `data.id` |

## 仓库可见离线网关/SQLite 规则

这些规则属于仓库内离线实现，不等同于线上后端真实规则。

离线网关处理 `SavePatient`：

| 字段 | 离线处理/校验 | 标记 | 可验证方式 |
| --- | --- | --- | --- |
| `name` | 转文本并 `trim()`；trim 后为空返回“患者姓名不能为空” | `API` + `SPECIAL` | 离线接口验证或数据层单元测试 |
| `dateOfBirth` | 支持 `Date`、数字、字符串解析；无效、空值、非正数转为 `null` | `API` + `SPECIAL` | 离线接口验证或数据层单元测试 |
| `gender` | API `1` 转本地 `1`；API `2` 或 `0` 转本地 `0`；其他值转为 `null` | `API` + `SPECIAL` | 离线接口验证或数据库检查 |
| `identityCard` | trim 后空值转为 `null` | `API` + `SPECIAL` | 离线接口验证或数据库检查 |
| `telephone` | trim 后空值转为 `null` | `API` + `SPECIAL` | 离线接口验证或数据库检查 |
| `desc` | trim 后空值转为 `null` | `API` + `SPECIAL` | 离线接口验证或数据库检查 |

SQLite 表结构约束：

| 字段 | SQLite 约束 | 标记 |
| --- | --- | --- |
| `id` | `TEXT PRIMARY KEY NOT NULL` | `SPECIAL` |
| `name` | `TEXT NOT NULL` | `SPECIAL` |
| `gender` | `INTEGER CHECK (gender IN (0, 1))`，可为空 | `SPECIAL` |
| `dateOfBirth` | `INTEGER`，可为空 | `SPECIAL` |
| `desc` | `TEXT DEFAULT ''` | `SPECIAL` |
| `identityCard` | `TEXT`，可为空 | `SPECIAL` |
| `telephone` | `TEXT`，可为空 | `SPECIAL` |
| `deleted` | `INTEGER NOT NULL DEFAULT 0` | `SPECIAL` |

离线层未发现以下硬校验：

- 电话号码格式校验。
- 身份证 15/18 位格式校验。
- 生日范围校验。
- 姓名最大 200 字符校验。
- 电话最大 50 字符校验。
- 备注最大 4096 字符校验。

## 汇总矩阵

| 字段/规则 | UI 可验证 | API 可验证 | SPECIAL | UNKNOWN_BACKEND |
| --- | --- | --- | --- | --- |
| 姓名必填 | 是，断言前端错误提示 | 是，需真实接口响应确认 | 后端/离线会 trim | 线上规则未知 |
| 姓名最多 200 字符 | 是，断言前端错误提示 | 是，需真实接口响应确认 | 前端不 trim | 线上规则未知 |
| 生日非必填 | 是，空生日可提交到接口调用阶段 | 是，需真实接口响应确认 | 提交前转毫秒；非法值离线转 `null` | 线上规则未知 |
| 电话非必填 | 是，空电话可提交到接口调用阶段 | 是，需真实接口响应确认 | 提交前 trim；离线空值转 `null` | 线上规则未知 |
| 电话最多 50 字符 | 部分可验证；输入框 `maxLength=50` 会阻止输入超长 | 是，需绕过 UI 直接发接口确认 | 前端表单也有 max 规则 | 线上规则未知 |
| 电话格式 | 否，当前 UI 无格式校验 | 是，需真实接口响应确认 | 离线未发现格式校验 | 线上规则未知 |
| 性别非必填 | 是，不选性别可提交到接口调用阶段 | 是，需真实接口响应确认 | 离线会映射 `1/2` 到 `1/0` | 线上规则未知 |
| 备注最多 4096 字符 | 是，断言前端错误提示 | 是，需真实接口响应确认 | 离线未发现长度校验 | 线上规则未知 |
| 身份证格式 | 否，UI 无身份证字段 | 是，直接接口验证 | 离线仅 trim/空转 null | 线上规则未知 |
