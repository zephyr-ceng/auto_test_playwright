# Apifox 模块集合

本目录下每个 `.postman.json` 文件对应标准接口文档中的一个现有分组，可单独导入 Apifox。

导入前请先导入上级目录的 `apifox-shared-environment.postman_environment.json`，或在 Apifox 项目/环境变量中维护同名变量。

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
