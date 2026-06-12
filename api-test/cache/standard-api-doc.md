# TARS Admin Frontend 标准接口文档

> 根据前端代码静态整理生成。统一 API 封装来源：`src/api/request.ts`。

## 环境与通用约定

- 本地前端登录页：`http://localhost:3000/login`
- `{{baseUrl}}`：`http://localhost:3000/tars/v1`
- `{{gatewayUrl}}`：`http://localhost:3000/tars/v1/gateway`
- `{{controlNodeBaseUrl}}`：`http://192.168.0.52:38080/tars/v1`
- `{{rosBaseUrl}}`：`http://192.168.0.52:38081/ros_api/v1`
- `{{chatBaseUrl}}`：`http://192.168.2.159:9999/api/v3`

前端运行时会自动补充以下 header；Apifox 导入文件已移除这些非必要 header，只保留调试必需项：

| Header | 值 | 说明 |
| --- | --- | --- |
| `PlatFrom` | `web` | 前端固定请求头 |
| `Version` | `v1` | 前端固定请求头 |
| `Request-ID` | `{{$guid}}` | 前端运行时自动生成 UUID |
| `Cookie` | `{{cookie}}` | 浏览器 withCredentials 自动携带；Apifox 中可手动设置登录后的 Cookie |

网关接口统一请求 `POST {{gatewayUrl}}`，必须额外携带 `command` header。接口身份由 `command` 数值区分，业务请求体仍放在 JSON body 中。

### Apifox 导入变量与执行链路

导入 `apifox-collection.postman.json` 或 `modules/*.postman.json` 前，建议先导入 `apifox-shared-environment.postman_environment.json`。集合和模块文件不再写入集合/模块变量；前置/后置脚本通过环境变量和全局变量在接口之间自动传递登录态、患者、病例、文件、设计、任务和消息等 ID。DICOM/模型文件相关接口统一使用 `{{patientID}}`，默认值为 `692776867656982528`。

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `username` | `admin` | 登录用户名 |
| `password` | `admin` | 登录密码 |
| `sessionCookie` | `` | 登录接口 Set-Cookie 提取值；http-only Cookie 由客户端 Cookie Jar 维护 |
| `token` | `` | 登录 returnToken=true 时的 token |
| `userId` | `1` | 当前登录用户 ID |
| `tenantId` | `1` | 当前租户 ID |
| `accountId` | `5` | 当前账户 ID |
| `patientId` | `` | 新增患者或查询患者列表后提取的普通患者 ID |
| `patientID` | `692776867656982528` | DICOM/模型文件相关接口固定患者 ID |
| `patientName` | `李松` | 新增、查询、更新患者姓名 |
| `patientIdentityCard` | `110101199001010011` | 新增、更新患者身份证号 |
| `patientTelephone` | `13800138000` | 新增、查询、更新患者电话 |
| `caseId` | `` | 新增/更新病例后提取的病例 ID |
| `treatmentId` | `` | 新增治疗阶段后提取的治疗阶段 ID |
| `fileKey` | `` | 开始分片上传后提取的文件 key |
| `oldFileKey` | `` | 变更绑定文件时使用的旧文件 key |
| `thumbnailFileKey` | `` | 设计缩略图文件 key，默认可由 fileKey 回填 |
| `designId` | `` | 创建设计后提取的手术设计 ID |
| `designVersion` | `0` | 创建设计、修改设计或查询详情后提取的设计版本 |
| `taskId` | `` | AI 分割任务 ID |
| `messageId` | `` | 系统消息 ID |
| `hwid` | `` | 控制节点硬件 ID |
| `otpSecret` | `` | 生成 OTP Secret 后提取的 secret |
| `otpCode` | `` | 获取用户 OTP Code 后提取的动态码 |
| `filename` | `model.stl` | ROS 下载模型文件名 |
| `streamId` | `1710000000000` | ROS JPEG 流 ID |

推荐执行顺序：登录 -> 获取当前用户 -> 新增患者 -> 新增病例 -> 新增治疗阶段 -> 开始文件上传 -> 创建设计 -> 修改/查询设计。依赖 DICOM 文件的接口可直接使用默认 `{{patientID}}`。

## 接口架构梳理

| 客户端 | 创建位置 | 基址 | 用途 |
| --- | --- | --- | --- |
| `commonHttp` | `src/api/request.ts` | `{{baseUrl}}` | 登录、登出、短信、设置、后端中转文件上传等普通 `/tars/v1` 接口 |
| `gateWayHttp` | `src/api/request.ts` | `{{gatewayUrl}}` | 业务网关接口，固定 `POST /tars/v1/gateway`，通过 `command` header 区分业务接口；离线模式下会经过 `GatewayHttpOfflineInterceptorManager` |
| `controlNodeHttp` | `src/api/request.ts` | `{{controlNodeBaseUrl}}` | 控制节点接口，包括文件、Wi-Fi、版本、录屏、升级、OTP 本地校验等 |
| `rosHttp` | `src/api/request.ts` | `{{rosBaseUrl}}` | ROS HTTP 接口，包括 Marker、模型文件同步、JPEG 流、MR 升级和灯光控制 |
| `chatHttp` | `src/api/request.ts` | `{{chatBaseUrl}}` | 聊天节点流式接口 |
| 直接网络调用 | 多处 | 预签名 URL / `ws://...:9090` / `/cs/gdcmconv.js` | 文件分片下载、ROS WebSocket、SSE、静态运行时资源加载等补充入口 |

## 分组总览

| 分组 | 接口数 | 说明 |
| --- | ---: | --- |
| 登录认证 | 6 | 登录、登出、短信验证码、密码重置和当前用户信息。 |
| 患者管理 | 8 | 患者新增、更新、查询、删除和模型文件绑定。 |
| 病例与治疗序列 | 7 | 病例新增、更新、删除和治疗阶段维护。 |
| 手术设计 | 11 | 设计列表、创建、修改、详情、开始和结束手术。 |
| 文件管理 | 6 | 文件分片上传、单文件上传、上传完成通知和文件描述查询。 |
| 控制节点 | 19 | 本机文件、设备关机重启、版本、导出、录屏和升级。 |
| 网络与 Wi-Fi | 7 | 网络速率、Wi-Fi 列表、连接状态和热点开关。 |
| 植体系统 | 4 | 植体系统配置和收藏管理。 |
| OTP 密钥 | 6 | OTP secret 生成、校验、上传、查询和按设备取验证码。 |
| AI 分割 | 3 | 启动 AI 分割任务、查询任务状态和牙尖异常分析。 |
| 积分 | 3 | 积分总览、明细和提醒列表。 |
| 系统消息与设备 | 4 | 系统消息列表、已读、删除和设备列表。 |
| 用户配置 | 2 | 用户级配置读取和保存。 |
| ROS 与导航 | 15 | ROS HTTP 接口、模型文件同步、JPEG 流、灯光控制和眼镜升级。 |
| 聊天与助手 | 2 | 聊天补全流式接口和全局助手 SSE。 |
| 外部资源与连接 | 4 | 预签名资源下载、网络探测、ROS WebSocket 和静态运行时资源。 |

## 接口明细

### 登录认证

说明：登录、登出、短信验证码、密码重置和当前用户信息。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| loginByUserName | 使用 username/password 登录，可通过 returnToken 要求后端返回 token。 | `POST` | `{{baseUrl}}/login_by_username` | username, password, returnToken | JSON | `src/api/login/index.ts` |
| logout | 退出当前登录会话。 | `POST` | `{{baseUrl}}/logout` | 无 | JSON | `src/api/login/index.ts` |
| loginByTel | 使用 telephone/code 登录，可通过 returnToken 要求后端返回 token。 | `POST` | `{{baseUrl}}/login_by_telephone` | telephone, code, returnToken | JSON | `src/api/login/index.ts` |
| sendSMS | 发送登录或重置密码短信验证码。 | `POST` | `{{baseUrl}}/send_sms` | telephone, type | JSON | `src/api/login/index.ts` |
| resetPassword | 通过手机号验证码重置密码。 | `POST` | `{{baseUrl}}/reset_password` | telephone, code, newPassword | JSON | `src/api/login/index.ts` |
| getUserInfo | 通过网关 Command 获取当前登录用户信息。 | `POST` | `{{gatewayUrl}}` | Header: command=16001 | JSON | `src/api/login/index.ts` |

#### 登录认证 / 用户名密码登录

- 接口名称：`loginByUserName`
- 接口描述：使用 username/password 登录，可通过 returnToken 要求后端返回 token。
- 请求地址：`{{baseUrl}}/login_by_username`
- 请求方式：`POST`
- 代码来源：`src/api/login/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "username": "{{username}}",
  "password": "{{password}}",
  "returnToken": false
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "accountID": "account-id",
    "name": "管理员",
    "tenantID": "tenant-id",
    "tenantType": "clinic",
    "userID": "user-id",
    "username": "admin",
    "token": ""
  },
  "message": "success"
}
```

#### 登录认证 / 登出

- 接口名称：`logout`
- 接口描述：退出当前登录会话。
- 请求地址：`{{baseUrl}}/logout`
- 请求方式：`POST`
- 代码来源：`src/api/login/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "message": "success"
}
```

#### 登录认证 / 手机号验证码登录

- 接口名称：`loginByTel`
- 接口描述：使用 telephone/code 登录，可通过 returnToken 要求后端返回 token。
- 请求地址：`{{baseUrl}}/login_by_telephone`
- 请求方式：`POST`
- 代码来源：`src/api/login/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "telephone": "13800138000",
  "code": "123456",
  "returnToken": true
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "accountID": "account-id",
    "name": "用户",
    "tenantID": "tenant-id",
    "userID": "user-id",
    "token": "token-if-returnToken"
  },
  "message": "success"
}
```

#### 登录认证 / 发送短信验证码

