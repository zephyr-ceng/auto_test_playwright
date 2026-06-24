# 患者管理

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

患者新增、更新、查询、删除、附件上传和模型文件绑定。

附件补充来源：`api-test/cache/modules/upload_attachment_to_patient.apifox.postman.json`。该附件流程为：登录 -> 查询目标患者 -> 初始化上传 -> 上传分片 -> 完成上传 -> 绑定附件到患者 -> 验证绑定结果；其中登录接口已归属登录鉴权模块，本文件补充患者附件上传与绑定相关接口。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `savePatient` | `POST` | `{{gatewayUrl}}` | `13002` | 是 | `src/api/patient/index.ts` |
| `updatePatient` | `POST` | `{{gatewayUrl}}` | `13003` | 是 | `src/api/patient/index.ts` |
| `queryPatientPage` | `POST` | `{{gatewayUrl}}` | `13001` | 是 | `src/api/patient/index.ts` |
| `delPatient` | `POST` | `{{gatewayUrl}}` | `13004` | 是 | `src/api/patient/index.ts` |
| `startFileUpload` | `POST` | `{{gatewayUrl}}` | `11001` | 是 | `src/api/file/index.ts` |
| `uploadFileChunk` | `POST` | `{{baseUrl}}/upload_part` | - | 是 | `src/api/file/index.ts` |
| `finishFileUpload` | `POST` | `{{gatewayUrl}}` | `11002` | 是 | `src/api/file/index.ts` |
| `bindModelFileToPatient` | `POST` | `{{gatewayUrl}}` | `13005` | 是 | `src/api/patient/index.ts` |
| `unbindModelFileToPatient` | `POST` | `{{gatewayUrl}}` | `13006` | 是 | `src/api/patient/index.ts` |
| `searchPatientDetailsMessageV2` | `POST` | `{{gatewayUrl}}` | `13007` | 是 | `src/api/patient/index.ts` |
| `changeBindFile` | `POST` | `{{gatewayUrl}}` | `13008` | 是 | `src/api/patient/index.ts` |

## 接口明细

### 新增患者

- 接口名称：`savePatient`
- 接口描述：创建患者基础信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13002`
- 网关说明：网关分发指令，CommandId.SavePatient = 13002
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientIdentityCard`, `patientName`, `patientTelephone`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13002` | 网关分发指令，CommandId.SavePatient = 13002 |

#### 请求体


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

#### 响应示例


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

### 更新患者

- 接口名称：`updatePatient`
- 接口描述：更新患者姓名和电话等基础信息。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13003`
- 网关说明：网关分发指令，CommandId.UpdatePatient = 13003
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientId`, `patientIdentityCard`, `patientName`, `patientTelephone`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13003` | 网关分发指令，CommandId.UpdatePatient = 13003 |

#### 请求体


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

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 分页查询患者

