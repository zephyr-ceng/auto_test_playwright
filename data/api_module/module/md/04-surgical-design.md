# 手术设计

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

设计列表、创建、修改、详情、开始和结束手术。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `querySurgicalDesign` | `POST` | `{{gatewayUrl}}` | `14001` | 是 | `src/api/design/index.ts` |
| `addDesign` | `POST` | `{{gatewayUrl}}` | `14002` | 是 | `src/api/design/index.ts` |
| `addDesignV2` | `POST` | `{{gatewayUrl}}` | `14002` | 是 | `src/api/design/index.ts` |
| `changeDesign` | `POST` | `{{gatewayUrl}}` | `14003` | 是 | `src/api/design/index.ts` |
| `navChangeDesign` | `POST` | `{{gatewayUrl}}` | `14009` | 是 | `src/api/design/index.ts` |
| `completeDesign` | `POST` | `{{gatewayUrl}}` | `14004` | 是 | `src/api/design/index.ts` |
| `queryDesignDetail` | `POST` | `{{gatewayUrl}}` | `14005` | 是 | `src/api/design/index.ts` |
| `startSurgical` | `POST` | `{{gatewayUrl}}` | `14006` | 是 | `src/api/design/index.ts` |
| `finishSurgical` | `POST` | `{{gatewayUrl}}` | `14007` | 是 | `src/api/design/index.ts` |
| `getSetting` | `GET` | `{{baseUrl}}/settings` | - | 是 | `src/api/design/index.ts` |
| `delDesign` | `POST` | `{{gatewayUrl}}` | `14008` | 是 | `src/api/design/index.ts` |

## 接口明细

### 查询手术设计列表

- 接口名称：`querySurgicalDesign`
- 接口描述：按患者姓名、设计状态、审批状态分页查询设计列表。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14001`
- 网关说明：网关分发指令，CommandId.QuerySurgicalDesignList = 14001
- 代码来源：`src/api/design/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientName`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14001` | 网关分发指令，CommandId.QuerySurgicalDesignList = 14001 |

#### 请求体


```json
{
  "pageIndex": 1,
  "pageSize": 10,
  "name": "{{patientName}}",
  "status": 1,
  "approveStatus": 1
}
```

#### 响应示例


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

### 创建设计

- 接口名称：`addDesign`
- 接口描述：基于病例创建手术设计。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14002`
- 网关说明：网关分发指令，CommandId.AddSurgicalDesign = 14002
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `fileKey`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14002` | 网关分发指令，CommandId.AddSurgicalDesign = 14002 |

#### 请求体


```json
{
  "medicalRecordID": "{{caseId}}",
  "modelFileKey": "{{fileKey}}"
}
```

#### 响应示例


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

### 创建设计 V2

- 接口名称：`addDesignV2`
- 接口描述：当前实现与 addDesign 相同，保留为调用入口。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14002`
- 网关说明：网关分发指令，CommandId.AddSurgicalDesign = 14002
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `fileKey`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14002` | 网关分发指令，CommandId.AddSurgicalDesign = 14002 |

#### 请求体


```json
{
  "medicalRecordID": "{{caseId}}",
  "modelFileKey": "{{fileKey}}"
}
```

#### 响应示例


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

### 修改设计文件

- 接口名称：`changeDesign`
- 接口描述：保存设计内容、缩略图、模型文件和版本信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14003`
- 网关说明：网关分发指令，CommandId.UpdateSurgicalDesign = 14003
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `fileKey`, `gatewayUrl`, `thumbnailFileKey`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14003` | 网关分发指令，CommandId.UpdateSurgicalDesign = 14003 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "version": 1
  },
  "message": "success"
}
```

### 导航页修改设计文件

- 接口名称：`navChangeDesign`
- 接口描述：导航页保存设计内容，使用独立 Command。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14009`
- 网关说明：网关分发指令，CommandId.NavSurgicalDesign = 14009
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14009` | 网关分发指令，CommandId.NavSurgicalDesign = 14009 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "version": 1
  },
  "message": "success"
}
```

### 完成手术设计

- 接口名称：`completeDesign`
- 接口描述：提交设计内容并标记设计完成。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14004`
- 网关说明：网关分发指令，CommandId.CompleteSurgicalDesign = 14004
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14004` | 网关分发指令，CommandId.CompleteSurgicalDesign = 14004 |

#### 请求体


```json
{
  "surgicalDesignID": "{{designId}}",
  "version": 1,
  "content": "{}"
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

### 查询设计详情

- 接口名称：`queryDesignDetail`
- 接口描述：按 SurgicalDesignID 获取设计详情、患者信息、病例信息和模型文件信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14005`
- 网关说明：网关分发指令，CommandId.QuerySurgicalDesignDetail = 14005
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14005` | 网关分发指令，CommandId.QuerySurgicalDesignDetail = 14005 |

#### 请求体


```json
{
  "SurgicalDesignID": "{{designId}}"
}
```

#### 响应示例


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

### 开始手术

- 接口名称：`startSurgical`
- 接口描述：将设计进入手术中状态并返回设计详情。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14006`
- 网关说明：网关分发指令，CommandId.StartSurgical = 14006
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14006` | 网关分发指令，CommandId.StartSurgical = 14006 |

#### 请求体


```json
{
  "surgicalDesignID": "{{designId}}"
}
```

#### 响应示例


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

### 完成手术

- 接口名称：`finishSurgical`
- 接口描述：提交手术完成信息和偏差信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14007`
- 网关说明：网关分发指令，CommandId.FinishSurgical = 14007
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14007` | 网关分发指令，CommandId.FinishSurgical = 14007 |

#### 请求体


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

#### 响应示例


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

### 获取系统设置

- 接口名称：`getSetting`
- 接口描述：获取帮助课程、钻针配置和功能配置。
- 请求地址：`{{baseUrl}}/settings`
- 本地解析地址：`http://localhost:3000/tars/v1/settings`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/design/index.ts`
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
  "data": {
    "Courses": [],
    "Drills": [],
    "FeatureConfig": {}
  },
  "message": "success"
}
```

### 删除手术设计

- 接口名称：`delDesign`
- 接口描述：按设计 ID 删除设计。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`14008`
- 网关说明：网关分发指令，CommandId.DeleteSurgical = 14008
- 代码来源：`src/api/design/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `14008` | 网关分发指令，CommandId.DeleteSurgical = 14008 |

#### 请求体


```json
{
  "id": "{{designId}}"
}
```

#### 响应示例


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