- 接口名称：`sendSMS`
- 接口描述：发送登录或重置密码短信验证码。
- 请求地址：`{{baseUrl}}/send_sms`
- 请求方式：`POST`
- 代码来源：`src/api/login/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "telephone": "13800138000",
  "type": "login"
}
```
- Res：

```json
{
  "code": 0,
  "data": "sms-id-or-message",
  "message": "success"
}
```

#### 登录认证 / 重置密码

- 接口名称：`resetPassword`
- 接口描述：通过手机号验证码重置密码。
- 请求地址：`{{baseUrl}}/reset_password`
- 请求方式：`POST`
- 代码来源：`src/api/login/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "telephone": "13800138000",
  "code": "123456",
  "newPassword": "new-password"
}
```
- Res：

```json
{
  "code": 0,
  "data": "ok",
  "message": "success"
}
```

#### 登录认证 / 获取当前用户信息

- 接口名称：`getUserInfo`
- 接口描述：通过网关 Command 获取当前登录用户信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`16001`（CommandId.GetUserInfo）
- 代码来源：`src/api/login/index.ts`
- 请求头：
  - `command: 16001`：网关分发指令，CommandId.GetUserInfo = 16001
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "AccountID": "account-id",
    "ID": "user-id",
    "Name": "管理员",
    "TenantID": "tenant-id",
    "TenantType": "clinic"
  },
  "message": "success"
}
```

### 患者管理

说明：患者新增、更新、查询、删除和模型文件绑定。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| savePatient | 创建患者基础信息。 | `POST` | `{{gatewayUrl}}` | Header: command=13002 | JSON | `src/api/patient/index.ts` |
| updatePatient | 更新患者姓名和电话等基础信息。 | `POST` | `{{gatewayUrl}}` | Header: command=13003 | JSON | `src/api/patient/index.ts` |
| queryPatientPage | 按姓名、性别、电话分页查询患者。 | `POST` | `{{gatewayUrl}}` | Header: command=13001 | JSON | `src/api/patient/index.ts` |
| delPatient | 按患者 ID 删除患者。 | `POST` | `{{gatewayUrl}}` | Header: command=13004 | JSON | `src/api/patient/index.ts` |
| bindModelFileToPatient | 将已上传文件绑定到患者。 | `POST` | `{{gatewayUrl}}` | Header: command=13005 | JSON | `src/api/patient/index.ts` |
| unbindModelFileToPatient | 解除患者与文件的绑定关系。 | `POST` | `{{gatewayUrl}}` | Header: command=13006 | JSON | `src/api/patient/index.ts` |
| searchPatientDetailsMessageV2 | 查询患者详情，固定携带 needFiles 和 needMedicalRecords。 | `POST` | `{{gatewayUrl}}` | Header: command=13007 | JSON | `src/api/patient/index.ts` |
| changeBindFile | 变更患者关联文件信息，调用处传入 data，结构以后端约定为准。 | `POST` | `{{gatewayUrl}}` | Header: command=13008 | JSON | `src/api/patient/index.ts` |

#### 患者管理 / 新增患者

- 接口名称：`savePatient`
- 接口描述：创建患者基础信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13002`（CommandId.SavePatient）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13002`：网关分发指令，CommandId.SavePatient = 13002
- Req：

```json
{
  "name": "{{patientName}}",
  "gender": 1,
  "dateOfBirth": 631123200000,
  "identityCard": "{{patientIdentityCard}}",
  "telephone": "{{patientTelephone}}",
  "desc": ""
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "id": "patient-id",
    "name": "张三",
    "gender": 1,
    "dateOfBirth": 631123200000,
    "identityCard": "110101199001010011",
    "telephone": "13800138000",
    "desc": ""
  },
  "message": "success"
}
```

#### 患者管理 / 更新患者

- 接口名称：`updatePatient`
- 接口描述：更新患者姓名和电话等基础信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13003`（CommandId.UpdatePatient）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13003`：网关分发指令，CommandId.UpdatePatient = 13003
- Req：

```json
{
  "id": "{{patientId}}",
  "name": "{{patientName}}",
  "gender": 1,
  "dateOfBirth": 631123200000,
  "identityCard": "{{patientIdentityCard}}",
  "telephone": "{{patientTelephone}}",
  "desc": ""
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 患者管理 / 分页查询患者

- 接口名称：`queryPatientPage`
- 接口描述：按姓名、性别、电话分页查询患者。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13001`（CommandId.QueryPatientPage）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13001`：网关分发指令，CommandId.QueryPatientPage = 13001
- Req：

```json
{
  "pageIndex": 1,
  "pageSize": 10,
  "name": "{{patientName}}",
  "gender": 1,
  "telephone": "{{patientTelephone}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "data": [],
    "pageIndex": 1,
    "pageSize": 10,
    "total": 0
  },
  "message": "success"
}
```

#### 患者管理 / 删除患者

- 接口名称：`delPatient`
- 接口描述：按患者 ID 删除患者。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13004`（CommandId.DeletePatient）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13004`：网关分发指令，CommandId.DeletePatient = 13004
- Req：

```json
{
  "id": "{{patientId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "code": 0,
    "message": "success"
  },
  "message": "success"
}
```

#### 患者管理 / 绑定模型文件到患者

- 接口名称：`bindModelFileToPatient`
- 接口描述：将已上传文件绑定到患者。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13005`（CommandId.bindModelFile）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13005`：网关分发指令，CommandId.bindModelFile = 13005
- Req：

```json
{
  "patientID": "{{patientID}}",
  "fileKey": "{{fileKey}}",
  "tags": [
    "ct"
  ],
  "name": "CT.dcm",
  "type": "dcm",
  "params": "{}",
  "jawType": "upper",
  "treatmentID": "{{treatmentId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 患者管理 / 解绑患者模型文件

- 接口名称：`unbindModelFileToPatient`
- 接口描述：解除患者与文件的绑定关系。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13006`（CommandId.unbindModelFile）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13006`：网关分发指令，CommandId.unbindModelFile = 13006
- Req：

```json
{
  "patientID": "{{patientID}}",
  "fileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 患者管理 / 查询患者详情 V2

- 接口名称：`searchPatientDetailsMessageV2`
- 接口描述：查询患者详情，固定携带 needFiles 和 needMedicalRecords。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13007`（CommandId.SearchPatientV2）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13007`：网关分发指令，CommandId.SearchPatientV2 = 13007
- Req：

```json
{
  "id": "{{patientID}}",
  "needFiles": true,
  "needMedicalRecords": true
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "id": "patient-id",
    "name": "张三",
    "gender": 1,
    "medicalRecordList": [],
    "medicalRecords": [],
    "files": []
  },
  "message": "success"
}
```

#### 患者管理 / 变更绑定文件

- 接口名称：`changeBindFile`
- 接口描述：变更患者关联文件信息，调用处传入 data，结构以后端约定为准。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`13008`（CommandId.ChangeBindFile）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 13008`：网关分发指令，CommandId.ChangeBindFile = 13008
- Req：

```json
{
  "patientID": "{{patientID}}",
  "oldFileKey": "{{oldFileKey}}",
  "newFileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 病例与治疗序列

说明：病例新增、更新、删除和治疗阶段维护。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| addCase | 为患者新增病例记录。 | `POST` | `{{gatewayUrl}}` | Header: command=15001 | JSON | `src/api/case/index.ts` |
| updateCase | 更新病例记录；当前代码同样使用 Command 15001。 | `POST` | `{{gatewayUrl}}` | Header: command=15001 | JSON | `src/api/case/index.ts` |
| deleteCase | 按病例 ID 删除病例。 | `POST` | `{{gatewayUrl}}` | Header: command=15002 | JSON | `src/api/case/index.ts` |
| treatmentSequence | 添加治疗阶段或治疗方案节点。 | `POST` | `{{gatewayUrl}}` | Header: command=15003 | JSON | `src/api/patient/index.ts` |
| changeTreatmentSequence | 更新治疗阶段名称、日期、描述和状态。 | `POST` | `{{gatewayUrl}}` | Header: command=15003 | JSON | `src/api/patient/index.ts` |
| sortTreatmentSequence | 按 treatmentsOrders 调整治疗阶段顺序。 | `POST` | `{{gatewayUrl}}` | Header: command=15005 | JSON | `src/api/patient/index.ts` |
| delTreatmentSequence | 删除某个治疗阶段。 | `POST` | `{{gatewayUrl}}` | Header: command=15004 | JSON | `src/api/patient/index.ts` |

#### 病例与治疗序列 / 新增病例

- 接口名称：`addCase`
- 接口描述：为患者新增病例记录。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15001`（CommandId.AddCase）
- 代码来源：`src/api/case/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15001`：网关分发指令，CommandId.AddCase = 15001
- Req：

```json
{
  "patientID": "{{patientId}}",
  "FDINotations": [
    "11",
    "12"
  ],
  "record": "术前检查记录",
  "tags": [],
  "diagnosis": "edentulous_jaw"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "id": "{{caseId}}",
    "patientID": "{{patientId}}",
    "FDINotations": [
      "11",
      "12"
    ],
    "record": "术前检查记录",
    "status": 1
  },
  "message": "success"
}
```

#### 病例与治疗序列 / 更新病例

- 接口名称：`updateCase`
- 接口描述：更新病例记录；当前代码同样使用 Command 15001。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15001`（CommandId.AddCase）
- 代码来源：`src/api/case/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15001`：网关分发指令，CommandId.AddCase = 15001
- Req：

```json
{
  "id": "{{caseId}}",
  "patientID": "{{patientId}}",
  "FDINotations": [
    "11"
  ],
  "record": "复诊记录",
  "status": 2,
  "tags": [],
  "diagnosis": ""
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "id": "case-id",
    "status": 2
  },
  "message": "success"
}
```

#### 病例与治疗序列 / 删除病例

- 接口名称：`deleteCase`
- 接口描述：按病例 ID 删除病例。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15002`（CommandId.DelCase）
- 代码来源：`src/api/case/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15002`：网关分发指令，CommandId.DelCase = 15002
- Req：

```json
{
  "id": "{{caseId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "code": 0,
    "message": "success"
  },
  "message": "success"
}
```

#### 病例与治疗序列 / 新增治疗阶段

- 接口名称：`treatmentSequence`
- 接口描述：添加治疗阶段或治疗方案节点。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15003`（CommandId.TreatmentSequence）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15003`：网关分发指令，CommandId.TreatmentSequence = 15003
- Req：

```json
{
  "name": "一期手术",
  "date": 1710000000000,
  "description": "治疗说明",
  "status": 1,
  "medicalRecordID": "{{caseId}}",
  "order": 1
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "id": "treatment-id"
  },
  "message": "success"
}
```

#### 病例与治疗序列 / 更新治疗阶段

- 接口名称：`changeTreatmentSequence`
- 接口描述：更新治疗阶段名称、日期、描述和状态。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15003`（CommandId.TreatmentSequence）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15003`：网关分发指令，CommandId.TreatmentSequence = 15003
- Req：

```json
{
  "id": "{{treatmentId}}",
  "name": "一期手术",
  "date": 1710000000000,
  "description": "更新说明",
  "status": 1,
  "medicalRecordID": "{{caseId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 病例与治疗序列 / 治疗阶段排序

- 接口名称：`sortTreatmentSequence`
- 接口描述：按 treatmentsOrders 调整治疗阶段顺序。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15005`（CommandId.sortTreatmentSequence）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15005`：网关分发指令，CommandId.sortTreatmentSequence = 15005
- Req：

```json
{
  "medicalRecordID": "{{caseId}}",
  "treatmentsOrders": [
    "{{treatmentId}}"
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 病例与治疗序列 / 删除治疗阶段

- 接口名称：`delTreatmentSequence`
- 接口描述：删除某个治疗阶段。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`15004`（CommandId.DelTreatmentSequence）
- 代码来源：`src/api/patient/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 15004`：网关分发指令，CommandId.DelTreatmentSequence = 15004
- Req：

```json
{
  "medicalRecordID": "{{caseId}}",
  "id": "{{treatmentId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 手术设计

说明：设计列表、创建、修改、详情、开始和结束手术。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| querySurgicalDesign | 按患者姓名、设计状态、审批状态分页查询设计列表。 | `POST` | `{{gatewayUrl}}` | Header: command=14001 | JSON | `src/api/design/index.ts` |
| addDesign | 基于病例创建手术设计。 | `POST` | `{{gatewayUrl}}` | Header: command=14002 | JSON | `src/api/design/index.ts` |
| addDesignV2 | 当前实现与 addDesign 相同，保留为调用入口。 | `POST` | `{{gatewayUrl}}` | Header: command=14002 | JSON | `src/api/design/index.ts` |
| changeDesign | 保存设计内容、缩略图、模型文件和版本信息。 | `POST` | `{{gatewayUrl}}` | Header: command=14003 | JSON | `src/api/design/index.ts` |
| navChangeDesign | 导航页保存设计内容，使用独立 Command。 | `POST` | `{{gatewayUrl}}` | Header: command=14009 | JSON | `src/api/design/index.ts` |
| completeDesign | 提交设计内容并标记设计完成。 | `POST` | `{{gatewayUrl}}` | Header: command=14004 | JSON | `src/api/design/index.ts` |
| queryDesignDetail | 按 SurgicalDesignID 获取设计详情、患者信息、病例信息和模型文件信息。 | `POST` | `{{gatewayUrl}}` | Header: command=14005 | JSON | `src/api/design/index.ts` |
| startSurgical | 将设计进入手术中状态并返回设计详情。 | `POST` | `{{gatewayUrl}}` | Header: command=14006 | JSON | `src/api/design/index.ts` |
| finishSurgical | 提交手术完成信息和偏差信息。 | `POST` | `{{gatewayUrl}}` | Header: command=14007 | JSON | `src/api/design/index.ts` |
| getSetting | 获取帮助课程、钻针配置和功能配置。 | `GET` | `{{baseUrl}}/settings` | 无 | JSON | `src/api/design/index.ts` |
| delDesign | 按设计 ID 删除设计。 | `POST` | `{{gatewayUrl}}` | Header: command=14008 | JSON | `src/api/design/index.ts` |

#### 手术设计 / 查询手术设计列表

- 接口名称：`querySurgicalDesign`
- 接口描述：按患者姓名、设计状态、审批状态分页查询设计列表。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14001`（CommandId.QuerySurgicalDesignList）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14001`：网关分发指令，CommandId.QuerySurgicalDesignList = 14001
- Req：

```json
{
  "pageIndex": 1,
  "pageSize": 10,
  "name": "{{patientName}}",
  "status": 1,
  "approveStatus": 1
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "data": [],
    "pageIndex": 1,
    "pageSize": 10,
    "total": 0
  },
  "message": "success"
}
```

#### 手术设计 / 创建设计

- 接口名称：`addDesign`
- 接口描述：基于病例创建手术设计。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14002`（CommandId.AddSurgicalDesign）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14002`：网关分发指令，CommandId.AddSurgicalDesign = 14002
- Req：

```json
{
  "medicalRecordID": "{{caseId}}",
  "modelFileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "surgicalDesignID": "design-id",
    "version": 0
  },
  "message": "success"
}
```

#### 手术设计 / 创建设计 V2

- 接口名称：`addDesignV2`
- 接口描述：当前实现与 addDesign 相同，保留为调用入口。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14002`（CommandId.AddSurgicalDesign）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14002`：网关分发指令，CommandId.AddSurgicalDesign = 14002
- Req：

```json
{
  "medicalRecordID": "{{caseId}}",
  "modelFileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "surgicalDesignID": "design-id",
    "version": 0
  },
  "message": "success"
}
```

#### 手术设计 / 修改设计文件

- 接口名称：`changeDesign`
- 接口描述：保存设计内容、缩略图、模型文件和版本信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14003`（CommandId.UpdateSurgicalDesign）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14003`：网关分发指令，CommandId.UpdateSurgicalDesign = 14003
- Req：

```json
{
  "surgicalDesignID": "{{designId}}",
  "version": 0,
  "content": "{}",
  "FDINotation": [
    "11"
  ],
  "modelFileKey": "{{fileKey}}",
  "extraModelFileKeys": [],
  "thumbnail": "{{thumbnailFileKey}}",
  "images": {}
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "version": 1
  },
  "message": "success"
}
```

#### 手术设计 / 导航页修改设计文件

- 接口名称：`navChangeDesign`
- 接口描述：导航页保存设计内容，使用独立 Command。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14009`（CommandId.NavSurgicalDesign）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14009`：网关分发指令，CommandId.NavSurgicalDesign = 14009
- Req：

```json
{
  "surgicalDesignID": "{{designId}}",
  "version": 0,
  "content": "{}",
  "FDINotation": [
    "11"
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "version": 1
  },
  "message": "success"
}
```

#### 手术设计 / 完成手术设计

- 接口名称：`completeDesign`
- 接口描述：提交设计内容并标记设计完成。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14004`（CommandId.CompleteSurgicalDesign）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14004`：网关分发指令，CommandId.CompleteSurgicalDesign = 14004
- Req：

```json
{
  "surgicalDesignID": "{{designId}}",
  "version": 1,
  "content": "{}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 手术设计 / 查询设计详情

- 接口名称：`queryDesignDetail`
- 接口描述：按 SurgicalDesignID 获取设计详情、患者信息、病例信息和模型文件信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14005`（CommandId.QuerySurgicalDesignDetail）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14005`：网关分发指令，CommandId.QuerySurgicalDesignDetail = 14005
- Req：

```json
{
  "SurgicalDesignID": "{{designId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "surgicalDesignDetail": {
      "ID": "design-id",
      "Version": 0,
      "Status": 1
    },
    "patientInfo": {
      "id": "patient-id",
      "name": "张三"
    },
    "medicalRecordInfo": {
      "id": "case-id"
    },
    "modelFileKey": "file-key",
    "extraModelFileKeys": [],
    "token": "download-token",
    "files": [],
    "jawType": "upper"
  },
  "message": "success"
}
```

#### 手术设计 / 开始手术

- 接口名称：`startSurgical`
- 接口描述：将设计进入手术中状态并返回设计详情。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14006`（CommandId.StartSurgical）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14006`：网关分发指令，CommandId.StartSurgical = 14006
- Req：

```json
{
  "surgicalDesignID": "{{designId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "surgicalDesignDetail": {
      "ID": "design-id",
      "Status": 3
    }
  },
  "message": "success"
}
```

#### 手术设计 / 完成手术

- 接口名称：`finishSurgical`
- 接口描述：提交手术完成信息和偏差信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14007`（CommandId.FinishSurgical）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14007`：网关分发指令，CommandId.FinishSurgical = 14007
- Req：

```json
{
  "SurgicalDesignID": "{{designId}}",
  "SurgicalInfo": {
    "registration": {
      "handpieces": null,
      "jaw": null
    },
    "navigation": {
      "horizontalDeviationMin": null,
      "depthDeviationMin": null,
      "axialDeviationMin": null
    }
  }
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "content": "{}",
    "status": 4,
    "ApproveStatus": 1,
    "ModelFile": {}
  },
  "message": "success"
}
```

#### 手术设计 / 获取系统设置

- 接口名称：`getSetting`
- 接口描述：获取帮助课程、钻针配置和功能配置。
- 请求地址：`{{baseUrl}}/settings`
- 请求方式：`GET`
- 代码来源：`src/api/design/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "Courses": [],
    "Drills": [],
    "FeatureConfig": {}
  },
  "message": "success"
}
```

#### 手术设计 / 删除手术设计

- 接口名称：`delDesign`
- 接口描述：按设计 ID 删除设计。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`14008`（CommandId.DeleteSurgical）
- 代码来源：`src/api/design/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 14008`：网关分发指令，CommandId.DeleteSurgical = 14008
- Req：

```json
{
  "id": "{{designId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "code": 0,
    "message": "success"
  },
  "message": "success"
}
```

### 文件管理

说明：文件分片上传、单文件上传、上传完成通知和文件描述查询。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| startFileUpload | 初始化分片上传，可选择前端直传 OSS/COS。 | `POST` | `{{gatewayUrl}}` | Header: command=11001 | JSON | `src/api/file/index.ts` |
| uploadFileChunk | 后端中转上传单个分片，multipart/form-data。 | `POST` | `{{baseUrl}}/upload_part` | partID, content, fileKey | JSON | `src/api/file/index.ts` |
| notifyFileChunkUploadResult | 前端直传 OSS/COS 后通知后端单个分片结果。 | `POST` | `{{gatewayUrl}}` | Header: command=11003 | JSON | `src/api/file/index.ts` |
| finishFileUpload | 通知后端所有分片已上传完成。 | `POST` | `{{gatewayUrl}}` | Header: command=11002 | JSON | `src/api/file/index.ts` |
| uploadSingleFile | 使用 multipart/form-data 上传单个文件。 | `POST` | `{{baseUrl}}/upload` | fileName, fileSize, entryPoint, md5, file | JSON | `src/api/file/index.ts` |
| searchFileDescription | 按 fileKeys 查询文件下载和分片描述。 | `POST` | `{{gatewayUrl}}` | Header: command=11004 | JSON | `src/api/file/index.ts` |

#### 文件管理 / 开始分片上传

- 接口名称：`startFileUpload`
- 接口描述：初始化分片上传，可选择前端直传 OSS/COS。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`11001`（CommandId.StartFileChunkUpload）
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 11001`：网关分发指令，CommandId.StartFileChunkUpload = 11001
- Req：

