# 系统消息与设备

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

系统消息列表、已读、删除和设备列表。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `searchMessage` | `POST` | `{{gatewayUrl}}` | `19001` | 是 | `src/api/systemMessage/index.ts` |
| `deleteMessage` | `POST` | `{{gatewayUrl}}` | `19003` | 是 | `src/api/systemMessage/index.ts` |
| `readMessage` | `POST` | `{{gatewayUrl}}` | `19002` | 是 | `src/api/systemMessage/index.ts` |
| `getDeviceList` | `POST` | `{{gatewayUrl}}` | `20001` | 是 | `src/api/systemMessage/index.ts` |

## 接口明细

### 查询系统消息

- 接口名称：`searchMessage`
- 接口描述：分页查询系统消息、未读数和总数。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`19001`
- 网关说明：网关分发指令，CommandId.getMessage = 19001
- 代码来源：`src/api/systemMessage/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `19001` | 网关分发指令，CommandId.getMessage = 19001 |

#### 请求体


```json
{
  "pageSize": 10,
  "current": 1
}
```

#### 响应示例


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

### 删除系统消息

- 接口名称：`deleteMessage`
- 接口描述：按消息 ID 删除；id 可选时由后端决定批量/全部行为。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`19003`
- 网关说明：网关分发指令，CommandId.deleteMessage = 19003
- 代码来源：`src/api/systemMessage/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `messageId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `19003` | 网关分发指令，CommandId.deleteMessage = 19003 |

#### 请求体


```json
{
  "id": "{{messageId}}"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 标记系统消息已读

- 接口名称：`readMessage`
- 接口描述：按消息 ID 标记已读；id 可选时由后端决定批量/全部行为。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`19002`
- 网关说明：网关分发指令，CommandId.readMessage = 19002
- 代码来源：`src/api/systemMessage/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `messageId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `19002` | 网关分发指令，CommandId.readMessage = 19002 |

#### 请求体


```json
{
  "id": "{{messageId}}"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 获取设备列表

- 接口名称：`getDeviceList`
- 接口描述：获取已发现或已登记设备。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`20001`
- 网关说明：网关分发指令，CommandId.GetDeviceList = 20001
- 代码来源：`src/api/systemMessage/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `command` | `20001` | 网关分发指令，CommandId.GetDeviceList = 20001 |

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "devices": []
  },
  "message": "success"
}
```
