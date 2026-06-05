# API Docs

本目录由前端代码静态整理接口生成，已按业务域分组，并支持按模块单独导入 Apifox。

## 文件说明

- `standard-api-doc.md`：标准接口文档，包含接口名称、描述、请求地址、方式、请求头、Req、Res 和源码位置。
- `apifox-collection.postman.json`：完整集合文件，保留 16 个现有分组和网关 `command` header，不写入集合变量。
- `apifox-shared-environment.postman_environment.json`：共享环境变量文件，供完整集合和模块集合共同使用。
- `modules/*.postman.json`：按现有分组拆分后的模块集合文件，可分模块导入 Apifox。
- `tars-admin-frontend.har`：可导入 Apifox 的 HAR 文件，按接口生成请求包；网关接口通过 `command` header 区分。
- `validation-report.md`：接口验证记录、已修正问题、变量提取链路和未执行接口说明。
- `test-cases.md`：接口测试用例设计、CSV 数据驱动字段映射和后置断言说明。
- `generate-api-docs.mjs`：文档生成脚本。

## 本地环境

- 前端登录页：`http://localhost:3000/login`
- 普通后端接口：`http://localhost:3000/tars/v1`
- 网关接口：`http://localhost:3000/tars/v1/gateway`
- 控制节点接口：`http://192.168.0.52:38080/tars/v1`
- ROS 接口：`http://192.168.0.52:38081/ros_api/v1`
- 聊天接口：`http://192.168.2.159:9999/api/v3`

## Apifox 使用建议

1. 需要一次性导入时，导入 `apifox-collection.postman.json`；需要分模块导入时，按需导入 `modules/*.postman.json`。
2. 变量已提升到共享环境/全局变量，不再设置为集合或模块变量；建议先导入 `apifox-shared-environment.postman_environment.json`。
3. 接口级前置校验和后置提取脚本会把登录态、患者、病例、文件、设计、任务和消息等关联值写入环境变量和全局变量。
4. 网关接口统一请求 `POST {{gatewayUrl}}`，并保留小写 `command` header 作为分发指令。
5. DICOM/模型文件相关接口统一使用 `{{patientID}}`，共享环境默认值为 `692776867656982528`。
6. 登录和新增患者接口支持 CSV 数据驱动；不挂载 CSV 时使用共享环境变量中的默认有效用例。
7. 登录后如接口需要鉴权，在 Apifox 的 Cookie 管理器或环境鉴权配置中维护登录态；导入请求中不预置 Cookie/HWID 等非必要 header。

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