```json
{
  "entryPoint": 1,
  "fileName": "model.stl",
  "fileSize": 1024,
  "md5": "file-md5",
  "frontendOssUpload": true,
  "partsInfo": [
    {
      "partID": 1,
      "partMD5": "part-md5",
      "partSize": 1024
    }
  ],
  "extra": {
    "files": [
      {
        "filename": "model.stl",
        "offset": 0,
        "length": 1024
      }
    ],
    "compressVersion": 0,
    "cryptoVersion": 0
  },
  "parentKey": "parent-file-key"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "fileKey": "file-key",
    "frontendOssUploadPartsInfo": [
      {
        "partID": 1,
        "fileKey": "oss-key"
      }
    ],
    "ossAuthInfo": {
      "accessKey": "access-key",
      "accessSecret": "access-secret",
      "securityToken": "security-token",
      "bucketName": "bucket",
      "endpoint": "endpoint",
      "provider": 1,
      "region": "region"
    }
  },
  "message": "success"
}
```

#### 文件管理 / 上传分片

- 接口名称：`uploadFileChunk`
- 接口描述：后端中转上传单个分片，multipart/form-data。
- 请求地址：`{{baseUrl}}/upload_part`
- 请求方式：`POST`
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: multipart/form-data`：由 FormData 生成
- Req：

```json
{
  "partID": 1,
  "content": "<File>",
  "fileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 文件管理 / 通知分片上传结果

- 接口名称：`notifyFileChunkUploadResult`
- 接口描述：前端直传 OSS/COS 后通知后端单个分片结果。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`11003`（CommandId.NotifyFileChunkUploadResult）
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 11003`：网关分发指令，CommandId.NotifyFileChunkUploadResult = 11003
- Req：

```json
{
  "fileKey": "{{fileKey}}",
  "partID": 1,
  "cryptoKey": "",
  "cryptoAlgo": 0
}
```
- Res：

```json
{
  "code": 0,
  "data": "ok",
  "message": "success"
}
```

#### 文件管理 / 完成分片上传

- 接口名称：`finishFileUpload`
- 接口描述：通知后端所有分片已上传完成。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`11002`（CommandId.FinishFileChunkUpload）
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 11002`：网关分发指令，CommandId.FinishFileChunkUpload = 11002
- Req：

```json
{
  "fileKey": "{{fileKey}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 文件管理 / 上传单文件

- 接口名称：`uploadSingleFile`
- 接口描述：使用 multipart/form-data 上传单个文件。
- 请求地址：`{{baseUrl}}/upload`
- 请求方式：`POST`
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: multipart/form-data`：由 FormData 生成
- Req：

```json
{
  "fileName": "thumbnail.png",
  "fileSize": 1024,
  "entryPoint": 2,
  "md5": "md5",
  "file": "<File>"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 文件管理 / 查询文件描述

- 接口名称：`searchFileDescription`
- 接口描述：按 fileKeys 查询文件下载和分片描述。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`11004`（CommandId.SearchFileDescription）
- 代码来源：`src/api/file/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 11004`：网关分发指令，CommandId.SearchFileDescription = 11004
- Req：

```json
{
  "fileKeys": [
    "{{fileKey}}"
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "files": []
  },
  "message": "success"
}
```

### 控制节点

说明：本机文件、设备关机重启、版本、导出、录屏和升级。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getDirTree | 按路径和后缀过滤查询控制节点目录树。 | `POST` | `{{controlNodeBaseUrl}}/get_dir_tree` | path, fileFilter | JSON | `src/api/controlNode/index.ts` |
| downloadLocalFile | 从控制节点下载本地文件，返回 Blob。 | `POST` | `{{controlNodeBaseUrl}}/download_local_file` | filePath | <Blob> | `src/api/controlNode/index.ts` |
| downloadLocalFileWithProgress | 同下载本地文件，前端额外监听下载进度。 | `POST` | `{{controlNodeBaseUrl}}/download_local_file` | filePath | <Blob> | `src/api/controlNode/index.ts` |
| shutDownApi | 关闭控制节点设备。 | `POST` | `{{controlNodeBaseUrl}}/shutdown` | 无 | JSON | `src/api/controlNode/index.ts` |
| rebootApi | 重启控制节点设备。 | `POST` | `{{controlNodeBaseUrl}}/reboot` | 无 | JSON | `src/api/controlNode/index.ts` |
| getCurrentWifi | 获取当前连接 Wi-Fi、密码和控制节点 IP。 | `GET` | `{{controlNodeBaseUrl}}/wifi_info` | 无 | JSON | `src/api/controlNode/index.ts` |
| getControlNodeHealthCheck | 控制节点 ping 检查，返回 hwid。 | `GET` | `{{controlNodeBaseUrl}}/ping` | 无 | JSON | `src/api/controlNode/index.ts` |
| exportFileToMobileDrive | multipart/form-data 上传并写入指定路径。 | `POST` | `{{controlNodeBaseUrl}}/put_caldata` | fileName, file, path | JSON | `src/api/controlNode/index.ts` |
| getVersionInfo | 获取当前版本、下一版本和升级开关。 | `GET` | `{{controlNodeBaseUrl}}/version` | 无 | JSON | `src/api/controlNode/index.ts` |
| getFileList | 获取设计文件、录屏文件和磁盘空间。 | `GET` | `{{controlNodeBaseUrl}}/file_list` | 无 | JSON | `src/api/controlNode/index.ts` |
| exportFile | 将本地文件导出到指定路径。 | `POST` | `{{controlNodeBaseUrl}}/export_local` | fileName, exportPath, localPath | JSON | `src/api/controlNode/index.ts` |
| getExportStatus | 按本地路径查询导出进度。 | `POST` | `{{controlNodeBaseUrl}}/export_status` | localPath | JSON | `src/api/controlNode/index.ts` |
| deleteFile | 按路径删除控制节点本地文件。 | `POST` | `{{controlNodeBaseUrl}}/delete_file` | path | JSON | `src/api/controlNode/index.ts` |
| startScreenRecord | 启动指定录屏任务。 | `POST` | `{{controlNodeBaseUrl}}/task/start` | taskName | JSON | `src/api/controlNode/index.ts` |
| stopScreenRecord | 停止指定录屏任务。 | `POST` | `{{controlNodeBaseUrl}}/task/stop` | taskName | JSON | `src/api/controlNode/index.ts` |
| getScreenRecordStatus | 查询指定录屏任务是否运行中。 | `POST` | `{{controlNodeBaseUrl}}/task/status` | taskName | JSON | `src/api/controlNode/index.ts` |
| getUpgradeStatus | 获取软件升级进度和目标版本。 | `GET` | `{{controlNodeBaseUrl}}/upgrade_status` | 无 | JSON | `src/api/controlNode/index.ts` |
| startUpgrade | 触发控制节点升级。 | `POST` | `{{controlNodeBaseUrl}}/start_upgrade` | 无 | JSON | `src/api/controlNode/index.ts` |
| setUpgrade | 开启或关闭自动升级。 | `POST` | `{{controlNodeBaseUrl}}/set_upgrade` | autoUpgrade | JSON | `src/api/controlNode/index.ts` |

#### 控制节点 / 获取目录树

- 接口名称：`getDirTree`
- 接口描述：按路径和后缀过滤查询控制节点目录树。
- 请求地址：`{{controlNodeBaseUrl}}/get_dir_tree`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "path": "/data",
  "fileFilter": [
    "stl",
    "dcm"
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "IsDir": true,
    "Name": "data",
    "Path": "/data",
    "Child": []
  },
  "message": "success"
}
```

#### 控制节点 / 下载本地文件

- 接口名称：`downloadLocalFile`
- 接口描述：从控制节点下载本地文件，返回 Blob。
- 请求地址：`{{controlNodeBaseUrl}}/download_local_file`
- 请求方式：`POST`
- 响应类型：`blob`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "filePath": "/data/model.stl"
}
```
- Res：
`<Blob>`

#### 控制节点 / 下载本地文件并上报进度

- 接口名称：`downloadLocalFileWithProgress`
- 接口描述：同下载本地文件，前端额外监听下载进度。
- 请求地址：`{{controlNodeBaseUrl}}/download_local_file`
- 请求方式：`POST`
- 响应类型：`blob`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "filePath": "/data/model.stl"
}
```
- Res：
`<Blob>`

