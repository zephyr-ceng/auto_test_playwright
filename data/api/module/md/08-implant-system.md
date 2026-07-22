# 植体系统

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

植体系统配置和收藏管理。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getImplantSystemAPI` | `GET` | `{{controlNodeBaseUrl}}/implant_system` | - | 是 | `src/api/implant/index.ts` |
| `getImplantFavorites` | `POST` | `{{gatewayUrl}}` | `18004` | 是 | `src/api/implant/index.ts` |
| `addImplantFavorite` | `POST` | `{{gatewayUrl}}` | `18005` | 是 | `src/api/implant/index.ts` |
| `deleteImplantFavorite` | `POST` | `{{gatewayUrl}}` | `18006` | 是 | `src/api/implant/index.ts` |

## 接口明细

### 获取植体系统列表

- 接口名称：`getImplantSystemAPI`
- 接口描述：获取本地植体/钻针系统配置。
- 请求地址：`{{controlNodeBaseUrl}}/implant_system`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/implant_system`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/implant/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


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

### 获取植体收藏

- 接口名称：`getImplantFavorites`
- 接口描述：获取当前用户收藏的植体类型。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`18004`
- 网关说明：网关分发指令，CommandId.GetImplantFavorites = 18004
- 代码来源：`src/api/implant/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `command` | `18004` | 网关分发指令，CommandId.GetImplantFavorites = 18004 |

#### 请求体

无

#### 响应示例


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

### 新增植体收藏

- 接口名称：`addImplantFavorite`
- 接口描述：收藏指定植体类型。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`18005`
- 网关说明：网关分发指令，CommandId.AddImplantFavorite = 18005
- 代码来源：`src/api/implant/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `18005` | 网关分发指令，CommandId.AddImplantFavorite = 18005 |

#### 请求体


```json
{
  "type": "implant-type"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": true,
  "message": "success"
}
```

### 取消植体收藏

- 接口名称：`deleteImplantFavorite`
- 接口描述：取消收藏指定植体类型。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`18006`
- 网关说明：网关分发指令，CommandId.DeleteImplantFavorite = 18006
- 代码来源：`src/api/implant/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `18006` | 网关分发指令，CommandId.DeleteImplantFavorite = 18006 |

#### 请求体


```json
{
  "type": "implant-type"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": true,
  "message": "success"
}
```
