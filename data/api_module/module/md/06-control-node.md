# 控制节点

来源：`api-docs/api-build.md`
接口规范版本：`v1.0.0`
项目接口来源：`api-docs/apifox-collection.postman.json`

## 模块说明

本机文件、设备关机重启、版本、导出、录屏和升级。

## 接口总览

| 接口名称 | 请求方式 | 请求地址 | command | 是否鉴权 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `getDirTree` | `POST` | `{{controlNodeBaseUrl}}/get_dir_tree` | - | 是 | `src/api/controlNode/index.ts` |
| `downloadLocalFile` | `POST` | `{{controlNodeBaseUrl}}/download_local_file` | - | 是 | `src/api/controlNode/index.ts` |
| `downloadLocalFileWithProgress` | `POST` | `{{controlNodeBaseUrl}}/download_local_file` | - | 是 | `src/api/controlNode/index.ts` |
| `shutDownApi` | `POST` | `{{controlNodeBaseUrl}}/shutdown` | - | 是 | `src/api/controlNode/index.ts` |
| `rebootApi` | `POST` | `{{controlNodeBaseUrl}}/reboot` | - | 是 | `src/api/controlNode/index.ts` |
| `getCurrentWifi` | `GET` | `{{controlNodeBaseUrl}}/wifi_info` | - | 是 | `src/api/controlNode/index.ts` |
| `getControlNodeHealthCheck` | `GET` | `{{controlNodeBaseUrl}}/ping` | - | 是 | `src/api/controlNode/index.ts` |
| `exportFileToMobileDrive` | `POST` | `{{controlNodeBaseUrl}}/put_caldata` | - | 是 | `src/api/controlNode/index.ts` |
| `getVersionInfo` | `GET` | `{{controlNodeBaseUrl}}/version` | - | 是 | `src/api/controlNode/index.ts` |
| `getFileList` | `GET` | `{{controlNodeBaseUrl}}/file_list` | - | 是 | `src/api/controlNode/index.ts` |
| `exportFile` | `POST` | `{{controlNodeBaseUrl}}/export_local` | - | 是 | `src/api/controlNode/index.ts` |
| `getExportStatus` | `POST` | `{{controlNodeBaseUrl}}/export_status` | - | 是 | `src/api/controlNode/index.ts` |
| `deleteFile` | `POST` | `{{controlNodeBaseUrl}}/delete_file` | - | 是 | `src/api/controlNode/index.ts` |
| `startScreenRecord` | `POST` | `{{controlNodeBaseUrl}}/task/start` | - | 是 | `src/api/controlNode/index.ts` |
| `stopScreenRecord` | `POST` | `{{controlNodeBaseUrl}}/task/stop` | - | 是 | `src/api/controlNode/index.ts` |
| `getScreenRecordStatus` | `POST` | `{{controlNodeBaseUrl}}/task/status` | - | 是 | `src/api/controlNode/index.ts` |
| `getUpgradeStatus` | `GET` | `{{controlNodeBaseUrl}}/upgrade_status` | - | 是 | `src/api/controlNode/index.ts` |
| `startUpgrade` | `POST` | `{{controlNodeBaseUrl}}/start_upgrade` | - | 是 | `src/api/controlNode/index.ts` |
| `setUpgrade` | `POST` | `{{controlNodeBaseUrl}}/set_upgrade` | - | 是 | `src/api/controlNode/index.ts` |

## 接口明细

### 获取目录树

- 接口名称：`getDirTree`
- 接口描述：按路径和后缀过滤查询控制节点目录树。
- 请求地址：`{{controlNodeBaseUrl}}/get_dir_tree`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/get_dir_tree`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "path": "/data",
  "fileFilter": [
    "stl",
    "dcm"
  ]
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "IsDir": true,
    "Name": "data",
    "Path": "/data",
    "Child": []
  },
  "message": "success"
}
```

### 下载本地文件

- 接口名称：`downloadLocalFile`
- 接口描述：从控制节点下载本地文件，返回 Blob。
- 请求地址：`{{controlNodeBaseUrl}}/download_local_file`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/download_local_file`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "filePath": "/data/model.stl"
}
```

#### 响应示例

`<Blob>`

### 下载本地文件并上报进度

- 接口名称：`downloadLocalFileWithProgress`
- 接口描述：同下载本地文件，前端额外监听下载进度。
- 请求地址：`{{controlNodeBaseUrl}}/download_local_file`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/download_local_file`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "filePath": "/data/model.stl"
}
```

#### 响应示例

`<Blob>`

### 关机

- 接口名称：`shutDownApi`
- 接口描述：关闭控制节点设备。
- 请求地址：`{{controlNodeBaseUrl}}/shutdown`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/shutdown`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": null,
  "message": "success"
}
```

### 重启

- 接口名称：`rebootApi`
- 接口描述：重启控制节点设备。
- 请求地址：`{{controlNodeBaseUrl}}/reboot`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/reboot`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": null,
  "message": "success"
}
```

### 获取当前 Wi-Fi