#### 控制节点 / 关机

- 接口名称：`shutDownApi`
- 接口描述：关闭控制节点设备。
- 请求地址：`{{controlNodeBaseUrl}}/shutdown`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 重启

- 接口名称：`rebootApi`
- 接口描述：重启控制节点设备。
- 请求地址：`{{controlNodeBaseUrl}}/reboot`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 获取当前 Wi-Fi

- 接口名称：`getCurrentWifi`
- 接口描述：获取当前连接 Wi-Fi、密码和控制节点 IP。
- 请求地址：`{{controlNodeBaseUrl}}/wifi_info`
- 请求方式：`GET`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "ssid": "wifi-name",
    "password": "wifi-password",
    "ip": "192.168.0.52"
  },
  "message": "success"
}
```

#### 控制节点 / 控制节点健康检查

- 接口名称：`getControlNodeHealthCheck`
- 接口描述：控制节点 ping 检查，返回 hwid。
- 请求地址：`{{controlNodeBaseUrl}}/ping`
- 请求方式：`GET`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "hwid": "control-node-hwid"
  },
  "message": "success"
}
```

#### 控制节点 / 导出文件到移动盘

- 接口名称：`exportFileToMobileDrive`
- 接口描述：multipart/form-data 上传并写入指定路径。
- 请求地址：`{{controlNodeBaseUrl}}/put_caldata`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: multipart/form-data`：由 FormData 生成
- Req：

```json
{
  "fileName": "model.stl",
  "file": "<File>",
  "path": "/usb"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 获取版本信息

- 接口名称：`getVersionInfo`
- 接口描述：获取当前版本、下一版本和升级开关。
- 请求地址：`{{controlNodeBaseUrl}}/version`
- 请求方式：`GET`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "fullVersion": "1.0.0",
  "majorVersion": "1",
  "changeNotes": "",
  "nextVersion": "1.0.1",
  "autoUpgrade": true,
  "hwid": "control-node-hwid"
}
```

#### 控制节点 / 获取本地文件列表

- 接口名称：`getFileList`
- 接口描述：获取设计文件、录屏文件和磁盘空间。
- 请求地址：`{{controlNodeBaseUrl}}/file_list`
- 请求方式：`GET`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "design_files": [],
    "screen_files": [],
    "total_available_space": "10GB",
    "total_used_space": "1GB"
  },
  "message": "success"
}
```

