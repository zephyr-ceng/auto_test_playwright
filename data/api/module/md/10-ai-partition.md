# AI 分割

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

启动 AI 分割任务、查询任务状态和牙尖异常分析。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `starAiPartition` | `POST` | `{{gatewayUrl}}` | `17001` | 是 | `src/api/partition/index.ts` |
| `getAiPartitionStatus` | `POST` | `{{gatewayUrl}}` | `17002` | 是 | `src/api/partition/index.ts` |
| `getExpByToothCusp` | `POST` | `{{gatewayUrl}}` | `17003` | 是 | `src/api/partition/index.ts` |

## 接口明细

### 启动 AI 分割

- 接口名称：`starAiPartition`
- 接口描述：启动指定 taskType 的 AI 分割任务。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`17001`
- 网关说明：网关分发指令，CommandId.StarAiPartion = 17001
- 代码来源：`src/api/partition/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `17001` | 网关分发指令，CommandId.StarAiPartion = 17001 |

#### 请求体


```json
{
  "surgicalDesignID": "{{designId}}",
  "taskType": "dentalsegment",
  "nextTaskType": "dentalarch"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "taskID": "task-id"
  },
  "message": "success"
}
```

### 查询 AI 分割状态

- 接口名称：`getAiPartitionStatus`
- 接口描述：查询 AI 分割任务状态和结果数据。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`17002`
- 网关说明：网关分发指令，CommandId.QueryAiPartitionResult = 17002
- 代码来源：`src/api/partition/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`gatewayUrl`, `taskId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `17002` | 网关分发指令，CommandId.QueryAiPartitionResult = 17002 |

#### 请求体


```json
{
  "taskID": "{{taskId}}",
  "parameters": {}
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "taskID": "task-id",
    "status": "COMPLETED",
    "data": "result-file-key"
  },
  "message": "success"
}
```

### 牙尖异常分析

- 接口名称：`getExpByToothCusp`
- 接口描述：获取牙尖点异常分析任务。
- 请求地址：`{{gatewayUrl}}`
- 本地解析地址：`http://localhost:3000/tars/v1/gateway`
- 请求方式：`POST`
- 是否需要登录态：是
- 网关 command：`17003`
- 网关说明：网关分发指令，CommandId.ExpByToothCusp = 17003
- 代码来源：`src/api/partition/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `gatewayUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |
| `command` | `17003` | 网关分发指令，CommandId.ExpByToothCusp = 17003 |

#### 请求体


```json
{
  "surgicalDesignID": "{{designId}}",
  "taskType": "dentalcusp"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "taskID": "task-id"
  },
  "message": "success"
}
```
