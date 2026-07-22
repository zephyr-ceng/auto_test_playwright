# 登录认证

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

登录、登出、短信验证码、密码重置和当前用户信息。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `loginByUserName` | `POST` | `{{baseUrl}}/login_by_username` | - | 否 | `src/api/login/index.ts` |
| `logout` | `POST` | `{{baseUrl}}/logout` | - | 是 | `src/api/login/index.ts` |
| `loginByTel` | `POST` | `{{baseUrl}}/login_by_telephone` | - | 是 | `src/api/login/index.ts` |
| `sendSMS` | `POST` | `{{baseUrl}}/send_sms` | - | 否 | `src/api/login/index.ts` |
| `resetPassword` | `POST` | `{{baseUrl}}/reset_password` | - | 是 | `src/api/login/index.ts` |
| `getUserInfo` | `POST` | `{{gatewayUrl}}` | `16001` | 是 | `src/api/login/index.ts` |

## 接口明细

### 用户名密码登录

- 接口名称：`loginByUserName`
- 接口描述：使用 username/password 登录，可通过 returnToken 要求后端返回 token。
- 请求地址：`{{baseUrl}}/login_by_username`
- 本地解析地址：`http://localhost:3000/tars/v1/login_by_username`
- 请求方式：`POST`
- 是否需要登录态：否
- 代码来源：`src/api/login/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`baseUrl`, `password`, `username`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "username": "{{username}}",
  "password": "{{password}}",
  "returnToken": false
}
```

#### 响应示例


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

### 登出

- 接口名称：`logout`
- 接口描述：退出当前登录会话。
- 请求地址：`{{baseUrl}}/logout`
- 本地解析地址：`http://localhost:3000/tars/v1/logout`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/login/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`baseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "message": "success"
}
```

### 手机号验证码登录

- 接口名称：`loginByTel`
- 接口描述：使用 telephone/code 登录，可通过 returnToken 要求后端返回 token。
- 请求地址：`{{baseUrl}}/login_by_telephone`
- 本地解析地址：`http://localhost:3000/tars/v1/login_by_telephone`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/login/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`baseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "telephone": "13800138000",
  "code": "123456",
  "returnToken": true
}
```

#### 响应示例


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

### 发送短信验证码

- 接口名称：`sendSMS`
- 接口描述：发送登录或重置密码短信验证码。
- 请求地址：`{{baseUrl}}/send_sms`
- 本地解析地址：`http://localhost:3000/tars/v1/send_sms`
- 请求方式：`POST`
- 是否需要登录态：否
- 代码来源：`src/api/login/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`baseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "telephone": "13800138000",
  "type": "login"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": "sms-id-or-message",
  "message": "success"
}
```

### 重置密码

- 接口名称：`resetPassword`
- 接口描述：通过手机号验证码重置密码。
- 请求地址：`{{baseUrl}}/reset_password`
- 本地解析地址：`http://localhost:3000/tars/v1/reset_password`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/login/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`baseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "telephone": "13800138000",
  "code": "123456",
  "newPassword": "new-password"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": "ok",
  "message": "success"
}
```

### 获取当前用户信息

- 接口名称：`getUserInfo`
- 接口描述：通过网关 Command 获取当前登录用户信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`16001`
- 网关说明：网关分发指令，CommandId.GetUserInfo = 16001
- 代码来源：`src/api/login/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `command` | `16001` | 网关分发指令，CommandId.GetUserInfo = 16001 |

#### 请求体

无

#### 响应示例


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