- 接口名称：`queryPatientPage`
- 接口描述：按姓名、性别、电话分页查询患者。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13001`
- 网关说明：网关分发指令，CommandId.QueryPatientPage = 13001
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientName`, `patientTelephone`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13001` | 网关分发指令，CommandId.QueryPatientPage = 13001 |

#### 请求体


```json
{
  "pageIndex": 1,
  "pageSize": 10,
  "name": "{{patientName}}",
  "gender": 1,
  "telephone": "{{patientTelephone}}"
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

### 删除患者

- 接口名称：`delPatient`
- 接口描述：按患者 ID 删除患者。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13004`
- 网关说明：网关分发指令，CommandId.DeletePatient = 13004
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13004` | 网关分发指令，CommandId.DeletePatient = 13004 |

#### 请求体


```json
{
  "id": "{{patientId}}"
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

### 初始化附件上传

- 接口名称：`startFileUpload`
- 接口描述：初始化单分片附件上传。`fileSize`、`fileMd5` 默认对应 `data/dicom/wujia/SLZ+000.dcm`；如换文件，需要同步修改 `fileName`、`fileSize`、`fileMd5`。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`11001`
- 网关说明：网关分发指令，CommandId.StartFileChunkUpload = 11001
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileMd5`, `fileName`, `fileSize`, `gatewayUrl`, `partID`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `11001` | 网关分发指令，CommandId.StartFileChunkUpload = 11001 |

#### 请求体


```json
{
  "entryPoint": 1,
  "fileName": "{{fileName}}",
  "fileSize": {{fileSize}},
  "md5": "{{fileMd5}}",
  "frontendOssUpload": false,
  "partsInfo": [
    {
      "partID": {{partID}},
      "partMD5": "{{fileMd5}}",
      "partSize": {{fileSize}}
    }
  ],
  "extra": {
    "files": [
      {
        "filename": "{{fileName}}",
        "offset": 0,
        "length": {{fileSize}}
      }
    ],
    "compressVersion": 0,
    "cryptoVersion": 0
  }
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "fileKey": "file-key"
  },
  "message": "success"
}
```

### 上传附件分片

- 接口名称：`uploadFileChunk`
- 接口描述：上传附件分片，Body 使用 `multipart/form-data`。`content` 字段需选择与 `fileName`、`fileSize`、`fileMd5` 对应的本地 DICOM 文件。
- 请求地址：`{{baseUrl}}/upload_part`
- 本地解析地址：`http://localhost:3000/tars/v1/upload_part`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`baseUrl`, `fileKey`, `partID`, `sessionCookie`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Cookie` | `{{sessionCookie}}` | 登录态 Cookie |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `partID` | `text` | `{{partID}}` | 分片 ID |
| `content` | `file` | `data/dicom/wujia/SLZ+000.dcm` | 与初始化参数对应的 DICOM 文件 |
| `fileKey` | `text` | `{{fileKey}}` | 初始化上传返回的文件 key |

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 完成附件上传

- 接口名称：`finishFileUpload`
- 接口描述：通知服务端所有附件分片已经上传完成。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`11002`
- 网关说明：网关分发指令，CommandId.FinishFileChunkUpload = 11002
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `11002` | 网关分发指令，CommandId.FinishFileChunkUpload = 11002 |

#### 请求体


```json
{
  "fileKey": "{{fileKey}}"
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

### 绑定附件到患者

- 接口名称：`bindModelFileToPatient`
- 接口描述：将已上传附件绑定到 `createDesign` 页面中的患者。不要传 `treatmentID` 空字符串或 `0`；附件模块不传 `treatmentID`。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13005`
- 网关说明：网关分发指令，CommandId.bindModelFile = 13005
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `fileName`, `fileTag`, `fileType`, `gatewayUrl`, `jawType`, `patientID`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13005` | 网关分发指令，CommandId.bindModelFile = 13005 |

#### 请求体


```json
{
  "patientID": "{{patientID}}",
  "fileKey": "{{fileKey}}",
  "tags": [
    "{{fileTag}}"
  ],
  "name": "{{fileName}}",
  "type": "{{fileType}}",
  "params": "{}",
  "jawType": "{{jawType}}"
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

### 解绑患者模型文件

- 接口名称：`unbindModelFileToPatient`
- 接口描述：解除患者与文件的绑定关系。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13006`
- 网关说明：网关分发指令，CommandId.unbindModelFile = 13006
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `gatewayUrl`, `patientID`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13006` | 网关分发指令，CommandId.unbindModelFile = 13006 |

#### 请求体


```json
{
  "patientID": "{{patientID}}",
  "fileKey": "{{fileKey}}"
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

### 查询患者详情 V2

- 接口名称：`searchPatientDetailsMessageV2`
- 接口描述：查询患者详情，固定携带 needFiles 和 needMedicalRecords。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13007`
- 网关说明：网关分发指令，CommandId.SearchPatientV2 = 13007
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `patientID`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13007` | 网关分发指令，CommandId.SearchPatientV2 = 13007 |

#### 请求体


```json
{
  "id": "{{patientID}}",
  "needFiles": true,
  "needMedicalRecords": true
}
```

#### 响应示例


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

### 变更绑定文件

- 接口名称：`changeBindFile`
- 接口描述：变更患者关联文件信息，调用处传入 data，结构以后端约定为准。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`13008`
- 网关说明：网关分发指令，CommandId.ChangeBindFile = 13008
- 代码来源：`src/api/patient/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `gatewayUrl`, `oldFileKey`, `patientID`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `13008` | 网关分发指令，CommandId.ChangeBindFile = 13008 |

#### 请求体


```json
{
  "patientID": "{{patientID}}",
  "oldFileKey": "{{oldFileKey}}",
  "newFileKey": "{{fileKey}}"
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
