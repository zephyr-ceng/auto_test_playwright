# ROS 与导航

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

ROS HTTP 接口、模型文件同步、JPEG 流、灯光控制和眼镜升级。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getMarkersList` | `GET` | `{{rosBaseUrl}}/get_markers_list` | - | 是 | `src/api/ros/index.ts` |
| `setMarker` | `POST` | `{{rosBaseUrl}}/set_marker` | - | 是 | `src/api/ros/index.ts` |
| `getUserConfigRos` | `GET` | `{{rosBaseUrl}}/get_user_config?user_id={{userId}}` | - | 是 | `src/api/ros/index.ts` |
| `saveUserConfigRos` | `POST` | `{{rosBaseUrl}}/save_user_config` | - | 是 | `src/api/ros/index.ts` |
| `upLoadFile` | `POST` | `{{rosBaseUrl}}/upload_model_file?id={{designId}}` | - | 是 | `src/api/ros/index.ts` |
| `setModelFile` | `POST` | `{{rosBaseUrl}}/set_model_file` | - | 是 | `src/api/ros/index.ts` |
| `downLoadFile` | `GET` | `{{rosBaseUrl}}/download_model_file?id={{designId}}&filename={{filename}}` | - | 是 | `src/api/ros/index.ts` |
| `checkMrVersion` | `GET` | `{{rosBaseUrl}}/check_mr_version` | - | 是 | `src/api/ros/index.ts` |
| `upgradeMrVersion` | `POST` | `{{rosBaseUrl}}/update_mr_version` | - | 是 | `src/api/ros/index.ts` |
| `jpegStreamStop` | `GET` | `{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}` | - | 是 | `src/api/ros/index.ts` |
| `setDesignContent` | `POST` | `{{rosBaseUrl}}/set_design_content` | - | 是 | `src/api/ros/index.ts` |
| `closeLampApi` | `GET` | `{{rosBaseUrl}}/close_lamp` | - | 是 | `src/api/ros/index.ts` |
| `getTowerStatus` | `GET` | `{{rosBaseUrl}}/tower/status` | - | 是 | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |
| `getJpegStreamStatus` | `GET` | `{{rosBaseUrl}}/jpeg_stream/status` | - | 是 | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |
| `stopJpegStream` | `GET` | `{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}` | - | 是 | `src/v2/page/ScreenSharingPage/compoment/util/index.ts` |

## 接口明细

### 获取 Marker 列表

- 接口名称：`getMarkersList`
- 接口描述：获取当前和可选 Marker 序列号列表。
- 请求地址：`{{rosBaseUrl}}/get_markers_list`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/get_markers_list`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "currentBoardMarker": "board-1",
  "currentJawMarker": "jaw-1",
  "currentHandpieceMarker": "handpiece-1",
  "currentPlaceMarker": "place-1",
  "currentCutMarker": "cut-1",
  "boardMarkerList": [],
  "jawMarkerList": [],
  "handpieceMarkerList": [],
  "placeMarkerList": [],
  "cutMarkerList": []
}
```

### 设置 Marker

- 接口名称：`setMarker`
- 接口描述：设置某类 Marker 的序列号。
- 请求地址：`{{rosBaseUrl}}/set_marker`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/set_marker`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "markerType": "boardMarker",
  "markerSerialNumber": "marker-sn"
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

### ROS 读取用户配置

- 接口名称：`getUserConfigRos`
- 接口描述：从 ROS 节点读取用户配置。
- 请求地址：`{{rosBaseUrl}}/get_user_config?user_id={{userId}}`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/get_user_config?user_id=1`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`, `userId`

#### 请求头

无

#### 请求体

无

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

### ROS 保存用户配置

- 接口名称：`saveUserConfigRos`
- 接口描述：向 ROS 节点保存用户配置。
- 请求地址：`{{rosBaseUrl}}/save_user_config`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/save_user_config`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`, `userId`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "user_id": "{{userId}}",
  "configs": [
    {
      "key": "key",
      "value": "1"
    }
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

### 上传导航模型文件

- 接口名称：`upLoadFile`
- 接口描述：multipart/form-data 上传多个模型文件，query id 为设计 ID。
- 请求地址：`{{rosBaseUrl}}/upload_model_file?id={{designId}}`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/upload_model_file?id={{designId}}`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `rosBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `multipart/form-data` | 由 FormData 生成 |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `files` | `file` | `` | ["<File>"] |
| `id` | `string` | `{{designId}}` | - |

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 设置模型文件

- 接口名称：`setModelFile`
- 接口描述：multipart/form-data 增量上传模型文件。
- 请求地址：`{{rosBaseUrl}}/set_model_file`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/set_model_file`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `multipart/form-data` | 由 FormData 生成 |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `files` | `file` | `` | ["<File>"] |

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 下载导航模型文件

- 接口名称：`downLoadFile`
- 接口描述：按设计 ID 和文件名下载模型文件，返回 Blob。
- 请求地址：`{{rosBaseUrl}}/download_model_file?id={{designId}}&filename={{filename}}`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/download_model_file?id={{designId}}&filename=model.stl`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：有
- 后置断言/提取：有
- 关联变量：`designId`, `filename`, `rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例

`<Blob>`

### 检查 MR 版本

- 接口名称：`checkMrVersion`
- 接口描述：检查连接眼镜版本兼容性。
- 请求地址：`{{rosBaseUrl}}/check_mr_version`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/check_mr_version`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "minCompatibleVersion": "1.0.0",
    "connectMRs": []
  },
  "message": "success"
}
```

### 升级 MR 版本

- 接口名称：`upgradeMrVersion`
- 接口描述：按眼镜 IP 触发升级。
- 请求地址：`{{rosBaseUrl}}/update_mr_version`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/update_mr_version`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "ip": "192.168.0.60"
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

### 停止 JPEG 流

- 接口名称：`jpegStreamStop`
- 接口描述：按 stream_id 停止 JPEG 图片流。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/jpeg_stream/stop?stream_id=1710000000000`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`, `streamId`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 设置设计 Content

- 接口名称：`setDesignContent`
- 接口描述：向 ROS 节点设置当前手术设计 content。
- 请求地址：`{{rosBaseUrl}}/set_design_content`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/set_design_content`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
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

### 关闭无影灯

- 接口名称：`closeLampApi`
- 接口描述：关闭无影灯。
- 请求地址：`{{rosBaseUrl}}/close_lamp`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/close_lamp`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/ros/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{
  "code": 0,
  "data": {},
  "message": "success"
}
```

### 获取塔台状态

- 接口名称：`getTowerStatus`
- 接口描述：按设备 IP 动态创建 ROS HTTP client 后获取塔台状态。
- 请求地址：`{{rosBaseUrl}}/tower/status`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/tower/status`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{}
```

### 获取 JPEG 流状态

- 接口名称：`getJpegStreamStatus`
- 接口描述：查询 JPEG 流状态。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/status`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/jpeg_stream/status`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{}
```

### 按设备 IP 停止 JPEG 流

- 接口名称：`stopJpegStream`
- 接口描述：使用动态设备 IP 停止 JPEG 流。
- 请求地址：`{{rosBaseUrl}}/jpeg_stream/stop?stream_id={{streamId}}`
- 本地解析地址：`http://192.168.0.52:38081/ros_api/v1/jpeg_stream/stop?stream_id=1710000000000`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/v2/page/ScreenSharingPage/compoment/util/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`rosBaseUrl`, `streamId`

#### 请求头

无

#### 请求体

无

#### 响应示例


```json
{}
```
