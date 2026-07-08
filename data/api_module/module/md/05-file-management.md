# 文件管理

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

文件分片上传、单文件上传、上传完成通知和文件描述查询。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `startFileUpload` | `POST` | `{{gatewayUrl}}` | `11001` | 是 | `src/api/file/index.ts` |
| `uploadFileChunk` | `POST` | `{{baseUrl}}/upload_part` | - | 是 | `src/api/file/index.ts` |
| `notifyFileChunkUploadResult` | `POST` | `{{gatewayUrl}}` | `11003` | 是 | `src/api/file/index.ts` |
| `finishFileUpload` | `POST` | `{{gatewayUrl}}` | `11002` | 是 | `src/api/file/index.ts` |
| `uploadSingleFile` | `POST` | `{{baseUrl}}/upload` | - | 是 | `src/api/file/index.ts` |
| `searchFileDescription` | `POST` | `{{gatewayUrl}}` | `11004` | 是 | `src/api/file/index.ts` |

## 接口明细

### 开始分片上传

- 接口名称：`startFileUpload`
- 接口描述：初始化分片上传，可选择前端直传 OSS/COS。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`11001`
- 网关说明：网关分发指令，CommandId.StartFileChunkUpload = 11001
- 代码来源：`src/api/file/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `11001` | 网关分发指令，CommandId.StartFileChunkUpload = 11001 |

#### 请求体


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

#### 响应示例


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

### 上传分片

- 接口名称：`uploadFileChunk`
- 接口描述：后端中转上传单个分片，multipart/form-data。
- 请求地址：`{{baseUrl}}/upload_part`
- 本地解析地址：`http://localhost:3000/tars/v1/upload_part`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`baseUrl`, `fileKey`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `multipart/form-data` | 由 FormData 生成 |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `partID` | `string` | `1` | - |
| `content` | `file` | `<File>` | - |
| `fileKey` | `string` | `{{fileKey}}` | - |

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 通知分片上传结果

- 接口名称：`notifyFileChunkUploadResult`
- 接口描述：前端直传 OSS/COS 后通知后端单个分片结果。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`11003`
- 网关说明：网关分发指令，CommandId.NotifyFileChunkUploadResult = 11003
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `11003` | 网关分发指令，CommandId.NotifyFileChunkUploadResult = 11003 |

#### 请求体


```json
{
  "fileKey": "{{fileKey}}",
  "partID": 1,
  "cryptoKey": "",
  "cryptoAlgo": 0
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

### 完成分片上传

- 接口名称：`finishFileUpload`
- 接口描述：通知后端所有分片已上传完成。
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

### 上传单文件

- 接口名称：`uploadSingleFile`
- 接口描述：使用 multipart/form-data 上传单个文件。
- 请求地址：`{{baseUrl}}/upload`
- 本地解析地址：`http://localhost:3000/tars/v1/upload`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/file/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`baseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `multipart/form-data` | 由 FormData 生成 |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `fileName` | `string` | `thumbnail.png` | - |
| `fileSize` | `string` | `1024` | - |
| `entryPoint` | `string` | `2` | - |
| `md5` | `string` | `md5` | - |
| `file` | `file` | `<File>` | - |

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 查询文件描述

- 接口名称：`searchFileDescription`
- 接口描述：按 fileKeys 查询文件下载和分片描述。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`11004`
- 网关说明：网关分发指令，CommandId.SearchFileDescription = 11004
- 代码来源：`src/api/file/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`fileKey`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `11004` | 网关分发指令，CommandId.SearchFileDescription = 11004 |

#### 请求体


```json
{
  "fileKeys": [
    "{{fileKey}}"
  ]
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "files": []
  },
  "message": "success"
}
```