#### 控制节点 / 导出本地文件

- 接口名称：`exportFile`
- 接口描述：将本地文件导出到指定路径。
- 请求地址：`{{controlNodeBaseUrl}}/export_local`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "fileName": "model.stl",
  "exportPath": "/usb",
  "localPath": "/data/model.stl"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 查询导出状态

- 接口名称：`getExportStatus`
- 接口描述：按本地路径查询导出进度。
- 请求地址：`{{controlNodeBaseUrl}}/export_status`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "localPath": "/data/model.stl"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "fileName": "model.stl",
    "progress": 50,
    "status": "running"
  },
  "message": "success"
}
```

#### 控制节点 / 删除本地文件

- 接口名称：`deleteFile`
- 接口描述：按路径删除控制节点本地文件。
- 请求地址：`{{controlNodeBaseUrl}}/delete_file`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "path": "/data/model.stl"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 开始录屏

- 接口名称：`startScreenRecord`
- 接口描述：启动指定录屏任务。
- 请求地址：`{{controlNodeBaseUrl}}/task/start`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "taskName": "screen-record"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 停止录屏

- 接口名称：`stopScreenRecord`
- 接口描述：停止指定录屏任务。
- 请求地址：`{{controlNodeBaseUrl}}/task/stop`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "taskName": "screen-record"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 查询录屏状态

- 接口名称：`getScreenRecordStatus`
- 接口描述：查询指定录屏任务是否运行中。
- 请求地址：`{{controlNodeBaseUrl}}/task/status`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "taskName": "screen-record"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "isActive": true
  },
  "message": "success"
}
```

#### 控制节点 / 获取升级状态

- 接口名称：`getUpgradeStatus`
- 接口描述：获取软件升级进度和目标版本。
- 请求地址：`{{controlNodeBaseUrl}}/upgrade_status`
- 请求方式：`GET`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "progress": 0,
    "status": 0,
    "version": "1.0.1"
  },
  "message": "success"
}
```

#### 控制节点 / 开始升级

- 接口名称：`startUpgrade`
- 接口描述：触发控制节点升级。
- 请求地址：`{{controlNodeBaseUrl}}/start_upgrade`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 控制节点 / 设置自动升级

- 接口名称：`setUpgrade`
- 接口描述：开启或关闭自动升级。
- 请求地址：`{{controlNodeBaseUrl}}/set_upgrade`
- 请求方式：`POST`
- 代码来源：`src/api/controlNode/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "autoUpgrade": true
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 网络与 Wi-Fi

说明：网络速率、Wi-Fi 列表、连接状态和热点开关。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getNetworkRealtimeRate | 查询有线/Wi-Fi/无网络状态及上下行速率。 | `GET` | `{{controlNodeBaseUrl}}/network_status` | 无 | JSON | `src/api/network/index.ts` |
| getWifiListAPI | 扫描可连接 Wi-Fi。 | `GET` | `{{controlNodeBaseUrl}}/scan_wifi` | 无 | JSON | `src/api/wifi/index.ts` |
| connectWifiAPI | 按 ssid/password 连接 Wi-Fi。 | `POST` | `{{controlNodeBaseUrl}}/connect_wifi` | ssid, password, save | JSON | `src/api/wifi/index.ts` |
| disConnectWifiAPI | 断开指定 Wi-Fi。 | `POST` | `{{controlNodeBaseUrl}}/disconnect_wifi` | ssid | JSON | `src/api/wifi/index.ts` |
| getAPListAPI | 获取控制节点热点接口列表。 | `GET` | `{{controlNodeBaseUrl}}/ap_list` | 无 | JSON | `src/api/wifi/index.ts` |
| OpenHotspotAPI | 开启指定网卡热点。 | `POST` | `{{controlNodeBaseUrl}}/open_hotspot` | iface, ssid, password, auto_start | JSON | `src/api/wifi/index.ts` |
| closeHotspotAPI | 关闭指定网卡热点。 | `POST` | `{{controlNodeBaseUrl}}/close_hotspot` | iface, auto_start | JSON | `src/api/wifi/index.ts` |

#### 网络与 Wi-Fi / 获取网络实时速率

- 接口名称：`getNetworkRealtimeRate`
- 接口描述：查询有线/Wi-Fi/无网络状态及上下行速率。
- 请求地址：`{{controlNodeBaseUrl}}/network_status`
- 请求方式：`GET`
- 代码来源：`src/api/network/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "networkType": "wifi",
    "downloadSpeed": 1024,
    "uploadSpeed": 512
  },
  "message": "success"
}
```

#### 网络与 Wi-Fi / 扫描 Wi-Fi 列表

- 接口名称：`getWifiListAPI`
- 接口描述：扫描可连接 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/scan_wifi`
- 请求方式：`GET`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": [
    {
      "key": "wifi-key",
      "ssid": "wifi-name",
      "signal": "-40",
      "security": "WPA2",
      "authRequired": true,
      "connected": false,
      "save": false
    }
  ],
  "message": "success"
}
```

#### 网络与 Wi-Fi / 连接 Wi-Fi

- 接口名称：`connectWifiAPI`
- 接口描述：按 ssid/password 连接 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/connect_wifi`
- 请求方式：`POST`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "ssid": "wifi-name",
  "password": "wifi-password",
  "save": true
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 网络与 Wi-Fi / 断开 Wi-Fi

- 接口名称：`disConnectWifiAPI`
- 接口描述：断开指定 Wi-Fi。
- 请求地址：`{{controlNodeBaseUrl}}/disconnect_wifi`
- 请求方式：`POST`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "ssid": "wifi-name"
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

#### 网络与 Wi-Fi / 获取热点列表

- 接口名称：`getAPListAPI`
- 接口描述：获取控制节点热点接口列表。
- 请求地址：`{{controlNodeBaseUrl}}/ap_list`
- 请求方式：`GET`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": [
    {
      "iface": "wlan0",
      "hotspot_active": true,
      "ssid": "tars-hotspot",
      "password": "12345678",
      "auto_start": true
    }
  ],
  "message": "success"
}
```

#### 网络与 Wi-Fi / 开启热点

- 接口名称：`OpenHotspotAPI`
- 接口描述：开启指定网卡热点。
- 请求地址：`{{controlNodeBaseUrl}}/open_hotspot`
- 请求方式：`POST`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "iface": "wlan0",
  "ssid": "tars-hotspot",
  "password": "12345678",
  "auto_start": true
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "code": 0,
    "msg": "success",
    "data": null
  },
  "message": "success"
}
```

#### 网络与 Wi-Fi / 关闭热点

- 接口名称：`closeHotspotAPI`
- 接口描述：关闭指定网卡热点。
- 请求地址：`{{controlNodeBaseUrl}}/close_hotspot`
- 请求方式：`POST`
- 代码来源：`src/api/wifi/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "iface": "wlan0",
  "auto_start": false
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 植体系统

