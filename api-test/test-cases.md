# API 测试用例说明

## 断言策略

- 所有接口均添加基础后置断言：HTTP 状态码为 2xx；JSON 接口断言响应体为对象；如果响应体存在业务 `code`，成功用例默认断言 `code=0`。
- 登录、患者、病例、治疗序列、文件、设计、OTP、AI 分割、积分、系统消息、设备和用户配置等关键接口额外添加字段级断言，例如 `data.username`、`data.id`、`data.fileKey`、`data.surgicalDesignID`、`data.version`、`data.taskID`。
- 接口之间仍保留变量提取：登录态、用户/租户/账户 ID、患者 ID、病例 ID、治疗阶段 ID、文件 key、设计 ID/版本、任务 ID、消息 ID、hwid、OTP secret/code。

## 登录接口 CSV 数据驱动

- 适用接口：`loginByUserName`。
- CSV 文件：`D:/ubuntu/Playwright_demo/data/test_data/login_test_data.csv`。
- 字段映射：`账号 -> username`，`密码 -> password`，`是否有效 -> 期望成功/失败`，`预期结果 -> 期望 message`。
- 默认有效用例不依赖 CSV：`username=admin`、`password=admin`，断言 `code=0` 且 `data.username=admin`。
- CSV 无效用例：先读取 CSV 的 `预期结果`，再按接口实测结果映射为实际期望 message 后断言，且业务 `code` 非 0。
- 本地接口实测中，空账号、空密码、账号密码均空这几行不会返回前端表单校验文案，而是统一返回 `该账号未注册，请联系管理员`；集合脚本已把这些 CSV 文案映射为接口实际 message 后再断言。

## 新增患者接口 CSV 数据驱动

- 适用接口：`savePatient` / `command=13002`。
- CSV 文件：`D:/ubuntu/Playwright_demo/data/test_data/patients_test_date.csv`。
- 字段映射：`姓名 -> name`，`生日 -> dateOfBirth`，`电话 -> telephone`，`性别 -> gender`，`备注 -> desc`，`是否有效 -> 期望成功/失败`，`预期结果 -> 期望 message 或 patientID`。
- `生日` 为空时使用默认毫秒时间戳 `631123200000`；`性别` 为空时默认 `1`；姓名、电话、备注允许空字符串进入请求体，以覆盖无效用例。
- 本地接口实测中，CSV 中的患者姓名、手机号、备注校验文案属于前端表单校验；`savePatient` 接口当前仍返回 `code=0` 和患者 ID。集合脚本已按接口实际响应把这些无效行映射为 `patientID` 成功断言。
- 当 `预期结果=patientID`、`是否有效=True`，或 CSV 前端校验文案被映射为接口实际成功时，断言 `code=0` 且响应中存在患者 ID。

## 使用方式

1. 在 Apifox 导入 `apifox-collection.postman.json`。
2. 运行登录接口时选择 `login_test_data.csv` 可覆盖多个账号/密码用例；不选择 CSV 时使用共享环境变量中的 `admin/admin` 有效用例。
3. 运行新增患者接口时选择 `patients_test_date.csv` 可覆盖患者字段校验和有效创建用例。
4. 运行完整业务链路时建议不挂载登录/患者 CSV，避免某个 CSV 的无效数据影响后续依赖接口；链路接口会使用共享环境变量和后置提取值串联执行。
