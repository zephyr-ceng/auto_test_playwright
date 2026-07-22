# OTP 密钥

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

OTP secret 生成、校验、上传、查询和按设备取验证码。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `generateOtpSecret` | `POST` | `{{controlNodeBaseUrl}}/otp/generate_secret` | - | 是 | `src/api/opt/index.ts` |
| `verifyOtpCode` | `POST` | `{{controlNodeBaseUrl}}/otp/verify` | - | 是 | `src/api/opt/index.ts` |
| `uploadUserSecret` | `POST` | `{{gatewayUrl}}` | `12002` | 是 | `src/api/opt/index.ts` |
| `getUserSecretMeta` | `POST` | `{{gatewayUrl}}` | `12003` | 是 | `src/api/opt/index.ts` |
| `listUserSecretDevices` | `POST` | `{{gatewayUrl}}` | `12004` | 是 | `src/api/opt/index.ts` |
| `getUserOtpCode` | `POST` | `{{gatewayUrl}}` | `12005` | 是 | `src/api/opt/index.ts` |

## 接口明细

### 生成 OTP Secret

- 接口名称：`generateOtpSecret`
- 接口描述：按 username 生成或获取当前有效 OTP secret。
- 请求地址：`{{controlNodeBaseUrl}}/otp/generate_secret`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/otp/generate_secret`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`, `username`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "username": "{{username}}",
  "serverSecretVersion": 1
}
```

#### 响应示例


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

### 校验 OTP Code

- 接口名称：`verifyOtpCode`
- 接口描述：校验 username 对应的 OTP 动态码。
- 请求地址：`{{controlNodeBaseUrl}}/otp/verify`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/otp/verify`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`, `otpCode`, `username`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "username": "{{username}}",
  "otp_code": "{{otpCode}}"
}
```

#### 响应示例


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

### 上传用户 Secret

- 接口名称：`uploadUserSecret`
- 接口描述：上传当前用户在当前设备上的 secret。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`12002`
- 网关说明：网关分发指令，CommandId.UploadUserSecret = 12002
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `hwid`, `otpSecret`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `12002` | 网关分发指令，CommandId.UploadUserSecret = 12002 |

#### 请求体


```json
{
  "secret": "{{otpSecret}}",
  "hwid": "{{hwid}}",
  "secretVersion": 1
}
```

#### 响应示例


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

### 查询用户 Secret 元信息

- 接口名称：`getUserSecretMeta`
- 接口描述：查询当前用户在指定设备上的服务端 secret 版本信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`12003`
- 网关说明：网关分发指令，CommandId.GetUserSecretMeta = 12003
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `hwid`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `12003` | 网关分发指令，CommandId.GetUserSecretMeta = 12003 |

#### 请求体


```json
{
  "hwid": "{{hwid}}"
}
```

#### 响应示例


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

### 列出 Secret 绑定设备

- 接口名称：`listUserSecretDevices`
- 接口描述：列出当前用户服务端已绑定设备，不返回原始 hwid。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`12004`
- 网关说明：网关分发指令，CommandId.ListUserSecretDevices = 12004
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `command` | `12004` | 网关分发指令，CommandId.ListUserSecretDevices = 12004 |

#### 请求体

无

#### 响应示例


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

### 获取用户 OTP Code

- 接口名称：`getUserOtpCode`
- 接口描述：按当前用户和设备 hwid 获取对应 secret 生成的当前 OTP 动态码。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`12005`
- 网关说明：网关分发指令，CommandId.GetUserOTPCode = 12005
- 代码来源：`src/api/opt/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `hwid`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `12005` | 网关分发指令，CommandId.GetUserOTPCode = 12005 |

#### 请求体


```json
{
  "hwid": "{{hwid}}"
}
```

#### 响应示例


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
