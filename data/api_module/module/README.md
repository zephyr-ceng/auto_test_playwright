# 项目接口模块文档

本目录依据 `api-docs/api-build.md` 的接口描述规范，结合当前项目接口集合 `api-docs/apifox-collection.postman.json` 生成。

## 来源与版本

- 规范来源：`api-docs/api-build.md`
- 项目接口来源：`api-docs/apifox-collection.postman.json`
- 共享变量来源：`api-docs/apifox-shared-environment.postman_environment.json`
- 接口规范版本：`v1.0.0`
- 生成日期：`2026-06-24`
- 编码：`UTF-8`

## 目录结构

| 目录 | 说明 |
| --- | --- |
| `md/` | 按项目模块拆分后的 Markdown 接口文档 |
| `yaml/` | 与 `md/` 文件一一对应的结构化 YAML 接口文档 |

## 环境

| 环境项 | 地址 |
| --- | --- |
| 前端登录页 | `http://localhost:3000/login` |
| 普通接口基址 | `http://localhost:3000/tars/v1` |
| 网关接口 | `http://localhost:3000/tars/v1/gateway` |
| 控制节点接口 | `http://192.168.0.52:38080/tars/v1` |
| ROS 接口 | `http://192.168.0.52:38081/ros_api/v1` |
| 聊天接口 | `http://192.168.2.159:9999/api/v3` |

## 通用约定

- 默认请求与响应编码为 `UTF-8`。
- JSON 接口默认使用 `Content-Type: application/json`。
- 登录成功后服务端通过 `Set-Cookie` 返回 `session`，Cookie 带 `HttpOnly`。
- 后续需要登录态的接口由客户端 Cookie Jar 或 Apifox Cookie 管理器维护登录态。
- 统一网关接口固定请求 `POST {{gatewayUrl}}`，通过小写 `command` 请求头区分业务指令。
- YAML 文档使用项目自定义结构 `TarsModuleApiDocument`，用于完整保留同一路径下的多个网关 command 接口。

## 业务状态码

| code | 含义 | 处理建议 |
| ---: | --- | --- |
| `0` | Success | 请求成功且业务逻辑处理正常 |
| `40001` | Unauthorized | 未登录或登录态 Cookie 已过期，客户端应重新登录 |
| `40003` | Permission Denied | 权限不足，禁止访问该资源 |
| `50000` | Internal Error | 服务器内部未知异常，请联系系统管理员 |

## 模块对应关系

| 序号 | 模块 | 接口数 | Markdown | YAML |
| ---: | --- | ---: | --- | --- |
| 1 | 登录认证 | 6 | `md/01-login-auth.md` | `yaml/01-login-auth.yaml` |
| 2 | 患者管理 | 8 | `md/02-patient-management.md` | `yaml/02-patient-management.yaml` |
| 3 | 病例与治疗序列 | 7 | `md/03-case-treatment-sequence.md` | `yaml/03-case-treatment-sequence.yaml` |
| 4 | 手术设计 | 11 | `md/04-surgical-design.md` | `yaml/04-surgical-design.yaml` |
| 5 | 文件管理 | 6 | `md/05-file-management.md` | `yaml/05-file-management.yaml` |
| 6 | 控制节点 | 19 | `md/06-control-node.md` | `yaml/06-control-node.yaml` |
| 7 | 网络与 Wi-Fi | 7 | `md/07-network-wifi.md` | `yaml/07-network-wifi.yaml` |
| 8 | 植体系统 | 4 | `md/08-implant-system.md` | `yaml/08-implant-system.yaml` |
| 9 | OTP 密钥 | 6 | `md/09-otp-secret.md` | `yaml/09-otp-secret.yaml` |
| 10 | AI 分割 | 3 | `md/10-ai-partition.md` | `yaml/10-ai-partition.yaml` |
| 11 | 积分 | 3 | `md/11-points.md` | `yaml/11-points.yaml` |
| 12 | 系统消息与设备 | 4 | `md/12-system-message-device.md` | `yaml/12-system-message-device.yaml` |
| 13 | 用户配置 | 2 | `md/13-user-config.md` | `yaml/13-user-config.yaml` |
| 14 | ROS 与导航 | 15 | `md/14-ros-navigation.md` | `yaml/14-ros-navigation.yaml` |
| 15 | 聊天与助手 | 2 | `md/15-chat-assistant.md` | `yaml/15-chat-assistant.yaml` |
| 16 | 外部资源与连接 | 4 | `md/16-external-resource-connection.md` | `yaml/16-external-resource-connection.yaml` |
