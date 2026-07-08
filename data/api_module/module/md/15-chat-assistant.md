# 聊天与助手

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

聊天补全流式接口和全局助手 SSE。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `addChat` | `POST` | `{{chatBaseUrl}}/bots/chat/completions` | - | 是 | `src/api/chat/index.ts` |
| `fetchEventSourceChatCompletions` | `POST` | `{{baseUrl}}/chat_completions` | - | 是 | `src/layout/GlobalWin/index.tsx` |

## 接口明细

### 聊天补全流

- 接口名称：`addChat`
- 接口描述：调用聊天节点 /api/v3/bots/chat/completions，返回 stream。
- 请求地址：`{{chatBaseUrl}}/bots/chat/completions`
- 本地解析地址：`http://192.168.2.159:9999/api/v3/bots/chat/completions`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/chat/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`chatBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "model": "test",
  "messages": [
    {
      "role": "user",
      "content": "你好"
    }
  ],
  "stream": true,
  "patients_info": [],
  "machine_info": {
    "lamp_brightness": 50
  },
  "cur_patients_info": null
}
```

#### 响应示例


```json
{
  "choices": [
    {
      "delta": {
        "content": "你好"
      },
      "finish_reason": null
    }
  ]
}
```

### 全局助手 SSE

- 接口名称：`fetchEventSourceChatCompletions`
- 接口描述：全局助手使用 fetchEventSource 请求 /tars/v1/chat_completions，响应 text/event-stream。
- 请求地址：`{{baseUrl}}/chat_completions`
- 本地解析地址：`http://localhost:3000/tars/v1/chat_completions`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/layout/GlobalWin/index.tsx`
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
  "model": "test",
  "stream": true,
  "metadata": {
    "patients_info": [],
    "cur_patient_info": null,
    "machine_info": {
      "lamp_brightness": 50
    },
    "is_audio": true
  },
  "messages": [
    {
      "role": "user",
      "content": "调亮无影灯"
    }
  ]
}
```

#### 响应示例

`data: {"choices":[{"delta":{"content":"ok"},"finish_reason":null}]}\n\ndata: [DONE]`