说明：植体系统配置和收藏管理。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getImplantSystemAPI | 获取本地植体/钻针系统配置。 | `GET` | `{{controlNodeBaseUrl}}/implant_system` | 无 | JSON | `src/api/implant/index.ts` |
| getImplantFavorites | 获取当前用户收藏的植体类型。 | `POST` | `{{gatewayUrl}}` | Header: command=18004 | JSON | `src/api/implant/index.ts` |
| addImplantFavorite | 收藏指定植体类型。 | `POST` | `{{gatewayUrl}}` | Header: command=18005 | JSON | `src/api/implant/index.ts` |
| deleteImplantFavorite | 取消收藏指定植体类型。 | `POST` | `{{gatewayUrl}}` | Header: command=18006 | JSON | `src/api/implant/index.ts` |

#### 植体系统 / 获取植体系统列表

- 接口名称：`getImplantSystemAPI`
- 接口描述：获取本地植体/钻针系统配置。
- 请求地址：`{{controlNodeBaseUrl}}/implant_system`
- 请求方式：`GET`
- 代码来源：`src/api/implant/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "name": "implant-system",
      "systems": []
    }
  ],
  "message": "success"
}
```

#### 植体系统 / 获取植体收藏

- 接口名称：`getImplantFavorites`
- 接口描述：获取当前用户收藏的植体类型。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`18004`（CommandId.GetImplantFavorites）
- 代码来源：`src/api/implant/index.ts`
- 请求头：
  - `command: 18004`：网关分发指令，CommandId.GetImplantFavorites = 18004
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "favorites": [
      "implant-type"
    ]
  },
  "message": "success"
}
```

#### 植体系统 / 新增植体收藏

- 接口名称：`addImplantFavorite`
- 接口描述：收藏指定植体类型。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`18005`（CommandId.AddImplantFavorite）
- 代码来源：`src/api/implant/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 18005`：网关分发指令，CommandId.AddImplantFavorite = 18005
- Req：

```json
{
  "type": "implant-type"
}
```
- Res：

```json
{
  "code": 0,
  "data": true,
  "message": "success"
}
```

#### 植体系统 / 取消植体收藏

- 接口名称：`deleteImplantFavorite`
- 接口描述：取消收藏指定植体类型。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`18006`（CommandId.DeleteImplantFavorite）
- 代码来源：`src/api/implant/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 18006`：网关分发指令，CommandId.DeleteImplantFavorite = 18006
- Req：

```json
{
  "type": "implant-type"
}
```
- Res：

```json
{
  "code": 0,
  "data": true,
  "message": "success"
}
```

### OTP 密钥

说明：OTP secret 生成、校验、上传、查询和按设备取验证码。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| generateOtpSecret | 按 username 生成或获取当前有效 OTP secret。 | `POST` | `{{controlNodeBaseUrl}}/otp/generate_secret` | username, serverSecretVersion | JSON | `src/api/opt/index.ts` |
| verifyOtpCode | 校验 username 对应的 OTP 动态码。 | `POST` | `{{controlNodeBaseUrl}}/otp/verify` | username, otp_code | JSON | `src/api/opt/index.ts` |
| uploadUserSecret | 上传当前用户在当前设备上的 secret。 | `POST` | `{{gatewayUrl}}` | Header: command=12002 | JSON | `src/api/opt/index.ts` |
| getUserSecretMeta | 查询当前用户在指定设备上的服务端 secret 版本信息。 | `POST` | `{{gatewayUrl}}` | Header: command=12003 | JSON | `src/api/opt/index.ts` |
| listUserSecretDevices | 列出当前用户服务端已绑定设备，不返回原始 hwid。 | `POST` | `{{gatewayUrl}}` | Header: command=12004 | JSON | `src/api/opt/index.ts` |
| getUserOtpCode | 按当前用户和设备 hwid 获取对应 secret 生成的当前 OTP 动态码。 | `POST` | `{{gatewayUrl}}` | Header: command=12005 | JSON | `src/api/opt/index.ts` |

#### OTP 密钥 / 生成 OTP Secret

- 接口名称：`generateOtpSecret`
- 接口描述：按 username 生成或获取当前有效 OTP secret。
- 请求地址：`{{controlNodeBaseUrl}}/otp/generate_secret`
- 请求方式：`POST`
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "username": "{{username}}",
  "serverSecretVersion": 1
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "hwid": "control-node-hwid",
    "secret": "otp-secret",
    "otpauth_url": "otpauth://totp/...",
    "secretVersion": 1
  },
  "message": "success"
}
```

#### OTP 密钥 / 校验 OTP Code

- 接口名称：`verifyOtpCode`
- 接口描述：校验 username 对应的 OTP 动态码。
- 请求地址：`{{controlNodeBaseUrl}}/otp/verify`
- 请求方式：`POST`
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "username": "{{username}}",
  "otp_code": "{{otpCode}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "valid": true
  },
  "message": "success"
}
```

#### OTP 密钥 / 上传用户 Secret

- 接口名称：`uploadUserSecret`
- 接口描述：上传当前用户在当前设备上的 secret。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`12002`（CommandId.UploadUserSecret）
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 12002`：网关分发指令，CommandId.UploadUserSecret = 12002
- Req：

```json
{
  "secret": "{{otpSecret}}",
  "hwid": "{{hwid}}",
  "secretVersion": 1
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "hwid": "control-node-hwid",
    "hwidHash": "hwid-hash",
    "secretVersion": 1
  },
  "message": "success"
}
```

#### OTP 密钥 / 查询用户 Secret 元信息

- 接口名称：`getUserSecretMeta`
- 接口描述：查询当前用户在指定设备上的服务端 secret 版本信息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`12003`（CommandId.GetUserSecretMeta）
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 12003`：网关分发指令，CommandId.GetUserSecretMeta = 12003
- Req：

```json
{
  "hwid": "{{hwid}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "hwid": "control-node-hwid",
    "hwidHash": "hwid-hash",
    "exists": true,
    "secretVersion": 1
  },
  "message": "success"
}
```

#### OTP 密钥 / 列出 Secret 绑定设备

- 接口名称：`listUserSecretDevices`
- 接口描述：列出当前用户服务端已绑定设备，不返回原始 hwid。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`12004`（CommandId.ListUserSecretDevices）
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `command: 12004`：网关分发指令，CommandId.ListUserSecretDevices = 12004
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "devices": []
  },
  "message": "success"
}
```

#### OTP 密钥 / 获取用户 OTP Code

- 接口名称：`getUserOtpCode`
- 接口描述：按当前用户和设备 hwid 获取对应 secret 生成的当前 OTP 动态码。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`12005`（CommandId.GetUserOTPCode）
- 代码来源：`src/api/opt/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 12005`：网关分发指令，CommandId.GetUserOTPCode = 12005
- Req：

```json
{
  "hwid": "{{hwid}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "username": "admin",
    "hwid": "control-node-hwid",
    "hwidHash": "hwid-hash",
    "exists": true,
    "otpCode": "123456",
    "secretVersion": 1
  },
  "message": "success"
}
```

### AI 分割

说明：启动 AI 分割任务、查询任务状态和牙尖异常分析。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| starAiPartition | 启动指定 taskType 的 AI 分割任务。 | `POST` | `{{gatewayUrl}}` | Header: command=17001 | JSON | `src/api/partition/index.ts` |
| getAiPartitionStatus | 查询 AI 分割任务状态和结果数据。 | `POST` | `{{gatewayUrl}}` | Header: command=17002 | JSON | `src/api/partition/index.ts` |
| getExpByToothCusp | 获取牙尖点异常分析任务。 | `POST` | `{{gatewayUrl}}` | Header: command=17003 | JSON | `src/api/partition/index.ts` |

#### AI 分割 / 启动 AI 分割

- 接口名称：`starAiPartition`
- 接口描述：启动指定 taskType 的 AI 分割任务。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`17001`（CommandId.StarAiPartion）
- 代码来源：`src/api/partition/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 17001`：网关分发指令，CommandId.StarAiPartion = 17001
- Req：

```json
{
  "surgicalDesignID": "{{designId}}",
  "taskType": "dentalsegment",
  "nextTaskType": "dentalarch"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "taskID": "task-id"
  },
  "message": "success"
}
```

#### AI 分割 / 查询 AI 分割状态

- 接口名称：`getAiPartitionStatus`
- 接口描述：查询 AI 分割任务状态和结果数据。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`17002`（CommandId.QueryAiPartitionResult）
- 代码来源：`src/api/partition/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 17002`：网关分发指令，CommandId.QueryAiPartitionResult = 17002
- Req：

```json
{
  "taskID": "{{taskId}}",
  "parameters": {}
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "taskID": "task-id",
    "status": "COMPLETED",
    "data": "result-file-key"
  },
  "message": "success"
}
```

#### AI 分割 / 牙尖异常分析

- 接口名称：`getExpByToothCusp`
- 接口描述：获取牙尖点异常分析任务。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`17003`（CommandId.ExpByToothCusp）
- 代码来源：`src/api/partition/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 17003`：网关分发指令，CommandId.ExpByToothCusp = 17003
- Req：

```json
{
  "surgicalDesignID": "{{designId}}",
  "taskType": "dentalcusp"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "taskID": "task-id"
  },
  "message": "success"
}
```

### 积分

说明：积分总览、明细和提醒列表。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getPointSummary | 获取个人、租户、手术和冻结积分。 | `POST` | `{{gatewayUrl}}` | Header: command=20002 | JSON | `src/api/points/index.ts` |
| getPointDetails | 分页查询积分明细，可按状态过滤。 | `POST` | `{{gatewayUrl}}` | Header: command=20003 | JSON | `src/api/points/index.ts` |
| getPointRemind | 分页查询积分提醒消息。 | `POST` | `{{gatewayUrl}}` | Header: command=20004 | JSON | `src/api/points/index.ts` |

