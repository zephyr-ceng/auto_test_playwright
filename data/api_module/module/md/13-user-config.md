# 用户配置

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

用户级配置读取和保存。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getUserConfig` | `POST` | `{{gatewayUrl}}` | `18002` | 是 | `src/api/user/index.ts` |
| `saveUserConfig` | `POST` | `{{gatewayUrl}}` | `18003` | 是 | `src/api/user/index.ts` |

## 接口明细

### 读取用户配置

- 接口名称：`getUserConfig`
- 接口描述：按 user_id 读取网关侧用户配置。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`18002`
- 网关说明：网关分发指令，CommandId.getUserConfig = 18002
- 代码来源：`src/api/user/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `18002` | 网关分发指令，CommandId.getUserConfig = 18002 |

#### 请求体


```json
{
  "user_id": "{{userId}}"
}
```

#### 响应示例


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

### 保存用户配置

- 接口名称：`saveUserConfig`
- 接口描述：保存用户配置键值列表。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`18003`
- 网关说明：网关分发指令，CommandId.saveUserConfig = 18003
- 代码来源：`src/api/user/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `18003` | 网关分发指令，CommandId.saveUserConfig = 18003 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```
