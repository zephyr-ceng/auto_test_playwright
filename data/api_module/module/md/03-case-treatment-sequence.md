# 病例与治疗序列

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

病例新增、更新、删除和治疗阶段维护。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `addCase` | `POST` | `{{gatewayUrl}}` | `15001` | 是 | `src/api/case/index.ts` |
| `updateCase` | `POST` | `{{gatewayUrl}}` | `15001` | 是 | `src/api/case/index.ts` |
| `deleteCase` | `POST` | `{{gatewayUrl}}` | `15002` | 是 | `src/api/case/index.ts` |
| `treatmentSequence` | `POST` | `{{gatewayUrl}}` | `15003` | 是 | `src/api/patient/index.ts` |
| `changeTreatmentSequence` | `POST` | `{{gatewayUrl}}` | `15003` | 是 | `src/api/patient/index.ts` |
| `sortTreatmentSequence` | `POST` | `{{gatewayUrl}}` | `15005` | 是 | `src/api/patient/index.ts` |
| `delTreatmentSequence` | `POST` | `{{gatewayUrl}}` | `15004` | 是 | `src/api/patient/index.ts` |

## 接口明细

### 新增病例

- 接口名称：`addCase`
- 接口描述：为患者新增病例记录。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15001`
- 网关说明：网关分发指令，CommandId.AddCase = 15001
- 代码来源：`src/api/case/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`, `patientId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15001` | 网关分发指令，CommandId.AddCase = 15001 |

#### 请求体


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

#### 响应示例


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

### 更新病例

- 接口名称：`updateCase`
- 接口描述：更新病例记录；当前代码同样使用 Command 15001。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15001`
- 网关说明：网关分发指令，CommandId.AddCase = 15001
- 代码来源：`src/api/case/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`, `patientId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15001` | 网关分发指令，CommandId.AddCase = 15001 |

#### 请求体


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

#### 响应示例


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

### 删除病例

- 接口名称：`deleteCase`
- 接口描述：按病例 ID 删除病例。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15002`
- 网关说明：网关分发指令，CommandId.DelCase = 15002
- 代码来源：`src/api/case/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15002` | 网关分发指令，CommandId.DelCase = 15002 |

#### 请求体


```json
{
  "id": "{{caseId}}"
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

### 新增治疗阶段

- 接口名称：`treatmentSequence`
- 接口描述：添加治疗阶段或治疗方案节点。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15003`
- 网关说明：网关分发指令，CommandId.TreatmentSequence = 15003
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15003` | 网关分发指令，CommandId.TreatmentSequence = 15003 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "id": "treatment-id"
  },
  "message": "success"
}
```

### 更新治疗阶段

- 接口名称：`changeTreatmentSequence`
- 接口描述：更新治疗阶段名称、日期、描述和状态。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15003`
- 网关说明：网关分发指令，CommandId.TreatmentSequence = 15003
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`, `treatmentId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15003` | 网关分发指令，CommandId.TreatmentSequence = 15003 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 治疗阶段排序

- 接口名称：`sortTreatmentSequence`
- 接口描述：按 treatmentsOrders 调整治疗阶段顺序。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15005`
- 网关说明：网关分发指令，CommandId.sortTreatmentSequence = 15005
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`, `treatmentId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15005` | 网关分发指令，CommandId.sortTreatmentSequence = 15005 |

#### 请求体


```json
{
  "medicalRecordID": "{{caseId}}",
  "treatmentsOrders": [
    "{{treatmentId}}"
  ]
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

### 删除治疗阶段

- 接口名称：`delTreatmentSequence`
- 接口描述：删除某个治疗阶段。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`15004`
- 网关说明：网关分发指令，CommandId.DelTreatmentSequence = 15004
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`caseId`, `gatewayUrl`, `treatmentId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `15004` | 网关分发指令，CommandId.DelTreatmentSequence = 15004 |

#### 请求体


```json
{
  "medicalRecordID": "{{caseId}}",
  "id": "{{treatmentId}}"
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