#### 积分 / 获取积分总览

- 接口名称：`getPointSummary`
- 接口描述：获取个人、租户、手术和冻结积分。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`20002`（CommandId.GetPointSummary）
- 代码来源：`src/api/points/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 20002`：网关分发指令，CommandId.GetPointSummary = 20002
- Req：

```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "vipLevel": 1,
    "userName": "管理员",
    "tenantName": "诊所",
    "personalPoint": 100,
    "personalSurgeryPoint": 20,
    "tenantPoint": 1000,
    "freezePoint": 0
  },
  "message": "success"
}
```

#### 积分 / 获取积分明细

- 接口名称：`getPointDetails`
- 接口描述：分页查询积分明细，可按状态过滤。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`20003`（CommandId.GetPointDetails）
- 代码来源：`src/api/points/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 20003`：网关分发指令，CommandId.GetPointDetails = 20003
- Req：

```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}",
  "filterStatus": 1,
  "page": 1,
  "pageSize": 10
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "data": [],
    "total": 0,
    "page": 1,
    "pageSize": 10
  },
  "message": "success"
}
```

#### 积分 / 获取积分提醒

- 接口名称：`getPointRemind`
- 接口描述：分页查询积分提醒消息。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`20004`（CommandId.GetPointRemind）
- 代码来源：`src/api/points/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 20004`：网关分发指令，CommandId.GetPointRemind = 20004
- Req：

```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}",
  "page": 1,
  "pageSize": 10
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "data": [],
    "total": 0,
    "page": 1,
    "pageSize": 10
  },
  "message": "success"
}
```

### 系统消息与设备

说明：系统消息列表、已读、删除和设备列表。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| searchMessage | 分页查询系统消息、未读数和总数。 | `POST` | `{{gatewayUrl}}` | Header: command=19001 | JSON | `src/api/systemMessage/index.ts` |
| deleteMessage | 按消息 ID 删除；id 可选时由后端决定批量/全部行为。 | `POST` | `{{gatewayUrl}}` | Header: command=19003 | JSON | `src/api/systemMessage/index.ts` |
| readMessage | 按消息 ID 标记已读；id 可选时由后端决定批量/全部行为。 | `POST` | `{{gatewayUrl}}` | Header: command=19002 | JSON | `src/api/systemMessage/index.ts` |
| getDeviceList | 获取已发现或已登记设备。 | `POST` | `{{gatewayUrl}}` | Header: command=20001 | JSON | `src/api/systemMessage/index.ts` |

#### 系统消息与设备 / 查询系统消息

- 接口名称：`searchMessage`
- 接口描述：分页查询系统消息、未读数和总数。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`19001`（CommandId.getMessage）
- 代码来源：`src/api/systemMessage/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 19001`：网关分发指令，CommandId.getMessage = 19001
- Req：

```json
{
  "pageSize": 10,
  "current": 1
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "systemMessageList": [],
    "total": 0,
    "unread": 0,
    "pageIndex": 1
  },
  "message": "success"
}
```

#### 系统消息与设备 / 删除系统消息

- 接口名称：`deleteMessage`
- 接口描述：按消息 ID 删除；id 可选时由后端决定批量/全部行为。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`19003`（CommandId.deleteMessage）
- 代码来源：`src/api/systemMessage/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 19003`：网关分发指令，CommandId.deleteMessage = 19003
- Req：

```json
{
  "id": "{{messageId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 系统消息与设备 / 标记系统消息已读

- 接口名称：`readMessage`
- 接口描述：按消息 ID 标记已读；id 可选时由后端决定批量/全部行为。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`19002`（CommandId.readMessage）
- 代码来源：`src/api/systemMessage/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 19002`：网关分发指令，CommandId.readMessage = 19002
- Req：

```json
{
  "id": "{{messageId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### 系统消息与设备 / 获取设备列表

- 接口名称：`getDeviceList`
- 接口描述：获取已发现或已登记设备。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`20001`（CommandId.GetDeviceList）
- 代码来源：`src/api/systemMessage/index.ts`
- 请求头：
  - `command: 20001`：网关分发指令，CommandId.GetDeviceList = 20001
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "devices": []
  },
  "message": "success"
}
```

### 用户配置

说明：用户级配置读取和保存。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getUserConfig | 按 user_id 读取网关侧用户配置。 | `POST` | `{{gatewayUrl}}` | Header: command=18002 | JSON | `src/api/user/index.ts` |
| saveUserConfig | 保存用户配置键值列表。 | `POST` | `{{gatewayUrl}}` | Header: command=18003 | JSON | `src/api/user/index.ts` |

#### 用户配置 / 读取用户配置

- 接口名称：`getUserConfig`
- 接口描述：按 user_id 读取网关侧用户配置。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`18002`（CommandId.getUserConfig）
- 代码来源：`src/api/user/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 18002`：网关分发指令，CommandId.getUserConfig = 18002
- Req：

```json
{
  "user_id": "{{userId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "configs": {
      "key": {
        "value": 1
      }
    }
  },
  "message": "success"
}
```

#### 用户配置 / 保存用户配置

- 接口名称：`saveUserConfig`
- 接口描述：保存用户配置键值列表。
- 请求地址：`{{gatewayUrl}}`
- 请求方式：`POST`
- 网关 command：`18003`（CommandId.saveUserConfig）
- 代码来源：`src/api/user/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
  - `command: 18003`：网关分发指令，CommandId.saveUserConfig = 18003
- Req：

```json
{
  "user_id": "{{userId}}",
  "configs": [
    {
      "key": "theme",
      "value": "dark"
    }
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### ROS 与导航

说明：ROS HTTP 接口、模型文件同步、JPEG 流、灯光控制和眼镜升级。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| getMarkersList | 获取当前和可选 Marker 序列号列表。 | `GET` | `{{rosBaseUrl}}/get_markers_list` | 无 | JSON | `src/api/ros/index.ts` |
| setMarker | 设置某类 Marker 的序列号。 | `POST` | `{{rosBaseUrl}}/set_marker` | markerType, markerSerialNumber | JSON | `src/api/ros/index.ts` |
| getUserConfigRos | 从 ROS 节点读取用户配置。 | `GET` | `{{rosBaseUrl}}/get_user_config?user_id={{userId}}` | user_id | JSON | `src/api/ros/index.ts` |
| saveUserConfigRos | 向 ROS 节点保存用户配置。 | `POST` | `{{rosBaseUrl}}/save_user_config` | user_id, configs | JSON | `src/api/ros/index.ts` |
| upLoadFile | multipart/form-data 上传多个模型文件，query id 为设计 ID。 | `POST` | `{{rosBaseUrl}}/upload_model_file?id={{designId}}` | files, id | JSON | `src/api/ros/index.ts` |
| setModelFile | multipart/form-data 增量上传模型文件。 | `POST` | `{{rosBaseUrl}}/set_model_file` | files | JSON | `src/api/ros/index.ts` |
| downLoadFile | 按设计 ID 和文件名下载模型文件，返回 Blob。 | `GET` | `{{rosBaseUrl}}/download_model_file?id={{designId}}&filename={{filename}}` | id, filename | <Blob> | `src/api/ros/index.ts` |
| checkMrVersion | 检查连接眼镜版本兼容性。 | `GET` | `{{rosBaseUrl}}/check_mr_version` | 无 | JSON | `src/api/ros/index.ts` |
| upgradeMrVersion | 按眼镜 IP 触发升级。 | `POST` | `{{rosBaseUrl}}/update_mr_version` | ip | JSON | `src/api/ros/index.ts` |
| jpegStreamStop | 按 stream_id 停止 JPEG 图片流。 | `GET` | `{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}` | stream_id | JSON | `src/api/ros/index.ts` |
| setDesignContent | 向 ROS 节点设置当前手术设计 content。 | `POST` | `{{rosBaseUrl}}/set_design_content` | content | JSON | `src/api/ros/index.ts` |
| closeLampApi | 关闭无影灯。 | `GET` | `{{rosBaseUrl}}/close_lamp` | 无 | JSON | `src/api/ros/index.ts` |
| getTowerStatus | 按设备 IP 动态创建 ROS HTTP client 后获取塔台状态。 | `GET` | `{{rosBaseUrl}}/tower/status` | 无 | JSON | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |
| getJpegStreamStatus | 查询 JPEG 流状态。 | `GET` | `{{rosBaseUrl}}/jpeg_stream/status` | 无 | JSON | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |
| stopJpegStream | 使用动态设备 IP 停止 JPEG 流。 | `GET` | `{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}` | stream_id, ip | JSON | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |

#### ROS 与导航 / 获取 Marker 列表

- 接口名称：`getMarkersList`
- 接口描述：获取当前和可选 Marker 序列号列表。
- 请求地址：`{{rosBaseUrl}}/get_markers_list`
- 请求方式：`GET`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "currentBoardMarker": "board-1",
  "currentJawMarker": "jaw-1",
  "currentHandpieceMarker": "handpiece-1",
  "currentPlaceMarker": "place-1",
  "currentCutMarker": "cut-1",
  "boardMarkerList": [],
  "jawMarkerList": [],
  "handpieceMarkerList": [],
  "placeMarkerList": [],
  "cutMarkerList": []
}
```

#### ROS 与导航 / 设置 Marker

- 接口名称：`setMarker`
- 接口描述：设置某类 Marker 的序列号。
- 请求地址：`{{rosBaseUrl}}/set_marker`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "markerType": "boardMarker",
  "markerSerialNumber": "marker-sn"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / ROS 读取用户配置

- 接口名称：`getUserConfigRos`
- 接口描述：从 ROS 节点读取用户配置。
- 请求地址：`{{rosBaseUrl}}/get_user_config?user_id={{userId}}`
- 请求方式：`GET`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：

