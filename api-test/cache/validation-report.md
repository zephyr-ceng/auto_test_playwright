# API 验证报告

- 验证日期：2026-06-05
- 本地登录页：`http://localhost:3000/login`
- 普通接口基址：`http://localhost:3000/tars/v1`
- 网关接口基址：`http://localhost:3000/tars/v1/gateway`

## 已实际请求验证

- 登录接口 `POST /tars/v1/login_by_username`：`username=admin`、`password=admin`、`returnToken=false` 可返回 `Set-Cookie: session=...`；该 Cookie 为 http-only，集合后置脚本只提取响应头中的 `sessionCookie` 变量，不在请求头中预置 Cookie。
- 登录接口 `returnToken=true`：本地返回 token，不返回 Cookie；文档默认改为 `returnToken=false`，更贴近后续 Cookie 鉴权链路。
- 登录 CSV 无效用例实测：`demo/123` 与空账号/空密码组合在接口层均返回 `该账号未注册，请联系管理员`；空字段提示属于前端表单校验，不是当前接口响应。
- 网关患者新增 `command=13002`：`dateOfBirth` 必须为 int64 毫秒时间戳，字符串日期会返回 Go 反序列化错误；文档已改为 `631123200000`。
- 患者 CSV 无效字段实测：姓名为空、姓名超长、手机号格式错误、备注超长当前在 `savePatient` 接口层仍返回 `code=0` 和患者 ID；这些校验文案属于前端表单校验，不是当前接口响应。
- 已串联验证通过：登录 -> `16001 getUserInfo` -> `13002 savePatient` -> `13001 queryPatientPage` -> `13003 updatePatient` -> `13007 searchPatientV2` -> `15001 addCase` -> `15003 treatmentSequence`。
- 文件与设计链路验证通过：`11001 startFileUpload` -> `14002 addDesign` -> `14005 queryDesignDetail` -> `14003 changeDesign`；`14002` 实际返回 `version=0`，`14003` 使用 `version=0` 后返回下一版本。
- 辅助接口抽样验证通过：`18004 getImplantFavorites`、`18002 getUserConfig`、`20002 getPointSummary`、`19001 searchMessage`、`20001 getDeviceList`。

## 已修正文档问题

- 网关接口统一保留小写 `command` header，移除 `PlatFrom`、`Version`、`Request-ID`、`Cookie`、`HWID`、`Command` 等非必要导入请求头。
- 登录请求体改为共享环境变量：`username={{username}}`、`password={{password}}`、`returnToken=false`。
- `savePatient`、`queryPatientPage`、`updatePatient` 使用 `patientName`、`patientIdentityCard`、`patientTelephone` 变量；`updatePatient` 补齐 `gender`、`dateOfBirth`、`identityCard`，避免只传部分字段导致后端把字段清零。
- 病例、治疗序列、文件上传、手术设计、AI 分割、系统消息、OTP、积分和用户配置接口均补充前置变量校验与后置变量提取。
- 所有导入集合接口均添加基础后置断言；重点接口按实际响应字段增加字段级断言。登录和新增患者接口支持读取 CSV 数据并映射为接口实际预期后断言。
- DICOM/模型文件相关接口 `bindModelFileToPatient`、`unbindModelFileToPatient`、`searchPatientDetailsMessageV2`、`changeBindFile` 统一使用 `{{patientID}}`，默认值为 `692776867656982528`。
- `changeTreatmentSequence.status` 改为 number 示例，避免后端按数字字段解析失败。
- `addDesign`/`addDesignV2` 响应示例版本改为 `0`，`changeDesign` 使用 `version=0` 并提取返回的新 `designVersion`。
- ROS/导航中带 query 的 `{designID}`、`{filename}`、`{stream_id}` 占位改为共享环境变量。

## 前置/后置脚本

- 集合/模块前置脚本：写入默认变量，并把 `patientID=692776867656982528` 同步到全局变量，供 DICOM/模型文件相关接口复用。
- 接口级前置脚本：对依赖变量做断言，例如 `patientId`、`caseId`、`treatmentId`、`fileKey`、`designId`、`designVersion`、`taskId`、`messageId`、`hwid`、`otpSecret`、`otpCode`。
- 接口级后置脚本：从响应 JSON 或响应头提取关联变量，包括登录 Cookie、用户/租户/账户 ID、患者 ID、病例 ID、治疗阶段 ID、文件 key、设计 ID/版本、AI 任务 ID、消息 ID、控制节点 hwid、OTP secret/code。

## 未执行或需人工验证

- 控制节点破坏性或设备状态变更接口未实测：关机、重启、删除本地文件、开始升级、设置升级、连接/断开 Wi-Fi、开启/关闭热点、导出到移动盘、录屏开始/停止。
- ROS、聊天流、SSE、WebSocket、外部预签名下载、GDCM WASM 静态资源接口受设备/外部服务依赖限制，已做静态结构校验。
- `navChangeDesign` 使用当前本地样例和前端真实字段均返回业务错误 `code=-10602`，文档保留接口与变量链路，但报告中标记为需后端或有效设计数据进一步确认。

## 模块化导入 Apifox

- `apifox-collection.postman.json`：完整集合入口，仍保留 16 个现有分组，但不再写入集合变量。
- `apifox-shared-environment.postman_environment.json`：共享环境变量文件，包含 `baseUrl`、`gatewayUrl`、`username`、`password`、`patientID=692776867656982528` 等变量。
- `modules/*.postman.json`：按现有分组拆分后的模块集合文件，每个文件只包含一个分组的接口，可单独导入 Apifox。
- 模块集合不包含 `variable` 字段，也不设置文件夹/模块变量；接口脚本会把登录、患者、病例、文件、设计等关联 ID 写入环境变量和全局变量。
- 建议导入顺序：先导入共享环境变量文件，再按需导入 `modules/` 下的模块集合。

| 模块文件 | 分组 | 接口数 |
| --- | --- | ---: |
| `modules/01-login-auth.postman.json` | 登录认证 | 6 |
| `modules/02-patient-management.postman.json` | 患者管理 | 8 |
| `modules/03-case-treatment-sequence.postman.json` | 病例与治疗序列 | 7 |
| `modules/04-surgical-design.postman.json` | 手术设计 | 11 |
| `modules/05-file-management.postman.json` | 文件管理 | 6 |
| `modules/06-control-node.postman.json` | 控制节点 | 19 |
| `modules/07-network-wifi.postman.json` | 网络与 Wi-Fi | 7 |
| `modules/08-implant-system.postman.json` | 植体系统 | 4 |
| `modules/09-otp-secret.postman.json` | OTP 密钥 | 6 |
| `modules/10-ai-partition.postman.json` | AI 分割 | 3 |
| `modules/11-points.postman.json` | 积分 | 3 |
| `modules/12-system-message-device.postman.json` | 系统消息与设备 | 4 |
| `modules/13-user-config.postman.json` | 用户配置 | 2 |
| `modules/14-ros-navigation.postman.json` | ROS 与导航 | 15 |
| `modules/15-chat-assistant.postman.json` | 聊天与助手 | 2 |
| `modules/16-external-resource-connection.postman.json` | 外部资源与连接 | 4 |
