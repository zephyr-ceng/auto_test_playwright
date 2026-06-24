# 积分

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

积分总览、明细和提醒列表。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getPointSummary` | `POST` | `{{gatewayUrl}}` | `20002` | 是 | `src/api/points/index.ts` |
| `getPointDetails` | `POST` | `{{gatewayUrl}}` | `20003` | 是 | `src/api/points/index.ts` |
| `getPointRemind` | `POST` | `{{gatewayUrl}}` | `20004` | 是 | `src/api/points/index.ts` |

## 接口明细

### 获取积分总览

- 接口名称：`getPointSummary`
- 接口描述：获取个人、租户、手术和冻结积分。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`20002`
- 网关说明：网关分发指令，CommandId.GetPointSummary = 20002
- 代码来源：`src/api/points/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `tenantId`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `20002` | 网关分发指令，CommandId.GetPointSummary = 20002 |

#### 请求体


```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}"
}
```

#### 响应示例


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

### 获取积分明细

- 接口名称：`getPointDetails`
- 接口描述：分页查询积分明细，可按状态过滤。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`20003`
- 网关说明：网关分发指令，CommandId.GetPointDetails = 20003
- 代码来源：`src/api/points/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `tenantId`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `20003` | 网关分发指令，CommandId.GetPointDetails = 20003 |

#### 请求体


```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}",
  "filterStatus": 1,
  "page": 1,
  "pageSize": 10
}
```

#### 响应示例


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

### 获取积分提醒

- 接口名称：`getPointRemind`
- 接口描述：分页查询积分提醒消息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`20004`
- 网关说明：网关分发指令，CommandId.GetPointRemind = 20004
- 代码来源：`src/api/points/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `tenantId`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `20004` | 网关分发指令，CommandId.GetPointRemind = 20004 |

#### 请求体


```json
{
  "userId": "{{userId}}",
  "tenantId": "{{tenantId}}",
  "page": 1,
  "pageSize": 10
}
```

#### 响应示例


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