- 接口名称：`getCurrentWifi`
- 接口描述：获取当前连接 Wi-Fi、密码和控制节点 IP。
- 请求地址：`{{controlNodeBaseUrl}}/wifi_info`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/wifi_info`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": {
    "ssid": "wifi-name",
    "password": "wifi-password",
    "ip": "192.168.0.52"
  },
  "message": "success"
}
```

### 控制节点健康检查

- 接口名称：`getControlNodeHealthCheck`
- 接口描述：控制节点 ping 检查，返回 hwid。
- 请求地址：`{{controlNodeBaseUrl}}/ping`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/ping`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": {
    "hwid": "control-node-hwid"
  },
  "message": "success"
}
```

### 导出文件到移动盘

- 接口名称：`exportFileToMobileDrive`
- 接口描述：multipart/form-data 上传并写入指定路径。
- 请求地址：`{{controlNodeBaseUrl}}/put_caldata`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/put_caldata`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `multipart/form-data` | 由 FormData 生成 |

#### 请求体

| 字段 | 类型 | 示例值 | 说明 |
| --- | --- | --- | --- |
| `fileName` | `string` | `model.stl` | - |
| `file` | `file` | `<File>` | - |
| `path` | `string` | `/usb` | - |

#### 响应示例


```json
{
  "code": 0,
  "data": null,
  "message": "success"
}
```

### 获取版本信息

- 接口名称：`getVersionInfo`
- 接口描述：获取当前版本、下一版本和升级开关。
- 请求地址：`{{controlNodeBaseUrl}}/version`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/version`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "fullVersion": "1.0.0",
  "majorVersion": "1",
  "changeNotes": "",
  "nextVersion": "1.0.1",
  "autoUpgrade": true,
  "hwid": "control-node-hwid"
}
```

### 获取本地文件列表

- 接口名称：`getFileList`
- 接口描述：获取设计文件、录屏文件和磁盘空间。
- 请求地址：`{{controlNodeBaseUrl}}/file_list`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/file_list`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": {
    "design_files": [],
    "screen_files": [],
    "total_available_space": "10GB",
    "total_used_space": "1GB"
  },
  "message": "success"
}
```

### 导出本地文件

- 接口名称：`exportFile`
- 接口描述：将本地文件导出到指定路径。
- 请求地址：`{{controlNodeBaseUrl}}/export_local`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/export_local`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "fileName": "model.stl",
  "exportPath": "/usb",
  "localPath": "/data/model.stl"
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

### 查询导出状态

- 接口名称：`getExportStatus`
- 接口描述：按本地路径查询导出进度。
- 请求地址：`{{controlNodeBaseUrl}}/export_status`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/export_status`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "localPath": "/data/model.stl"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "fileName": "model.stl",
    "progress": 50,
    "status": "running"
  },
  "message": "success"
}
```

### 删除本地文件

- 接口名称：`deleteFile`
- 接口描述：按路径删除控制节点本地文件。
- 请求地址：`{{controlNodeBaseUrl}}/delete_file`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/delete_file`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "path": "/data/model.stl"
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

### 开始录屏

- 接口名称：`startScreenRecord`
- 接口描述：启动指定录屏任务。
- 请求地址：`{{controlNodeBaseUrl}}/task/start`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/task/start`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "taskName": "screen-record"
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

### 停止录屏

- 接口名称：`stopScreenRecord`
- 接口描述：停止指定录屏任务。
- 请求地址：`{{controlNodeBaseUrl}}/task/stop`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/task/stop`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "taskName": "screen-record"
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

### 查询录屏状态

- 接口名称：`getScreenRecordStatus`
- 接口描述：查询指定录屏任务是否运行中。
- 请求地址：`{{controlNodeBaseUrl}}/task/status`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/task/status`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "taskName": "screen-record"
}
```

#### 响应示例


```json
{
  "code": 0,
  "data": {
    "isActive": true
  },
  "message": "success"
}
```

### 获取升级状态

- 接口名称：`getUpgradeStatus`
- 接口描述：获取软件升级进度和目标版本。
- 请求地址：`{{controlNodeBaseUrl}}/upgrade_status`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/upgrade_status`
- 请求方式：`GET`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": {
    "progress": 0,
    "status": 0,
    "version": "1.0.1"
  },
  "message": "success"
}
```

### 开始升级

- 接口名称：`startUpgrade`
- 接口描述：触发控制节点升级。
- 请求地址：`{{controlNodeBaseUrl}}/start_upgrade`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/start_upgrade`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
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
  "data": null,
  "message": "success"
}
```

### 设置自动升级

- 接口名称：`setUpgrade`
- 接口描述：开启或关闭自动升级。
- 请求地址：`{{controlNodeBaseUrl}}/set_upgrade`
- 本地解析地址：`http://192.168.0.52:38080/tars/v1/set_upgrade`
- 请求方式：`POST`
- 是否需要登录态：是
- 代码来源：`src/api/controlNode/index.ts`
- 前置脚本：无
- 后置断言/提取：有
- 关联变量：`controlNodeBaseUrl`

#### 请求头

| Header | 示例值 | 说明 |
| --- | --- | --- |
| `Content-Type` | `application/json` | JSON 请求体 |

#### 请求体


```json
{
  "autoUpgrade": true
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