```json
{
  "user_id": "{{userId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {
    "configs": {
      "key": {
        "value": 1
      }
    }
  },
  "message": "success"
}
```

#### ROS 与导航 / ROS 保存用户配置

- 接口名称：`saveUserConfigRos`
- 接口描述：向 ROS 节点保存用户配置。
- 请求地址：`{{rosBaseUrl}}/save_user_config`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "user_id": "{{userId}}",
  "configs": [
    {
      "key": "key",
      "value": "1"
    }
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 上传导航模型文件

- 接口名称：`upLoadFile`
- 接口描述：multipart/form-data 上传多个模型文件，query id 为设计 ID。
- 请求地址：`{{rosBaseUrl}}/upload_model_file?id={{designId}}`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: multipart/form-data`：由 FormData 生成
- Req：

```json
{
  "files": [
    "<File>"
  ],
  "id": "{{designId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 设置模型文件

- 接口名称：`setModelFile`
- 接口描述：multipart/form-data 增量上传模型文件。
- 请求地址：`{{rosBaseUrl}}/set_model_file`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: multipart/form-data`：由 FormData 生成
- Req：

```json
{
  "files": [
    "<File>"
  ]
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 下载导航模型文件

- 接口名称：`downLoadFile`
- 接口描述：按设计 ID 和文件名下载模型文件，返回 Blob。
- 请求地址：`{{rosBaseUrl}}/download_model_file?id={{designId}}&filename={{filename}}`
- 请求方式：`GET`
- 响应类型：`blob`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：

```json
{
  "id": "{{designId}}",
  "filename": "{{filename}}"
}
```
- Res：
`<Blob>`

#### ROS 与导航 / 检查 MR 版本

- 接口名称：`checkMrVersion`
- 接口描述：检查连接眼镜版本兼容性。
- 请求地址：`{{rosBaseUrl}}/check_mr_version`
- 请求方式：`GET`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {
    "minCompatibleVersion": "1.0.0",
    "connectMRs": []
  },
  "message": "success"
}
```

#### ROS 与导航 / 升级 MR 版本

- 接口名称：`upgradeMrVersion`
- 接口描述：按眼镜 IP 触发升级。
- 请求地址：`{{rosBaseUrl}}/update_mr_version`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "ip": "192.168.0.60"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 停止 JPEG 流

- 接口名称：`jpegStreamStop`
- 接口描述：按 stream_id 停止 JPEG 图片流。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}`
- 请求方式：`GET`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：

```json
{
  "stream_id": "{{streamId}}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 设置设计 Content

- 接口名称：`setDesignContent`
- 接口描述：向 ROS 节点设置当前手术设计 content。
- 请求地址：`{{rosBaseUrl}}/set_design_content`
- 请求方式：`POST`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "content": "{}"
}
```
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 关闭无影灯

- 接口名称：`closeLampApi`
- 接口描述：关闭无影灯。
- 请求地址：`{{rosBaseUrl}}/close_lamp`
- 请求方式：`GET`
- 代码来源：`src/api/ros/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

#### ROS 与导航 / 获取塔台状态

- 接口名称：`getTowerStatus`
- 接口描述：按设备 IP 动态创建 ROS HTTP client 后获取塔台状态。
- 请求地址：`{{rosBaseUrl}}/tower/status`
- 请求方式：`GET`
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{}
```

#### ROS 与导航 / 获取 JPEG 流状态

- 接口名称：`getJpegStreamStatus`
- 接口描述：查询 JPEG 流状态。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/status`
- 请求方式：`GET`
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 请求头：
- Req：
`无`
- Res：

```json
{}
```

#### ROS 与导航 / 按设备 IP 停止 JPEG 流

- 接口名称：`stopJpegStream`
- 接口描述：使用动态设备 IP 停止 JPEG 流。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}`
- 请求方式：`GET`
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 请求头：
- Req：

```json
{
  "stream_id": "{{streamId}}",
  "ip": "192.168.0.52"
}
```
- Res：

```json
{}
```

### 聊天与助手

说明：聊天补全流式接口和全局助手 SSE。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| addChat | 调用聊天节点 /api/v3/bots/chat/completions，返回 stream。 | `POST` | `{{chatBaseUrl}}/bots/chat/completions` | model, messages, stream, patients_info, machine_info, cur_patients_info | stream | `src/api/chat/index.ts` |
| fetchEventSourceChatCompletions | 全局助手使用 fetchEventSource 请求 /tars/v1/chat_completions，响应 text/event-stream。 | `POST` | `{{baseUrl}}/chat_completions` | model, stream, metadata, messages | data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\n\ndata: [DONE] | `src/layout/GlobalWin/index.tsx` |

#### 聊天与助手 / 聊天补全流

- 接口名称：`addChat`
- 接口描述：调用聊天节点 /api/v3/bots/chat/completions，返回 stream。
- 请求地址：`{{chatBaseUrl}}/bots/chat/completions`
- 请求方式：`POST`
- 响应类型：`stream`
- 代码来源：`src/api/chat/index.ts`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "model": "test",
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true,
  "patients_info": [],
  "machine_info": {
    "lamp_brightness": 50
  },
  "cur_patients_info": null
}
```
- Res：

```json
{
  "choices": [
    {
      "delta": {
        "content": "你好"
      },
      "finish_reason": null
    }
  ]
}
```

#### 聊天与助手 / 全局助手 SSE

- 接口名称：`fetchEventSourceChatCompletions`
- 接口描述：全局助手使用 fetchEventSource 请求 /tars/v1/chat_completions，响应 text/event-stream。
- 请求地址：`{{baseUrl}}/chat_completions`
- 请求方式：`POST`
- 响应类型：`text/event-stream`
- 代码来源：`src/layout/GlobalWin/index.tsx`
- 请求头：
  - `Content-Type: application/json`：JSON 请求体
- Req：

```json
{
  "model": "test",
  "stream": true,
  "metadata": {
    "patients_info": [],
    "cur_patient_info": null,
    "machine_info": {
      "lamp_brightness": 50
    },
    "is_audio": true
  },
  "messages": [
    {
      "role": "user",
      "content": "调亮无影灯"
    }
  ]
}
```
- Res：
`data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\n\ndata: [DONE]`

### 外部资源与连接

说明：预签名资源下载、网络探测、ROS WebSocket 和静态运行时资源。

| 接口名称 | 接口描述 | 请求方式 | 请求地址 | 关键参数 | 响应 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| downloadChunks | 从后端返回的 Part.DownloadURL 直接下载分片；URL 通常为 OSS/COS 预签名地址。 | `GET` | `https://example-cdn.invalid/path/to/part` | DownloadURL, CryptoKey | <Blob> | `src/utils/chunkDownload.ts` |
| loopWatchInternet | 默认探测公网 ping 地址判断网络连通性。 | `GET` | `{{internetPingUrl}}` | 无 | HTTP 2xx/非 2xx | `src/layout/AdminLayout/components/SettingModal/components/Setting/hooks/useIntervalWifi.ts` |
| ROSClient | 通过 roslib 连接 ROS bridge，默认 ws://localhost:9090，可由界面输入 ws://{ip}:9090。 | `WEBSOCKET` | `ws://localhost:9090` | url | WebSocket messages | `src/services/tower-ros/client.ts` |
| fetchGdcmconvJs | 压缩 worker 加载公共静态脚本 /cs/gdcmconv.js。 | `GET` | `{{frontendBaseUrl}}/cs/gdcmconv.js` | 无 | JavaScript runtime | `src/pages/SurgicalDesign/components/UploadModelFileFromLocalExploreModal/pipeline/worker/compressWorkerLogic.ts` |

#### 外部资源与连接 / 预签名分片下载

- 接口名称：`downloadChunks`
- 接口描述：从后端返回的 Part.DownloadURL 直接下载分片；URL 通常为 OSS/COS 预签名地址。
- 请求地址：`https://example-cdn.invalid/path/to/part`
- 请求方式：`GET`
- 代码来源：`src/utils/chunkDownload.ts`
- 请求头：
- Req：

```json
{
  "DownloadURL": "https://example-cdn.invalid/path/to/part",
  "CryptoKey": "optional-key"
}
```
- Res：
`<Blob>`

#### 外部资源与连接 / 网络在线探测

- 接口名称：`loopWatchInternet`
- 接口描述：默认探测公网 ping 地址判断网络连通性。
- 请求地址：`{{internetPingUrl}}`
- 请求方式：`GET`
- 代码来源：`src/layout/AdminLayout/components/SettingModal/components/Setting/hooks/useIntervalWifi.ts`
- 请求头：
- Req：
`无`
- Res：
`HTTP 2xx/非 2xx`

#### 外部资源与连接 / ROS Bridge WebSocket

- 接口名称：`ROSClient`
- 接口描述：通过 roslib 连接 ROS bridge，默认 ws://localhost:9090，可由界面输入 ws://{ip}:9090。
- 请求地址：`ws://localhost:9090`
- 请求方式：`WEBSOCKET`
- 代码来源：`src/services/tower-ros/client.ts`
- 请求头：
- Req：

```json
{
  "url": "ws://192.168.0.52:9090"
}
```
- Res：
`WebSocket messages`

#### 外部资源与连接 / GDCM WASM 脚本

- 接口名称：`fetchGdcmconvJs`
- 接口描述：压缩 worker 加载公共静态脚本 /cs/gdcmconv.js。
- 请求地址：`{{frontendBaseUrl}}/cs/gdcmconv.js`
- 请求方式：`GET`
- 代码来源：`src/pages/SurgicalDesign/components/UploadModelFileFromLocalExploreModal/pipeline/worker/compressWorkerLogic.ts`
- 请求头：
- Req：
`无`
- Res：
`JavaScript runtime`

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
